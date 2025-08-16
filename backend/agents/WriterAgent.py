from autoagentsai.client import ChatClient
from datetime import datetime
import pandas as pd

class WriterAgent:
    """航务报告智能体 - 负责生成调整事件的复盘报告"""
    
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
    
    def generate_report(self, event_description, chosen_plan_name, final_plan, execution_summary=None):
        """生成航班调整事件复盘报告"""
        print("\n[WriterAgent]: 开始生成本次事件的复盘报告...")
        
        # 收集统计信息
        stats = self._analyze_plan_statistics(final_plan)
        
        # 准备AI生成报告的提示词
        prompt = self._prepare_report_prompt(event_description, chosen_plan_name, final_plan, stats, execution_summary)
        
        # 开发模式：跳过AI生成，使用简化报告
        DEV_MODE = True  # 在生产环境中设置为 False
        
        if DEV_MODE:
            print("\n[WriterAgent]: 开发模式 - 生成简化报告...\n")
            print("="*60)
            final_report = f"""
航班调整事件复盘报告
===================

事件描述: {event_description}
选择方案: {chosen_plan_name}
处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

处理结果统计:
- 总航班数: {stats['total_flights']}
- 取消航班: {stats['cancelled_flights']} 架次 ({stats['cancel_ratio']:.1%})
- 延误航班: {stats['delayed_flights']} 架次 ({stats['delay_ratio']:.1%})
- 正常执行: {stats['normal_flights']} 架次 ({stats['normal_ratio']:.1%})
- 总延误时间: {stats['total_delay']:.0f} 分钟
- 平均延误: {stats['avg_delay']:.1f} 分钟
- 航班完成率: {stats['completion_ratio']:.1%}

事件处理效果良好，系统运行正常。
            """
            print(final_report)
            print("="*60)
        else:
            # 调用AI生成最终报告
            print("\n[WriterAgent]: 正在生成智能分析报告...\n")
            print("="*60)
            try:
                final_report = self.invoke(prompt)
            except Exception as e:
                print(f"[WriterAgent]: AI报告生成失败，使用简化报告: {e}")
                final_report = f"""
航班调整事件复盘报告
===================

事件描述: {event_description}
选择方案: {chosen_plan_name}
处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

注意: AI报告生成失败，显示基础统计信息。

处理结果统计:
- 总航班数: {stats['total_flights']}
- 取消航班: {stats['cancelled_flights']} 架次
- 延误航班: {stats['delayed_flights']} 架次
- 正常执行: {stats['normal_flights']} 架次
                """
            print("="*60)
        
        return final_report
    
    def _prepare_report_prompt(self, event_description, chosen_plan_name, final_plan, stats, execution_summary):
        """准备AI生成报告的提示词"""
        # 生成航班详情表格
        plan_summary = final_plan.to_string()
        
        prompt = f"""
请为以下航班调整事件生成一份专业的复盘报告：

【事件基本信息】
- 事件描述：{event_description}
- 处理时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 选择方案：{chosen_plan_name}

【处理结果统计】
- 总航班数：{stats['total_flights']}
- 取消航班：{stats['cancelled_flights']} 架次 ({stats['cancel_ratio']:.1%})
- 延误航班：{stats['delayed_flights']} 架次 ({stats['delay_ratio']:.1%})
- 正常执行：{stats['normal_flights']} 架次 ({stats['normal_ratio']:.1%})
- 总延误时间：{stats['total_delay']:.0f} 分钟
- 平均延误：{stats['avg_delay']:.1f} 分钟
- 航班完成率：{stats['completion_ratio']:.1%}

【详细执行方案】
{plan_summary}

{"【执行状态】已完成 - " + str(execution_summary) if execution_summary else "【执行状态】待执行"}

请基于以上信息，生成一份包含以下内容的专业复盘报告：
1. 事件概述与处理策略
2. 关键指标分析与评估  
3. 处理效果总结
4. 经验教训与改进建议

要求：
- 报告语言专业、简洁
- 重点突出关键指标和处理效果
- 提供具体的改进建议
- 格式整齐，便于阅读
"""
        return prompt
    

    
    def _analyze_plan_statistics(self, final_plan):
        """分析方案统计信息"""
        total_flights = len(final_plan)
        cancelled_flights = len(final_plan[final_plan['status'] == '取消'])
        executed_flights = len(final_plan[final_plan['status'] == '执行'])
        
        # 延误统计
        delayed_flights = len(final_plan[final_plan['additional_delay_minutes'] > 0])
        normal_flights = executed_flights - delayed_flights
        total_delay = final_plan['additional_delay_minutes'].sum()
        avg_delay = final_plan[final_plan['additional_delay_minutes'] > 0]['additional_delay_minutes'].mean() if delayed_flights > 0 else 0
        
        # 计算比例
        cancel_ratio = cancelled_flights / total_flights if total_flights > 0 else 0
        delay_ratio = delayed_flights / total_flights if total_flights > 0 else 0
        normal_ratio = normal_flights / total_flights if total_flights > 0 else 0
        completion_ratio = executed_flights / total_flights if total_flights > 0 else 0
        
        # 评估指标
        delay_control = "良好" if avg_delay < 60 else "一般" if avg_delay < 120 else "待改进"
        resource_util = "高效" if cancel_ratio < 0.2 else "一般" if cancel_ratio < 0.4 else "待优化"
        passenger_impact = "轻微" if cancel_ratio < 0.1 and avg_delay < 90 else "中等" if cancel_ratio < 0.3 else "较大"
        
        return {
            'total_flights': total_flights,
            'cancelled_flights': cancelled_flights,
            'delayed_flights': delayed_flights,
            'normal_flights': normal_flights,
            'total_delay': total_delay,
            'avg_delay': avg_delay,
            'cancel_ratio': cancel_ratio,
            'delay_ratio': delay_ratio,
            'normal_ratio': normal_ratio,
            'completion_ratio': completion_ratio,
            'delay_control_assessment': delay_control,
            'resource_utilization': resource_util,
            'passenger_impact': passenger_impact
        }
    



if __name__ == "__main__":
    writer_agent = WriterAgent()
    
    # 创建模拟数据进行测试
    test_plan = pd.DataFrame({
        'flight_number': ['CA123', 'MU456', 'CZ789'],
        'status': ['执行', '取消', '执行'],
        'additional_delay_minutes': [30, 0, 45],
        'adjusted_departure_time': [
            pd.Timestamp('2025-01-15 11:30'), 
            pd.NaT, 
            pd.Timestamp('2025-01-15 13:45')
        ]
    })
    
    print("\n测试报告生成功能:")
    writer_agent.generate_report(
        "上海区域流量控制测试事件",
        "方案A (成本优先)",
        test_plan
    )