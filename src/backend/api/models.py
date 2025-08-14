"""
API数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class WeightConfig(BaseModel):
    """权重配置模型"""
    cancel: float = Field(default=1.0, description="取消成本权重")
    delay: float = Field(default=0.1, description="延误成本权重")
    late_pax: float = Field(default=0.5, description="晚点旅客影响权重")
    revenue: float = Field(default=1.0, description="收入损失权重")
    change_time: float = Field(default=0.2, description="变更时刻成本权重")
    change_aircraft: float = Field(default=0.8, description="更换飞机成本权重")
    cancel_flight: float = Field(default=1.0, description="取消航班成本权重")
    change_airport: float = Field(default=0.6, description="变更机场成本权重")
    change_nature: float = Field(default=0.3, description="变更性质成本权重")
    add_flight: float = Field(default=0.9, description="新增航班成本权重")

class EventRequest(BaseModel):
    """事件请求模型"""
    description: str = Field(..., description="事件描述")
    event_type: Optional[str] = Field(default=None, description="事件类型")
    severity: Optional[str] = Field(default=None, description="严重程度")
    custom_weights: Optional[Dict[str, WeightConfig]] = Field(default=None, description="自定义权重")

class EventAnalysisResponse(BaseModel):
    """事件分析响应模型"""
    event_type: str
    severity: str
    confidence: float
    description: str
    weights: Dict[str, WeightConfig]
    risk_factors: List[Dict[str, Any]]
    recommendations: List[str]

class OptimizationRequest(BaseModel):
    """优化请求模型"""
    event_description: str
    weights: Dict[str, WeightConfig]
    cdm_data_file: Optional[str] = Field(default=None, description="CDM数据文件路径")
    constraint_dir: Optional[str] = Field(default=None, description="约束数据目录")

class FlightAdjustment(BaseModel):
    """航班调整结果模型"""
    flight_number: str
    adjustment_action: str
    status: str
    additional_delay_minutes: float
    adjusted_departure_time: Optional[datetime]
    reason: Optional[str]

class OptimizationResponse(BaseModel):
    """优化响应模型"""
    chosen_plan_name: str
    solutions: Dict[str, List[FlightAdjustment]]
    summary: Dict[str, Any]
    execution_status: str

class SystemStatus(BaseModel):
    """系统状态模型"""
    is_running: bool
    current_event: Optional[str]
    processing_step: Optional[str]
    last_update: datetime
    statistics: Dict[str, Any]

class PresetEvent(BaseModel):
    """预设事件模型"""
    id: str
    name: str
    description: str
    event_type: str
    severity: str
    default_weights: Dict[str, WeightConfig]
    typical_scenarios: List[str]
