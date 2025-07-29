"""
协作决策相关的数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class StakeholderRole(Enum):
    """利益相关者角色"""
    DISPATCHER = "dispatcher"        # 调度员
    CREW_SCHEDULER = "crew_scheduler" # 机组排班员
    MAINTENANCE = "maintenance"      # 维修
    ATC = "atc"                     # 空管
    SLOT_COORDINATOR = "slot_coordinator"  # 时刻协调员
    GROUND_SERVICES = "ground_services"    # 地面服务
    PASSENGER_SERVICES = "passenger_services"  # 旅客服务
    FUEL_COORDINATOR = "fuel_coordinator"      # 加油协调员
    CARGO_HANDLER = "cargo_handler"           # 货运处理
    STATION_MANAGER = "station_manager"       # 现场经理


class DecisionStatus(Enum):
    """决策状态"""
    INITIATED = "initiated"     # 已发起
    PENDING = "pending"         # 待审批
    APPROVED = "approved"       # 已批准
    REJECTED = "rejected"       # 已拒绝
    DELEGATED = "delegated"     # 已委托
    EXECUTED = "executed"       # 已执行
    CANCELLED = "cancelled"     # 已取消


class UrgencyLevel(Enum):
    """紧急程度"""
    LOW = "low"           # 低优先级
    NORMAL = "normal"     # 正常
    HIGH = "high"         # 高优先级
    CRITICAL = "critical" # 紧急


@dataclass
class Stakeholder:
    """利益相关者"""
    role: StakeholderRole
    name: str
    contact_info: Dict[str, str]
    priority: int  # 优先级，数字越小优先级越高
    timeout_minutes: int  # 超时时间（分钟）
    auto_approve_threshold: Optional[float] = None  # 自动批准阈值


@dataclass
class ApprovalRecord:
    """批准记录"""
    stakeholder_role: StakeholderRole
    operator_name: str
    decision: str  # "approved", "rejected", "delegated"
    timestamp: datetime
    comments: str = ""
    conditions: List[str] = field(default_factory=list)


@dataclass
class DecisionRequest:
    """决策请求"""
    decision_id: str
    title: str
    description: str
    adjustment_plan: Dict[str, Any]
    urgency_level: UrgencyLevel
    required_stakeholders: List[StakeholderRole]
    approval_records: List[ApprovalRecord] = field(default_factory=list)
    status: DecisionStatus = DecisionStatus.INITIATED
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    final_decision: Optional[str] = None
    final_operator: Optional[str] = None
    completion_time: Optional[datetime] = None 