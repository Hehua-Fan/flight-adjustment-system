"""
API数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime


class PlanGenerationRequest(BaseModel):
    """方案生成请求模型"""
    plan_name: str = Field(..., description="方案名称")
    plan_description: Optional[str] = Field(default="", description="方案描述")
    weights: Dict[str, float] = Field(..., description="权重配置")
    constraints: List[Dict[str, Any]] = Field(default=[], description="约束条件")
    allowed_actions: List[str] = Field(default=[], description="允许的调整动作")
    flight_range: str = Field(default="all", description="航班范围: all 或 selected")
    selected_flights: List[str] = Field(default=[], description="选定的航班ID列表")
    test_mode: bool = Field(default=True, description="是否启用测试模式")
    cdm_file_id: Optional[str] = Field(default=None, description="上传的CDM文件ID")

class DispatchAction(BaseModel):
    """调度操作模型"""
    action_id: str
    action_type: str  # 操作类型：通知、调配、协调、监控
    description: str
    responsible_dept: str  # 负责部门
    deadline: str  # 完成时限
    priority: str  # 优先级
    related_flights: List[str]  # 相关航班
    checklist: List[str]  # 检查清单

class PlanResults(BaseModel):
    """方案结果模型"""
    total_flights: int
    executed_flights: int
    cancelled_flights: int
    total_delay: int
    total_cost: float
    flight_adjustments: List[Dict[str, Any]]
    cost_breakdown: Dict[str, float]
    summary: Dict[str, float]
    dispatch_actions: Optional[List[DispatchAction]] = Field(default=[], description="调度操作清单")

class OptimizationPlan(BaseModel):
    """优化方案模型"""
    id: str
    name: str
    description: str
    detailed_description: Optional[str] = Field(default="", description="WriterAgent生成的详细描述")
    weights: Dict[str, float]
    status: str
    generated_at: datetime
    results: Optional[PlanResults]

class MultiPlanResponse(BaseModel):
    """多方案响应模型"""
    plans: List[OptimizationPlan]
    total_generated: int
    successful_plans: int
