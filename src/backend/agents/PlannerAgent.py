from autoagentsai.client import ChatClient

class PlannerAgent:
    """调度规划智能体 - 负责调用优化器生成调整方案"""
    
    def __init__(self):
        self.client = ChatClient(
            agent_id="7e46d18945fc49379063e3057a143c58",
            personal_auth_key="339859fa69934ea8b2b0ebd19d94d7f1",
            personal_auth_secret="93TsBecJplOawEipqAdF7TJ0g4IoBMtA",
            base_url="https://uat.autoagents.cn"
        )

    def invoke(self, prompt: str):
        """通用的LLM调用接口"""
        content = ""
        for event in self.client.invoke(prompt="人工智能的历史"):
            if event['type'] == 'start_bubble':
                print(f"\n{'=' * 20} 消息气泡{event['bubble_id']}开始 {'=' * 20}")
                content += event['content']
        return content
    
    def create_adjustment_plan(self, flights_df, airport_res_df, weights, optimizer):
        """创建航班调整计划"""
        print(f"[PlannerAgent]: 收到规划指令，正在使用权重 {list(weights.values())} 进行优化...")
        
        # 可以调用LLM来分析数据特征和约束条件
        data_summary = self._analyze_data_characteristics(flights_df, airport_res_df)
        print(f"[PlannerAgent]: 数据分析完成 - {data_summary}")
        
        # 构建优化模型
        model = optimizer.build_model(flights_df, airport_res_df, weights)
        
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
    
    def _analyze_data_characteristics(self, flights_df, airport_res_df):
        """分析数据特征"""
        flight_count = len(flights_df)
        
        # 分析航班分布
        departure_airports = flights_df['departure_airport'].nunique() if 'departure_airport' in flights_df.columns else 0
        arrival_airports = flights_df['arrival_airport'].nunique() if 'arrival_airport' in flights_df.columns else 0
        
        # 分析限制条件
        restriction_count = len(airport_res_df) if airport_res_df is not None and not airport_res_df.empty else 0
        
        summary = f"航班数量: {flight_count}, 起飞机场: {departure_airports}, 到达机场: {arrival_airports}, 限制条件: {restriction_count}"
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
    
    def optimize_plan_with_feedback(self, flights_df, airport_res_df, weights, optimizer, feedback=None):
        """基于反馈优化调整方案"""
        print(f"[PlannerAgent]: 收到优化反馈，重新规划...")
        
        if feedback:
            print(f"[PlannerAgent]: 反馈内容: {feedback}")
            # 可以调用LLM来解析反馈并调整策略
            # adjusted_weights = self._adjust_weights_based_on_feedback(weights, feedback)
        
        # 重新生成方案
        return self.create_adjustment_plan(flights_df, airport_res_df, weights, optimizer)


if __name__ == "__main__":
    planner_agent = PlannerAgent()
    
    # 测试通用调用功能
    response = planner_agent.invoke("Hello, how are you?")
    print(f"LLM响应: {response}")
    
    # 这里可以添加更多的测试代码