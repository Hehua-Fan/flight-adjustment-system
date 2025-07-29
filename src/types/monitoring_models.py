"""
实时监控相关的数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any
from enum import Enum


class AlertLevel(Enum):
    """预警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RiskType(Enum):
    """风险类型"""
    WEATHER = "weather"
    AIRCRAFT = "aircraft"
    CREW = "crew"
    ATC = "atc"
    MAINTENANCE = "maintenance"
    SLOT = "slot"
    FUEL = "fuel"


@dataclass
class Alert:
    """预警信息"""
    alert_id: str
    flight_no: str
    risk_type: RiskType
    level: AlertLevel
    title: str
    description: str
    current_value: Any
    threshold_value: Any
    recommended_actions: List[str]
    time_to_impact: timedelta
    time_to_decision: timedelta
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class MonitoringRule:
    """监控规则"""
    rule_id: str
    name: str
    risk_type: RiskType
    check_function: str  # 检查函数名
    parameters: Dict[str, Any]
    alert_thresholds: Dict[AlertLevel, float]
    enabled: bool = True
    frequency_seconds: int = 60 