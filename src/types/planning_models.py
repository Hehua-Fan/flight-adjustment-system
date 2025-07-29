"""
规划管理相关的数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from .flight_models import Flight


@dataclass
class PlanConflict:
    """计划冲突"""
    conflict_id: str
    conflict_type: str  # 'aircraft', 'crew', 'slot', 'maintenance'
    severity: str  # 'low', 'medium', 'high', 'critical'
    affected_flights: List[str]
    description: str
    suggested_resolution: Optional[str] = None
    resolution_deadline: Optional[datetime] = None


@dataclass
class PlanningWindow:
    """计划窗口"""
    plan_id: str
    valid_from: datetime
    valid_until: datetime
    flights: List[Flight]
    conflicts: List[PlanConflict] = field(default_factory=list)
    confidence_level: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now) 