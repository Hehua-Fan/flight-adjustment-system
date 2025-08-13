import pandas as pd
import pyomo.environ as pyo
from datetime import datetime

class FlightOptimizer:
    """航班调整优化器类 - 专注于模型构建和求解"""
    
    def __init__(self):
        """初始化优化器"""
        pass
        
    def build_model(self, flights_df, airport_res_df, weights, all_constraints=None):
        """
        构建优化模型 - 包含所有约束条件
        
        Args:
            flights_df: 航班数据DataFrame
            airport_res_df: 机场限制数据DataFrame  
            weights: 目标函数权重字典
            all_constraints: 所有约束数据字典（可选）
            
        Returns:
            pyo.ConcreteModel: 构建好的优化模型
        """
        print(f"\n--- 开始构建优化模型: {weights} ---")
        
        model = pyo.ConcreteModel(name="Flight_Adjustment_Optimization")

        # === 1. 索引定义 ===
        model.flights = pyo.Set(initialize=flights_df.index)

        # === 2. 决策变量定义 ===
        model.x = pyo.Var(model.flights, within=pyo.Binary, doc="1 if flight operates, 0 if canceled")
        model.d = pyo.Var(model.flights, within=pyo.NonNegativeReals, doc="Delay in minutes")
        model.l = pyo.Var(model.flights, within=pyo.Binary, doc="1 if delay > 120 mins")
        
        # === 3. 辅助变量 (用于处理跨天时间) ===
        model.departure_day_offset = pyo.Var(model.flights, within=pyo.NonNegativeIntegers, doc="Day offset for departure")
        model.arrival_day_offset = pyo.Var(model.flights, within=pyo.NonNegativeIntegers, doc="Day offset for arrival")
        model.dep_time_of_day = pyo.Var(model.flights, within=pyo.NonNegativeReals, doc="Minute of the day for departure (0-1439)")
        model.arr_time_of_day = pyo.Var(model.flights, within=pyo.NonNegativeReals, doc="Minute of the day for arrival (0-1439)")

        # === 4. 目标函数定义 ===
        revenue_loss = sum((1 - model.x[f]) * flights_df.loc[f, 'revenue'] for f in model.flights)
        total_delay = sum(model.d[f] for f in model.flights)
        late_pax_impact = sum(model.l[f] * flights_df.loc[f, 'passenger_count'] for f in model.flights)
        late_revenue_loss = sum(model.l[f] * flights_df.loc[f, 'passenger_count'] * 200 for f in model.flights)

        model.objective = pyo.Objective(
            expr = weights['cancel'] * revenue_loss + \
                   weights['delay'] * total_delay + \
                   weights['late_pax'] * late_pax_impact + \
                   weights['revenue'] * late_revenue_loss,
            sense=pyo.minimize
        )

        # === 5. 约束条件定义 ===
        model.constraints = pyo.ConstraintList()
        BIG_M = 10000
        MINUTES_IN_DAY = 24 * 60

        print("正在添加基础约束条件...")
        for f in model.flights:
            flight = flights_df.loc[f]

            # === 5.1 基础逻辑约束 ===
            # 延误只有在航班执行时才有意义
            model.constraints.add(model.d[f] <= BIG_M * model.x[f])
            # 大延误标识约束
            model.constraints.add(model.d[f] - 120 <= BIG_M * model.l[f])
            model.constraints.add(model.d[f] >= 120 - BIG_M * (1 - model.l[f]))
            
            # === 5.2 机组值勤时间约束 ===
            duty_time = (60 + flight['flight_duration_minutes'] + 30) + model.d[f]
            MAX_DUTY_MINUTES = 14 * 60
            model.constraints.add(duty_time <= MAX_DUTY_MINUTES + BIG_M * (1 - model.x[f]))

            # === 5.3 时间计算约束 ===
            planned_dep_minute_of_day = flight['planned_departure_time'].hour * 60 + flight['planned_departure_time'].minute
            actual_dep_total_minutes = planned_dep_minute_of_day + model.d[f]
            actual_arr_total_minutes = planned_dep_minute_of_day + flight['flight_duration_minutes'] + model.d[f]
            
            # 起飞时间约束
            model.constraints.add(expr= actual_dep_total_minutes == model.departure_day_offset[f] * MINUTES_IN_DAY + model.dep_time_of_day[f])
            model.constraints.add(model.dep_time_of_day[f] <= MINUTES_IN_DAY)
            
            # 到达时间约束
            model.constraints.add(expr= actual_arr_total_minutes == model.arrival_day_offset[f] * MINUTES_IN_DAY + model.arr_time_of_day[f])
            model.constraints.add(model.arr_time_of_day[f] <= MINUTES_IN_DAY)

            # === 5.4 机场宵禁约束 ===
            # 起飞机场宵禁
            dep_restrictions = airport_res_df[airport_res_df['AIRPORT_CODE'] == flight['departure_airport']]
            for _, r in dep_restrictions.iterrows():
                if r['RESTRICTION_TYPE'] == 'AIRPORT_CURFEW':
                    curfew_start = datetime.strptime(r['START_TIME_OF_DAY'], '%H:%M').hour * 60 + datetime.strptime(r['START_TIME_OF_DAY'], '%H:%M').minute
                    curfew_end = datetime.strptime(r['END_TIME_OF_DAY'], '%H:%M').hour * 60 + datetime.strptime(r['END_TIME_OF_DAY'], '%H:%M').minute
                    if curfew_start < curfew_end: continue
                    model.constraints.add(model.dep_time_of_day[f] >= curfew_end - BIG_M * (1 - model.x[f]))
                    model.constraints.add(model.dep_time_of_day[f] <= curfew_start + BIG_M * (1 - model.x[f]))

            # 到达机场宵禁
            arr_restrictions = airport_res_df[airport_res_df['AIRPORT_CODE'] == flight['arrival_airport']]
            for _, r in arr_restrictions.iterrows():
                if r['RESTRICTION_TYPE'] == 'AIRPORT_CURFEW':
                    curfew_start = datetime.strptime(r['START_TIME_OF_DAY'], '%H:%M').hour * 60 + datetime.strptime(r['START_TIME_OF_DAY'], '%H:%M').minute
                    curfew_end = datetime.strptime(r['END_TIME_OF_DAY'], '%H:%M').hour * 60 + datetime.strptime(r['END_TIME_OF_DAY'], '%H:%M').minute
                    if curfew_start < curfew_end: continue
                    model.constraints.add(model.arr_time_of_day[f] >= curfew_end - BIG_M * (1 - model.x[f]))
                    model.constraints.add(model.arr_time_of_day[f] <= curfew_start + BIG_M * (1 - model.x[f]))

        # === 5.5 额外约束条件处理 ===
        if all_constraints:
            print("正在添加额外约束条件...")
            
            # === 5.5.1 航班限制约束 ===
            flight_restrictions = all_constraints.get('flight_restrictions')
            if flight_restrictions is not None and not flight_restrictions.empty:
                print(f"  添加航班限制约束: {len(flight_restrictions)} 条")
                for _, restriction in flight_restrictions.iterrows():
                    if restriction['PRIORITY'] == 'MUST':
                        # 查找受影响的航班
                        for f in model.flights:
                            flight = flights_df.loc[f]
                            is_affected = True
                            
                            # 检查航班号匹配
                            if restriction.get('FLIGHT_NUMBER') and str(flight.get('flight_number', '')).find(str(restriction['FLIGHT_NUMBER'])) == -1:
                                is_affected = False
                            
                            # 检查起飞机场匹配
                            if restriction.get('DEPARTURE_AIRPORT_CODE') and flight.get('departure_airport') != restriction['DEPARTURE_AIRPORT_CODE']:
                                is_affected = False
                                
                            # 检查到达机场匹配
                            if restriction.get('ARRIVAL_AIRPORT_CODE') and flight.get('arrival_airport') != restriction['ARRIVAL_AIRPORT_CODE']:
                                is_affected = False
                            
                            # 如果航班受影响，强制取消
                            if is_affected:
                                model.constraints.add(model.x[f] == 0)
            
            # === 5.5.2 航段特殊要求约束 ===
            sector_requirements = all_constraints.get('sector_special_requirements')
            if sector_requirements is not None and not sector_requirements.empty:
                must_requirements = sector_requirements[sector_requirements['PRIORITY'] == 'MUST']
                print(f"  添加航段特殊要求约束: {len(must_requirements)} 条")
                for _, requirement in must_requirements.iterrows():
                    if requirement['REQUIREMENT_TYPE'] in ['AIRCRAFT', 'WATERCROSS']:
                        # 查找匹配的航段
                        for f in model.flights:
                            flight = flights_df.loc[f]
                            dep_match = requirement.get('DEPARTURE_AIRPORT_CODE') == flight.get('departure_airport')
                            arr_match = requirement.get('ARRIVAL_AIRPORT_CODE') == flight.get('arrival_airport')
                            
                            if dep_match and arr_match:
                                # 对于跨水运行等特殊要求，可以增加额外的延误惩罚
                                if requirement['REQUIREMENT_TYPE'] == 'WATERCROSS':
                                    # 增加特殊运行的延误惩罚（作为示例）
                                    model.constraints.add(model.d[f] >= 30 * model.x[f])  # 至少30分钟准备时间
            
            # === 5.5.3 机场特殊要求约束 ===
            airport_special_req = all_constraints.get('airport_special_requirements')
            if airport_special_req is not None and not airport_special_req.empty:
                print(f"  添加机场特殊要求约束: {len(airport_special_req)} 条")
                for _, req in airport_special_req.iterrows():
                    if req['PRIORITY'] == 'MUST':
                        # 处理机场特殊要求
                        for f in model.flights:
                            flight = flights_df.loc[f]
                            if (req.get('AIRPORT_CODE') == flight.get('departure_airport') or 
                                req.get('AIRPORT_CODE') == flight.get('arrival_airport')):
                                # 根据要求类型添加约束
                                pass  # 可以根据具体要求类型添加特定约束
            
            # === 5.5.4 航班特殊要求约束 ===
            flight_special_req = all_constraints.get('flight_special_requirements')
            if flight_special_req is not None and not flight_special_req.empty:
                print(f"  添加航班特殊要求约束: {len(flight_special_req)} 条")
                for _, req in flight_special_req.iterrows():
                    if req['PRIORITY'] == 'MUST':
                        # 处理航班特殊要求
                        for f in model.flights:
                            flight = flights_df.loc[f]
                            if req.get('FLIGHT_NUMBER') and str(flight.get('flight_number', '')).find(str(req['FLIGHT_NUMBER'])) != -1:
                                # 根据要求类型添加约束
                                pass  # 可以根据具体要求类型添加特定约束

        print("✓ 模型构建完成")
        return model

    def solve_model(self, model, solver_name='glpk'):
        """
        求解优化模型
        
        Args:
            model: 已构建的优化模型
            solver_name: 求解器名称，默认为'glpk'
            
        Returns:
            tuple: (求解器结果, 是否求解成功)
        """
        print(f"--- 开始求解模型（使用{solver_name}求解器）---")
        
        try:
            solver = pyo.SolverFactory(solver_name) 
            result = solver.solve(model, tee=False) 
            
            print(f"求解完成，求解器状态: {result.solver.status}, 终止条件: {result.solver.termination_condition}")
            
            is_optimal = result.solver.termination_condition == pyo.TerminationCondition.optimal
            return result, is_optimal
            
        except Exception as e:
            print(f"❌ 求解过程中出现错误: {str(e)}")
            return None, False