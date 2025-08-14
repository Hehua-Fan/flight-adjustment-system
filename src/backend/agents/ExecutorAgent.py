from autoagentsai.client import ChatClient
from datetime import datetime
import pandas as pd

class ExecutorAgent:
    """运行执行智能体 - 负责执行最终的调整指令"""

    def __init__(self):
        self.client = ChatClient(
            agent_id="1b0e78e1bc1f475d9856123506e39ef5",
            personal_auth_key="7217394b7d3e4becab017447adeac239",
            personal_auth_secret="f4Ziua6B0NexIMBGj1tQEVpe62EhkCWB"
        )
        self.execution_log = []

    def invoke(self, prompt: str):
        """通用的LLM调用接口"""
        content = ""
        for event in self.client.invoke(prompt):
            if event['type'] == 'token':
                content += event['content']
                print(event['content'], end="", flush=True)
        return content
    
    def execute_plan(self, chosen_plan):
        """执行航班调整计划"""
        if chosen_plan is None or chosen_plan.empty:
            print("[ExecutorAgent]: 错误 - 收到空的调整计划")
            return False
        
        print(f"\n[ExecutorAgent]: 收到最终指令，开始执行调整计划...")
        print(f"[ExecutorAgent]: 计划包含 {len(chosen_plan)} 个航班的调整指令")
        
        execution_summary = {
            'total_flights': len(chosen_plan),
            'cancelled_flights': 0,
            'delayed_flights': 0,
            'executed_flights': 0,
            'total_delay_minutes': 0,
            'execution_time': datetime.now(),
            'instructions': []
        }
        
        # 逐个执行调整指令
        for index, row in chosen_plan.iterrows():
            instruction = self._generate_instruction(row)
            self._execute_single_instruction(instruction, row)
            execution_summary['instructions'].append(instruction)
            
            # 更新统计信息
            if row['status'] == '取消':
                execution_summary['cancelled_flights'] += 1
            else:
                execution_summary['executed_flights'] += 1
                if row['additional_delay_minutes'] > 0:
                    execution_summary['delayed_flights'] += 1
                    execution_summary['total_delay_minutes'] += row['additional_delay_minutes']
        
        # 记录执行日志
        self.execution_log.append(execution_summary)
        
        # 输出执行总结
        self._print_execution_summary(execution_summary)
        
        print("[ExecutorAgent]: 所有调整指令已下发完毕")
        return True
    
    def _generate_instruction(self, flight_row):
        """生成单个航班的调整指令"""
        # 兼容不同的列名
        flight_number = flight_row.get('航班号', flight_row.get('flight_number', 'UNKNOWN'))
        
        # 根据adjustment_action字段生成对应的指令
        action = flight_row.get('adjustment_action', '正常执行')
        
        if action == '取消航班':
            instruction = {
                'type': 'CANCEL_FLIGHT',
                'flight_number': flight_number,
                'reason': '根据运行优化决策',
                'message': f"取消航班 {flight_number}",
                'compensation_needed': True,
                'passenger_count': flight_row.get('旅客人数(订座)', 0)
            }
        elif action == '变更时刻':
            instruction = {
                'type': 'CHANGE_TIME',
                'flight_number': flight_number,
                'delay_minutes': flight_row['additional_delay_minutes'],
                'old_departure_time': flight_row.get('target_departure_time'),
                'new_departure_time': flight_row.get('adjusted_departure_time'),
                'message': f"航班 {flight_number} 变更起飞时间，延误 {flight_row['additional_delay_minutes']:.0f} 分钟"
            }
        elif action == '更换飞机':
            instruction = {
                'type': 'CHANGE_AIRCRAFT',
                'flight_number': flight_number,
                'reason': '飞机资源调配',
                'message': f"航班 {flight_number} 更换执行飞机",
                'requires_crew_check': True,
                'requires_maintenance_sign': True
            }
        elif action == '变更机场':
            instruction = {
                'type': 'CHANGE_AIRPORT',
                'flight_number': flight_number,
                'reason': '机场运营调整',
                'message': f"航班 {flight_number} 变更起降机场",
                'requires_atc_approval': True,
                'requires_passenger_notice': True
            }
        elif action == '变更性质':
            instruction = {
                'type': 'CHANGE_NATURE',
                'flight_number': flight_number,
                'reason': '运营性质调整',
                'message': f"航班 {flight_number} 变更航班性质",
                'requires_regulatory_approval': True
            }
        elif action == '新增航班':
            instruction = {
                'type': 'ADD_FLIGHT',
                'flight_number': flight_number,
                'reason': '运力补充或补偿',
                'message': f"新增航班 {flight_number}",
                'requires_slot_allocation': True,
                'requires_crew_assignment': True
            }
        else:  # 正常执行
            instruction = {
                'type': 'NORMAL',
                'flight_number': flight_number,
                'message': f"航班 {flight_number} 按原计划执行"
            }
        
        return instruction
    
    def _execute_single_instruction(self, instruction, flight_row):
        """执行单个调整指令"""
        print(f"  - 指令: {instruction['message']}")
        
        # 这里可以集成真实的系统接口
        # 例如：调用航班管理系统API、发送通知等
        
        if instruction['type'] == 'CANCEL_FLIGHT':
            self._handle_cancellation(instruction, flight_row)
        elif instruction['type'] == 'CHANGE_TIME':
            self._handle_time_change(instruction, flight_row)
        elif instruction['type'] == 'CHANGE_AIRCRAFT':
            self._handle_aircraft_change(instruction, flight_row)
        elif instruction['type'] == 'CHANGE_AIRPORT':
            self._handle_airport_change(instruction, flight_row)
        elif instruction['type'] == 'CHANGE_NATURE':
            self._handle_nature_change(instruction, flight_row)
        elif instruction['type'] == 'ADD_FLIGHT':
            self._handle_flight_addition(instruction, flight_row)
        else:  # NORMAL
            self._handle_normal_execution(instruction, flight_row)
    
    def _handle_cancellation(self, instruction, flight_row):
        """处理航班取消"""
        # 在真实系统中，这里会：
        # 1. 更新航班状态
        # 2. 通知相关部门
        # 3. 处理旅客改签
        # 4. 释放资源
        print(f"    └─ 处理取消指令：通知相关部门，安排旅客改签")
    
    def _handle_time_change(self, instruction, flight_row):
        """处理时刻变更"""
        # 在真实系统中，这里会：
        # 1. 更新航班时刻表
        # 2. 通知机组和地服
        # 3. 发布旅客通告
        # 4. 调整资源配置
        print(f"    └─ 处理时刻变更：延误 {instruction.get('delay_minutes', 0):.0f} 分钟，更新系统时间")
    
    def _handle_aircraft_change(self, instruction, flight_row):
        """处理飞机更换"""
        print("    └─ 处理飞机更换：协调机务、机组，确保资源到位")
        if instruction.get('requires_crew_check'):
            print("    └─ 正在检查机组资质和适配性")
        if instruction.get('requires_maintenance_sign'):
            print("    └─ 正在获取机务签署")
    
    def _handle_airport_change(self, instruction, flight_row):
        """处理机场变更"""
        print("    └─ 处理机场变更：申请空管审批，协调地面保障")
        if instruction.get('requires_atc_approval'):
            print("    └─ 正在申请空管部门审批")
        if instruction.get('requires_passenger_notice'):
            print("    └─ 正在通知旅客机场变更信息")
    
    def _handle_nature_change(self, instruction, flight_row):
        """处理性质变更"""
        print("    └─ 处理性质变更：申请监管审批，更新航班属性")
        if instruction.get('requires_regulatory_approval'):
            print("    └─ 正在申请监管部门审批")
    
    def _handle_flight_addition(self, instruction, flight_row):
        """处理新增航班"""
        print("    └─ 处理新增航班：分配时刻、机组，申请必要许可")
        if instruction.get('requires_slot_allocation'):
            print("    └─ 正在申请机场时刻分配")
        if instruction.get('requires_crew_assignment'):
            print("    └─ 正在安排机组人员")
    
    def _handle_normal_execution(self, instruction, flight_row):
        """处理正常执行"""
        # 确认航班按原计划执行
        print(f"    └─ 确认正常执行：无需特殊处理")
    
    def _print_execution_summary(self, summary):
        """打印执行总结"""
        print(f"\n[ExecutorAgent]: 执行总结")
        print(f"  总航班数: {summary['total_flights']}")
        print(f"  取消航班: {summary['cancelled_flights']}")
        print(f"  延误航班: {summary['delayed_flights']}")
        print(f"  正常执行: {summary['executed_flights'] - summary['delayed_flights']}")
        print(f"  总延误时间: {summary['total_delay_minutes']:.0f} 分钟")
        print(f"  执行时间: {summary['execution_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    def get_execution_status(self):
        """获取执行状态"""
        if not self.execution_log:
            return "无执行记录"
        
        latest_execution = self.execution_log[-1]
        return {
            'last_execution_time': latest_execution['execution_time'],
            'total_executions': len(self.execution_log),
            'latest_summary': latest_execution
        }
    
    def rollback_last_execution(self):
        """回滚最后一次执行（模拟功能）"""
        if not self.execution_log:
            print("[ExecutorAgent]: 无可回滚的执行记录")
            return False
        
        last_execution = self.execution_log[-1]
        print(f"[ExecutorAgent]: 正在回滚 {last_execution['execution_time']} 的执行...")
        
        # 在真实系统中，这里会执行反向操作
        # 例如：恢复取消的航班、撤销延误指令等
        
        print("[ExecutorAgent]: 回滚完成（模拟）")
        return True
    
    def validate_execution_feasibility(self, plan):
        """验证执行可行性"""
        issues = []
        
        # 检查时间冲突
        delayed_flights = plan[plan['additional_delay_minutes'] > 0]
        if len(delayed_flights) > 0:
            max_delay = delayed_flights['additional_delay_minutes'].max()
            if max_delay > 300:  # 超过5小时延误
                issues.append(f"存在过长延误（{max_delay:.0f}分钟），可能影响后续航班")
        
        # 检查取消比例
        cancelled_ratio = len(plan[plan['status'] == '取消']) / len(plan)
        if cancelled_ratio > 0.3:
            issues.append(f"取消比例过高（{cancelled_ratio:.1%}），可能影响运营")
        
        if issues:
            print(f"[ExecutorAgent]: 执行可行性警告: {'; '.join(issues)}")
            return False, issues
        else:
            print("[ExecutorAgent]: 执行可行性验证通过")
            return True, []


if __name__ == "__main__":
    executor_agent = ExecutorAgent()
    
    # 测试通用调用功能
    response = executor_agent.invoke("Hello, how are you?")
    print(f"LLM响应: {response}")
    
    # 创建模拟的执行计划进行测试
    test_plan = pd.DataFrame({
        'flight_number': ['CA123', 'MU456'],
        'status': ['执行', '取消'],
        'additional_delay_minutes': [30, 0],
        'adjusted_departure_time': [pd.Timestamp('2025-01-15 11:30'), pd.NaT]
    })
    
    print("\n测试执行功能:")
    executor_agent.execute_plan(test_plan)