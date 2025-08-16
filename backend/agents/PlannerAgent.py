from autoagentsai.client import ChatClient

class PlannerAgent:
    """调度规划智能体 - 负责调用优化器生成调整方案"""
    
    def __init__(self):
        self.client = ChatClient(
            agent_id="1b0e78e1bc1f475d9856123506e39ef5",
            personal_auth_key="7217394b7d3e4becab017447adeac239",
            personal_auth_secret="f4Ziua6B0NexIMBGj1tQEVpe62EhkCWB"
        )

    def invoke(self, prompt: str):
        """通用的LLM调用接口"""
        content = ""
        for event in self.client.invoke(prompt):
            if event['type'] == 'token':
                content += event['content']
                print(event['content'], end="", flush=True)
        return content
    
    def create_adjustment_plan(self, flights_df, constraint_data, weights, optimizer):
        """创建航班调整计划"""
        print(f"[PlannerAgent]: 收到规划指令，正在使用权重 {list(weights.values())} 进行优化...")
        
        # 可以调用LLM来分析数据特征和约束条件
        data_summary = self._analyze_data_characteristics(flights_df, constraint_data)
        print(f"[PlannerAgent]: 数据分析完成 - {data_summary}")
        
        # 构建优化模型
        model = optimizer.build_model(flights_df, constraint_data, weights)
        
        if model is None:
            print("[PlannerAgent]: 模型构建失败")
            return None
        
        # 求解模型
        result = optimizer.solve_model(model)
        
        if result is None:
            print("[PlannerAgent]: 模型求解失败")
            return None
        
        # 提取结果
        solution_df = optimizer.get_optimization_results(model, flights_df, result)
        
        if solution_df is not None:
            print(f"[PlannerAgent]: 优化完成，生成 {len(solution_df)} 个航班的调整方案")
        else:
            print("[PlannerAgent]: 结果提取失败")
            
        return solution_df
    
    def _analyze_data_characteristics(self, flights_df, constraint_data):
        """分析数据特征"""
        flight_count = len(flights_df)
        
        # 分析航班分布
        departure_airports = flights_df['计划起飞机场'].nunique() if '计划起飞机场' in flights_df.columns else (
            flights_df['departure_airport'].nunique() if 'departure_airport' in flights_df.columns else 0
        )
        arrival_airports = flights_df['计划落地机场'].nunique() if '计划落地机场' in flights_df.columns else (
            flights_df['arrival_airport'].nunique() if 'arrival_airport' in flights_df.columns else 0
        )
        
        # 分析限制条件
        total_restriction_count = 0
        if constraint_data and isinstance(constraint_data, dict):
            for constraint_type, df in constraint_data.items():
                if df is not None and not df.empty:
                    total_restriction_count += len(df)
        
        print(f"[PlannerAgent]: ===== 数据特征分析 =====")
        print(f"✓ 航班数据:")
        print(f"  - 总航班数: {flight_count}")
        print(f"  - 起飞机场数: {departure_airports}")
        print(f"  - 到达机场数: {arrival_airports}")
        
        # 分析约束条件详情
        print(f"✓ 约束条件详情:")
        constraint_details = {}
        if constraint_data and isinstance(constraint_data, dict):
            for constraint_type, df in constraint_data.items():
                count = len(df) if df is not None and not df.empty else 0
                constraint_details[constraint_type] = count
                print(f"  - {constraint_type}: {count} 条")
        
        print(f"  - 总约束条数: {total_restriction_count}")
        print(f"[PlannerAgent]: ===========================")
        
        summary = f"航班数量: {flight_count}, 起飞机场: {departure_airports}, 到达机场: {arrival_airports}, 限制条件: {total_restriction_count}"
        return summary
    
    def validate_plan(self, solution_df, flights_df):
        """验证生成的调整方案"""
        if solution_df is None or solution_df.empty:
            return False, "方案为空"
        
        # 检查基本约束
        cancelled_flights = solution_df[solution_df['status'] == '取消']
        executed_flights = solution_df[solution_df['status'] == '执行']
        
        # 验证逻辑
        issues = []
        
        # 检查是否有无效的延误时间
        invalid_delays = executed_flights[executed_flights['additional_delay_minutes'] < 0]
        if not invalid_delays.empty:
            issues.append(f"发现 {len(invalid_delays)} 个航班有负延误时间")
        
        # 检查取消比例是否过高
        cancel_ratio = len(cancelled_flights) / len(solution_df)
        if cancel_ratio > 0.5:
            issues.append(f"取消航班比例过高: {cancel_ratio:.2%}")
        
        if issues:
            return False, "; ".join(issues)
        else:
            return True, "方案验证通过"
    
    def optimize_plan_with_feedback(self, flights_df, constraint_data, weights, optimizer, feedback=None):
        """基于反馈优化调整方案"""
        print(f"[PlannerAgent]: 收到优化反馈，重新规划...")
        
        if feedback:
            print(f"[PlannerAgent]: 反馈内容: {feedback}")
            # 可以调用LLM来解析反馈并调整策略
            # adjusted_weights = self._adjust_weights_based_on_feedback(weights, feedback)
        
        # 重新生成方案
        return self.create_adjustment_plan(flights_df, constraint_data, weights, optimizer)


if __name__ == "__main__":
    planner_agent = PlannerAgent()
    
    # 测试通用调用功能
    response = planner_agent.invoke("Hello, how are you?")
    print(f"LLM响应: {response}")
    
    # 这里可以添加更多的测试代码