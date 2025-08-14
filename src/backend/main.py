import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from agents import MasterAgent, PlannerAgent, ExecutorAgent, WriterAgent
from tools import Optimizer, DataLoader


class FlightAdjustmentSystem:
    """航班调整系统主类"""
    def __init__(self):
        self.master_agent = MasterAgent()      # 运控调度智能体
        self.planner_agent = PlannerAgent()    # 调度规划智能体  
        self.executor_agent = ExecutorAgent()  # 运行执行智能体
        self.writer_agent = WriterAgent()      # 航务报告智能体
        self.optimizer = Optimizer()           # 优化模型构建和求解
        self.data_loader = DataLoader()        # 数据加载和处理

    def run(self, event_description: str, cdm_data_file_path: str, constraint_dir_path: str):
        """
        运行航班调整场景
        """        
        try:
            # 1. 指挥智能体分析事件，生成多种策略权重
            print("[系统]: 步骤1 - 事件分析和策略生成")
            weights = self.master_agent.get_weights(event_description)
            
            # 2. 数据加载器处理最新的CDM数据
            print("[系统]: 步骤2 - 数据加载和预处理")
            cdm_data = self.data_loader.load_cdm_data(cdm_data_file_path).copy()
            constraint_data = self.data_loader.load_constraint_data(constraint_dir_path, filter_active=True)

            # 3. 规划智能体为每种权重方案生成调整计划
            print("[系统]: 步骤3 - 生成调整方案")
            solutions = {}
            for name, weights in weights.items():
                print(f"[系统]: 正在生成 {name} 方案...")
                solution = self.planner_agent.create_adjustment_plan(
                    cdm_data, 
                    constraint_data, 
                    weights, 
                    self.optimizer
                )
                solutions[name] = solution
                
                # 验证方案
                if solution is not None:
                    is_valid, validation_msg = self.planner_agent.validate_plan(solution, cdm_data)
                    if not is_valid:
                        print(f"[系统]: 警告 - {name} 方案验证失败: {validation_msg}")
                
            # 4. 指挥智能体解读方案，并辅助决策出最终计划
            print("[系统]: 步骤4 - 方案分析和决策")
            chosen_plan_name, final_plan = self.master_agent.interpret_and_present_solutions(solutions)
            
            if final_plan is None or final_plan.empty:
                print("[系统]: 未能决策出最终方案，流程终止。")
                return False

            # 5. 执行智能体验证可行性并下发最终的调整指令
            print("[系统]: 步骤5 - 执行调整指令")
            is_feasible, feasibility_issues = self.executor_agent.validate_execution_feasibility(final_plan)
            if not is_feasible:
                print(f"[系统]: 执行可行性检查失败: {'; '.join(feasibility_issues)}")
                print("[系统]: 继续执行但需要人工确认...")
            
            execution_success = self.executor_agent.execute_plan(final_plan)
            if not execution_success:
                print("[系统]: 执行失败，流程异常终止。")
                return False
            
            # 获取执行状态
            execution_status = self.executor_agent.get_execution_status()
            
            # 6. 报告智能体生成本次事件的复盘报告
            print("[系统]: 步骤6 - 生成复盘报告")
            final_report = self.writer_agent.generate_report(
                event_description, 
                chosen_plan_name, 
                final_plan, 
                execution_status.get('latest_summary') if execution_status != "无执行记录" else None
            )
            
            print(f"\n[系统]: 处理完成！智能报告已生成。")
            print(f"{'='*20} 事件处理完毕 {'='*20}")
            return True
            
        except Exception as e:
            print(f"[系统]: 系统运行异常: {e}")
            print(f"{'='*20} 事件处理异常终止 {'='*20}")
            return False
    



# =============================================================================
#  程序主入口
# =============================================================================
if __name__ == "__main__":
    # 初始化系统
    flight_adjustment_system = FlightAdjustmentSystem()

    # 定义本次需要处理的数据文件
    cdm_data_file_path = 'assets/cdm/cdm_cleaned.xlsx'
    constraint_dir_path = 'assets/restriction'
    
    # 模拟一个外部事件触发系统
    event_description = "上海区域流量控制，多个航班收到CTOT指令"
    
    # 运行完整的场景处理流程
    result = flight_adjustment_system.run(event_description, cdm_data_file_path, constraint_dir_path)
    print(result)