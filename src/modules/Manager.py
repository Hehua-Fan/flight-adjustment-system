from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import uuid
from ..types.flight_models import Flight
from ..types.planning_models import PlanConflict, PlanningWindow
from ..modules.Engine import FlightAdjustmentEngine


class PlanningHorizonManager:
    """
    72小时滚动计划管理器
    负责中长期航班计划的优化和动态调整
    """

    def __init__(self, adjustment_engine: FlightAdjustmentEngine):
        self.engine = adjustment_engine
        self.planning_window = timedelta(hours=72)
        self.update_frequency = timedelta(hours=6)
        self.current_plan: Optional[PlanningWindow] = None
        self.plan_history: List[PlanningWindow] = []
        
        # 计划优化参数
        self.optimization_weights = {
            "on_time_performance": 0.3,
            "resource_utilization": 0.25,
            "operational_cost": 0.2,
            "passenger_satisfaction": 0.15,
            "flexibility_buffer": 0.1
        }
    
    def generate_72h_baseline_plan(self, base_time: datetime = None):
        """生成72小时基准计划"""
        if base_time is None:
            base_time = datetime.now()
        
        end_time = base_time + self.planning_window
        
        # 获取计划窗口内的所有航班
        flights = self._get_flights_in_window(base_time, end_time)
        
        # 优化计划
        optimized_flights = self._optimize_long_term_plan(flights, base_time)
        
        # 检测冲突
        conflicts = self._detect_plan_conflicts(optimized_flights)
        
        # 计算置信度
        confidence = self._calculate_plan_confidence(optimized_flights, conflicts)
        
        plan = PlanningWindow(
            plan_id=f"72H_{base_time.strftime('%Y%m%d_%H%M%S')}",
            valid_from=base_time,
            valid_until=end_time,
            flights=optimized_flights,
            conflicts=conflicts,
            confidence_level=confidence
        )
        
        self.current_plan = plan
        return plan
    
    def rolling_update_plan(self):
        """滚动更新计划"""
        current_time = datetime.now()
        
        if (self.current_plan is None or 
            current_time - self.current_plan.last_updated >= self.update_frequency):
            
            # 保存当前计划到历史
            if self.current_plan:
                self.plan_history.append(self.current_plan)
                # 只保留最近10个计划版本
                if len(self.plan_history) > 10:
                    self.plan_history.pop(0)
            
            # 生成新计划
            new_plan = self.generate_72h_baseline_plan(current_time)
            
            # 分析计划变化
            if self.current_plan:
                changes = self._analyze_plan_changes(self.current_plan, new_plan)
                self._notify_plan_changes(changes)
            
            return new_plan
        
        return self.current_plan
    
    def detect_plan_conflicts(self, flights: List[Flight] = None):
        """检测计划冲突"""
        if flights is None and self.current_plan:
            flights = self.current_plan.flights
        elif flights is None:
            return []
        
        return self._detect_plan_conflicts(flights)
    
    def resolve_conflict(self, conflict_id: str, resolution_strategy: str):
        """解决计划冲突"""
        if not self.current_plan:
            return {"success": False, "error": "没有当前计划"}
        
        # 查找冲突
        conflict = next((c for c in self.current_plan.conflicts if c.conflict_id == conflict_id), None)
        if not conflict:
            return {"success": False, "error": "冲突不存在"}
        
        # 根据策略解决冲突
        if resolution_strategy == "automatic":
            return self._auto_resolve_conflict(conflict)
        elif resolution_strategy == "manual":
            return self._prepare_manual_resolution(conflict)
        else:
            return {"success": False, "error": "未知解决策略"}
    
    def get_plan_statistics(self):
        """获取计划统计信息"""
        if not self.current_plan:
            return {"error": "没有当前计划"}
        
        flights = self.current_plan.flights
        conflicts = self.current_plan.conflicts
        
        stats = {
            "plan_id": self.current_plan.plan_id,
            "total_flights": len(flights),
            "total_conflicts": len(conflicts),
            "confidence_level": self.current_plan.confidence_level,
            "conflicts_by_type": self._group_conflicts_by_type(conflicts),
            "flights_by_status": self._group_flights_by_status(flights),
            "resource_utilization": self._calculate_resource_utilization(flights),
            "predicted_delays": self._predict_potential_delays(flights)
        }
        
        return stats
    
    # 私有方法
    def _get_flights_in_window(self, start_time: datetime, end_time: datetime):
        """获取时间窗口内的航班"""
        # 这里应该从数据库或外部系统获取真实数据
        # 为演示目的，生成模拟数据
        flights = []
        
        # 生成每天约100个航班的示例数据
        for day_offset in range(3):  # 3天
            day_start = start_time + timedelta(days=day_offset)
            
            for flight_num in range(1, 101):  # 每天100个航班
                flight_time = day_start + timedelta(
                    hours=6 + (flight_num * 12) // 100,  # 6点到18点分布
                    minutes=(flight_num * 30) % 60
                )
                
                if flight_time < end_time:
                    flight = Flight(
                        flight_no=f"CA{1000 + flight_num + day_offset * 100}",
                        departure_airport=["PEK", "PVG", "CAN", "CTU", "KMG"][flight_num % 5],
                        arrival_airport=["PVG", "CAN", "CTU", "KMG", "PEK"][flight_num % 5],
                        scheduled_departure=flight_time,
                        scheduled_arrival=flight_time + timedelta(hours=2, minutes=30),
                        aircraft_registration=f"B-{1000 + (flight_num % 50):04d}",
                        crew_id=f"CREW{(flight_num % 20):03d}",
                        aircraft_type=["A320", "A330", "B737", "B777"][flight_num % 4],
                        passenger_count=150 + flight_num % 100
                    )
                    flights.append(flight)
        
        return flights
    
    def _optimize_long_term_plan(self, flights: List[Flight], base_time: datetime):
        """优化长期计划"""
        optimized_flights = flights.copy()
        
        # 按时间排序
        optimized_flights.sort(key=lambda f: f.scheduled_departure)
        
        # 应用优化策略
        optimized_flights = self._optimize_aircraft_utilization(optimized_flights)
        optimized_flights = self._optimize_crew_scheduling(optimized_flights)
        optimized_flights = self._optimize_slot_allocation(optimized_flights)
        
        return optimized_flights
    
    def _detect_plan_conflicts(self, flights: List[Flight]):
        """检测计划冲突"""
        conflicts = []
        
        # 检测飞机冲突
        aircraft_conflicts = self._check_aircraft_conflicts(flights)
        conflicts.extend(aircraft_conflicts)
        
        # 检测机组冲突
        crew_conflicts = self._check_crew_conflicts(flights)
        conflicts.extend(crew_conflicts)
        
        # 检测时刻冲突
        slot_conflicts = self._check_slot_conflicts(flights)
        conflicts.extend(slot_conflicts)
        
        # 检测维修冲突
        maintenance_conflicts = self._check_maintenance_conflicts(flights)
        conflicts.extend(maintenance_conflicts)
        
        return conflicts
    
    def _check_aircraft_conflicts(self, flights: List[Flight]):
        """检查飞机冲突"""
        conflicts = []
        aircraft_schedule = {}
        
        for flight in flights:
            aircraft_reg = flight.aircraft_registration
            if aircraft_reg not in aircraft_schedule:
                aircraft_schedule[aircraft_reg] = []
            aircraft_schedule[aircraft_reg].append(flight)
        
        for aircraft_reg, aircraft_flights in aircraft_schedule.items():
            # 按时间排序
            aircraft_flights.sort(key=lambda f: f.scheduled_departure)
            
            # 检查过站时间冲突
            for i in range(len(aircraft_flights) - 1):
                current_flight = aircraft_flights[i]
                next_flight = aircraft_flights[i + 1]
                
                # 计算过站时间
                turnaround_time = next_flight.scheduled_departure - current_flight.scheduled_arrival
                min_turnaround = timedelta(minutes=45)  # 最小过站时间45分钟
                
                if turnaround_time < min_turnaround:
                    conflict = PlanConflict(
                        conflict_id=str(uuid.uuid4()),
                        conflict_type="aircraft",
                        severity="high",
                        affected_flights=[current_flight.flight_no, next_flight.flight_no],
                        description=f"飞机{aircraft_reg}过站时间不足，需要{min_turnaround}，实际只有{turnaround_time}",
                        suggested_resolution=f"延误{next_flight.flight_no}至少{min_turnaround - turnaround_time}",
                        resolution_deadline=next_flight.scheduled_departure - timedelta(hours=2)
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _check_crew_conflicts(self, flights: List[Flight]):
        """检查机组冲突"""
        conflicts = []
        crew_schedule = {}
        
        for flight in flights:
            crew_id = flight.crew_id
            if crew_id not in crew_schedule:
                crew_schedule[crew_id] = []
            crew_schedule[crew_id].append(flight)
        
        for crew_id, crew_flights in crew_schedule.items():
            crew_flights.sort(key=lambda f: f.scheduled_departure)
            
            # 检查值勤时间限制
            total_duty_time = timedelta()
            for flight in crew_flights:
                flight_duration = flight.get_flight_duration()
                total_duty_time += flight_duration
                
                # 检查单日值勤时间（最大14小时）
                if total_duty_time > timedelta(hours=14):
                    conflict = PlanConflict(
                        conflict_id=str(uuid.uuid4()),
                        conflict_type="crew",
                        severity="critical",
                        affected_flights=[f.flight_no for f in crew_flights],
                        description=f"机组{crew_id}值勤时间超限，总计{total_duty_time}",
                        suggested_resolution="重新分配机组或调整航班时刻",
                        resolution_deadline=crew_flights[0].scheduled_departure - timedelta(hours=4)
                    )
                    conflicts.append(conflict)
                    break
        
        return conflicts
    
    def _check_slot_conflicts(self, flights: List[Flight]):
        """检查时刻冲突"""
        conflicts = []
        airport_slots = {}
        
        for flight in flights:
            # 检查起飞时刻
            dep_airport = flight.departure_airport
            dep_time = flight.scheduled_departure
            
            if dep_airport not in airport_slots:
                airport_slots[dep_airport] = {"departures": [], "arrivals": []}
            
            airport_slots[dep_airport]["departures"].append((dep_time, flight))
            
            # 检查降落时刻
            arr_airport = flight.arrival_airport
            arr_time = flight.scheduled_arrival
            
            if arr_airport not in airport_slots:
                airport_slots[arr_airport] = {"departures": [], "arrivals": []}
            
            airport_slots[arr_airport]["arrivals"].append((arr_time, flight))
        
        # 检查时刻间隔
        for airport, slots in airport_slots.items():
            # 检查起飞时刻冲突
            departures = sorted(slots["departures"])
            for i in range(len(departures) - 1):
                time_diff = departures[i + 1][0] - departures[i][0]
                if time_diff < timedelta(minutes=2):  # 最小间隔2分钟
                    conflict = PlanConflict(
                        conflict_id=str(uuid.uuid4()),
                        conflict_type="slot",
                        severity="medium",
                        affected_flights=[departures[i][1].flight_no, departures[i + 1][1].flight_no],
                        description=f"机场{airport}起飞时刻冲突，间隔仅{time_diff}",
                        suggested_resolution="调整其中一个航班起飞时刻"
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _check_maintenance_conflicts(self, flights: List[Flight]):
        """检查维修冲突"""
        conflicts = []
        
        # 简化实现：假设每架飞机每24小时需要2小时维修时间
        aircraft_flying_time = {}
        
        for flight in flights:
            aircraft_reg = flight.aircraft_registration
            if aircraft_reg not in aircraft_flying_time:
                aircraft_flying_time[aircraft_reg] = timedelta()
            
            aircraft_flying_time[aircraft_reg] += flight.get_flight_duration()
        
        for aircraft_reg, total_time in aircraft_flying_time.items():
            # 如果飞行时间超过22小时，需要安排维修
            if total_time > timedelta(hours=22):
                conflict = PlanConflict(
                    conflict_id=str(uuid.uuid4()),
                    conflict_type="maintenance",
                    severity="medium",
                    affected_flights=[f.flight_no for f in flights if f.aircraft_registration == aircraft_reg],
                    description=f"飞机{aircraft_reg}需要安排维修时间，当前飞行时间{total_time}",
                    suggested_resolution="在72小时内安排2小时维修时间"
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _calculate_plan_confidence(self, flights: List[Flight], conflicts: List[PlanConflict]):
        """计算计划置信度"""
        base_confidence = 100.0
        
        # 根据冲突数量和严重程度降低置信度
        for conflict in conflicts:
            if conflict.severity == "critical":
                base_confidence -= 20
            elif conflict.severity == "high":
                base_confidence -= 10
            elif conflict.severity == "medium":
                base_confidence -= 5
            else:  # low
                base_confidence -= 2
        
        # 根据时间窗口内的复杂度调整
        complexity_factor = len(flights) / 300.0  # 假设300航班为标准复杂度
        base_confidence -= complexity_factor * 10
        
        return max(0.0, min(100.0, base_confidence))
    
    def _optimize_aircraft_utilization(self, flights: List[Flight]):
        """优化飞机利用率"""
        # 简化实现：按机型分组，优化连续航班的安排
        aircraft_groups = {}
        
        for flight in flights:
            aircraft_type = flight.aircraft_type
            if aircraft_type not in aircraft_groups:
                aircraft_groups[aircraft_type] = []
            aircraft_groups[aircraft_type].append(flight)
        
        optimized_flights = []
        
        for aircraft_type, type_flights in aircraft_groups.items():
            # 按出发时间排序
            type_flights.sort(key=lambda f: f.scheduled_departure)
            
            # 重新分配飞机注册号以优化利用率
            available_aircraft = [f"B-{1000 + i:04d}" for i in range(len(type_flights) // 3)]
            
            aircraft_index = 0
            for i, flight in enumerate(type_flights):
                # 简单的轮询分配
                flight.aircraft_registration = available_aircraft[aircraft_index % len(available_aircraft)]
                aircraft_index += 1
                optimized_flights.append(flight)
        
        return optimized_flights
    
    def _optimize_crew_scheduling(self, flights: List[Flight]):
        """优化机组排班"""
        # 简化实现：确保机组值勤时间不超限
        crew_workload = {}
        
        for flight in flights:
            crew_id = flight.crew_id
            if crew_id not in crew_workload:
                crew_workload[crew_id] = timedelta()
            
            crew_workload[crew_id] += flight.get_flight_duration()
            
            # 如果单个机组工作量过重，重新分配
            if crew_workload[crew_id] > timedelta(hours=12):
                # 寻找工作量较轻的机组
                min_workload_crew = min(crew_workload.keys(), 
                                      key=lambda c: crew_workload[c])
                flight.crew_id = min_workload_crew
                crew_workload[min_workload_crew] += flight.get_flight_duration()
                crew_workload[crew_id] -= flight.get_flight_duration()
        
        return flights
    
    def _optimize_slot_allocation(self, flights: List[Flight]):
        """优化时刻分配"""
        # 简化实现：确保最小时刻间隔
        airport_schedules = {}
        
        for flight in flights:
            dep_airport = flight.departure_airport
            if dep_airport not in airport_schedules:
                airport_schedules[dep_airport] = []
            airport_schedules[dep_airport].append(flight)
        
        # 为每个机场调整时刻
        for airport, airport_flights in airport_schedules.items():
            airport_flights.sort(key=lambda f: f.scheduled_departure)
            
            # 确保最小间隔
            for i in range(1, len(airport_flights)):
                prev_flight = airport_flights[i - 1]
                curr_flight = airport_flights[i]
                
                min_interval = timedelta(minutes=3)
                actual_interval = curr_flight.scheduled_departure - prev_flight.scheduled_departure
                
                if actual_interval < min_interval:
                    # 调整当前航班时刻
                    delay = min_interval - actual_interval
                    curr_flight.scheduled_departure += delay
                    curr_flight.scheduled_arrival += delay
        
        return flights
    
    def _auto_resolve_conflict(self, conflict: PlanConflict):
        """自动解决冲突"""
        if not self.current_plan:
            return {"success": False, "error": "没有当前计划"}
        
        affected_flights = [f for f in self.current_plan.flights 
                          if f.flight_no in conflict.affected_flights]
        
        if conflict.conflict_type == "aircraft":
            return self._resolve_aircraft_conflict(conflict, affected_flights)
        elif conflict.conflict_type == "crew":
            return self._resolve_crew_conflict(conflict, affected_flights)
        elif conflict.conflict_type == "slot":
            return self._resolve_slot_conflict(conflict, affected_flights)
        elif conflict.conflict_type == "maintenance":
            return self._resolve_maintenance_conflict(conflict, affected_flights)
        
        return {"success": False, "error": "未知冲突类型"}
    
    def _resolve_aircraft_conflict(self, conflict: PlanConflict, flights: List[Flight]):
        """解决飞机冲突"""
        if len(flights) < 2:
            return {"success": False, "error": "冲突航班数量不足"}
        
        # 延误后面的航班
        later_flight = max(flights, key=lambda f: f.scheduled_departure)
        delay_minutes = 60  # 延误1小时
        
        later_flight.scheduled_departure += timedelta(minutes=delay_minutes)
        later_flight.scheduled_arrival += timedelta(minutes=delay_minutes)
        
        # 从冲突列表中移除
        self.current_plan.conflicts = [c for c in self.current_plan.conflicts 
                                     if c.conflict_id != conflict.conflict_id]
        
        return {
            "success": True,
            "resolution": f"航班{later_flight.flight_no}延误{delay_minutes}分钟",
            "affected_flight": later_flight.flight_no
        }
    
    def _resolve_crew_conflict(self, conflict: PlanConflict, flights: List[Flight]):
        """解决机组冲突"""
        # 重新分配机组
        for flight in flights[len(flights)//2:]:  # 后半部分航班换机组
            new_crew_id = f"CREW{(int(flight.crew_id[-3:]) + 100) % 999:03d}"
            flight.crew_id = new_crew_id
        
        # 从冲突列表中移除
        self.current_plan.conflicts = [c for c in self.current_plan.conflicts 
                                     if c.conflict_id != conflict.conflict_id]
        
        return {
            "success": True,
            "resolution": "重新分配机组",
            "affected_flights": [f.flight_no for f in flights[len(flights)//2:]]
        }
    
    def _resolve_slot_conflict(self, conflict: PlanConflict, flights: List[Flight]):
        """解决时刻冲突"""
        if len(flights) < 2:
            return {"success": False, "error": "冲突航班数量不足"}
        
        # 调整后面航班的时刻
        later_flight = max(flights, key=lambda f: f.scheduled_departure)
        adjustment = timedelta(minutes=5)
        
        later_flight.scheduled_departure += adjustment
        later_flight.scheduled_arrival += adjustment
        
        # 从冲突列表中移除
        self.current_plan.conflicts = [c for c in self.current_plan.conflicts 
                                     if c.conflict_id != conflict.conflict_id]
        
        return {
            "success": True,
            "resolution": f"调整{later_flight.flight_no}时刻",
            "affected_flight": later_flight.flight_no
        }
    
    def _resolve_maintenance_conflict(self, conflict: PlanConflict, flights: List[Flight]):
        """解决维修冲突"""
        # 在航班间隙安排维修时间
        flights.sort(key=lambda f: f.scheduled_departure)
        
        # 找到最大间隙
        max_gap = timedelta()
        gap_position = 0
        
        for i in range(len(flights) - 1):
            gap = flights[i + 1].scheduled_departure - flights[i].scheduled_arrival
            if gap > max_gap:
                max_gap = gap
                gap_position = i
        
        # 如果间隙足够大（超过2小时），安排维修
        if max_gap >= timedelta(hours=2):
            maintenance_start = flights[gap_position].scheduled_arrival + timedelta(minutes=30)
            maintenance_end = maintenance_start + timedelta(hours=2)
            
            # 从冲突列表中移除
            self.current_plan.conflicts = [c for c in self.current_plan.conflicts 
                                         if c.conflict_id != conflict.conflict_id]
            
            return {
                "success": True,
                "resolution": f"安排维修时间 {maintenance_start.strftime('%H:%M')}-{maintenance_end.strftime('%H:%M')}",
                "maintenance_window": {
                    "start": maintenance_start.isoformat(),
                    "end": maintenance_end.isoformat()
                }
            }
        
        return {"success": False, "error": "无法找到合适的维修时间窗口"}
    
    def _prepare_manual_resolution(self, conflict: PlanConflict):
        """准备手动解决方案"""
        return {
            "success": True,
            "conflict": {
                "id": conflict.conflict_id,
                "type": conflict.conflict_type,
                "severity": conflict.severity,
                "description": conflict.description,
                "affected_flights": conflict.affected_flights,
                "suggested_resolution": conflict.suggested_resolution
            },
            "manual_options": self._generate_manual_options(conflict)
        }
    
    def _generate_manual_options(self, conflict: PlanConflict):
        """生成手动解决选项"""
        options = []
        
        if conflict.conflict_type == "aircraft":
            options.extend([
                {"option": "delay_flight", "description": "延误后续航班"},
                {"option": "change_aircraft", "description": "更换飞机"},
                {"option": "cancel_flight", "description": "取消航班"}
            ])
        elif conflict.conflict_type == "crew":
            options.extend([
                {"option": "reassign_crew", "description": "重新分配机组"},
                {"option": "extend_duty", "description": "申请值勤时间延长"},
                {"option": "split_flights", "description": "分配给多个机组"}
            ])
        elif conflict.conflict_type == "slot":
            options.extend([
                {"option": "adjust_time", "description": "调整起飞时刻"},
                {"option": "change_airport", "description": "更换备降机场"},
                {"option": "request_priority", "description": "申请优先起飞"}
            ])
        
        return options
    
    def _analyze_plan_changes(self, old_plan: PlanningWindow, new_plan: PlanningWindow):
        """分析计划变化"""
        changes = {
            "flights_added": [],
            "flights_removed": [],
            "flights_modified": [],
            "conflicts_resolved": [],
            "conflicts_new": []
        }
        
        old_flight_nos = {f.flight_no for f in old_plan.flights}
        new_flight_nos = {f.flight_no for f in new_plan.flights}
        
        # 分析航班变化
        changes["flights_added"] = list(new_flight_nos - old_flight_nos)
        changes["flights_removed"] = list(old_flight_nos - new_flight_nos)
        
        # 分析冲突变化
        old_conflict_ids = {c.conflict_id for c in old_plan.conflicts}
        new_conflict_ids = {c.conflict_id for c in new_plan.conflicts}
        
        changes["conflicts_resolved"] = list(old_conflict_ids - new_conflict_ids)
        changes["conflicts_new"] = list(new_conflict_ids - old_conflict_ids)
        
        return changes
    
    def _notify_plan_changes(self, changes):
        """通知计划变化"""
        # 这里应该发送通知到相关部门
        # 为演示目的，只打印日志
        if any(changes.values()):
            print(f"计划变化通知: {json.dumps(changes, indent=2, ensure_ascii=False)}")
    
    def _group_conflicts_by_type(self, conflicts: List[PlanConflict]):
        """按类型分组冲突"""
        groups = {}
        for conflict in conflicts:
            conflict_type = conflict.conflict_type
            groups[conflict_type] = groups.get(conflict_type, 0) + 1
        return groups
    
    def _group_flights_by_status(self, flights: List[Flight]):
        """按状态分组航班"""
        # 简化实现，所有航班默认为计划状态
        return {
            "scheduled": len(flights),
            "delayed": 0,
            "cancelled": 0,
            "completed": 0
        }
    
    def _calculate_resource_utilization(self, flights: List[Flight]):
        """计算资源利用率"""
        # 计算飞机利用率
        aircraft_hours = {}
        total_aircraft = set()
        
        for flight in flights:
            aircraft_reg = flight.aircraft_registration
            total_aircraft.add(aircraft_reg)
            
            if aircraft_reg not in aircraft_hours:
                aircraft_hours[aircraft_reg] = timedelta()
            
            aircraft_hours[aircraft_reg] += flight.get_flight_duration()
        
        # 平均利用率
        if total_aircraft:
            avg_utilization = sum(hours.total_seconds() for hours in aircraft_hours.values()) / len(total_aircraft) / 3600
            utilization_rate = avg_utilization / 72  # 72小时窗口
        else:
            utilization_rate = 0.0
        
        return {
            "aircraft_utilization": min(1.0, utilization_rate),
            "total_aircraft": len(total_aircraft),
            "total_flight_hours": sum(hours.total_seconds() for hours in aircraft_hours.values()) / 3600
        }
    
    def _predict_potential_delays(self, flights: List[Flight]):
        """预测潜在延误"""
        # 简化实现：基于历史模式预测
        high_risk_flights = []
        
        for flight in flights:
            # 模拟延误风险评估
            risk_factors = 0
            
            # 早班或晚班风险高
            hour = flight.scheduled_departure.hour
            if hour < 7 or hour > 22:
                risk_factors += 1
            
            # 国际航班风险高
            if flight.is_international:
                risk_factors += 1
            
            # 连接航班风险高（简化判断）
            if any(f.aircraft_registration == flight.aircraft_registration and 
                   f.scheduled_departure < flight.scheduled_departure and
                   flight.scheduled_departure - f.scheduled_arrival < timedelta(hours=1)
                   for f in flights):
                risk_factors += 1
            
            if risk_factors >= 2:
                high_risk_flights.append({
                    "flight_no": flight.flight_no,
                    "risk_factors": risk_factors,
                    "predicted_delay": risk_factors * 15  # 每个风险因素15分钟延误
                })
        
        return {
            "high_risk_count": len(high_risk_flights),
            "high_risk_flights": high_risk_flights[:10],  # 只返回前10个
            "average_predicted_delay": sum(f["predicted_delay"] for f in high_risk_flights) / max(1, len(high_risk_flights))
        } 