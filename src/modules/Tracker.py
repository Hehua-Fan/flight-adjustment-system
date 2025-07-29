import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from ..types.execution_models import (
    ExecutionStage, MetricType, ExecutionEvent, 
    PerformanceMetrics, ExecutionRecord
)


class ExecutionTrackingSystem:
    """
    执行跟踪与效果评估模块
    负责跟踪调整方案的执行状态并评估效果
    """
    
    def __init__(self):
        self.execution_records: Dict[str, ExecutionRecord] = {}
        self.event_handlers: List[Callable[[ExecutionEvent], None]] = []
        self.evaluation_handlers: List[Callable[[ExecutionRecord], None]] = []
        
        # 评估权重配置
        self.evaluation_weights = {
            MetricType.TIMING_ACCURACY: 0.25,
            MetricType.COST_VARIANCE: 0.20,
            MetricType.PASSENGER_IMPACT: 0.20,
            MetricType.OPERATIONAL_EFFICIENCY: 0.15,
            MetricType.SAFETY_COMPLIANCE: 0.15,
            MetricType.CUSTOMER_SATISFACTION: 0.05
        }
        
        # 基准值配置
        self.benchmarks = {
            "timing_accuracy_threshold": 0.9,      # 90%时间准确性
            "cost_variance_threshold": 0.1,        # 10%成本差异
            "passenger_satisfaction_threshold": 7.0,  # 7分客户满意度
            "operational_efficiency_threshold": 0.8,  # 80%运行效率
            "safety_compliance_threshold": 1.0     # 100%安全合规
        }
    
    def start_tracking(self, adjustment_plan: Dict[str, Any], decision_id: str = None) -> str:
        """开始跟踪调整方案执行"""
        
        tracking_id = str(uuid.uuid4())
        
        # 创建执行记录
        record = ExecutionRecord(
            tracking_id=tracking_id,
            adjustment_plan=adjustment_plan,
            decision_id=decision_id,
            performance_metrics=self._initialize_performance_metrics(adjustment_plan)
        )
        
        # 添加初始事件
        initial_event = ExecutionEvent(
            event_id=str(uuid.uuid4()),
            stage=ExecutionStage.APPROVED,
            timestamp=datetime.now(),
            operator="system",
            description="调整方案开始执行跟踪"
        )
        
        record.execution_events.append(initial_event)
        self.execution_records[tracking_id] = record
        
        # 通知事件处理器
        self._notify_event_handlers(initial_event)
        
        return tracking_id
    
    def update_stage(self, 
                    tracking_id: str, 
                    new_stage: ExecutionStage,
                    operator: str,
                    description: str = "",
                    data: Dict[str, Any] = None,
                    issues: List[str] = None) -> bool:
        """更新执行阶段"""
        
        if tracking_id not in self.execution_records:
            return False
        
        record = self.execution_records[tracking_id]
        
        # 验证阶段转换是否合法
        if not self._is_valid_stage_transition(record.current_stage, new_stage):
            return False
        
        # 创建执行事件
        event = ExecutionEvent(
            event_id=str(uuid.uuid4()),
            stage=new_stage,
            timestamp=datetime.now(),
            operator=operator,
            description=description or f"阶段更新为 {new_stage.value}",
            data=data or {},
            issues=issues or []
        )
        
        # 更新记录
        record.execution_events.append(event)
        record.current_stage = new_stage
        
        # 如果完成或失败，设置完成时间
        if new_stage in [ExecutionStage.COMPLETED, ExecutionStage.FAILED, ExecutionStage.CANCELLED]:
            record.completed_at = datetime.now()
            
            # 如果完成，开始效果评估
            if new_stage == ExecutionStage.COMPLETED:
                self._start_effectiveness_evaluation(record)
        
        # 通知事件处理器
        self._notify_event_handlers(event)
        
        return True
    
    def get_execution_status(self, tracking_id: str) -> Dict[str, Any]:
        """获取执行状态"""
        
        if tracking_id not in self.execution_records:
            return {"error": "执行记录不存在"}
        
        record = self.execution_records[tracking_id]
        
        return {
            "tracking_id": tracking_id,
            "current_stage": record.current_stage.value,
            "adjustment_plan": record.adjustment_plan,
            "decision_id": record.decision_id,
            "created_at": record.created_at.isoformat(),
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "execution_duration": self._calculate_execution_duration(record),
            "events_count": len(record.execution_events),
            "latest_event": self._get_latest_event_summary(record),
            "performance_metrics": self._serialize_performance_metrics(record.performance_metrics),
            "effectiveness_score": record.effectiveness_score,
            "has_issues": any(event.issues for event in record.execution_events)
        }
    
    def get_execution_timeline(self, tracking_id: str) -> List[Dict[str, Any]]:
        """获取执行时间线"""
        
        if tracking_id not in self.execution_records:
            return []
        
        record = self.execution_records[tracking_id]
        
        timeline = []
        for event in record.execution_events:
            timeline.append({
                "event_id": event.event_id,
                "stage": event.stage.value,
                "timestamp": event.timestamp.isoformat(),
                "operator": event.operator,
                "description": event.description,
                "data": event.data,
                "issues": event.issues
            })
        
        return timeline
    
    def evaluate_effectiveness(self, tracking_id: str) -> Dict[str, Any]:
        """评估执行效果"""
        
        if tracking_id not in self.execution_records:
            return {"error": "执行记录不存在"}
        
        record = self.execution_records[tracking_id]
        
        if record.current_stage != ExecutionStage.COMPLETED:
            return {"error": "执行尚未完成，无法评估效果"}
        
        # 执行详细评估
        evaluation_result = self._perform_detailed_evaluation(record)
        
        # 更新记录
        record.effectiveness_score = evaluation_result["overall_score"]
        record.lessons_learned = evaluation_result["lessons_learned"]
        record.recommendations = evaluation_result["recommendations"]
        
        # 更新阶段为已验证
        self.update_stage(
            tracking_id, 
            ExecutionStage.VERIFIED,
            "system",
            "效果评估完成"
        )
        
        return evaluation_result
    
    def get_execution_statistics(self, 
                               start_date: datetime = None,
                               end_date: datetime = None) -> Dict[str, Any]:
        """获取执行统计信息"""
        
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
        
        # 筛选时间范围内的记录
        filtered_records = [
            record for record in self.execution_records.values()
            if start_date <= record.created_at <= end_date
        ]
        
        if not filtered_records:
            return {"total_executions": 0}
        
        # 统计信息
        total_executions = len(filtered_records)
        completed_executions = len([r for r in filtered_records 
                                  if r.current_stage == ExecutionStage.COMPLETED])
        failed_executions = len([r for r in filtered_records 
                               if r.current_stage == ExecutionStage.FAILED])
        
        # 阶段分布
        stage_distribution = {}
        for record in filtered_records:
            stage = record.current_stage.value
            stage_distribution[stage] = stage_distribution.get(stage, 0) + 1
        
        # 平均执行时间
        completed_records = [r for r in filtered_records if r.completed_at]
        avg_execution_time = timedelta()
        if completed_records:
            total_time = sum([r.completed_at - r.created_at for r in completed_records], timedelta())
            avg_execution_time = total_time / len(completed_records)
        
        # 平均效果评分
        scored_records = [r for r in filtered_records if r.effectiveness_score is not None]
        avg_effectiveness = 0.0
        if scored_records:
            avg_effectiveness = sum(r.effectiveness_score for r in scored_records) / len(scored_records)
        
        # 按调整类型分组
        action_distribution = {}
        for record in filtered_records:
            action = record.adjustment_plan.get("action", "unknown")
            action_distribution[action] = action_distribution.get(action, 0) + 1
        
        return {
            "total_executions": total_executions,
            "completed_executions": completed_executions,
            "failed_executions": failed_executions,
            "success_rate": completed_executions / total_executions if total_executions > 0 else 0,
            "stage_distribution": stage_distribution,
            "average_execution_time_minutes": avg_execution_time.total_seconds() / 60,
            "average_effectiveness_score": avg_effectiveness,
            "action_distribution": action_distribution,
            "evaluations_completed": len(scored_records)
        }
    
    def get_lessons_learned(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取经验教训"""
        
        # 收集所有已完成评估的记录
        evaluated_records = [
            record for record in self.execution_records.values()
            if record.effectiveness_score is not None and record.lessons_learned
        ]
        
        # 按效果评分排序，获取最佳和最差的案例
        evaluated_records.sort(key=lambda r: r.effectiveness_score)
        
        lessons = []
        
        # 最差案例的教训
        for record in evaluated_records[:limit//2]:
            lessons.append({
                "type": "improvement_needed",
                "tracking_id": record.tracking_id,
                "effectiveness_score": record.effectiveness_score,
                "adjustment_action": record.adjustment_plan.get("action"),
                "lessons": record.lessons_learned,
                "recommendations": record.recommendations
            })
        
        # 最佳案例的经验
        for record in evaluated_records[-limit//2:]:
            lessons.append({
                "type": "best_practice",
                "tracking_id": record.tracking_id,
                "effectiveness_score": record.effectiveness_score,
                "adjustment_action": record.adjustment_plan.get("action"),
                "lessons": record.lessons_learned,
                "recommendations": record.recommendations
            })
        
        return lessons
    
    def add_event_handler(self, handler: Callable[[ExecutionEvent], None]):
        """添加事件处理器"""
        self.event_handlers.append(handler)
    
    def add_evaluation_handler(self, handler: Callable[[ExecutionRecord], None]):
        """添加评估处理器"""
        self.evaluation_handlers.append(handler)
    
    # 私有方法
    def _initialize_performance_metrics(self, adjustment_plan: Dict[str, Any]) -> PerformanceMetrics:
        """初始化性能指标"""
        
        action = adjustment_plan.get("action", "")
        
        # 根据调整类型估算计划执行时间和成本
        if action == "CHANGE_TIME":
            planned_duration = timedelta(minutes=15)
            planned_cost = 1000.0
        elif action == "CHANGE_AIRCRAFT":
            planned_duration = timedelta(minutes=45)
            planned_cost = 5000.0
        elif action == "CANCEL_FLIGHT":
            planned_duration = timedelta(minutes=30)
            planned_cost = 15000.0
        elif action == "CHANGE_AIRPORT":
            planned_duration = timedelta(hours=2)
            planned_cost = 8000.0
        else:
            planned_duration = timedelta(minutes=30)
            planned_cost = 2000.0
        
        return PerformanceMetrics(
            planned_duration=planned_duration,
            planned_cost=planned_cost
        )
    
    def _is_valid_stage_transition(self, current_stage: ExecutionStage, new_stage: ExecutionStage) -> bool:
        """验证阶段转换是否合法"""
        
        valid_transitions = {
            ExecutionStage.APPROVED: [ExecutionStage.DISPATCHED, ExecutionStage.CANCELLED],
            ExecutionStage.DISPATCHED: [ExecutionStage.IN_PROGRESS, ExecutionStage.FAILED, ExecutionStage.CANCELLED],
            ExecutionStage.IN_PROGRESS: [ExecutionStage.COMPLETED, ExecutionStage.FAILED, ExecutionStage.CANCELLED],
            ExecutionStage.COMPLETED: [ExecutionStage.VERIFIED],
            ExecutionStage.VERIFIED: [ExecutionStage.CLOSED],
            ExecutionStage.FAILED: [ExecutionStage.CLOSED],
            ExecutionStage.CANCELLED: [ExecutionStage.CLOSED]
        }
        
        return new_stage in valid_transitions.get(current_stage, [])
    
    def _calculate_execution_duration(self, record: ExecutionRecord) -> Optional[str]:
        """计算执行持续时间"""
        
        if record.completed_at:
            duration = record.completed_at - record.created_at
        else:
            duration = datetime.now() - record.created_at
        
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        else:
            return f"{minutes}分钟"
    
    def _get_latest_event_summary(self, record: ExecutionRecord) -> Dict[str, Any]:
        """获取最新事件摘要"""
        
        if not record.execution_events:
            return {}
        
        latest_event = record.execution_events[-1]
        return {
            "stage": latest_event.stage.value,
            "timestamp": latest_event.timestamp.isoformat(),
            "operator": latest_event.operator,
            "description": latest_event.description,
            "has_issues": bool(latest_event.issues)
        }
    
    def _serialize_performance_metrics(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """序列化性能指标"""
        
        return {
            "planned_duration_minutes": metrics.planned_duration.total_seconds() / 60,
            "actual_duration_minutes": (metrics.actual_duration.total_seconds() / 60 
                                      if metrics.actual_duration else None),
            "planned_cost": metrics.planned_cost,
            "actual_cost": metrics.actual_cost,
            "passenger_satisfaction_score": metrics.passenger_satisfaction_score,
            "operational_efficiency_score": metrics.operational_efficiency_score,
            "safety_compliance_score": metrics.safety_compliance_score,
            "overall_effectiveness_score": metrics.overall_effectiveness_score
        }
    
    def _start_effectiveness_evaluation(self, record: ExecutionRecord):
        """开始效果评估"""
        
        # 收集实际性能数据
        self._collect_actual_performance_data(record)
        
        # 通知评估处理器
        for handler in self.evaluation_handlers:
            try:
                handler(record)
            except Exception as e:
                print(f"评估处理器异常: {e}")
    
    def _collect_actual_performance_data(self, record: ExecutionRecord):
        """收集实际性能数据"""
        
        if record.completed_at:
            # 计算实际执行时间
            record.performance_metrics.actual_duration = record.completed_at - record.created_at
        
        # 模拟收集其他性能数据
        action = record.adjustment_plan.get("action", "")
        
        # 实际成本（基于计划成本的变动）
        cost_variance = 0.1 if any(event.issues for event in record.execution_events) else -0.05
        record.performance_metrics.actual_cost = (
            record.performance_metrics.planned_cost * (1 + cost_variance)
        )
        
        # 旅客满意度评分（模拟）
        if action == "CANCEL_FLIGHT":
            record.performance_metrics.passenger_satisfaction_score = 3.0
        elif action == "CHANGE_TIME":
            delay_minutes = record.adjustment_plan.get("details", {}).get("delay_minutes", 0)
            score = 8.0 - (delay_minutes / 30.0)  # 每30分钟延误减1分
            record.performance_metrics.passenger_satisfaction_score = max(1.0, score)
        else:
            record.performance_metrics.passenger_satisfaction_score = 7.0
        
        # 运行效率评分（模拟）
        timing_ratio = 1.0
        if record.performance_metrics.actual_duration:
            timing_ratio = (record.performance_metrics.planned_duration.total_seconds() / 
                          record.performance_metrics.actual_duration.total_seconds())
        
        record.performance_metrics.operational_efficiency_score = min(1.0, timing_ratio)
        
        # 安全合规评分（模拟）
        has_safety_issues = any("安全" in str(event.issues) for event in record.execution_events)
        record.performance_metrics.safety_compliance_score = 0.8 if has_safety_issues else 1.0
    
    def _perform_detailed_evaluation(self, record: ExecutionRecord) -> Dict[str, Any]:
        """执行详细评估"""
        
        metrics = record.performance_metrics
        
        # 计算各项指标评分
        timing_accuracy_score = self._calculate_timing_accuracy_score(metrics)
        cost_variance_score = self._calculate_cost_variance_score(metrics)
        passenger_impact_score = metrics.passenger_satisfaction_score / 10.0  # 归一化到0-1
        operational_efficiency_score = metrics.operational_efficiency_score
        safety_compliance_score = metrics.safety_compliance_score
        customer_satisfaction_score = metrics.passenger_satisfaction_score / 10.0
        
        # 计算加权总分
        overall_score = (
            timing_accuracy_score * self.evaluation_weights[MetricType.TIMING_ACCURACY] +
            cost_variance_score * self.evaluation_weights[MetricType.COST_VARIANCE] +
            passenger_impact_score * self.evaluation_weights[MetricType.PASSENGER_IMPACT] +
            operational_efficiency_score * self.evaluation_weights[MetricType.OPERATIONAL_EFFICIENCY] +
            safety_compliance_score * self.evaluation_weights[MetricType.SAFETY_COMPLIANCE] +
            customer_satisfaction_score * self.evaluation_weights[MetricType.CUSTOMER_SATISFACTION]
        )
        
        # 生成经验教训和建议
        lessons_learned = self._generate_lessons_learned(record, {
            "timing_accuracy": timing_accuracy_score,
            "cost_variance": cost_variance_score,
            "passenger_impact": passenger_impact_score,
            "operational_efficiency": operational_efficiency_score,
            "safety_compliance": safety_compliance_score
        })
        
        recommendations = self._generate_recommendations(record, {
            "timing_accuracy": timing_accuracy_score,
            "cost_variance": cost_variance_score,
            "passenger_impact": passenger_impact_score,
            "operational_efficiency": operational_efficiency_score,
            "safety_compliance": safety_compliance_score
        })
        
        return {
            "tracking_id": record.tracking_id,
            "overall_score": overall_score,
            "detailed_scores": {
                "timing_accuracy": timing_accuracy_score,
                "cost_variance": cost_variance_score,
                "passenger_impact": passenger_impact_score,
                "operational_efficiency": operational_efficiency_score,
                "safety_compliance": safety_compliance_score,
                "customer_satisfaction": customer_satisfaction_score
            },
            "performance_summary": {
                "planned_vs_actual_duration": {
                    "planned_minutes": metrics.planned_duration.total_seconds() / 60,
                    "actual_minutes": (metrics.actual_duration.total_seconds() / 60 
                                     if metrics.actual_duration else None),
                    "variance_percentage": self._calculate_duration_variance(metrics)
                },
                "planned_vs_actual_cost": {
                    "planned_cost": metrics.planned_cost,
                    "actual_cost": metrics.actual_cost,
                    "variance_percentage": self._calculate_cost_variance(metrics)
                }
            },
            "lessons_learned": lessons_learned,
            "recommendations": recommendations,
            "benchmark_comparison": self._compare_with_benchmarks(record)
        }
    
    def _calculate_timing_accuracy_score(self, metrics: PerformanceMetrics) -> float:
        """计算时间准确性评分"""
        
        if not metrics.actual_duration:
            return 0.5  # 默认中等评分
        
        variance = abs(metrics.actual_duration.total_seconds() - 
                      metrics.planned_duration.total_seconds())
        max_acceptable_variance = metrics.planned_duration.total_seconds() * 0.2  # 20%容差
        
        if variance <= max_acceptable_variance:
            return 1.0
        elif variance <= max_acceptable_variance * 2:
            return 0.7
        elif variance <= max_acceptable_variance * 3:
            return 0.4
        else:
            return 0.1
    
    def _calculate_cost_variance_score(self, metrics: PerformanceMetrics) -> float:
        """计算成本差异评分"""
        
        if not metrics.actual_cost:
            return 0.5
        
        variance_percentage = abs(metrics.actual_cost - metrics.planned_cost) / metrics.planned_cost
        
        if variance_percentage <= 0.05:  # 5%以内
            return 1.0
        elif variance_percentage <= 0.1:  # 10%以内
            return 0.8
        elif variance_percentage <= 0.2:  # 20%以内
            return 0.6
        elif variance_percentage <= 0.3:  # 30%以内
            return 0.4
        else:
            return 0.2
    
    def _calculate_duration_variance(self, metrics: PerformanceMetrics) -> Optional[float]:
        """计算执行时间差异百分比"""
        
        if not metrics.actual_duration:
            return None
        
        planned_seconds = metrics.planned_duration.total_seconds()
        actual_seconds = metrics.actual_duration.total_seconds()
        
        return ((actual_seconds - planned_seconds) / planned_seconds) * 100
    
    def _calculate_cost_variance(self, metrics: PerformanceMetrics) -> Optional[float]:
        """计算成本差异百分比"""
        
        if not metrics.actual_cost:
            return None
        
        return ((metrics.actual_cost - metrics.planned_cost) / metrics.planned_cost) * 100
    
    def _generate_lessons_learned(self, record: ExecutionRecord, scores: Dict[str, float]) -> List[str]:
        """生成经验教训"""
        
        lessons = []
        
        # 基于评分生成教训
        if scores["timing_accuracy"] < 0.7:
            lessons.append("执行时间控制需要改进，建议加强项目管理和进度监控")
        
        if scores["cost_variance"] < 0.7:
            lessons.append("成本控制需要优化，建议完善成本预算和监控机制")
        
        if scores["passenger_impact"] < 0.6:
            lessons.append("旅客体验受到较大影响，需要改进沟通和补偿措施")
        
        if scores["safety_compliance"] < 1.0:
            lessons.append("安全合规存在问题，需要加强安全检查和培训")
        
        # 基于执行事件中的问题生成教训
        all_issues = []
        for event in record.execution_events:
            all_issues.extend(event.issues)
        
        if all_issues:
            lessons.append(f"执行过程中遇到问题：{', '.join(set(all_issues))}")
        
        return lessons
    
    def _generate_recommendations(self, record: ExecutionRecord, scores: Dict[str, float]) -> List[str]:
        """生成改进建议"""
        
        recommendations = []
        action = record.adjustment_plan.get("action", "")
        
        # 基于调整类型和评分生成建议
        if action == "CHANGE_TIME" and scores["passenger_impact"] < 0.7:
            recommendations.append("建议建立更好的旅客沟通机制，提前通知延误信息")
            recommendations.append("考虑提供延误补偿服务，如餐食、住宿等")
        
        if action == "CHANGE_AIRCRAFT" and scores["timing_accuracy"] < 0.7:
            recommendations.append("建议优化换机流程，减少不必要的等待时间")
            recommendations.append("加强备用飞机的预先准备工作")
        
        if action == "CANCEL_FLIGHT":
            recommendations.append("建议完善取消航班的应急预案")
            recommendations.append("加强与旅客的沟通，提供多种改签选择")
        
        # 通用建议
        if scores["operational_efficiency"] < 0.8:
            recommendations.append("建议优化操作流程，提高执行效率")
        
        if any(event.issues for event in record.execution_events):
            recommendations.append("建议建立问题追踪机制，防止类似问题再次发生")
        
        return recommendations
    
    def _compare_with_benchmarks(self, record: ExecutionRecord) -> Dict[str, Any]:
        """与基准值比较"""
        
        metrics = record.performance_metrics
        comparison = {}
        
        # 时间准确性比较
        timing_accuracy = self._calculate_timing_accuracy_score(metrics)
        comparison["timing_accuracy"] = {
            "score": timing_accuracy,
            "benchmark": self.benchmarks["timing_accuracy_threshold"],
            "meets_benchmark": timing_accuracy >= self.benchmarks["timing_accuracy_threshold"]
        }
        
        # 成本差异比较
        cost_variance = abs(self._calculate_cost_variance(metrics) or 0) / 100
        comparison["cost_variance"] = {
            "variance": cost_variance,
            "benchmark": self.benchmarks["cost_variance_threshold"],
            "meets_benchmark": cost_variance <= self.benchmarks["cost_variance_threshold"]
        }
        
        # 旅客满意度比较
        satisfaction_score = metrics.passenger_satisfaction_score or 0
        comparison["passenger_satisfaction"] = {
            "score": satisfaction_score,
            "benchmark": self.benchmarks["passenger_satisfaction_threshold"],
            "meets_benchmark": satisfaction_score >= self.benchmarks["passenger_satisfaction_threshold"]
        }
        
        return comparison
    
    def _notify_event_handlers(self, event: ExecutionEvent):
        """通知事件处理器"""
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"事件处理器异常: {e}")


# 事件处理器示例
def console_execution_handler(event: ExecutionEvent):
    """控制台执行事件处理器"""
    stage_colors = {
        ExecutionStage.APPROVED: '\033[94m',     # 蓝色
        ExecutionStage.DISPATCHED: '\033[96m',   # 青色
        ExecutionStage.IN_PROGRESS: '\033[93m',  # 黄色
        ExecutionStage.COMPLETED: '\033[92m',    # 绿色
        ExecutionStage.FAILED: '\033[91m',       # 红色
        ExecutionStage.CANCELLED: '\033[95m'     # 紫色
    }
    
    color = stage_colors.get(event.stage, '\033[0m')
    reset_color = '\033[0m'
    
    print(f"{color}📋 执行事件 [{event.stage.value.upper()}]{reset_color}")
    print(f"时间: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"操作员: {event.operator}")
    print(f"描述: {event.description}")
    
    if event.issues:
        print(f"⚠️  问题: {', '.join(event.issues)}")
    
    print("-" * 50)


def database_execution_handler(event: ExecutionEvent):
    """数据库执行事件处理器（模拟）"""
    # 在真实系统中，这里会将事件保存到数据库
    print(f"💾 保存执行事件到数据库: {event.event_id}")


def notification_execution_handler(event: ExecutionEvent):
    """通知执行事件处理器（模拟）"""
    if event.stage in [ExecutionStage.COMPLETED, ExecutionStage.FAILED]:
        # 在真实系统中，这里会发送通知
        print(f"📧 发送执行完成通知: {event.description}")


def evaluation_completion_handler(record: ExecutionRecord):
    """评估完成处理器"""
    print(f"📊 效果评估完成: {record.tracking_id}")
    print(f"总体评分: {record.effectiveness_score:.2f}")
    if record.lessons_learned:
        print(f"经验教训: {'; '.join(record.lessons_learned[:2])}")  # 只显示前两条 