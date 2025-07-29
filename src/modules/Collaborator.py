#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多部门协同决策模块
负责管理涉及多个部门的航班调整决策流程
"""

import uuid
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from ..types.collaboration_models import (
    StakeholderRole, DecisionStatus, UrgencyLevel, 
    Stakeholder, ApprovalRecord, DecisionRequest
)



class CollaborativeDecisionMaking:
    """协同决策系统"""
    
    def __init__(self):
        self.decision_requests: Dict[str, DecisionRequest] = {}
        self.stakeholders = self._initialize_stakeholders()
        self.decision_handlers: List[Callable[[DecisionRequest], None]] = []
        self.active_decisions: Dict[str, threading.Timer] = {}
        
        # 决策规则配置
        self.decision_rules = self._initialize_decision_rules()
        
        # 自动批准规则
        self.auto_approval_rules = {
            "time_change_minor": {"threshold": 30, "conditions": ["delay < 30 minutes"]},
            "aircraft_change_same_type": {"threshold": 0.8, "conditions": ["same aircraft type"]},
            "crew_change_qualified": {"threshold": 0.9, "conditions": ["qualified crew available"]}
        }
    
    def initiate_decision(self, 
                         title: str,
                         description: str,
                         adjustment_plan: Dict[str, Any],
                         urgency_level: UrgencyLevel = UrgencyLevel.NORMAL,
                         deadline: Optional[datetime] = None) -> str:
        """发起协同决策"""
        
        decision_id = str(uuid.uuid4())
        
        # 确定需要参与的利益相关者
        required_stakeholders = self._identify_required_stakeholders(adjustment_plan, urgency_level)
        
        # 评估业务影响
        business_impact = self._assess_business_impact(adjustment_plan)
        
        # 评估风险
        risk_assessment = self._assess_decision_risk(adjustment_plan)
        
        # 计算截止时间
        if deadline is None:
            deadline = self._calculate_deadline(urgency_level, adjustment_plan)
        
        # 创建决策请求
        request = DecisionRequest(
            decision_id=decision_id,
            title=title,
            description=description,
            adjustment_plan=adjustment_plan,
            urgency_level=urgency_level,
            required_stakeholders=required_stakeholders,
            deadline=deadline,
            business_impact=business_impact,
            risk_assessment=risk_assessment
        )
        
        # 检查是否可以自动批准
        if self._can_auto_approve(request):
            request.status = DecisionStatus.APPROVED
            request.auto_approve_at = datetime.now()
            self._notify_auto_approval(request)
        else:
            # 启动决策流程
            request.status = DecisionStatus.IN_PROGRESS
            self._start_decision_process(request)
        
        self.decision_requests[decision_id] = request
        
        # 通知决策处理器
        self._notify_decision_handlers(request)
        
        return decision_id
    
    def submit_approval(self, 
                       decision_id: str, 
                       stakeholder_role: StakeholderRole,
                       operator_name: str,
                       decision: str,
                       comments: str = "",
                       conditions: List[str] = None) -> Dict[str, Any]:
        """提交批准决策"""
        
        if decision_id not in self.decision_requests:
            return {"success": False, "error": "决策请求不存在"}
        
        request = self.decision_requests[decision_id]
        
        if request.status != DecisionStatus.IN_PROGRESS:
            return {"success": False, "error": f"决策状态不正确: {request.status.value}"}
        
        if stakeholder_role not in request.required_stakeholders:
            return {"success": False, "error": "您不在此决策的相关方列表中"}
        
        # 检查是否已经提交过决策
        existing_record = next((r for r in request.approval_records 
                              if r.stakeholder_role == stakeholder_role), None)
        if existing_record:
            return {"success": False, "error": "您已经提交过决策"}
        
        # 创建批准记录
        approval_record = ApprovalRecord(
            stakeholder_role=stakeholder_role,
            operator_name=operator_name,
            decision=decision,
            timestamp=datetime.now(),
            comments=comments,
            conditions=conditions or []
        )
        
        request.approval_records.append(approval_record)
        
        # 检查决策是否完成
        self._check_decision_completion(request)
        
        return {
            "success": True,
            "decision_id": decision_id,
            "status": request.status.value,
            "remaining_approvers": self._get_remaining_approvers(request)
        }
    
    def get_decision_status(self, decision_id: str) -> Dict[str, Any]:
        """获取决策状态"""
        if decision_id not in self.decision_requests:
            return {"error": "决策请求不存在"}
        
        request = self.decision_requests[decision_id]
        
        return {
            "decision_id": decision_id,
            "title": request.title,
            "status": request.status.value,
            "urgency_level": request.urgency_level.value,
            "created_at": request.created_at.isoformat(),
            "deadline": request.deadline.isoformat() if request.deadline else None,
            "required_stakeholders": [role.value for role in request.required_stakeholders],
            "approvals_received": len(request.approval_records),
            "approvals_required": len(request.required_stakeholders),
            "approval_records": [
                {
                    "stakeholder": record.stakeholder_role.value,
                    "operator": record.operator_name,
                    "decision": record.decision,
                    "timestamp": record.timestamp.isoformat(),
                    "comments": record.comments
                }
                for record in request.approval_records
            ],
            "remaining_approvers": self._get_remaining_approvers(request),
            "time_remaining": self._calculate_time_remaining(request),
            "business_impact": request.business_impact,
            "risk_assessment": request.risk_assessment
        }
    
    def get_pending_decisions(self, stakeholder_role: StakeholderRole) -> List[Dict[str, Any]]:
        """获取待处理的决策"""
        pending_decisions = []
        
        for request in self.decision_requests.values():
            if (request.status == DecisionStatus.IN_PROGRESS and 
                stakeholder_role in request.required_stakeholders):
                
                # 检查是否已经批准
                already_approved = any(record.stakeholder_role == stakeholder_role 
                                     for record in request.approval_records)
                
                if not already_approved:
                    pending_decisions.append({
                        "decision_id": request.decision_id,
                        "title": request.title,
                        "urgency_level": request.urgency_level.value,
                        "created_at": request.created_at.isoformat(),
                        "deadline": request.deadline.isoformat() if request.deadline else None,
                        "time_remaining": self._calculate_time_remaining(request),
                        "adjustment_plan": request.adjustment_plan,
                        "business_impact": request.business_impact,
                        "risk_assessment": request.risk_assessment
                    })
        
        # 按紧急程度和创建时间排序
        pending_decisions.sort(key=lambda x: (
            0 if x["urgency_level"] == "critical" else
            1 if x["urgency_level"] == "high" else
            2 if x["urgency_level"] == "normal" else 3,
            x["created_at"]
        ))
        
        return pending_decisions
    
    def cancel_decision(self, decision_id: str, reason: str = "") -> Dict[str, Any]:
        """取消决策"""
        if decision_id not in self.decision_requests:
            return {"success": False, "error": "决策请求不存在"}
        
        request = self.decision_requests[decision_id]
        
        if request.status not in [DecisionStatus.INITIATED, DecisionStatus.IN_PROGRESS]:
            return {"success": False, "error": f"无法取消状态为{request.status.value}的决策"}
        
        request.status = DecisionStatus.CANCELLED
        
        # 取消定时器
        if decision_id in self.active_decisions:
            self.active_decisions[decision_id].cancel()
            del self.active_decisions[decision_id]
        
        return {"success": True, "decision_id": decision_id, "reason": reason}
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """获取决策统计信息"""
        total_decisions = len(self.decision_requests)
        
        if total_decisions == 0:
            return {"total_decisions": 0}
        
        status_counts = {}
        urgency_counts = {}
        avg_approval_time = timedelta()
        completed_decisions = 0
        
        for request in self.decision_requests.values():
            # 状态统计
            status = request.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # 紧急程度统计
            urgency = request.urgency_level.value
            urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
            
            # 平均批准时间
            if request.status in [DecisionStatus.APPROVED, DecisionStatus.REJECTED]:
                if request.approval_records:
                    completion_time = max(record.timestamp for record in request.approval_records)
                    approval_duration = completion_time - request.created_at
                    avg_approval_time += approval_duration
                    completed_decisions += 1
        
        if completed_decisions > 0:
            avg_approval_time = avg_approval_time / completed_decisions
        
        return {
            "total_decisions": total_decisions,
            "status_distribution": status_counts,
            "urgency_distribution": urgency_counts,
            "average_approval_time_minutes": avg_approval_time.total_seconds() / 60,
            "completion_rate": completed_decisions / total_decisions if total_decisions > 0 else 0,
            "active_decisions": len([r for r in self.decision_requests.values() 
                                   if r.status == DecisionStatus.IN_PROGRESS])
        }
    
    def add_decision_handler(self, handler: Callable[[DecisionRequest], None]):
        """添加决策处理器"""
        self.decision_handlers.append(handler)
    
    # 私有方法
    def _initialize_stakeholders(self) -> Dict[StakeholderRole, Stakeholder]:
        """初始化利益相关者"""
        stakeholders = {
            StakeholderRole.OPS_CONTROLLER: Stakeholder(
                role=StakeholderRole.OPS_CONTROLLER,
                name="运控员",
                contact_info={"phone": "010-12345678", "email": "ops@airline.com"},
                priority=1,
                timeout_minutes=5,
                auto_approve_threshold=0.8
            ),
            StakeholderRole.FLIGHT_MANAGER: Stakeholder(
                role=StakeholderRole.FLIGHT_MANAGER,
                name="飞行部经理",
                contact_info={"phone": "010-12345679", "email": "flight@airline.com"},
                priority=2,
                timeout_minutes=15,
                auto_approve_threshold=0.6
            ),
            StakeholderRole.MAINTENANCE: Stakeholder(
                role=StakeholderRole.MAINTENANCE,
                name="维修部门",
                contact_info={"phone": "010-12345680", "email": "maintenance@airline.com"},
                priority=2,
                timeout_minutes=10,
                auto_approve_threshold=0.7
            ),
            StakeholderRole.CREW_SCHEDULING: Stakeholder(
                role=StakeholderRole.CREW_SCHEDULING,
                name="机组排班",
                contact_info={"phone": "010-12345681", "email": "crew@airline.com"},
                priority=2,
                timeout_minutes=10,
                auto_approve_threshold=0.75
            ),
            StakeholderRole.GROUND_SERVICES: Stakeholder(
                role=StakeholderRole.GROUND_SERVICES,
                name="地面服务",
                contact_info={"phone": "010-12345682", "email": "ground@airline.com"},
                priority=3,
                timeout_minutes=15,
                auto_approve_threshold=0.8
            ),
            StakeholderRole.CUSTOMER_SERVICE: Stakeholder(
                role=StakeholderRole.CUSTOMER_SERVICE,
                name="客服部门",
                contact_info={"phone": "010-12345683", "email": "service@airline.com"},
                priority=3,
                timeout_minutes=15,
                auto_approve_threshold=0.9
            ),
            StakeholderRole.OPERATIONS_DIRECTOR: Stakeholder(
                role=StakeholderRole.OPERATIONS_DIRECTOR,
                name="运行总监",
                contact_info={"phone": "010-12345684", "email": "director@airline.com"},
                priority=1,
                timeout_minutes=30,
                auto_approve_threshold=0.5
            ),
            StakeholderRole.SAFETY_DEPARTMENT: Stakeholder(
                role=StakeholderRole.SAFETY_DEPARTMENT,
                name="安全部门",
                contact_info={"phone": "010-12345685", "email": "safety@airline.com"},
                priority=1,
                timeout_minutes=20,
                auto_approve_threshold=0.6
            )
        }
        
        return stakeholders
    
    def _initialize_decision_rules(self) -> Dict[str, Dict[str, Any]]:
        """初始化决策规则"""
        return {
            "CHANGE_TIME": {
                "minor_delay": {
                    "threshold": 30,  # 30分钟以内
                    "stakeholders": [StakeholderRole.OPS_CONTROLLER],
                    "auto_approve": True
                },
                "moderate_delay": {
                    "threshold": 120,  # 30-120分钟
                    "stakeholders": [StakeholderRole.OPS_CONTROLLER, StakeholderRole.CUSTOMER_SERVICE],
                    "auto_approve": False
                },
                "major_delay": {
                    "threshold": float('inf'),  # 超过120分钟
                    "stakeholders": [StakeholderRole.OPS_CONTROLLER, StakeholderRole.FLIGHT_MANAGER, 
                                   StakeholderRole.CUSTOMER_SERVICE, StakeholderRole.OPERATIONS_DIRECTOR],
                    "auto_approve": False
                }
            },
            "CHANGE_AIRCRAFT": {
                "same_type": {
                    "stakeholders": [StakeholderRole.OPS_CONTROLLER, StakeholderRole.MAINTENANCE],
                    "auto_approve": True
                },
                "different_type": {
                    "stakeholders": [StakeholderRole.OPS_CONTROLLER, StakeholderRole.MAINTENANCE,
                                   StakeholderRole.FLIGHT_MANAGER, StakeholderRole.CUSTOMER_SERVICE],
                    "auto_approve": False
                }
            },
            "CANCEL_FLIGHT": {
                "domestic": {
                    "stakeholders": [StakeholderRole.OPS_CONTROLLER, StakeholderRole.FLIGHT_MANAGER,
                                   StakeholderRole.CUSTOMER_SERVICE],
                    "auto_approve": False
                },
                "international": {
                    "stakeholders": [StakeholderRole.OPS_CONTROLLER, StakeholderRole.FLIGHT_MANAGER,
                                   StakeholderRole.CUSTOMER_SERVICE, StakeholderRole.OPERATIONS_DIRECTOR],
                    "auto_approve": False
                },
                "vip": {
                    "stakeholders": [StakeholderRole.OPERATIONS_DIRECTOR, StakeholderRole.SAFETY_DEPARTMENT],
                    "auto_approve": False
                }
            },
            "CHANGE_AIRPORT": {
                "same_city": {
                    "stakeholders": [StakeholderRole.OPS_CONTROLLER, StakeholderRole.GROUND_SERVICES,
                                   StakeholderRole.CUSTOMER_SERVICE],
                    "auto_approve": False
                },
                "different_city": {
                    "stakeholders": [StakeholderRole.OPS_CONTROLLER, StakeholderRole.FLIGHT_MANAGER,
                                   StakeholderRole.GROUND_SERVICES, StakeholderRole.CUSTOMER_SERVICE,
                                   StakeholderRole.OPERATIONS_DIRECTOR],
                    "auto_approve": False
                }
            }
        }
    
    def _identify_required_stakeholders(self, 
                                      adjustment_plan: Dict[str, Any], 
                                      urgency_level: UrgencyLevel) -> List[StakeholderRole]:
        """识别需要参与的利益相关者"""
        
        action = adjustment_plan.get("action", "")
        required_stakeholders = []
        
        # 基于调整类型确定相关方
        if action == "CHANGE_TIME":
            delay_minutes = adjustment_plan.get("details", {}).get("delay_minutes", 0)
            rules = self.decision_rules["CHANGE_TIME"]
            
            if delay_minutes <= rules["minor_delay"]["threshold"]:
                required_stakeholders = rules["minor_delay"]["stakeholders"]
            elif delay_minutes <= rules["moderate_delay"]["threshold"]:
                required_stakeholders = rules["moderate_delay"]["stakeholders"]
            else:
                required_stakeholders = rules["major_delay"]["stakeholders"]
                
        elif action == "CHANGE_AIRCRAFT":
            # 检查是否是同类型飞机
            original_type = adjustment_plan.get("details", {}).get("original_aircraft_type", "")
            new_type = adjustment_plan.get("details", {}).get("new_aircraft_type", "")
            
            if original_type == new_type:
                required_stakeholders = self.decision_rules["CHANGE_AIRCRAFT"]["same_type"]["stakeholders"]
            else:
                required_stakeholders = self.decision_rules["CHANGE_AIRCRAFT"]["different_type"]["stakeholders"]
                
        elif action == "CANCEL_FLIGHT":
            is_international = adjustment_plan.get("flight_info", {}).get("is_international", False)
            is_vip = adjustment_plan.get("flight_info", {}).get("is_vip", False)
            
            if is_vip:
                required_stakeholders = self.decision_rules["CANCEL_FLIGHT"]["vip"]["stakeholders"]
            elif is_international:
                required_stakeholders = self.decision_rules["CANCEL_FLIGHT"]["international"]["stakeholders"]
            else:
                required_stakeholders = self.decision_rules["CANCEL_FLIGHT"]["domestic"]["stakeholders"]
                
        elif action == "CHANGE_AIRPORT":
            # 简化判断：检查是否同城
            is_same_city = adjustment_plan.get("details", {}).get("same_city", True)
            
            if is_same_city:
                required_stakeholders = self.decision_rules["CHANGE_AIRPORT"]["same_city"]["stakeholders"]
            else:
                required_stakeholders = self.decision_rules["CHANGE_AIRPORT"]["different_city"]["stakeholders"]
        
        # 根据紧急程度调整相关方
        if urgency_level == UrgencyLevel.CRITICAL:
            # 紧急情况，简化决策流程
            required_stakeholders = [StakeholderRole.OPS_CONTROLLER]
            if action in ["CANCEL_FLIGHT", "CHANGE_AIRPORT"]:
                required_stakeholders.append(StakeholderRole.OPERATIONS_DIRECTOR)
        
        return list(set(required_stakeholders))  # 去重
    
    def _assess_business_impact(self, adjustment_plan: Dict[str, Any]) -> Dict[str, Any]:
        """评估业务影响"""
        
        passenger_count = adjustment_plan.get("flight_info", {}).get("passenger_count", 0)
        action = adjustment_plan.get("action", "")
        
        impact = {
            "passenger_count": passenger_count,
            "estimated_cost": 0,
            "reputation_risk": "low",
            "operational_complexity": "low"
        }
        
        # 根据调整类型评估影响
        if action == "CHANGE_TIME":
            delay_minutes = adjustment_plan.get("details", {}).get("delay_minutes", 0)
            impact["estimated_cost"] = passenger_count * delay_minutes * 0.5  # 简化成本计算
            
            if delay_minutes > 120:
                impact["reputation_risk"] = "high"
                impact["operational_complexity"] = "medium"
            elif delay_minutes > 60:
                impact["reputation_risk"] = "medium"
                
        elif action == "CANCEL_FLIGHT":
            impact["estimated_cost"] = passenger_count * 300  # 取消成本
            impact["reputation_risk"] = "high"
            impact["operational_complexity"] = "high"
            
        elif action == "CHANGE_AIRCRAFT":
            impact["estimated_cost"] = 5000  # 换机成本
            impact["operational_complexity"] = "medium"
            
        elif action == "CHANGE_AIRPORT":
            impact["estimated_cost"] = passenger_count * 100  # 机场变更成本
            impact["operational_complexity"] = "high"
            impact["reputation_risk"] = "medium"
        
        return impact
    
    def _assess_decision_risk(self, adjustment_plan: Dict[str, Any]) -> Dict[str, Any]:
        """评估决策风险"""
        
        action = adjustment_plan.get("action", "")
        
        risk_assessment = {
            "safety_risk": "low",
            "compliance_risk": "low",
            "financial_risk": "low",
            "customer_satisfaction_risk": "low",
            "overall_risk_score": 0.0
        }
        
        # 根据调整类型评估风险
        if action == "CHANGE_TIME":
            delay_minutes = adjustment_plan.get("details", {}).get("delay_minutes", 0)
            
            if delay_minutes > 240:  # 超过4小时
                risk_assessment["compliance_risk"] = "high"
                risk_assessment["customer_satisfaction_risk"] = "high"
                risk_assessment["overall_risk_score"] = 0.8
            elif delay_minutes > 120:
                risk_assessment["customer_satisfaction_risk"] = "medium"
                risk_assessment["overall_risk_score"] = 0.5
            else:
                risk_assessment["overall_risk_score"] = 0.2
                
        elif action == "CANCEL_FLIGHT":
            risk_assessment["customer_satisfaction_risk"] = "high"
            risk_assessment["financial_risk"] = "high"
            risk_assessment["overall_risk_score"] = 0.9
            
        elif action == "CHANGE_AIRCRAFT":
            risk_assessment["safety_risk"] = "medium"
            risk_assessment["operational_complexity"] = "medium"
            risk_assessment["overall_risk_score"] = 0.4
            
        elif action == "CHANGE_AIRPORT":
            risk_assessment["safety_risk"] = "medium"
            risk_assessment["customer_satisfaction_risk"] = "high"
            risk_assessment["overall_risk_score"] = 0.7
        
        return risk_assessment
    
    def _calculate_deadline(self, urgency_level: UrgencyLevel, adjustment_plan: Dict[str, Any]) -> datetime:
        """计算决策截止时间"""
        
        base_time = datetime.now()
        
        # 根据紧急程度设置基础时限
        if urgency_level == UrgencyLevel.CRITICAL:
            deadline = base_time + timedelta(minutes=10)
        elif urgency_level == UrgencyLevel.HIGH:
            deadline = base_time + timedelta(minutes=30)
        elif urgency_level == UrgencyLevel.NORMAL:
            deadline = base_time + timedelta(hours=2)
        else:  # LOW
            deadline = base_time + timedelta(hours=6)
        
        # 根据航班起飞时间调整
        scheduled_departure = adjustment_plan.get("flight_info", {}).get("scheduled_departure")
        if scheduled_departure:
            try:
                departure_time = datetime.fromisoformat(scheduled_departure)
                # 决策必须在起飞前完成
                deadline = min(deadline, departure_time - timedelta(hours=1))
            except:
                pass
        
        return deadline
    
    def _can_auto_approve(self, request: DecisionRequest) -> bool:
        """检查是否可以自动批准"""
        
        # 紧急情况不自动批准
        if request.urgency_level == UrgencyLevel.CRITICAL:
            return False
        
        # 高风险决策不自动批准
        if request.risk_assessment.get("overall_risk_score", 0) > 0.7:
            return False
        
        # 检查自动批准规则
        action = request.adjustment_plan.get("action", "")
        
        if action == "CHANGE_TIME":
            delay_minutes = request.adjustment_plan.get("details", {}).get("delay_minutes", 0)
            return delay_minutes <= self.auto_approval_rules["time_change_minor"]["threshold"]
        
        return False
    
    def _start_decision_process(self, request: DecisionRequest):
        """启动决策流程"""
        
        # 发送通知到相关方
        self._notify_stakeholders(request)
        
        # 设置超时处理
        timeout_minutes = self._calculate_timeout_minutes(request)
        timeout_timer = threading.Timer(
            timeout_minutes * 60, 
            self._handle_decision_timeout, 
            args=[request.decision_id]
        )
        timeout_timer.start()
        self.active_decisions[request.decision_id] = timeout_timer
    
    def _calculate_timeout_minutes(self, request: DecisionRequest) -> int:
        """计算超时时间"""
        if request.urgency_level == UrgencyLevel.CRITICAL:
            return 10
        elif request.urgency_level == UrgencyLevel.HIGH:
            return 30
        elif request.urgency_level == UrgencyLevel.NORMAL:
            return 120
        else:
            return 360
    
    def _notify_stakeholders(self, request: DecisionRequest):
        """通知利益相关者"""
        for stakeholder_role in request.required_stakeholders:
            stakeholder = self.stakeholders.get(stakeholder_role)
            if stakeholder:
                # 在真实系统中，这里会发送邮件/短信/推送通知
                print(f"📢 通知{stakeholder.name}: 决策请求 {request.title}")
    
    def _check_decision_completion(self, request: DecisionRequest):
        """检查决策是否完成"""
        
        # 获取所有批准记录
        approved_roles = {record.stakeholder_role for record in request.approval_records 
                         if record.decision == "approved"}
        rejected_roles = {record.stakeholder_role for record in request.approval_records 
                         if record.decision == "rejected"}
        
        # 检查是否有拒绝
        if rejected_roles:
            request.status = DecisionStatus.REJECTED
            self._handle_decision_completion(request)
            return
        
        # 检查是否所有必需的相关方都已批准
        if approved_roles.issuperset(set(request.required_stakeholders)):
            request.status = DecisionStatus.APPROVED
            self._handle_decision_completion(request)
    
    def _handle_decision_completion(self, request: DecisionRequest):
        """处理决策完成"""
        
        # 取消超时定时器
        if request.decision_id in self.active_decisions:
            self.active_decisions[request.decision_id].cancel()
            del self.active_decisions[request.decision_id]
        
        # 通知结果
        self._notify_decision_result(request)
    
    def _handle_decision_timeout(self, decision_id: str):
        """处理决策超时"""
        if decision_id in self.decision_requests:
            request = self.decision_requests[decision_id]
            request.status = DecisionStatus.TIMEOUT
            
            # 清理定时器
            if decision_id in self.active_decisions:
                del self.active_decisions[decision_id]
            
            self._notify_decision_timeout(request)
    
    def _get_remaining_approvers(self, request: DecisionRequest) -> List[str]:
        """获取剩余批准者"""
        approved_roles = {record.stakeholder_role for record in request.approval_records}
        remaining_roles = set(request.required_stakeholders) - approved_roles
        return [role.value for role in remaining_roles]
    
    def _calculate_time_remaining(self, request: DecisionRequest) -> Optional[str]:
        """计算剩余时间"""
        if not request.deadline:
            return None
        
        remaining = request.deadline - datetime.now()
        if remaining.total_seconds() <= 0:
            return "已超时"
        
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        else:
            return f"{minutes}分钟"
    
    def _notify_auto_approval(self, request: DecisionRequest):
        """通知自动批准"""
        print(f"✅ 自动批准决策: {request.title}")
    
    def _notify_decision_result(self, request: DecisionRequest):
        """通知决策结果"""
        status_text = {
            DecisionStatus.APPROVED: "✅ 已批准",
            DecisionStatus.REJECTED: "❌ 已拒绝"
        }
        print(f"{status_text.get(request.status, '')} 决策: {request.title}")
    
    def _notify_decision_timeout(self, request: DecisionRequest):
        """通知决策超时"""
        print(f"⏰ 决策超时: {request.title}")
    
    def _notify_decision_handlers(self, request: DecisionRequest):
        """通知决策处理器"""
        for handler in self.decision_handlers:
            try:
                handler(request)
            except Exception as e:
                print(f"决策处理器异常: {e}")


# 决策处理器示例
def console_decision_handler(request: DecisionRequest):
    """控制台决策处理器"""
    urgency_colors = {
        UrgencyLevel.LOW: '\033[92m',      # 绿色
        UrgencyLevel.NORMAL: '\033[94m',   # 蓝色
        UrgencyLevel.HIGH: '\033[93m',     # 黄色
        UrgencyLevel.CRITICAL: '\033[91m'  # 红色
    }
    
    color = urgency_colors.get(request.urgency_level, '\033[0m')
    reset_color = '\033[0m'
    
    print(f"\n{color}🔔 新决策请求 [{request.urgency_level.value.upper()}]{reset_color}")
    print(f"标题: {request.title}")
    print(f"描述: {request.description}")
    print(f"相关方: {', '.join([role.value for role in request.required_stakeholders])}")
    print(f"截止时间: {request.deadline.strftime('%Y-%m-%d %H:%M:%S') if request.deadline else '无'}")
    print(f"业务影响: 成本${request.business_impact.get('estimated_cost', 0):.0f}, "
          f"声誉风险{request.business_impact.get('reputation_risk', '未知')}")
    print("-" * 60) 