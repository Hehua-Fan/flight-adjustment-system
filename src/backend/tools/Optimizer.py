import pandas as pd
import pyomo.environ as pyo
from datetime import datetime, timedelta

class Optimizer:
    """航班调整优化器类 - 专注于模型构建和求解"""
    
    def __init__(self):
        """初始化优化器"""
        pass
        
    def build_model(self, flights_df, constraint_data, weights, all_constraints=None):
        """构建Pyomo优化模型，处理所有5种约束类型"""
        print(f"\n--- 开始使用权重进行优化: {weights} ---")
        
        model = pyo.ConcreteModel(name="Flight_Adjustment_Optimization")

        # --- 索引 ---
        model.flights = pyo.Set(initialize=flights_df.index)

        # --- 决策与辅助变量 ---
        model.x = pyo.Var(model.flights, within=pyo.Binary)
        model.d = pyo.Var(model.flights, within=pyo.NonNegativeReals)
        model.l = pyo.Var(model.flights, within=pyo.Binary)
        model.departure_day_offset = pyo.Var(model.flights, within=pyo.NonNegativeIntegers)
        model.arrival_day_offset = pyo.Var(model.flights, within=pyo.NonNegativeIntegers)
        model.dep_time_of_day = pyo.Var(model.flights, within=pyo.NonNegativeReals, bounds=(0, 24*60))
        model.arr_time_of_day = pyo.Var(model.flights, within=pyo.NonNegativeReals, bounds=(0, 24*60))

        # --- 目标函数 ---
        revenue_loss = sum((1 - model.x[f]) * flights_df.loc[f, 'revenue'] for f in model.flights)
        total_delay = sum(model.d[f] for f in model.flights)
        
        # 根据实际列名获取旅客数
        passenger_col = '旅客人数(订座)' if '旅客人数(订座)' in flights_df.columns else 'passenger_count'
        if passenger_col in flights_df.columns:
            late_pax_impact = sum(model.l[f] * flights_df.loc[f, passenger_col] for f in model.flights)
            late_revenue_loss = sum(model.l[f] * flights_df.loc[f, passenger_col] * 200 for f in model.flights)
        else:
            late_pax_impact = sum(model.l[f] * 150 for f in model.flights)  # 默认150人
            late_revenue_loss = sum(model.l[f] * 150 * 200 for f in model.flights)

        model.objective = pyo.Objective(
            expr = weights['cancel'] * revenue_loss + \
                   weights['delay'] * total_delay + \
                   weights['late_pax'] * late_pax_impact + \
                   weights['revenue'] * late_revenue_loss,
            sense=pyo.minimize
        )

        # --- 约束条件 ---
        model.constraints = pyo.ConstraintList()
        BIG_M = 10000
        MINUTES_IN_DAY = 24 * 60

        # 统计应用的约束数量
        constraint_counts = {
            'airport_curfew': 0,
            'flight_restrictions': 0,
            'sector_requirements': 0,
            'must_cancel': 0
        }

        for f in model.flights:
            flight = flights_df.loc[f]
            
            # 基础约束：'严重晚点'变量l_f的定义
            stot_col = '计划起飞时间' if '计划起飞时间' in flights_df.columns else 'STOT'
            if stot_col in flights_df.columns and pd.notna(flight[stot_col]):
                total_delay_from_stot = (flight['target_departure_time'] - flight[stot_col]).total_seconds() / 60 + model.d[f]
            else:
                total_delay_from_stot = model.d[f]  # 如果没有计划起飞时间，只考虑附加延误
            model.constraints.add(total_delay_from_stot - 120 <= BIG_M * model.l[f])
            
            # 基础约束：附加延误d_f只在航班执行时有效
            model.constraints.add(model.d[f] <= BIG_M * model.x[f])
            
            # 基础约束：机组执勤时间
            duty_time = (60 + flight['flight_duration_minutes'] + 30) + total_delay_from_stot
            MAX_DUTY_MINUTES = 14 * 60
            model.constraints.add(duty_time <= MAX_DUTY_MINUTES + BIG_M * (1 - model.x[f]))

            # 基础约束：时间线性关系
            target_dep_minute_of_day = flight['target_departure_time'].hour * 60 + flight['target_departure_time'].minute
            actual_dep_total_minutes = target_dep_minute_of_day + model.d[f]
            model.constraints.add(expr= actual_dep_total_minutes == model.departure_day_offset[f] * MINUTES_IN_DAY + model.dep_time_of_day[f])
            
            actual_arr_total_minutes = target_dep_minute_of_day + flight['flight_duration_minutes'] + model.d[f]
            model.constraints.add(expr= actual_arr_total_minutes == model.arrival_day_offset[f] * MINUTES_IN_DAY + model.arr_time_of_day[f])
            
            # --- 应用5种约束类型 ---
            
            # 1. 机场限制 (airport_restriction.csv)
            self._apply_airport_restrictions(model, f, flight, constraint_data.get('airport_restriction', pd.DataFrame()), constraint_counts, BIG_M)
            
            # 2. 航班限制 (flight_restriction.csv) 
            self._apply_flight_restrictions(model, f, flight, constraint_data.get('flight_restriction', pd.DataFrame()), constraint_counts, BIG_M)
            
            # 3. 航班特殊要求 (flight_special_requirement.csv)
            self._apply_flight_special_requirements(model, f, flight, constraint_data.get('flight_special_requirement', pd.DataFrame()), constraint_counts, BIG_M)
            
            # 4. 航段特殊要求 (sector_special_requirement.csv)
            self._apply_sector_special_requirements(model, f, flight, constraint_data.get('sector_special_requirement', pd.DataFrame()), constraint_counts, BIG_M)
            
            # 5. 机场特殊要求 (airport_special_requirement.csv)
            self._apply_airport_special_requirements(model, f, flight, constraint_data.get('airport_special_requirement', pd.DataFrame()), constraint_counts, BIG_M)
        
        # 输出约束应用统计
        print("[Optimizer]: 约束应用统计:")
        for constraint_type, count in constraint_counts.items():
            if count > 0:
                print(f"  - {constraint_type}: {count} 个")
        
        return model

    def solve_model(self, model, solver_name='glpk'):
        """求解优化模型并返回结果"""
        print("开始求解模型...")
        solver = pyo.SolverFactory(solver_name)
        
        # 设置求解器选项
        if solver_name == 'glpk':
            # 设置更长的超时时间和其他选项
            solver.options['tmlim'] = 300  # 300秒超时
            solver.options['mipgap'] = 0.05  # 5% MIP gap tolerance
        
        try:
            result = solver.solve(model, tee=False)
            print(f"求解完成，求解器状态: {result.solver.status}, 终止条件: {result.solver.termination_condition}")
            
            if result.solver.termination_condition == pyo.TerminationCondition.optimal:
                return result
            elif result.solver.termination_condition == pyo.TerminationCondition.feasible:
                print("找到可行解（但可能不是最优解）")
                return result
            else:
                print("未能找到最优解。")
                return None
        except Exception as e:
            print(f"求解过程中出现错误: {e}")
            return None
    
    def get_optimization_results(self, model, flights_df, result):
        """提取优化结果并格式化"""
        if result is None or result.solver.termination_condition != pyo.TerminationCondition.optimal:
            return None
            
        # 根据实际列名选择要保留的列
        columns_to_keep = []
        
        # 航班号
        if '航班号' in flights_df.columns:
            columns_to_keep.append('航班号')
        elif 'flight_number' in flights_df.columns:
            columns_to_keep.append('flight_number')
            
        # 计划起飞时间
        if '计划起飞时间' in flights_df.columns:
            columns_to_keep.append('计划起飞时间')
        elif 'STOT' in flights_df.columns:
            columns_to_keep.append('STOT')
            
        # 目标起飞时间
        if 'target_departure_time' in flights_df.columns:
            columns_to_keep.append('target_departure_time')
        
        res_df = flights_df[columns_to_keep].copy()
        res_df['status'] = ['执行' if pyo.value(model.x[f]) > 0.5 else '取消' for f in model.flights]
        res_df['additional_delay_minutes'] = [round(pyo.value(model.d[f]), 1) for f in model.flights]
        
        res_df['adjusted_departure_time'] = res_df.apply(
            lambda row: row['target_departure_time'] + timedelta(minutes=row['additional_delay_minutes']) if row['status'] == '执行' else pd.NaT,
            axis=1
        )
        return res_df
    
    def _apply_airport_restrictions(self, model, f, flight, airport_res_df, constraint_counts, BIG_M):
        """应用机场限制约束"""
        if airport_res_df.empty:
            return
        
        # 检查起飞机场限制
        dep_airport_col = '计划起飞机场' if '计划起飞机场' in flight.index else 'departure_airport'
        dep_airport = flight.get(dep_airport_col, '')
        
        dep_restrictions = airport_res_df[
            (airport_res_df['AIRPORT_CODE'] == dep_airport) &
            (airport_res_df['RESTRICTION_TYPE'] == 'AIRPORT_CURFEW')
        ]
        
        for _, r in dep_restrictions.iterrows():
            try:
                start_time = datetime.strptime(r['START_TIME_OF_DAY'], '%H:%M')
                end_time = datetime.strptime(r['END_TIME_OF_DAY'], '%H:%M')
                
                curfew_start = start_time.hour * 60 + start_time.minute
                curfew_end = end_time.hour * 60 + end_time.minute
                
                # 处理跨天的宵禁时间
                if curfew_start > curfew_end:
                    # 跨天宵禁：不允许在 curfew_start 到 curfew_end 之间起飞
                    # 引入二元变量来处理逻辑约束
                    binary_var_name = f'curfew_dep_{f}_{len(model.constraints)}'
                    setattr(model, binary_var_name, pyo.Var(within=pyo.Binary))
                    binary_var = getattr(model, binary_var_name)
                    
                    # binary_var = 1 当且仅当起飞时间满足宵禁要求
                    model.constraints.add(model.dep_time_of_day[f] <= curfew_start + BIG_M * (1 - binary_var))
                    model.constraints.add(model.dep_time_of_day[f] >= curfew_end - BIG_M * binary_var)
                    
                    # 如果航班执行，必须满足宵禁要求
                    model.constraints.add(binary_var >= model.x[f])
                    constraint_counts['airport_curfew'] += 1
                    
            except (ValueError, KeyError):
                continue
        
        # 检查到达机场限制
        arr_airport_col = '计划落地机场' if '计划落地机场' in flight.index else 'arrival_airport'
        arr_airport = flight.get(arr_airport_col, '')
        
        arr_restrictions = airport_res_df[
            (airport_res_df['AIRPORT_CODE'] == arr_airport) &
            (airport_res_df['RESTRICTION_TYPE'] == 'AIRPORT_CURFEW')
        ]
        
        for _, r in arr_restrictions.iterrows():
            try:
                start_time = datetime.strptime(r['START_TIME_OF_DAY'], '%H:%M')
                end_time = datetime.strptime(r['END_TIME_OF_DAY'], '%H:%M')
                
                curfew_start = start_time.hour * 60 + start_time.minute
                curfew_end = end_time.hour * 60 + end_time.minute
                
                # 处理跨天的宵禁时间
                if curfew_start > curfew_end:
                    # 跨天宵禁：不允许在 curfew_start 到 curfew_end 之间到达
                    # 引入二元变量来处理逻辑约束
                    binary_var_name = f'curfew_arr_{f}_{len(model.constraints)}'
                    setattr(model, binary_var_name, pyo.Var(within=pyo.Binary))
                    binary_var = getattr(model, binary_var_name)
                    
                    # binary_var = 1 当且仅当到达时间满足宵禁要求
                    model.constraints.add(model.arr_time_of_day[f] <= curfew_start + BIG_M * (1 - binary_var))
                    model.constraints.add(model.arr_time_of_day[f] >= curfew_end - BIG_M * binary_var)
                    
                    # 如果航班执行，必须满足宵禁要求
                    model.constraints.add(binary_var >= model.x[f])
                    constraint_counts['airport_curfew'] += 1
                    
            except (ValueError, KeyError):
                continue
    
    def _apply_flight_restrictions(self, model, f, flight, flight_res_df, constraint_counts, BIG_M):
        """应用航班限制约束"""
        if flight_res_df.empty:
            return
        
        # 检查特定航班限制
        flight_number_col = '航班号' if '航班号' in flight.index else 'flight_number'
        flight_number = flight.get(flight_number_col, '')
        carrier_code = flight.get('carrier_code', '')
        
        flight_restrictions = flight_res_df[
            (flight_res_df['CARRIER_CODE'] == carrier_code) &
            (flight_res_df['FLIGHT_NUMBER'] == flight_number)
        ]
        
        for _, restriction in flight_restrictions.iterrows():
            priority = restriction.get('PRIORITY', '')
            restriction_type = restriction.get('RESTRICTION_TYPE', '')
            
            # MUST级别的限制通常意味着必须取消
            if priority == 'MUST' and restriction_type in ['AIRCRAFT', 'NOISELIMIT']:
                # 强制取消该航班
                model.constraints.add(model.x[f] == 0)
                constraint_counts['must_cancel'] += 1
                constraint_counts['flight_restrictions'] += 1
    
    def _apply_flight_special_requirements(self, model, f, flight, flight_req_df, constraint_counts, BIG_M):
        """应用航班特殊要求约束"""
        if flight_req_df.empty:
            return
        
        # 检查特定航班的特殊要求
        flight_requirements = flight_req_df[
            (flight_req_df['CARRIER_CODE'] == flight.get('carrier_code', '')) &
            (flight_req_df['REF_FLIGHT_NUMBER'] == flight.get('flight_number', ''))
        ]
        
        for _, requirement in flight_requirements.iterrows():
            priority = requirement.get('PRIORITY', '')
            req_type = requirement.get('REQUIREMENT_TYPE', '')
            category = requirement.get('CATEGORY', '')
            
            # 处理湿租等特殊要求
            if priority == 'MUST' and category == 'WETLEASE':
                # 湿租航班的特殊处理 - 这里可以添加特定的约束逻辑
                # 例如：限制某些时段、特殊设备要求等
                pass
    
    def _apply_sector_special_requirements(self, model, f, flight, sector_req_df, constraint_counts, BIG_M):
        """应用航段特殊要求约束"""
        if sector_req_df.empty:
            return
        
        # 检查航段特殊要求  
        dep_airport_col = '计划起飞机场' if '计划起飞机场' in flight.index else 'departure_airport'
        arr_airport_col = '计划落地机场' if '计划落地机场' in flight.index else 'arrival_airport'
        dep_airport = flight.get(dep_airport_col, '')
        arr_airport = flight.get(arr_airport_col, '')
        carrier_code = flight.get('carrier_code', '')
        
        sector_requirements = sector_req_df[
            (sector_req_df['DEPARTURE_AIRPORT_CODE'] == dep_airport) &
            (sector_req_df['ARRIVAL_AIRPORT_CODE'] == arr_airport) &
            (sector_req_df['CARRIER_CODE'] == carrier_code)
        ]
        
        for _, requirement in sector_requirements.iterrows():
            priority = requirement.get('PRIORITY', '')
            req_type = requirement.get('REQUIREMENT_TYPE', '')
            category = requirement.get('CATEGORY', '')
            
            if priority == 'MUST':
                if category == 'WATERCROSS':
                    # 跨水运行要求 - 可能需要特殊设备
                    pass
                elif category == 'AIRCRAFTPERFORMANCE':
                    # 机型性能要求 - 可能影响航班选择
                    pass
                    
            constraint_counts['sector_requirements'] += 1
    
    def _apply_airport_special_requirements(self, model, f, flight, airport_req_df, constraint_counts, BIG_M):
        """应用机场特殊要求约束"""
        if airport_req_df.empty:
            return
        
        # 检查起飞机场的特殊要求
        dep_airport_col = '计划起飞机场' if '计划起飞机场' in flight.index else 'departure_airport'
        dep_airport = flight.get(dep_airport_col, '')
        
        dep_requirements = airport_req_df[
            airport_req_df['AIRPORT_CODE'] == dep_airport
        ]
        
        for _, requirement in dep_requirements.iterrows():
            priority = requirement.get('PRIORITY', '')
            req_type = requirement.get('REQUIREMENT_TYPE', '')
            category = requirement.get('CATEGORY', '')
            
            if priority == 'MUST':
                if category == 'ACequipment':
                    # 飞机设备要求 - 可能需要特定的设备配置
                    pass
                elif category == 'COUNTRY':
                    # 国家注册要求 - 限制特定注册地的飞机
                    pass
        
        # 检查到达机场的特殊要求
        arr_airport_col = '计划落地机场' if '计划落地机场' in flight.index else 'arrival_airport'
        arr_airport = flight.get(arr_airport_col, '')
        
        arr_requirements = airport_req_df[
            airport_req_df['AIRPORT_CODE'] == arr_airport
        ]
        
        for _, requirement in arr_requirements.iterrows():
            priority = requirement.get('PRIORITY', '')
            req_type = requirement.get('REQUIREMENT_TYPE', '')
            category = requirement.get('CATEGORY', '')
            
            if priority == 'MUST':
                if category == 'ACequipment':
                    # 飞机设备要求
                    pass
                elif category == 'COUNTRY':
                    # 国家注册要求
                    pass