from autoagentsai.client import ChatClient

class MasterAgent:
    """运控调度智能体 (LLM大脑) - 负责事件分析、策略生成和决策"""
    
    def __init__(self):
        self.client = ChatClient(
    agent_id="7e46d18945fc49379063e3057a143c58",
    personal_auth_key="339859fa69934ea8b2b0ebd19d94d7f1",
    personal_auth_secret="93TsBecJplOawEipqAdF7TJ0g4IoBMtA"
)

    def invoke(self, prompt: str):
        """通用的LLM调用接口"""
        content = ""
        for event in self.client.invoke(prompt):
            print(event.content, end="", flush=True)
            content += event.content
        return content
    
    def get_weights(self, event_description):
        """分析事件并生成多套权重方案"""
        print(f"[MasterAgent]: 正在分析事件: '{event_description}'")
        
        # 可以调用LLM来智能分析事件类型
        llm_prompt = f"""
        请分析以下航班调度事件，并判断事件类型和严重程度：
        事件描述: {event_description}
        
        请返回事件分析结果。
        """
        analysis = self.invoke(llm_prompt)
        
        # 基于事件类型生成权重方案
        if "流量控制" in event_description:
            print("[MasterAgent]: 判断为流量控制事件，生成对应权重方案。")
            weights_A = {'cancel': 1.0, 'delay': 0.1, 'late_pax': 0.5, 'revenue': 1.0}
            weights_B = {'cancel': 0.5, 'delay': 1.0, 'late_pax': 1.0, 'revenue': 0.2}
        elif "天气" in event_description:
            print("[MasterAgent]: 判断为天气事件，生成对应权重方案。")
            weights_A = {'cancel': 0.8, 'delay': 0.3, 'late_pax': 1.0, 'revenue': 0.8}
            weights_B = {'cancel': 0.3, 'delay': 1.5, 'late_pax': 1.2, 'revenue': 0.5}
        elif "设备故障" in event_description:
            print("[MasterAgent]: 判断为设备故障事件，生成对应权重方案。")
            weights_A = {'cancel': 1.2, 'delay': 0.2, 'late_pax': 0.8, 'revenue': 1.0}
            weights_B = {'cancel': 0.6, 'delay': 1.3, 'late_pax': 1.0, 'revenue': 0.4}
        else:
            print("[MasterAgent]: 使用默认权重方案。")
            weights_A = {'cancel': 1.0, 'delay': 0.1, 'late_pax': 0.5, 'revenue': 1.0}
            weights_B = {'cancel': 0.5, 'delay': 1.0, 'late_pax': 1.0, 'revenue': 0.2}
        
        return {
            "方案A (成本优先)": weights_A, 
            "方案B (运营优先)": weights_B
        }
    
    def interpret_and_present_solutions(self, solutions):
        """解读和对比优化方案，辅助决策"""
        print("\n[MasterAgent]: 接收到优化方案，正在进行解读和对比...")
        
        # 分析每个方案
        analysis_results = {}
        for name, result_df in solutions.items():
            if result_df is not None:
                cancelled_count = result_df[result_df['status'] == '取消'].shape[0]
                executed_count = result_df[result_df['status'] == '执行'].shape[0]
                total_delay = result_df['additional_delay_minutes'].sum()
                
                analysis_results[name] = {
                    'cancelled_count': cancelled_count,
                    'executed_count': executed_count,
                    'total_delay': total_delay
                }
                
                print(f"\n--- {name} ---")
                print(f"解读: 此方案建议取消 {cancelled_count} 个航班，保留 {executed_count} 个航班")
                print(f"     总附加延误为 {total_delay:.0f} 分钟")
                print(result_df.to_string())
        
        # 智能决策逻辑（可以调用LLM辅助决策）
        chosen_plan_name = self._make_decision(analysis_results, solutions)
        
        print(f"\n[MasterAgent]: 基于综合分析，推荐方案: '{chosen_plan_name}'")
        return chosen_plan_name, solutions.get(chosen_plan_name)
    
    def _make_decision(self, analysis_results, solutions):
        """内部决策逻辑"""
        # 简单的决策规则：优先选择取消航班较少且总延误较小的方案
        best_plan = None
        best_score = float('inf')
        
        for plan_name, metrics in analysis_results.items():
            # 计算综合评分：取消航班数 * 1000 + 总延误时间
            score = metrics['cancelled_count'] * 1000 + metrics['total_delay']
            if score < best_score:
                best_score = score
                best_plan = plan_name
        
        # 如果没有找到合适方案，选择第一个可用方案
        if best_plan is None:
            best_plan = next((name for name, df in solutions.items() if df is not None), None)
        
        return best_plan


if __name__ == "__main__":
    master_agent = MasterAgent()
    
    # 测试事件分析功能
    event = "上海区域流量控制，多个航班收到CTOT指令"
    weights = master_agent.get_weights(event)
    print(f"生成的权重方案: {weights}")
    
    # 测试通用调用功能
    response = master_agent.invoke("Hello, how are you?")
    print(f"LLM响应: {response}")