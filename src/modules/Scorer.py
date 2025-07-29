from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from ..types.flight_models import (
    Flight, Aircraft, Crew, Airport, OperationalContext, 
    AdjustmentOption, AdjustmentAction
)


class ScoringSystem:
    """调整方案评分系统"""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化评分系统
        
        Args:
            weights: 各项评分权重配置
        """
        self.weights = weights or {
            "passenger_impact": 0.30,     # 旅客影响权重
            "operational_cost": 0.25,     # 运营成本权重  
            "schedule_disruption": 0.20,  # 计划扰动权重
            "resource_utilization": 0.15, # 资源利用权重
            "safety_compliance": 0.10     # 安全合规权重
        }
    
    def score_adjustment_option(self, 
                               option: AdjustmentOption, 
                               flight: Flight,
                               context: OperationalContext) -> float:
        """对单个调整方案进行评分"""
        
        # 基础分数
        base_score = option.score
        
        # 各维度评分
        passenger_score = self._score_passenger_impact(option, flight, context)
        cost_score = self._score_operational_cost(option, flight, context)
        disruption_score = self._score_schedule_disruption(option, flight, context)
        resource_score = self._score_resource_utilization(option, flight, context)
        safety_score = self._score_safety_compliance(option, flight, context)
        
        # 加权综合评分
        final_score = (
            base_score * 0.4 +  # 基础分数权重
            passenger_score * self.weights["passenger_impact"] +
            cost_score * self.weights["operational_cost"] +
            disruption_score * self.weights["schedule_disruption"] +
            resource_score * self.weights["resource_utilization"] +
            safety_score * self.weights["safety_compliance"]
        ) / 1.4  # 归一化
        
        # 约束违反严重扣分
        if option.constraint_violations:
            violation_penalty = len(option.constraint_violations) * 15
            final_score = max(0, final_score - violation_penalty)
        
        return final_score
    
    def _score_passenger_impact(self, 
                               option: AdjustmentOption, 
                               flight: Flight,
                               context: OperationalContext) -> float:
        """评估对旅客的影响"""
        base_score = 100.0
        
        if option.action == AdjustmentAction.CHANGE_TIME:
            # 延误影响
            delay_minutes = option.details.get("delay_minutes", 0)
            if delay_minutes > 0:
                # 延误对旅客影响评分
                delay_penalty = min(delay_minutes * 0.3, 50.0)
                base_score -= delay_penalty
                
                # 国际航班延误影响更大
                if flight.is_international:
                    base_score -= delay_minutes * 0.1
        
        elif option.action == AdjustmentAction.CHANGE_AIRCRAFT:
            # 更换飞机对旅客影响
            seat_change = option.details.get("seat_change", 0)
            if seat_change < 0:  # 座位减少
                base_score -= abs(seat_change) * 0.5
        
        elif option.action == AdjustmentAction.CANCEL_FLIGHT:
            # 取消航班对旅客影响最大
            passenger_count = option.details.get("passenger_count", 0)
            base_score = max(10.0, 30.0 - passenger_count * 0.2)
        
        elif option.action == AdjustmentAction.CHANGE_AIRPORT:
            # 改机场对旅客影响较大
            base_score = 40.0
            if option.extra.get("ground_transport_required", False):
                base_score -= 20.0
        
        elif option.action == AdjustmentAction.ADD_FLIGHT:
            # 新增航班对旅客有利
            base_score = 120.0
        
        return max(0, base_score)
    
    def _score_operational_cost(self, 
                               option: AdjustmentOption, 
                               flight: Flight,
                               context: OperationalContext) -> float:
        """评估运营成本影响"""
        base_score = 100.0
        
        if option.action == AdjustmentAction.CHANGE_TIME:
            # 延误成本
            delay_minutes = option.details.get("delay_minutes", 0)
            # 每分钟延误成本（简化计算）
            delay_cost_penalty = delay_minutes * 0.1
            base_score -= delay_cost_penalty
        
        elif option.action == AdjustmentAction.CHANGE_AIRCRAFT:
            # 换飞机成本
            original_type = option.details.get("original_aircraft_type", "")
            new_type = option.details.get("new_aircraft_type", "")
            
            # 不同机型成本不同
            if original_type != new_type:
                base_score -= 15.0  # 机型变更额外成本
            
            seat_change = option.details.get("seat_change", 0)
            if seat_change > 0:  # 座位增加（大机型成本高）
                base_score -= seat_change * 0.05
        
        elif option.action == AdjustmentAction.CANCEL_FLIGHT:
            # 取消成本（包括赔偿）
            passenger_count = option.details.get("passenger_count", 0)
            cancellation_cost = passenger_count * 2.0  # 旅客赔偿成本
            base_score = max(20.0, 80.0 - cancellation_cost)
        
        elif option.action == AdjustmentAction.CHANGE_AIRPORT:
            # 改机场额外成本
            base_score = 60.0
        
        elif option.action == AdjustmentAction.ADD_FLIGHT:
            # 新增航班成本
            base_score = 50.0  # 新增航班有额外成本
        
        return max(0, base_score)
    
    def _score_schedule_disruption(self, 
                                  option: AdjustmentOption, 
                                  flight: Flight,
                                  context: OperationalContext) -> float:
        """评估对整体计划的扰动"""
        base_score = 100.0
        
        if option.action == AdjustmentAction.CHANGE_TIME:
            delay_minutes = option.details.get("delay_minutes", 0)
            # 延误时间越长，对后续计划影响越大
            disruption_penalty = delay_minutes * 0.2
            base_score -= disruption_penalty
            
            # 重保航班扰动影响更严重
            if flight.is_vip:
                base_score -= 30.0
        
        elif option.action == AdjustmentAction.CHANGE_AIRCRAFT:
            # 换飞机对后续计划影响
            base_score = 70.0
            if flight.is_vip:
                base_score -= 20.0
        
        elif option.action == AdjustmentAction.CANCEL_FLIGHT:
            # 取消对计划扰动大
            base_score = 30.0
            
            # 检查是否影响衔接航班
            affected_flights = option.details.get("affected_connecting_flights", [])
            base_score -= len(affected_flights) * 10
        
        elif option.action == AdjustmentAction.CHANGE_AIRPORT:
            # 改机场对计划扰动很大
            base_score = 25.0
        
        elif option.action == AdjustmentAction.ADD_FLIGHT:
            # 新增航班对现有计划扰动较小
            base_score = 90.0
        
        return max(0, base_score)
    
    def _score_resource_utilization(self, 
                                   option: AdjustmentOption, 
                                   flight: Flight,
                                   context: OperationalContext) -> float:
        """评估资源利用效率"""
        base_score = 100.0
        
        if option.action == AdjustmentAction.CHANGE_AIRCRAFT:
            # 评估飞机资源利用
            seat_change = option.details.get("seat_change", 0)
            if seat_change > 0:  # 座位增加（更好利用）
                base_score += min(seat_change * 0.1, 20.0)
            elif seat_change < 0:  # 座位减少（资源浪费）
                base_score -= abs(seat_change) * 0.1
        
        elif option.action == AdjustmentAction.CANCEL_FLIGHT:
            # 取消导致资源闲置
            base_score = 40.0
        
        elif option.action == AdjustmentAction.ADD_FLIGHT:
            # 新增航班提高资源利用
            base_score = 110.0
        
        return max(0, base_score)
    
    def _score_safety_compliance(self, 
                                option: AdjustmentOption, 
                                flight: Flight,
                                context: OperationalContext) -> float:
        """评估安全合规性"""
        base_score = 100.0
        
        # 有约束违反则大幅扣分
        if option.constraint_violations:
            safety_violations = [v for v in option.constraint_violations 
                               if any(keyword in v.lower() for keyword in 
                                     ["安全", "故障", "适航", "值勤", "限制"])]
            base_score -= len(safety_violations) * 25
        
        # 需要特别审批的方案合规性相对较低
        if option.extra.get("requires_approval", False):
            base_score -= 10.0
        
        # 重保航班相关调整需要更高安全标准
        if flight.is_vip:
            if option.action in [AdjustmentAction.CHANGE_AIRCRAFT, AdjustmentAction.CANCEL_FLIGHT]:
                base_score -= 20.0
        
        return max(0, base_score)
    
    def rank_options(self, 
                    options: List[AdjustmentOption],
                    flight: Flight,
                    context: OperationalContext) -> List[AdjustmentOption]:
        """对调整方案进行排序"""
        
        # 为每个选项计算最终评分
        scored_options = []
        for option in options:
            final_score = self.score_adjustment_option(option, flight, context)
            option.score = final_score  # 更新评分
            scored_options.append(option)
        
        # 按评分降序排列
        scored_options.sort(key=lambda x: x.score, reverse=True)
        
        return scored_options
    
    def filter_viable_options(self, 
                             options: List[AdjustmentOption],
                             min_score: float = 30.0) -> List[AdjustmentOption]:
        """过滤可行的调整方案"""
        
        viable_options = []
        for option in options:
            # 基本可行性检查
            if option.score >= min_score:
                # 硬约束检查：某些违反不可接受
                critical_violations = [v for v in option.constraint_violations 
                                     if any(keyword in v.lower() for keyword in 
                                           ["不允许", "禁止", "无法", "不能"])]
                
                if not critical_violations:
                    viable_options.append(option)
        
        return viable_options
    
    def get_best_options(self, 
                        options: List[AdjustmentOption],
                        flight: Flight,
                        context: OperationalContext,
                        max_count: int = 5) -> List[AdjustmentOption]:
        """获取最佳调整方案"""
        
        # 计算评分并排序
        ranked_options = self.rank_options(options, flight, context)
        
        # 过滤可行方案
        viable_options = self.filter_viable_options(ranked_options)
        
        # 返回前N个最佳方案
        return viable_options[:max_count]
    
    def explain_score(self, 
                     option: AdjustmentOption,
                     flight: Flight,
                     context: OperationalContext) -> Dict[str, Any]:
        """解释评分详情"""
        
        passenger_score = self._score_passenger_impact(option, flight, context)
        cost_score = self._score_operational_cost(option, flight, context)
        disruption_score = self._score_schedule_disruption(option, flight, context)
        resource_score = self._score_resource_utilization(option, flight, context)
        safety_score = self._score_safety_compliance(option, flight, context)
        
        return {
            "final_score": option.score,
            "breakdown": {
                "passenger_impact": {
                    "score": passenger_score,
                    "weight": self.weights["passenger_impact"],
                    "weighted_score": passenger_score * self.weights["passenger_impact"]
                },
                "operational_cost": {
                    "score": cost_score,
                    "weight": self.weights["operational_cost"],
                    "weighted_score": cost_score * self.weights["operational_cost"]
                },
                "schedule_disruption": {
                    "score": disruption_score,
                    "weight": self.weights["schedule_disruption"],
                    "weighted_score": disruption_score * self.weights["schedule_disruption"]
                },
                "resource_utilization": {
                    "score": resource_score,
                    "weight": self.weights["resource_utilization"],
                    "weighted_score": resource_score * self.weights["resource_utilization"]
                },
                "safety_compliance": {
                    "score": safety_score,
                    "weight": self.weights["safety_compliance"],
                    "weighted_score": safety_score * self.weights["safety_compliance"]
                }
            },
            "constraint_violations": option.constraint_violations,
            "requires_approval": option.extra.get("requires_approval", False)
        } 