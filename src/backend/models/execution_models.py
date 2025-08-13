"""
执行跟踪相关的数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum


class ExecutionStage(Enum):
    """执行阶段"""
    PLANNED = "planned"         # 已计划
    APPROVED = "approved"       # 已批准
    INITIATED = "initiated"     # 已启动
    IN_PROGRESS = "in_progress" # 执行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"          # 执行失败
    CANCELLED = "cancelled"     # 已取消


class MetricType(Enum):
    """指标类型"""
    EXECUTION_SUCCESS = "execution_success"     # 执行成功率
    TIMING_ACCURACY = "timing_accuracy"         # 时间准确性
    COST_VARIANCE = "cost_variance"             # 成本差异
    PASSENGER_IMPACT = "passenger_impact"       # 旅客影响
    OPERATIONAL_EFFICIENCY = "operational_efficiency"  # 运行效率
    SAFETY_COMPLIANCE = "safety_compliance"     # 安全合规
    CUSTOMER_SATISFACTION = "customer_satisfaction"  # 客户满意度


@dataclass
class ExecutionEvent:
    """执行事件"""
    event_id: str
    stage: ExecutionStage
    timestamp: datetime
    operator: str
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    planned_duration: timedelta
    actual_duration: Optional[timedelta] = None
    planned_cost: float = 0.0
    actual_cost: Optional[float] = None
    passenger_satisfaction_score: Optional[float] = None
    operational_efficiency_score: Optional[float] = None
    safety_compliance_score: Optional[float] = None
    overall_effectiveness_score: Optional[float] = None


@dataclass
class ExecutionRecord:
    """执行记录"""
    tracking_id: str
    adjustment_plan: Dict[str, Any]
    decision_id: Optional[str] = None
    current_stage: ExecutionStage = ExecutionStage.APPROVED
    execution_events: List[ExecutionEvent] = field(default_factory=list)
    performance_metrics: Optional[PerformanceMetrics] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    success_indicators: Dict[str, bool] = field(default_factory=dict)
    failure_reasons: List[str] = field(default_factory=list) 