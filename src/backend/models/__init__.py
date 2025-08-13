"""
数据类型定义模块

包含：
- flight_models: 航班、机场、飞机、机组等核心数据模型
- constraint_models: 约束条件数据模型
- collaboration_models: 协作决策相关数据模型
- monitoring_models: 实时监控相关数据模型
- planning_models: 规划管理相关数据模型
- integration_models: 外部系统集成相关数据模型
- execution_models: 执行跟踪相关数据模型
"""

from .flight_models import *
from .constraint_models import *
from .collaboration_models import *
from .monitoring_models import *
from .planning_models import *
from .integration_models import *
from .execution_models import *

__all__ = [
    # 来自 flight_models
    'Flight', 'Airport', 'Aircraft', 'Crew', 'CrewMember', 'OperationalContext', 'FlightStatus',
    
    # 来自 constraint_models  
    'Priority', 'RequirementType', 'Category', 'RestrictionType',
    'AirportSpecialRequirement', 'AirportRestriction', 'FlightRestriction',
    'FlightSpecialRequirement', 'SectorSpecialRequirement',
    
    # 来自 collaboration_models
    'StakeholderRole', 'DecisionStatus', 'UrgencyLevel', 'Stakeholder', 'ApprovalRecord', 'DecisionRequest',
    
    # 来自 monitoring_models
    'AlertLevel', 'RiskType', 'Alert', 'MonitoringRule',
    
    # 来自 planning_models
    'PlanConflict', 'PlanningWindow',
    
    # 来自 integration_models
    'SystemConnection',
    
    # 来自 execution_models
    'ExecutionStage', 'MetricType', 'ExecutionEvent', 'PerformanceMetrics', 'ExecutionRecord',
]