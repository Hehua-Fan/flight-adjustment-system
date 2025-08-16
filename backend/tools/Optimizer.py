#!/usr/bin/env python3
"""
航班调整最优化 - V4.0 (规则分级健壮版)
- 核心动作：变更时刻(延误) / 更换飞机 / 取消航班
- 约束分级：PRIORITY为'MUST'的规则采用刚性约束，其他采用柔性约束
- 目标：最小化动作成本 + 延误成本 + 违反柔性约束的惩罚成本
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import pyomo.environ as pyo

MINUTES_IN_DAY = 24 * 60
MINUTES_IN_TWO_DAYS = 48 * 60  # 支持跨天航班

class Optimizer:
    """航班调整最优化器（规则分级健壮版）"""

    def _to_dt(self, x) -> Optional[datetime]:
        if pd.isna(x): return None
        if isinstance(x, pd.Timestamp): 
            return x.to_pydatetime().replace(microsecond=0)  # 去除微秒避免精度问题
        if isinstance(x, datetime): return x
        try:
            dt = pd.to_datetime(x).to_pydatetime()
            return dt.replace(microsecond=0)  # 去除微秒避免精度问题
        except Exception:
            return None

    def _normalize_flight_df(self, flights_df: pd.DataFrame):
        df = flights_df.copy()
        if "航班号" in df.columns: df["flight_number"] = df["航班号"]
        if "计划起飞机场" in df.columns: df["departure_airport"] = df["计划起飞机场"]
        if "计划落地机场" in df.columns: df["arrival_airport"] = df["计划落地机场"]
        if "STOT" in df.columns: df["STOT"] = df["STOT"].apply(self._to_dt)
        else: df["STOT"] = pd.to_datetime(df["计划起飞时间"]).apply(self._to_dt)
        if "target_departure_time" not in df.columns: df["target_departure_time"] = df["STOT"]
        else: df["target_departure_time"] = df["target_departure_time"].apply(self._to_dt)
        if "flight_duration_minutes" not in df.columns: df["flight_duration_minutes"] = 120
        if "revenue" not in df.columns: df["revenue"] = 30000
        df["base_delay_minutes"] = (df["target_departure_time"] - df["STOT"]).dt.total_seconds() / 60
        df["target_dep_min_of_day"] = df["target_departure_time"].dt.hour * 60 + df["target_departure_time"].dt.minute
        if "flight_id" not in df.columns: df["flight_id"] = df["flight_number"].astype(str)
        df = df.set_index("flight_id", drop=False)
        return df

    def build_model(
        self,
        flights_df: pd.DataFrame,
        constraint_data: Dict[str, Any],
        weights: Dict[str, float],
        cost_params: Optional[Dict[str, float]] = None,
        max_delay_minutes: int = 240,
        severe_delay_threshold: int = 120,
        big_m: float = 10000.0,
    ) -> pyo.ConcreteModel:
        df = self._normalize_flight_df(flights_df)
        
        C = {
            "C_CANCEL": 30000.0, "C_SWAP": 15000.0, "C_DELAY_PER_MIN": 80.0,
            "PENALTY_HIGH": 1_000_000.0, "PENALTY_MEDIUM": 100_000.0, "PENALTY_LOW": 10_000.0,
        }
        if cost_params: C.update(cost_params)

        m = pyo.ConcreteModel("Priority_Robust_Optimizer")
        m.F = pyo.Set(initialize=list(df.index))

        # --- 核心决策变量 ---
        m.x = pyo.Var(m.F, within=pyo.Binary)
        m.cancel_flight = pyo.Var(m.F, within=pyo.Binary)
        m.change_aircraft = pyo.Var(m.F, within=pyo.Binary)
        m.d = pyo.Var(m.F, within=pyo.NonNegativeReals, bounds=(0, max_delay_minutes))
        
        # 时间与状态变量 (支持跨天)
        m.dep_time_of_day = pyo.Var(m.F, within=pyo.NonNegativeReals, bounds=(0, MINUTES_IN_TWO_DAYS - 1))
        m.arr_time_of_day = pyo.Var(m.F, within=pyo.NonNegativeReals, bounds=(0, MINUTES_IN_TWO_DAYS - 1))
        
        m.cons = pyo.ConstraintList()

        # --- 检查跨天航班（仅用于记录，不过滤） ---
        print(f"[build_model] 检查跨天航班...")
        cross_day_flights = []
        
        for f in m.F:
            base_dep = float(df.loc[f, "target_dep_min_of_day"])
            fdur = float(df.loc[f, "flight_duration_minutes"])
            latest_arrival = base_dep + fdur + max_delay_minutes
            
            if latest_arrival >= MINUTES_IN_DAY:
                cross_day_flights.append(f)
                flight_num = df.loc[f, "航班号"] if "航班号" in df.columns else f
                print(f"[INFO] 跨天航班 {flight_num}: 起飞{base_dep}分钟 + 飞行{fdur}分钟 + 延误{max_delay_minutes}分钟 = {latest_arrival}分钟")
        
        if cross_day_flights:
            print(f"[INFO] 发现 {len(cross_day_flights)} 个跨天航班，模型已支持跨天处理")

        # --- 基础逻辑约束 ---
        for f in m.F:
            m.cons.add(m.change_aircraft[f] + m.cancel_flight[f] <= 1)
            m.cons.add(m.x[f] == 1 - m.cancel_flight[f])
            m.cons.add(m.d[f] <= max_delay_minutes * m.x[f])
            
            base_dep = float(df.loc[f, "target_dep_min_of_day"])
            fdur = float(df.loc[f, "flight_duration_minutes"])
            
            m.cons.add(base_dep + m.d[f] == m.dep_time_of_day[f]) # 起飞时间
            m.cons.add(base_dep + fdur + m.d[f] == m.arr_time_of_day[f]) # 到达时间

        # --- 应用分级约束 ---
        print(f"[build_model] 开始应用约束...")
        penalty_terms = []
        
        # 重新启用约束条件，修复变量初始化问题
        airport_res = constraint_data.get("airport_restriction", pd.DataFrame())
        airport_cap = constraint_data.get("airport_capacity", {})
        quota = constraint_data.get("quota", {})
        
        if not airport_res.empty:
            print(f"[build_model] 应用机场限制约束，共{len(airport_res)}条")
            penalty_terms.extend(self._apply_airport_curfew(m, df, airport_res, big_m))
        
        if airport_cap:
            print(f"[build_model] 应用机场容量约束，共{len(airport_cap)}个机场")
            penalty_terms.extend(self._apply_hourly_capacity(m, df, airport_cap))
        
        if quota:
            print(f"[build_model] 应用配额约束，共{len(quota)}种类型")
            penalty_terms.extend(self._apply_quota(m, quota))
        
        print(f"[build_model] 约束应用完成，惩罚项数量: {len(penalty_terms)}")
        
        # --- 目标函数 ---
        cost_cancel = sum(m.cancel_flight[f] * df.loc[f, "revenue"] for f in m.F)
        cost_swap = sum(m.change_aircraft[f] * C["C_SWAP"] for f in m.F)
        cost_delay = sum(m.d[f] * C["C_DELAY_PER_MIN"] for f in m.F)
        
        cost_penalty = 0
        for var, priority in penalty_terms:
            if var is not None:  # 确保变量存在
                penalty_cost = C.get(f"PENALTY_{priority.upper()}", C["PENALTY_MEDIUM"])
                cost_penalty += var * penalty_cost
        
        w = lambda k, d: weights.get(k, d)
        m.objective = pyo.Objective(
            expr = w("cancel", 1.0) * cost_cancel + w("swap", 0.3) * cost_swap + w("delay", 0.3) * cost_delay + cost_penalty,
            sense=pyo.minimize
        )
        return m

    def _apply_airport_curfew(self, m: pyo.ConcreteModel, df: pd.DataFrame, airport_res_df: Optional[pd.DataFrame], BIG_M: float) -> list:
        if airport_res_df is None or airport_res_df.empty: return []
        
        penalty_vars = []
        for _, r in airport_res_df.iterrows():
            if r.get("RESTRICTION_TYPE") != "AIRPORT_CURFEW": continue
            try:
                ap = r["AIRPORT_CODE"]; st_str = r["START_TIME_OF_DAY"]; ed_str = r["END_TIME_OF_DAY"]
                priority = r.get("PRIORITY", "HIGH") # 默认为HIGH
                # 安全的时间字符串解析
                if isinstance(st_str, str) and ':' in st_str:
                    st_parts = st_str.split(':')
                    st_min = int(st_parts[0]) * 60 + int(st_parts[1])
                else:
                    continue  # 跳过无效的时间格式
                    
                if isinstance(ed_str, str) and ':' in ed_str:
                    ed_parts = ed_str.split(':')
                    ed_min = int(ed_parts[0]) * 60 + int(ed_parts[1])
                else:
                    continue  # 跳过无效的时间格式

                if st_min > ed_min: # 只处理跨夜宵禁
                    for f in m.F:
                        is_dep = df.loc[f, "departure_airport"] == ap
                        is_arr = df.loc[f, "arrival_airport"] == ap
                        if not (is_dep or is_arr): continue
                        
                        time_var = m.dep_time_of_day[f] if is_dep else m.arr_time_of_day[f]
                        
                        # 根据优先级决定约束类型
                        if priority == 'MUST':
                            # 刚性约束
                            y = pyo.Var(within=pyo.Binary)
                            m.add_component(f"curfew_hard_choice_{f}_{ap}", y)
                            m.cons.add(time_var <= ed_min + BIG_M * y + BIG_M * m.cancel_flight[f])
                            m.cons.add(time_var >= st_min - BIG_M * (1 - y) - BIG_M * m.cancel_flight[f])
                        else:
                            # 柔性约束 (简化处理：允许一个标志变量来违反)
                            var_name = f"curfew_soft_violation_{f}_{ap}".replace('-', '_').replace(':', '_')
                            v = pyo.Var(within=pyo.Binary, bounds=(0, 1), initialize=0)
                            m.add_component(var_name, v)
                            penalty_vars.append((v, priority))
                            
                            choice_name = f"curfew_soft_choice_{f}_{ap}".replace('-', '_').replace(':', '_')
                            y = pyo.Var(within=pyo.Binary, bounds=(0, 1), initialize=0)
                            m.add_component(choice_name, y)
                            # 如果不违反(v=0)，则必须遵守宵禁
                            m.cons.add(time_var <= ed_min + BIG_M * y + BIG_M * m.cancel_flight[f] + BIG_M * v)
                            m.cons.add(time_var >= st_min - BIG_M * (1 - y) - BIG_M * m.cancel_flight[f] - BIG_M * v)
            except Exception:
                continue
        return penalty_vars

    def _apply_hourly_capacity(self, m: pyo.ConcreteModel, df: pd.DataFrame, cap: Optional[Dict[str, Any]]) -> list:
        if not cap: return []
        penalty_vars = []
        
        for ap, winmap in cap.items():
            for win_key, details in winmap.items():
                # 兼容两种格式：新格式dict和旧格式int
                if isinstance(details, dict):
                    limit = details['limit']
                    priority = details.get('priority', 'HIGH')
                else:
                    # 旧格式：直接是数值
                    limit = int(details)
                    priority = 'HIGH'
                
                try:
                    # 支持两种格式：'08:00-09:00' 和 '08:00(+60)'
                    if '-' in win_key:
                        # 新格式：'08:00-09:00'
                        start_str, end_str = win_key.split('-')
                        if isinstance(start_str, str) and ':' in start_str:
                            start_min = int(start_str.split(':')[0]) * 60
                        else:
                            continue
                        if isinstance(end_str, str) and ':' in end_str:
                            end_min = int(end_str.split(':')[0]) * 60
                        else:
                            continue
                    elif '(+' in win_key and ')' in win_key:
                        # 旧格式：'08:00(+60)'
                        start_str = win_key.split('(')[0]
                        duration_str = win_key.split('(+')[1].split(')')[0]
                        if isinstance(start_str, str) and ':' in start_str:
                            start_min = int(start_str.split(':')[0]) * 60
                            duration = int(duration_str)
                            end_min = start_min + duration
                        else:
                            continue
                    else:
                        continue
                except: 
                    continue

                flights_in_window = [f for f in m.F if df.loc[f, "departure_airport"] == ap and start_min <= df.loc[f, "target_dep_min_of_day"] < end_min]
                if not flights_in_window: continue
                
                # sum(执行的航班)
                departures = sum(m.x[f] for f in flights_in_window)
                
                if priority == 'MUST':
                    m.cons.add(departures <= limit)
                else:
                    var_name = f"capacity_overage_{ap}_{win_key}".replace('-', '_').replace(':', '_').replace('(', '_').replace(')', '_').replace('+', '_')
                    overage = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, None), initialize=0)
                    m.add_component(var_name, overage)
                    m.cons.add(departures <= limit + overage)
                    penalty_vars.append((overage, priority))
        return penalty_vars

    def _apply_quota(self, m: pyo.ConcreteModel, quota: Optional[Dict[str, Any]]) -> list:
        if not quota: return []
        penalty_vars = []

        # 取消配额
        if "cancel" in quota:
            details = quota["cancel"]
            limit = details.get('max')
            priority = details.get('priority', 'HIGH')
            if limit is not None:
                if priority == 'MUST':
                    m.cons.add(sum(m.cancel_flight[f] for f in m.F) <= limit)
                else:
                    overage = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, None), initialize=0)
                    m.add_component("quota_overage_cancel", overage)
                    m.cons.add(sum(m.cancel_flight[f] for f in m.F) <= limit + overage)
                    penalty_vars.append((overage, priority))
        
        # 更换飞机配额
        if "swap" in quota:
            details = quota["swap"]
            limit = details.get('max')
            priority = details.get('priority', 'HIGH')
            if limit is not None:
                if priority == 'MUST':
                    m.cons.add(sum(m.change_aircraft[f] for f in m.F) <= limit)
                else:
                    overage = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, None), initialize=0)
                    m.add_component("quota_overage_swap", overage)
                    m.cons.add(sum(m.change_aircraft[f] for f in m.F) <= limit + overage)
                    penalty_vars.append((overage, priority))

        return penalty_vars

    def solve(self, flights_df: pd.DataFrame, constraint_data: Dict[str, Any], weights: Dict[str, float], solver_name: str = "glpk") -> Optional[pd.DataFrame]:
        m = self.build_model(flights_df, constraint_data, weights)
        solver = pyo.SolverFactory(solver_name)
        result = solver.solve(m, tee=False)
        
        print("\n--- 约束检查 ---")
        violated = False
        for v_name, v_obj in m.component_map(ctype=pyo.Var).items():
            if 'overage' in v_name or 'violation' in v_name:
                try:
                    val = pyo.value(v_obj)
                    if val is not None and val > 0.001:
                        print(f"[警告] 柔性约束被触发: {v_name} = {val:.2f}")
                        violated = True
                except:
                    # 跳过未初始化的变量
                    pass
        if not violated: print("所有柔性约束均已满足。")
            
        return self.get_optimization_results(m, flights_df, result)

    def batch_solve(
        self, 
        flights_df: pd.DataFrame, 
        constraint_data: Dict[str, Any], 
        weight_sets: List[Dict[str, float]], 
        solver_name: str = "glpk",
        time_limit: int = 60,
        severe_delay_threshold: int = 360,
        big_m: float = 50000.0,
        day_offset_ub: int = 3
    ) -> List[Optional[pd.DataFrame]]:
        """
        批量求解多个权重策略
        
        Args:
            flights_df: 航班数据
            constraint_data: 约束数据
            weight_sets: 权重策略列表
            solver_name: 求解器名称
            time_limit: 求解时间限制（秒）
            severe_delay_threshold: 严重延误阈值（分钟）
            big_m: Big-M 参数
            day_offset_ub: 最大天数偏移
            
        Returns:
            解决方案列表
        """
        solutions = []
        
        for i, weights in enumerate(weight_sets):
            print(f"\n--- 求解方案 {i+1}/{len(weight_sets)} ---")
            print(f"权重策略: {weights}")
            
            try:
                print(f"[Optimizer] 开始构建模型，权重: {weights}")
                print(f"[Optimizer] 航班数据形状: {flights_df.shape}")
                print(f"[Optimizer] 约束数据键: {list(constraint_data.keys())}")
                
                # 构建模型
                m = self.build_model(
                    flights_df=flights_df,
                    constraint_data=constraint_data,
                    weights=weights,
                    max_delay_minutes=severe_delay_threshold,
                    big_m=big_m
                )
                print(f"[Optimizer] 模型构建成功")
                
                # 求解
                solver = pyo.SolverFactory(solver_name)
                if time_limit > 0:
                    solver.options['tmlim'] = time_limit  # GLPK时间限制
                
                result = solver.solve(m, tee=False)  # 静默求解
                
                # 检查求解状态
                from pyomo.opt import SolverStatus, TerminationCondition
                print(f"[Optimizer] 求解状态: {result.solver.status}")
                print(f"[Optimizer] 终止条件: {result.solver.termination_condition}")
                
                # 检查约束
                violated = False
                for v_name, v_obj in m.component_map(ctype=pyo.Var).items():
                    if 'overage' in v_name or 'violation' in v_name:
                        try:
                            val = pyo.value(v_obj)
                            if val is not None and val > 0.001:
                                print(f"[警告] 柔性约束被触发: {v_name} = {val:.2f}")
                                violated = True
                        except:
                            # 跳过未初始化的变量
                            pass
                if not violated: 
                    print("所有柔性约束均已满足。")
                
                # 获取结果
                solution_df = self.get_optimization_results(m, flights_df, result)
                
                # 构造API期望的格式
                solution = {
                    "result": solution_df is not None,
                    "table": solution_df
                }
                solutions.append(solution)
                
                if solution_df is not None:
                    print(f"方案 {i+1} 求解成功")
                else:
                    print(f"方案 {i+1} 求解失败")
                    
            except Exception as e:
                print(f"方案 {i+1} 求解异常: {e}")
                solutions.append({
                    "result": False,
                    "table": None
                })
        
        return solutions

    def get_optimization_results(self, model: pyo.ConcreteModel, flights_df: pd.DataFrame, result) -> Optional[pd.DataFrame]:
        from pyomo.opt import SolverStatus, TerminationCondition
        if (result.solver.status != SolverStatus.ok or result.solver.termination_condition not in [TerminationCondition.optimal, TerminationCondition.feasible]):
            return None
            
        df = self._normalize_flight_df(flights_df)
        out = df[["航班号", "计划起飞时间", "target_departure_time"]].copy()
        
        actions, status, delays = [], [], []
        for f in model.F:
            is_cancelled = pyo.value(model.cancel_flight[f]) > 0.5
            is_swapped = pyo.value(model.change_aircraft[f]) > 0.5
            delay_val = pyo.value(model.d[f])
            
            if is_cancelled:
                actions.append("取消航班"); status.append("取消"); delays.append(0)
            else:
                status.append("执行"); delays.append(int(round(delay_val)))
                if is_swapped: actions.append("更换飞机")
                elif delay_val > 0.1: actions.append("变更时刻")
                else: actions.append("正常执行")

        out["adjustment_action"] = actions
        out["status"] = status
        out["additional_delay_minutes"] = delays
        out["adjusted_departure_time"] = out.apply(
            lambda row: row['target_departure_time'] + timedelta(minutes=row['additional_delay_minutes']) if row['status'] == '执行' else pd.NaT,
            axis=1)
        return out.reset_index(drop=True)

if __name__ == "__main__":
    flights_df = pd.DataFrame([
        {"航班号":"CA101","计划起飞机场":"PEK","计划落地机场":"SHA","计划起飞时间":"2025-08-16 08:10"},
        {"航班号":"CA203","计划起飞机场":"PEK","计划落地机场":"SHA","计划起飞时间":"2025-08-16 08:25"},
        {"航班号":"CA305","计划起飞机场":"PEK","计划落地机场":"SHA","计划起飞时间":"2025-08-16 08:55"},
    ])

    # 宵禁规则，从文件读取，自动判断优先级
    airport_restriction = pd.DataFrame([
        {"AIRPORT_CODE":"PEK","RESTRICTION_TYPE":"AIRPORT_CURFEW","START_TIME_OF_DAY":"01:00","END_TIME_OF_DAY":"05:00", "PRIORITY": "MUST"},
        {"AIRPORT_CODE":"SHA","RESTRICTION_TYPE":"AIRPORT_CURFEW","START_TIME_OF_DAY":"00:00","END_TIME_OF_DAY":"06:00", "PRIORITY": "HIGH"},
    ])
    
    # 【新格式】小时容量，需指定 limit 和 priority
    airport_capacity = {
        "PEK": {
            "08:00-09:00": {"limit": 1, "priority": "HIGH"} # 8点这个小时我们希望最多飞1架，但不是死命令
        }
    }
    
    # 【新格式】配额，需指定 max 和 priority
    quota = {
        "cancel": {"max": 0, "priority": "MUST"} # 绝对不允许取消航班
    }

    constraint_data = {
        "airport_restriction": airport_restriction,
        "airport_capacity": airport_capacity,
        "quota": quota,
    }

    weights = {"cancel": 0.8, "delay": 0.2, "swap": 0.1}

    opt = Optimizer()
    solution_df = opt.solve(
        flights_df=flights_df,
        constraint_data=constraint_data,
        weights=weights,
    )

    print("\n--- 最终优化方案 ---")
    if solution_df is not None:
        print(solution_df)
    else:
        print("未能找到可行的解决方案。")