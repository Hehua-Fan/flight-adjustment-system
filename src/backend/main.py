import sys
import os
from datetime import datetime
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from agents import MasterAgent, PlannerAgent, ExecutorAgent, WriterAgent
from tools import FlightOptimizer, FlightDataLoader


class FlightAdjustmentSystem:
    """航班调整系统主类"""
    def __init__(self):
        self.master_agent = MasterAgent()      # 运控调度智能体
        self.planner_agent = PlannerAgent()    # 调度规划智能体  
        self.executor_agent = ExecutorAgent()  # 运行执行智能体
        self.writer_agent = WriterAgent()      # 航务报告智能体
        self.optimizer = FlightOptimizer()     # 优化模型构建和求解
        self.data_loader = FlightDataLoader()  # 数据加载和处理



    def assess_problem_complexity(self, scenario_data):
        """
        使用运控调度智能体评估问题复杂度
        
        Args:
            scenario_data: 航班调整场景数据
            
        Returns:
            bool: True表示复杂问题，需要详细规划；False表示简单问题，可直接执行
        """
        print("\n=== 运控调度智能体评估问题复杂度 ===")
        
        # 构建评估提示
        assessment_prompt = f"""
        请评估以下航班调整场景的复杂度：
        
        场景ID: {scenario_data['scenario_id']}
        触发事件: {scenario_data['trigger_event']}
        受影响航班数量: {len(scenario_data['affected_flights'])}
        约束条件数量: {len(scenario_data['constraints'])}
        优先级: {scenario_data['priority']}
        
        受影响航班详情:
        {json.dumps(scenario_data['affected_flights'], ensure_ascii=False, indent=2)}
        
        约束条件:
        {json.dumps(scenario_data['constraints'], ensure_ascii=False, indent=2)}
        
        请评估：这是一个复杂的多约束优化问题吗？需要详细的调度规划吗？
        回答：简单 或 复杂
        """
        
        # 调用运控调度智能体
        response = self.master_agent.invoke(assessment_prompt)
        
        # 简单的复杂度判断逻辑
        is_complex = (
            len(scenario_data['affected_flights']) >= 3 or  # 3架以上航班
            len(scenario_data['constraints']) >= 3 or       # 3个以上约束
            '复杂' in response or 
            '详细' in response or
            '规划' in response
        )
        
        complexity_level = "复杂" if is_complex else "简单"
        print(f"✓ 复杂度评估结果: {complexity_level}")
        print(f"  评估依据: {response[:100]}...")
        
        return is_complex

    def create_adjustment_plan(self, scenario_data):
        """
        使用调度规划智能体制定调整方案
        
        Args:
            scenario_data: 航班调整场景数据
            
        Returns:
            dict: 调整规划方案
        """
        print("\n=== 调度规划智能体制定调整方案 ===")
        
        planning_prompt = f"""
        基于以下复杂航班调整场景，请制定详细的调整规划方案：
        
        场景信息:
        {json.dumps(scenario_data, ensure_ascii=False, indent=2)}
        
        请制定包括以下要素的调整方案：
        1. 优化策略选择（成本优先/运营优先/平衡策略）
        2. 关键约束分析
        3. 预期调整措施
        4. 风险评估
        
        请提供具体的规划建议。
        """
        
        planning_response = self.planner_agent.invoke(planning_prompt)
        
        # 基于响应内容选择优化策略
        if '成本' in planning_response or '收入' in planning_response:
            strategy = 'cost_focused'
        elif '运营' in planning_response or '准点' in planning_response:
            strategy = 'ops_focused'  
        else:
            strategy = 'balanced'
            
        plan = {
            "strategy": strategy,
            "planning_response": planning_response,
            "recommended_approach": "基于多约束优化的航班调整方案"
        }
        
        print(f"✓ 规划方案制定完成")
        print(f"  推荐策略: {strategy}")
        print(f"  规划要点: {planning_response[:100]}...")
        
        return plan

    def execute_optimization(self, scenario_data, plan=None):
        """
        使用运行执行智能体调用优化器进行航班调整
        
        Args:
            scenario_data: 航班调整场景数据
            plan: 调整规划方案（可选）
            
        Returns:
            pandas.DataFrame: 优化结果
        """
        print("\n=== 运行执行智能体执行优化算法 ===")
        
        # 确定优化策略
        strategy = plan['strategy'] if plan else 'balanced'
        
        execution_prompt = f"""
        执行航班调整优化任务：
        
        场景: {scenario_data['scenario_id']}
        策略: {strategy}
        
        正在调用航班优化算法工具进行计算...
        """
        
        execution_response = self.executor_agent.invoke(execution_prompt)
        print(f"✓ 执行智能体响应: {execution_response[:100]}...")
        
        try:
            # 步骤1: 准备数据
            print("  正在准备优化数据...")
            flights_df, airport_res_df = self.data_loader.load_data()
            
            # 步骤2: 获取权重配置
            weights = self.data_loader.get_weights_for_strategy(strategy)
            
            # 步骤3: 获取所有约束数据
            print("  正在获取约束数据...")
            all_constraints = self.data_loader.get_all_constraints()
            
            # 步骤4: 构建模型
            print("  正在构建优化模型...")
            model = self.optimizer.build_model(flights_df, airport_res_df, weights, all_constraints)
            
            # 步骤5: 求解模型
            print("  正在求解优化模型...")
            result, is_optimal = self.optimizer.solve_model(model)
            
            # 步骤6: 处理结果
            if is_optimal:
                print("  正在处理优化结果...")
                optimization_result = self.data_loader.process_optimization_results(model, result, flights_df)
                
                if optimization_result is not None:
                    print(f"✓ 优化计算完成，共处理 {len(optimization_result)} 架次航班")
                    return optimization_result
                else:
                    print("✗ 结果处理失败")
                    return None
            else:
                print("✗ 优化求解失败")
                return None
                
        except Exception as e:
            print(f"✗ 优化过程中出现异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def generate_report(self, scenario_data, optimization_result, plan=None):
        """
        使用航务报告智能体生成调整报告
        
        Args:
            scenario_data: 原始场景数据
            optimization_result: 优化结果
            plan: 调整规划方案（可选）
            
        Returns:
            str: 调整报告
        """
        print("\n=== 航务报告智能体生成调整报告 ===")
        
        if optimization_result is None:
            report_prompt = """
            航班调整优化失败，请生成异常情况报告，说明可能的原因和后续建议。
            """
        else:
            # 统计优化结果
            total_flights = len(optimization_result)
            canceled_flights = len(optimization_result[optimization_result['status'] == '取消'])
            delayed_flights = len(optimization_result[optimization_result['delay_minutes'] > 0])
            total_delay = optimization_result['delay_minutes'].sum()
            
            results_summary = {
                "总航班数": total_flights,
                "取消航班数": canceled_flights, 
                "延误航班数": delayed_flights,
                "总延误时间": f"{total_delay}分钟",
                "详细结果": optimization_result.to_dict('records')
            }
            
            report_prompt = f"""
            请基于以下航班调整优化结果生成专业的航务调整报告：
            
            原始场景:
            {json.dumps(scenario_data, ensure_ascii=False, indent=2)}
            
            优化结果统计:
            {json.dumps(results_summary, ensure_ascii=False, indent=2)}
            
            请生成包含以下内容的正式报告：
            1. 调整概况
            2. 主要调整措施
            3. 影响分析
            4. 建议与总结
            
            报告应专业、简洁、重点突出。
            """
        
        # 生成报告
        report = self.writer_agent.invoke(report_prompt)
        
        print("✓ 航务调整报告生成完成")
        print(f"  报告长度: {len(report)} 字符")
        
        return report

    def run(self):
        """运行完整的航班调整流程"""
        print("🛫 === 航班调整系统开始运行 ===")
        start_time = datetime.now()
        
        try:
            # 步骤1: 准备场景数据
            scenario_data = {
                "scenario_id": "FLIGHT_ADJ_001",
                "timestamp": datetime.now().isoformat(),
                "trigger_event": "航班调度优化需求",
                "priority": "标准"
            }
            
            # 步骤2: 运控调度智能体评估问题复杂度  
            is_complex = self.assess_problem_complexity(scenario_data)
            
            # 步骤3: 根据复杂度决定是否需要详细规划
            plan = None
            if is_complex:
                plan = self.create_adjustment_plan(scenario_data)
            else:
                print("\n=== 简单问题，跳过详细规划，直接执行优化 ===")
            
            # 步骤4: 运行执行智能体执行优化
            optimization_result = self.execute_optimization(scenario_data, plan)
            
            # 步骤5: 航务报告智能体生成报告
            final_report = self.generate_report(scenario_data, optimization_result, plan)
            
            # 显示最终结果
            print("\n" + "="*60)
            print("🎯 === 航班调整系统执行完成 ===")
            print("="*60)
            
            if optimization_result is not None:
                print("\n📊 优化结果概览:")
                print(optimization_result.to_string())
            
            print(f"\n📋 航务调整报告:")
            print("-" * 40)
            print(final_report)
            print("-" * 40)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"\n⏱️  总执行时间: {duration:.2f} 秒")
            print("✅ 系统运行成功完成")
            
        except Exception as e:
            print(f"\n❌ 系统运行出现异常: {str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """主函数入口"""
    print("🚀 启动航班调整系统...")
    
    # 创建并运行系统
    system = FlightAdjustmentSystem()
    system.run()


if __name__ == "__main__":
    main()
