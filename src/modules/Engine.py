from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from ..types.flight_models import (
    Flight, Aircraft, Crew, Airport, OperationalContext, 
    OperationalConstraint, AdjustmentOption, AdjustmentAction
)

from .Checker import ConstraintChecker
from .Planner import (
    TimeChangeStrategy, AircraftChangeStrategy, FlightCancellationStrategy,
    AirportChangeStrategy, FlightNatureChangeStrategy, AddFlightStrategy
)
from .Scorer import ScoringSystem


class FlightAdjustmentEngine:
    """航班调整算法引擎"""
    
    def __init__(self, 
                 airports: Dict[str, Airport],
                 aircrafts: Dict[str, Aircraft], 
                 crews: Dict[str, Crew],
                 constraints: Optional[OperationalConstraint] = None,
                 scoring_weights: Optional[Dict[str, float]] = None):
        """
        初始化航班调整引擎
        
        Args:
            airports: 机场信息字典
            aircrafts: 飞机信息字典
            crews: 机组信息字典
            constraints: 运行约束配置
            scoring_weights: 评分权重配置
        """
        self.airports = airports
        self.aircrafts = aircrafts
        self.crews = crews
        self.constraints = constraints or OperationalConstraint()
        
        # 初始化核心组件
        self.constraint_checker = ConstraintChecker(
            airports, aircrafts, crews, self.constraints
        )
        self.scoring_system = ScoringSystem(scoring_weights)
        
        # 初始化调整策略
        self.strategies = {
            AdjustmentAction.CHANGE_TIME: TimeChangeStrategy(self.constraint_checker),
            AdjustmentAction.CHANGE_AIRCRAFT: AircraftChangeStrategy(self.constraint_checker),
            AdjustmentAction.CANCEL_FLIGHT: FlightCancellationStrategy(self.constraint_checker),
            AdjustmentAction.CHANGE_AIRPORT: AirportChangeStrategy(self.constraint_checker),
            AdjustmentAction.CHANGE_NATURE: FlightNatureChangeStrategy(self.constraint_checker),
            AdjustmentAction.ADD_FLIGHT: AddFlightStrategy(self.constraint_checker)
        }
    
    def generate_adjustment_options(self, 
                                   flight: Flight,
                                   trigger_reason: str,
                                   context: OperationalContext,
                                   allowed_actions: Optional[List[AdjustmentAction]] = None) -> List[AdjustmentOption]:
        """
        生成航班调整选项
        
        Args:
            flight: 需要调整的航班
            trigger_reason: 触发调整的原因
            context: 运行环境上下文
            allowed_actions: 允许的调整动作类型
            
        Returns:
            调整选项列表
        """
        all_options = []
        
        # 如果没有指定允许的动作，则使用所有策略
        if allowed_actions is None:
            allowed_actions = list(self.strategies.keys())
        
        # 根据触发原因和航班情况，生成相应的调整选项
        for action in allowed_actions:
            if action in self.strategies:
                try:
                    strategy = self.strategies[action]
                    options = strategy.generate_options(flight, context, trigger_reason)
                    all_options.extend(options)
                except Exception as e:
                    # 记录策略执行错误，但不中断整个流程
                    print(f"策略 {action} 执行出错: {e}")
                    continue
        
        return all_options
    
    def get_best_adjustment_plans(self, 
                                 flight: Flight,
                                 trigger_reason: str,
                                 context: OperationalContext,
                                 max_options: int = 5,
                                 allowed_actions: Optional[List[AdjustmentAction]] = None) -> List[Dict[str, Any]]:
        """
        获取最佳调整方案
        
        Args:
            flight: 需要调整的航班
            trigger_reason: 触发调整的原因
            context: 运行环境上下文
            max_options: 返回的最大方案数
            allowed_actions: 允许的调整动作类型
            
        Returns:
            最佳调整方案列表，按评分降序排列
        """
        # 生成所有调整选项
        all_options = self.generate_adjustment_options(
            flight, trigger_reason, context, allowed_actions
        )
        
        if not all_options:
            return []
        
        # 获取最佳方案
        best_options = self.scoring_system.get_best_options(
            all_options, flight, context, max_options
        )
        
        # 转换为输出格式
        result = []
        for option in best_options:
            result.append(option.to_dict())
        
        return result
    
    def analyze_flight_adjustment_need(self, 
                                      flight: Flight,
                                      context: OperationalContext) -> Dict[str, Any]:
        """
        分析航班是否需要调整
        
        Args:
            flight: 待分析航班
            context: 运行环境上下文
            
        Returns:
            分析结果，包括是否需要调整、触发原因等
        """
        analysis = {
            "needs_adjustment": False,
            "triggers": [],
            "severity": "low",  # low, medium, high, critical
            "recommended_actions": [],
            "time_pressure": self._calculate_time_pressure(flight, context)
        }
        
        # 检查各种触发条件
        triggers = []
        
        # 1. 检查延误情况
        if flight.actual_departure:
            delay = flight.actual_departure - flight.scheduled_departure
            if delay > timedelta(minutes=30):
                triggers.append({
                    "type": "delay",
                    "reason": f"航班延误{delay.total_seconds()/60:.0f}分钟",
                    "severity": "medium" if delay < timedelta(hours=2) else "high"
                })
        
        # 2. 检查飞机状态
        aircraft = self.aircrafts.get(flight.aircraft_registration)
        if aircraft and not aircraft.is_available(flight.scheduled_departure):
            triggers.append({
                "type": "aircraft_unavailable",
                "reason": f"飞机{aircraft.registration}不可用",
                "severity": "high"
            })
        
        # 3. 检查机组状态
        crew = self.crews.get(flight.crew_id)
        if crew and not crew.is_available(flight.scheduled_departure, flight.aircraft_type):
            triggers.append({
                "type": "crew_unavailable", 
                "reason": f"机组{crew.crew_id}不可用",
                "severity": "high"
            })
        
        # 4. 检查天气情况
        if self._check_weather_impact(flight, context):
            triggers.append({
                "type": "weather",
                "reason": "恶劣天气影响",
                "severity": "medium"
            })
        
        # 5. 检查空管限制
        if self._check_atc_restrictions(flight, context):
            triggers.append({
                "type": "atc",
                "reason": "空管流量控制",
                "severity": "medium"
            })
        
        # 更新分析结果
        if triggers:
            analysis["needs_adjustment"] = True
            analysis["triggers"] = triggers
            
            # 确定整体严重程度
            severities = [t["severity"] for t in triggers]
            if "critical" in severities:
                analysis["severity"] = "critical"
            elif "high" in severities:
                analysis["severity"] = "high"
            elif "medium" in severities:
                analysis["severity"] = "medium"
            
            # 推荐调整动作
            analysis["recommended_actions"] = self._recommend_actions(triggers, flight)
        
        return analysis
    
    def handle_emergency_adjustment(self, 
                                   flight: Flight,
                                   emergency_type: str,
                                   context: OperationalContext) -> Dict[str, Any]:
        """
        处理紧急调整情况
        
        Args:
            flight: 航班信息
            emergency_type: 紧急情况类型
            context: 运行环境上下文
            
        Returns:
            紧急调整方案
        """
        emergency_actions = {
            "aircraft_failure": [AdjustmentAction.CHANGE_AIRCRAFT, AdjustmentAction.CANCEL_FLIGHT],
            "crew_emergency": [AdjustmentAction.CANCEL_FLIGHT, AdjustmentAction.CHANGE_TIME],
            "weather_severe": [AdjustmentAction.CHANGE_TIME, AdjustmentAction.CHANGE_AIRPORT, AdjustmentAction.CANCEL_FLIGHT],
            "airport_closure": [AdjustmentAction.CHANGE_AIRPORT, AdjustmentAction.CANCEL_FLIGHT],
            "security_incident": [AdjustmentAction.CANCEL_FLIGHT, AdjustmentAction.CHANGE_TIME]
        }
        
        allowed_actions = emergency_actions.get(emergency_type, list(self.strategies.keys()))
        
        # 紧急情况下，降低评分阈值，优先考虑可行性
        options = self.generate_adjustment_options(flight, emergency_type, context, allowed_actions)
        
        if options:
            # 紧急情况优先选择第一个可行方案
            viable_options = self.scoring_system.filter_viable_options(options, min_score=10.0)
            if viable_options:
                best_option = viable_options[0]
                return {
                    "emergency_response": True,
                    "recommended_action": best_option.to_dict(),
                    "all_options": [opt.to_dict() for opt in viable_options[:3]]
                }
        
        return {
            "emergency_response": True,
            "recommended_action": None,
            "message": "无可行调整方案，需要人工处理"
        }
    
    def batch_process_adjustments(self, 
                                 flights: List[Flight],
                                 context: OperationalContext) -> Dict[str, Any]:
        """
        批量处理航班调整
        
        Args:
            flights: 航班列表
            context: 运行环境上下文
            
        Returns:
            批量处理结果
        """
        results = {
            "processed_count": 0,
            "adjustment_needed": [],
            "no_adjustment": [],
            "errors": []
        }
        
        for flight in flights:
            try:
                analysis = self.analyze_flight_adjustment_need(flight, context)
                
                if analysis["needs_adjustment"]:
                    # 生成调整方案
                    trigger_reason = analysis["triggers"][0]["type"] if analysis["triggers"] else "unknown"
                    plans = self.get_best_adjustment_plans(flight, trigger_reason, context)
                    
                    results["adjustment_needed"].append({
                        "flight": flight.flight_no,
                        "analysis": analysis,
                        "plans": plans
                    })
                else:
                    results["no_adjustment"].append({
                        "flight": flight.flight_no,
                        "status": "normal"
                    })
                
                results["processed_count"] += 1
                
            except Exception as e:
                results["errors"].append({
                    "flight": flight.flight_no,
                    "error": str(e)
                })
        
        return results
    
    def explain_adjustment_decision(self, 
                                   option: AdjustmentOption,
                                   flight: Flight,
                                   context: OperationalContext) -> Dict[str, Any]:
        """
        解释调整决策
        
        Args:
            option: 调整选项
            flight: 航班信息
            context: 运行环境上下文
            
        Returns:
            决策解释
        """
        score_explanation = self.scoring_system.explain_score(option, flight, context)
        
        return {
            "decision_summary": {
                "action": option.action.value,
                "reason": option.reason,
                "score": option.score,
                "flight": flight.flight_no
            },
            "scoring_details": score_explanation,
            "constraints_checked": len(option.constraint_violations) == 0,
            "approval_required": option.extra.get("requires_approval", False),
            "implementation_notes": self._get_implementation_notes(option, flight)
        }
    
    # 私有辅助方法
    def _calculate_time_pressure(self, flight: Flight, context: OperationalContext) -> str:
        """计算时间压力"""
        time_to_departure = flight.scheduled_departure - context.current_time
        
        if time_to_departure < timedelta(hours=1):
            return "critical"
        elif time_to_departure < timedelta(hours=3):
            return "high"
        elif time_to_departure < timedelta(hours=12):
            return "medium"
        else:
            return "low"
    
    def _check_weather_impact(self, flight: Flight, context: OperationalContext) -> bool:
        """检查天气影响"""
        # 简化实现：检查上下文中的天气信息
        weather = context.weather_conditions
        
        dep_weather = weather.get(flight.departure_airport, "")
        arr_weather = weather.get(flight.arrival_airport, "")
        
        severe_conditions = ["thunderstorm", "heavy_rain", "snow", "fog"]
        return any(condition in dep_weather.lower() or condition in arr_weather.lower() 
                  for condition in severe_conditions)
    
    def _check_atc_restrictions(self, flight: Flight, context: OperationalContext):
        """检查空管限制"""
        # 简化实现：检查上下文中的空管限制
        restrictions = context.atc_restrictions
        
        return (flight.departure_airport in restrictions or 
                flight.arrival_airport in restrictions)
    
    def _recommend_actions(self, triggers: List[Dict], flight: Flight):
        """推荐调整动作"""
        recommendations = []
        
        for trigger in triggers:
            trigger_type = trigger["type"]
            
            if trigger_type == "delay":
                recommendations.append("CHANGE_TIME")
            elif trigger_type == "aircraft_unavailable":
                recommendations.extend(["CHANGE_AIRCRAFT", "CANCEL_FLIGHT"])
            elif trigger_type == "crew_unavailable":
                recommendations.extend(["CHANGE_TIME", "CANCEL_FLIGHT"])
            elif trigger_type == "weather":
                recommendations.extend(["CHANGE_TIME", "CHANGE_AIRPORT"])
            elif trigger_type == "atc":
                recommendations.append("CHANGE_TIME")
        
        # 去重并保持顺序
        return list(dict.fromkeys(recommendations))
    
    def _get_implementation_notes(self, option: AdjustmentOption, flight: Flight) -> List[str]:
        """获取实施注意事项"""
        notes = []
        
        if option.action == AdjustmentAction.CHANGE_TIME:
            delay_minutes = option.details.get("delay_minutes", 0)
            if delay_minutes > 120:
                notes.append("长时间延误需要通知旅客并提供服务")
            
        elif option.action == AdjustmentAction.CHANGE_AIRCRAFT:
            if option.details.get("seat_change", 0) < 0:
                notes.append("座位减少需要重新安排旅客")
            
        elif option.action == AdjustmentAction.CANCEL_FLIGHT:
            notes.append("需要安排旅客改签或退票")
            notes.append("需要通知相关保障单位")
        
        if option.extra.get("requires_approval", False):
            notes.append("此调整需要获得上级审批")
        
        if option.constraint_violations:
            notes.append("存在约束违反，需要特别关注")
        
        return notes
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "airports_count": len(self.airports),
            "aircrafts_count": len(self.aircrafts),
            "crews_count": len(self.crews),
            "strategies_available": [action.value for action in self.strategies.keys()],
            "constraints_config": {
                "min_turnaround_time": self.constraints.min_turnaround_time,
                "max_delay_threshold": self.constraints.max_delay_threshold,
                "crew_duty_limits": self.constraints.crew_duty_limits
            },
            "scoring_weights": self.scoring_system.weights
        } 