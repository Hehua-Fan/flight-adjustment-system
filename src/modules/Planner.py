from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from ..types.flight_models import (
    Flight, Aircraft, Crew, Airport, OperationalContext, 
    AdjustmentOption, AdjustmentAction, FlightStatus
)
from ..modules.Checker import ConstraintChecker


class AdjustmentStrategy:
    """调整策略基类"""
    
    def __init__(self, constraint_checker: ConstraintChecker):
        self.constraint_checker = constraint_checker
    
    def generate_options(self, 
                        flight: Flight, 
                        context: OperationalContext,
                        trigger_reason: str) -> List[AdjustmentOption]:
        """生成调整选项 - 由子类实现"""
        raise NotImplementedError


class TimeChangeStrategy(AdjustmentStrategy):
    """变更时刻策略"""
    
    def generate_options(self, 
                        flight: Flight, 
                        context: OperationalContext,
                        trigger_reason: str) -> List[AdjustmentOption]:
        """生成时刻变更选项"""
        options = []
        
        # 生成不同延误时长的选项
        delay_options = [30, 60, 120, 180, 240]  # 分钟
        
        for delay_minutes in delay_options:
            new_departure = flight.scheduled_departure + timedelta(minutes=delay_minutes)
            new_arrival = new_departure + flight.get_flight_duration()
            
            # 检查约束
            is_valid, violations = self.constraint_checker.check_time_change_constraints(
                flight, new_departure, context
            )
            
            # 计算评分（延误越少分数越高）
            base_score = 100.0
            delay_penalty = delay_minutes * 0.2
            violation_penalty = len(violations) * 10
            score = max(0, base_score - delay_penalty - violation_penalty)
            
            # 确定调整原因
            reason_mapping = {
                "weather": f"天气原因延误{delay_minutes}分钟",
                "atc": f"空管流控延误{delay_minutes}分钟", 
                "maintenance": f"飞机故障延误{delay_minutes}分钟",
                "crew": f"机组原因延误{delay_minutes}分钟",
                "default": f"运行调整延误{delay_minutes}分钟"
            }
            reason = reason_mapping.get(trigger_reason, reason_mapping["default"])
            
            option = AdjustmentOption(
                action=AdjustmentAction.CHANGE_TIME,
                flight_no=flight.flight_no,
                reason=reason,
                score=score,
                details={
                    "original_departure": flight.scheduled_departure.isoformat(),
                    "new_departure": new_departure.isoformat(),
                    "original_arrival": flight.scheduled_arrival.isoformat(),
                    "new_arrival": new_arrival.isoformat(),
                    "delay_minutes": delay_minutes
                },
                extra={
                    "requires_approval": delay_minutes >= 120 or flight.is_international and delay_minutes >= 60
                },
                constraint_violations=violations
            )
            options.append(option)
        
        return options


class AircraftChangeStrategy(AdjustmentStrategy):
    """更换飞机策略"""
    
    def generate_options(self, 
                        flight: Flight, 
                        context: OperationalContext,
                        trigger_reason: str) -> List[AdjustmentOption]:
        """生成更换飞机选项"""
        options = []
        
        # 查找可用的替代飞机
        available_aircraft = self._find_available_aircraft(flight, context)
        
        for aircraft_reg, aircraft in available_aircraft.items():
            # 检查约束
            is_valid, violations = self.constraint_checker.check_aircraft_change_constraints(
                flight, aircraft_reg, context
            )
            
            # 计算评分
            score = self._calculate_aircraft_change_score(flight, aircraft, violations)
            
            # 确定调整原因
            reason_mapping = {
                "maintenance": f"飞机故障更换为{aircraft_reg}",
                "capacity": f"座位需求更换为{aircraft_reg}",
                "route": f"航线要求更换为{aircraft_reg}",
                "default": f"运行需要更换为{aircraft_reg}"
            }
            reason = reason_mapping.get(trigger_reason, reason_mapping["default"])
            
            option = AdjustmentOption(
                action=AdjustmentAction.CHANGE_AIRCRAFT,
                flight_no=flight.flight_no,
                reason=reason,
                score=score,
                details={
                    "original_aircraft": flight.aircraft_registration,
                    "new_aircraft": aircraft_reg,
                    "original_aircraft_type": flight.aircraft_type,
                    "new_aircraft_type": aircraft.aircraft_type,
                    "seat_change": aircraft.seat_capacity - self.constraint_checker.aircrafts[flight.aircraft_registration].seat_capacity
                },
                extra={
                    "requires_approval": flight.is_vip or aircraft.aircraft_type != flight.aircraft_type
                },
                constraint_violations=violations
            )
            options.append(option)
        
        return options
    
    def _find_available_aircraft(self, flight: Flight, context: OperationalContext) -> Dict[str, Aircraft]:
        """查找可用替代飞机"""
        available = {}
        
        for reg, aircraft in self.constraint_checker.aircrafts.items():
            if reg == flight.aircraft_registration:
                continue
                
            # 基本可用性检查
            if aircraft.is_available(flight.scheduled_departure):
                # 位置检查（简化：假设飞机在出发机场或可以调配）
                if aircraft.current_airport == flight.departure_airport or self._can_position(aircraft, flight):
                    available[reg] = aircraft
        
        return available
    
    def _can_position(self, aircraft: Aircraft, flight: Flight) -> bool:
        """检查飞机是否可以调配到位"""
        # 简化实现：假设可以调配
        return True
    
    def _calculate_aircraft_change_score(self, flight: Flight, new_aircraft: Aircraft, violations: List[str]) -> float:
        """计算更换飞机的评分"""
        base_score = 80.0
        
        # 机型匹配加分
        if new_aircraft.aircraft_type == flight.aircraft_type:
            base_score += 20.0
        
        # 座位容量评分
        original_aircraft = self.constraint_checker.aircrafts[flight.aircraft_registration]
        seat_diff = new_aircraft.seat_capacity - original_aircraft.seat_capacity
        if seat_diff >= 0:  # 座位增加或相等
            base_score += min(seat_diff * 0.1, 10.0)
        else:  # 座位减少
            base_score += max(seat_diff * 0.2, -20.0)
        
        # 约束违反扣分
        violation_penalty = len(violations) * 15
        
        return max(0, base_score - violation_penalty)


class FlightCancellationStrategy(AdjustmentStrategy):
    """取消航班策略"""
    
    def generate_options(self, 
                        flight: Flight, 
                        context: OperationalContext,
                        trigger_reason: str) -> List[AdjustmentOption]:
        """生成取消航班选项"""
        options = []
        
        # 检查取消约束
        is_valid, violations = self.constraint_checker.check_flight_cancellation_constraints(
            flight, context
        )
        
        # 计算评分（取消通常是最后选择）
        base_score = 30.0
        
        # 根据航班重要性调整评分
        if flight.is_vip:
            base_score = 10.0  # 重保航班取消评分很低
        elif flight.is_international:
            base_score = 20.0  # 国际航班取消评分较低
        
        # 旅客数量影响评分
        passenger_penalty = min(flight.passenger_count * 0.1, 30.0)
        
        # 约束违反扣分
        violation_penalty = len(violations) * 20
        
        score = max(0, base_score - passenger_penalty - violation_penalty)
        
        # 确定调整原因
        reason_mapping = {
            "weather": "恶劣天气取消航班",
            "maintenance": "飞机故障取消航班",
            "crew": "机组不足取消航班",
            "atc": "空管限制取消航班",
            "default": "运行需要取消航班"
        }
        reason = reason_mapping.get(trigger_reason, reason_mapping["default"])
        
        option = AdjustmentOption(
            action=AdjustmentAction.CANCEL_FLIGHT,
            flight_no=flight.flight_no,
            reason=reason,
            score=score,
            details={
                "passenger_count": flight.passenger_count,
                "cancellation_time": context.current_time.isoformat(),
                "affected_connecting_flights": self._find_connecting_flights(flight)
            },
            extra={
                "requires_approval": True,  # 取消航班总是需要审批
                "passenger_compensation_required": flight.passenger_count > 0
            },
            constraint_violations=violations
        )
        options.append(option)
        
        return options
    
    def _find_connecting_flights(self, flight: Flight) -> List[str]:
        """查找受影响的衔接航班"""
        # 简化实现：返回空列表
        return []


class AirportChangeStrategy(AdjustmentStrategy):
    """变更起降机场策略"""
    
    def generate_options(self, 
                        flight: Flight, 
                        context: OperationalContext,
                        trigger_reason: str) -> List[AdjustmentOption]:
        """生成变更起降机场选项"""
        options = []
        
        # 查找备降机场选项
        alternative_airports = self._find_alternative_airports(flight)
        
        for new_dep, new_arr in alternative_airports:
            # 检查约束
            is_valid, violations = self.constraint_checker.check_airport_change_constraints(
                flight, new_dep, new_arr, context
            )
            
            # 计算评分
            score = self._calculate_airport_change_score(flight, new_dep, new_arr, violations)
            
            # 确定调整原因
            reason_mapping = {
                "weather": f"天气原因改为{new_dep}-{new_arr}",
                "runway": f"跑道关闭改为{new_dep}-{new_arr}",
                "capacity": f"机场容量限制改为{new_dep}-{new_arr}",
                "default": f"运行需要改为{new_dep}-{new_arr}"
            }
            reason = reason_mapping.get(trigger_reason, reason_mapping["default"])
            
            option = AdjustmentOption(
                action=AdjustmentAction.CHANGE_AIRPORT,
                flight_no=flight.flight_no,
                reason=reason,
                score=score,
                details={
                    "original_route": f"{flight.departure_airport}-{flight.arrival_airport}",
                    "new_route": f"{new_dep}-{new_arr}",
                    "distance_change": self._calculate_distance_change(flight, new_dep, new_arr)
                },
                extra={
                    "requires_approval": True,  # 改机场总是需要审批
                    "ground_transport_required": new_dep != flight.departure_airport or new_arr != flight.arrival_airport
                },
                constraint_violations=violations
            )
            options.append(option)
        
        return options
    
    def _find_alternative_airports(self, flight: Flight) -> List[tuple]:
        """查找备选机场"""
        alternatives = []
        
        # 同城机场替换
        city_airports = {
            "PEK": ["PKX"],  # 北京大兴
            "PKX": ["PEK"],  # 北京首都
            "PVG": ["SHA"],  # 上海虹桥
            "SHA": ["PVG"],  # 上海浦东
        }
        
        # 出发机场替换
        if flight.departure_airport in city_airports:
            for alt_dep in city_airports[flight.departure_airport]:
                alternatives.append((alt_dep, flight.arrival_airport))
        
        # 到达机场替换
        if flight.arrival_airport in city_airports:
            for alt_arr in city_airports[flight.arrival_airport]:
                alternatives.append((flight.departure_airport, alt_arr))
        
        return alternatives
    
    def _calculate_airport_change_score(self, flight: Flight, new_dep: str, new_arr: str, violations: List[str]) -> float:
        """计算机场变更评分"""
        base_score = 50.0
        
        # 同城机场变更评分较高
        if self._is_same_city_airport(flight.departure_airport, new_dep):
            base_score += 20.0
        if self._is_same_city_airport(flight.arrival_airport, new_arr):
            base_score += 20.0
        
        # 约束违反扣分
        violation_penalty = len(violations) * 15
        
        return max(0, base_score - violation_penalty)
    
    def _is_same_city_airport(self, airport1: str, airport2: str) -> bool:
        """检查是否为同城机场"""
        same_city_groups = [
            ["PEK", "PKX"],
            ["PVG", "SHA"],
            ["CAN", "SZX"]
        ]
        
        for group in same_city_groups:
            if airport1 in group and airport2 in group:
                return True
        return False
    
    def _calculate_distance_change(self, flight: Flight, new_dep: str, new_arr: str) -> Dict[str, int]:
        """计算距离变化（简化实现）"""
        return {"distance_km": 0, "time_minutes": 0}


class FlightNatureChangeStrategy(AdjustmentStrategy):
    """变更航班性质策略"""
    
    def generate_options(self, 
                        flight: Flight, 
                        context: OperationalContext,
                        trigger_reason: str) -> List[AdjustmentOption]:
        """生成变更航班性质选项"""
        options = []
        
        # 载客转货机
        if not flight.is_cargo and flight.passenger_count == 0:
            option = self._create_passenger_to_cargo_option(flight, trigger_reason)
            options.append(option)
        
        # 货机转载客
        if flight.is_cargo:
            option = self._create_cargo_to_passenger_option(flight, trigger_reason)
            options.append(option)
        
        # 正班转空机
        if flight.passenger_count == 0:
            option = self._create_to_ferry_option(flight, trigger_reason)
            options.append(option)
        
        return options
    
    def _create_passenger_to_cargo_option(self, flight: Flight, trigger_reason: str) -> AdjustmentOption:
        """创建载客转货机选项"""
        return AdjustmentOption(
            action=AdjustmentAction.CHANGE_NATURE,
            flight_no=flight.flight_no,
            reason="变更为货运航班",
            score=60.0,
            details={
                "original_nature": "passenger",
                "new_nature": "cargo",
                "passenger_impact": flight.passenger_count
            },
            extra={"requires_approval": True}
        )
    
    def _create_cargo_to_passenger_option(self, flight: Flight, trigger_reason: str) -> AdjustmentOption:
        """创建货机转载客选项"""
        return AdjustmentOption(
            action=AdjustmentAction.CHANGE_NATURE,
            flight_no=flight.flight_no,
            reason="变更为客运航班",
            score=70.0,
            details={
                "original_nature": "cargo",
                "new_nature": "passenger",
                "cargo_impact": "需要重新安排货物运输"
            },
            extra={"requires_approval": True}
        )
    
    def _create_to_ferry_option(self, flight: Flight, trigger_reason: str) -> AdjustmentOption:
        """创建转空机选项"""
        return AdjustmentOption(
            action=AdjustmentAction.CHANGE_NATURE,
            flight_no=flight.flight_no,
            reason="变更为空机调配",
            score=40.0,
            details={
                "original_nature": "scheduled",
                "new_nature": "ferry",
                "passenger_impact": flight.passenger_count
            },
            extra={"requires_approval": True}
        )


class AddFlightStrategy(AdjustmentStrategy):
    """新增航班策略"""
    
    def generate_options(self, 
                        flight: Flight, 
                        context: OperationalContext,
                        trigger_reason: str) -> List[AdjustmentOption]:
        """生成新增航班选项"""
        options = []
        
        # 补班航班（针对取消的航班）
        if trigger_reason == "compensation":
            option = self._create_compensation_flight_option(flight, context)
            options.append(option)
        
        # 加班航班（运力不足）
        if trigger_reason == "capacity":
            option = self._create_additional_capacity_option(flight, context)
            options.append(option)
        
        # 临时任务航班
        if trigger_reason == "special_mission":
            option = self._create_special_mission_option(flight, context)
            options.append(option)
        
        return options
    
    def _create_compensation_flight_option(self, flight: Flight, context: OperationalContext) -> AdjustmentOption:
        """创建补班航班选项"""
        new_flight_no = f"{flight.flight_no}X"  # 补班航班号
        
        return AdjustmentOption(
            action=AdjustmentAction.ADD_FLIGHT,
            flight_no=new_flight_no,
            reason="新增补班任务",
            score=85.0,
            details={
                "original_flight": flight.flight_no,
                "new_flight_no": new_flight_no,
                "route": f"{flight.departure_airport}-{flight.arrival_airport}",
                "aircraft_type": flight.aircraft_type,
                "scheduled_time": (context.current_time + timedelta(hours=2)).isoformat()
            },
            extra={
                "requires_approval": True,
                "new_flight_no": new_flight_no
            }
        )
    
    def _create_additional_capacity_option(self, flight: Flight, context: OperationalContext) -> AdjustmentOption:
        """创建加班航班选项"""
        new_flight_no = f"CA{int(flight.flight_no[2:]) + 1000}"  # 生成新航班号
        
        return AdjustmentOption(
            action=AdjustmentAction.ADD_FLIGHT,
            flight_no=new_flight_no,
            reason="新增加班航班",
            score=75.0,
            details={
                "new_flight_no": new_flight_no,
                "route": f"{flight.departure_airport}-{flight.arrival_airport}",
                "purpose": "增加运力",
                "scheduled_time": (flight.scheduled_departure + timedelta(hours=1)).isoformat()
            },
            extra={
                "requires_approval": True,
                "new_flight_no": new_flight_no
            }
        )
    
    def _create_special_mission_option(self, flight: Flight, context: OperationalContext) -> AdjustmentOption:
        """创建特殊任务航班选项"""
        new_flight_no = f"CA9{context.current_time.strftime('%d%H')}"  # 特殊任务航班号
        
        return AdjustmentOption(
            action=AdjustmentAction.ADD_FLIGHT,
            flight_no=new_flight_no,
            reason="新增特殊任务航班",
            score=90.0,
            details={
                "new_flight_no": new_flight_no,
                "mission_type": "特殊运输任务",
                "route": f"{flight.departure_airport}-{flight.arrival_airport}",
                "priority": "高"
            },
            extra={
                "requires_approval": True,
                "new_flight_no": new_flight_no
            }
        ) 