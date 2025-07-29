from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from ..types.flight_models import Flight, Aircraft, Crew, Airport, OperationalContext
from ..utils.DataLoader import DataLoader
from ..types.constraint_models import Priority


class ConstraintChecker:
    """
    基于真实数据的约束检查器
    负责检查航班调整的约束条件
    """
    
    def __init__(self, 
                 airports: Dict[str, Airport],
                 aircrafts: Dict[str, Aircraft], 
                 crews: Dict[str, Crew],
                 csv_data_loader: DataLoader):
        self.airports = airports
        self.aircrafts = aircrafts 
        self.crews = crews
        self.data_loader = csv_data_loader
    
    def check_time_change_constraints(self, 
                                     flight: Flight, 
                                     new_departure: datetime,
                                     context: OperationalContext):
        """检查变更时刻的约束条件 - 使用真实数据"""
        violations = []
        
        # 1. 检查机场宵禁（使用真实数据）
        departure_curfew_violations = self._check_airport_curfew_real_data(
            flight.departure_airport, new_departure, "DEPARTURE"
        )
        if departure_curfew_violations:
            violations.extend([f"出发机场 {flight.departure_airport} {v}" for v in departure_curfew_violations])
        
        new_arrival = new_departure + flight.get_flight_duration()
        arrival_curfew_violations = self._check_airport_curfew_real_data(
            flight.arrival_airport, new_arrival, "ARRIVAL"
        )
        if arrival_curfew_violations:
            violations.extend([f"到达机场 {flight.arrival_airport} {v}" for v in arrival_curfew_violations])
        
        # 2. 检查航班级别限制（使用真实数据）
        flight_no = flight.flight_no.replace("CA", "")  # 去掉航空公司代码
        flight_restrictions = self.data_loader.get_flight_restrictions(
            flight_no, "CA", flight.departure_airport, flight.arrival_airport, new_departure
        )
        for restriction in flight_restrictions:
            if restriction.priority in [Priority.MUST, Priority.HIGH]:
                violations.append(f"航班限制: {restriction.remarks} ({restriction.comments})")
        
        # 3. 检查机场特殊要求（使用真实数据）
        dep_airport_reqs = self.data_loader.get_airport_special_requirements(
            flight.departure_airport, new_departure
        )
        for req in dep_airport_reqs:
            if req.priority == Priority.MUST:
                violations.append(f"出发机场特殊要求: {req.comments}")
        
        arr_airport_reqs = self.data_loader.get_airport_special_requirements(
            flight.arrival_airport, new_arrival
        )
        for req in arr_airport_reqs:
            if req.priority == Priority.MUST:
                violations.append(f"到达机场特殊要求: {req.comments}")
        
        # 4. 检查航段特殊要求（使用真实数据）
        sector_reqs = self.data_loader.get_sector_special_requirements(
            flight.departure_airport, flight.arrival_airport, "CA", new_departure
        )
        for req in sector_reqs:
            if req.priority == Priority.MUST:
                violations.append(f"航段特殊要求: {req.comments}")
        
        # 5. 检查航班特殊要求（使用真实数据）
        flight_special_reqs = self.data_loader.get_flight_special_requirements(
            flight_no, "CA", flight.departure_airport, flight.arrival_airport, new_departure
        )
        for req in flight_special_reqs:
            if req.priority == Priority.MUST:
                violations.append(f"航班特殊要求: {req.comments}")
        
        # 6. 检查空勤组值勤期限（保留原有逻辑，因为需要实时机组状态）
        if not self._check_crew_duty_limits(flight.crew_id, new_departure, flight.get_flight_duration()):
            violations.append("空勤组值勤期限不满足")
        
        # 7. 检查海关边防工作时间（保留原有逻辑）
        if flight.is_international:
            if not self._check_customs_hours(flight.departure_airport, new_departure):
                violations.append("出发机场海关工作时间不符")
            if not self._check_customs_hours(flight.arrival_airport, new_arrival):
                violations.append("到达机场海关工作时间不符")
        
        return len(violations) == 0, violations
    
    def check_aircraft_change_constraints(self, 
                                        flight: Flight, 
                                        new_aircraft_registration: str,
                                        context: OperationalContext):
        """检查变更飞机的约束条件 - 使用真实数据"""
        violations = []
        new_aircraft = self.aircrafts.get(new_aircraft_registration)
        if not new_aircraft:
            return False, ["指定飞机不存在"]
        
        # 1. 检查机场特殊要求（使用真实数据）
        dep_airport_reqs = self.data_loader.get_airport_special_requirements(
            flight.departure_airport, flight.scheduled_departure
        )
        for req in dep_airport_reqs:
            if req.priority == Priority.MUST:
                # 检查是否是飞机相关要求
                if "飞机" in req.comments or "机型" in req.comments or "设备" in req.comments:
                    # 简化检查：假设新飞机满足大部分要求，但记录高优先级要求
                    if req.priority == Priority.MUST:
                        violations.append(f"出发机场飞机要求: {req.comments}")
        
        arr_airport_reqs = self.data_loader.get_airport_special_requirements(
            flight.arrival_airport, flight.scheduled_arrival
        )
        for req in arr_airport_reqs:
            if req.priority == Priority.MUST:
                if "飞机" in req.comments or "机型" in req.comments or "设备" in req.comments:
                    violations.append(f"到达机场飞机要求: {req.comments}")
        
        # 2. 检查扇区特殊要求（使用真实数据）
        sector_reqs = self.data_loader.get_sector_special_requirements(
            flight.departure_airport, flight.arrival_airport, "CA", flight.scheduled_departure
        )
        for req in sector_reqs:
            if req.priority == Priority.MUST:
                if req.is_extended_overwater():
                    violations.append(f"延伸跨水运行要求: {req.comments}")
                elif req.requires_special_performance():
                    violations.append(f"飞机性能要求: {req.comments}")
        
        # 3. 检查航班限制（使用真实数据）
        flight_no = flight.flight_no.replace("CA", "")
        flight_restrictions = self.data_loader.get_flight_restrictions(
            flight_no, "CA", flight.departure_airport, flight.arrival_airport, flight.scheduled_departure
        )
        for restriction in flight_restrictions:
            if restriction.priority == Priority.MUST and restriction.restriction_type == "AIRCRAFT":
                violations.append(f"航班飞机限制: {restriction.remarks}")
        
        # 4. 保留原有的基础检查
        if not self._check_aircraft_availability(new_aircraft, flight.scheduled_departure):
            violations.append("飞机不可用")
        
        if not self._check_passenger_accommodation(flight, new_aircraft):
            violations.append("座位配置不满足旅客需求")
        
        return len(violations) == 0, violations
    
    def check_airport_change_constraints(self, 
                                       flight: Flight, 
                                       new_departure_airport: Optional[str] = None,
                                       new_arrival_airport: Optional[str] = None,
                                       context: OperationalContext = None) -> Tuple[bool, List[str]]:
        """检查变更机场的约束条件 - 使用真实数据"""
        violations = []
        
        new_dep = new_departure_airport or flight.departure_airport
        new_arr = new_arrival_airport or flight.arrival_airport
        
        # 1. 检查新机场的特殊要求（使用真实数据）
        if new_departure_airport:
            dep_reqs = self.data_loader.get_airport_special_requirements(
                new_departure_airport, flight.scheduled_departure
            )
            for req in dep_reqs:
                if req.priority == Priority.MUST:
                    violations.append(f"新出发机场要求: {req.comments}")
        
        if new_arrival_airport:
            arr_reqs = self.data_loader.get_airport_special_requirements(
                new_arrival_airport, flight.scheduled_arrival
            )
            for req in arr_reqs:
                if req.priority == Priority.MUST:
                    violations.append(f"新到达机场要求: {req.comments}")
        
        # 2. 检查新航段的特殊要求（使用真实数据）
        sector_reqs = self.data_loader.get_sector_special_requirements(
            new_dep, new_arr, "CA", flight.scheduled_departure
        )
        for req in sector_reqs:
            if req.priority == Priority.MUST:
                violations.append(f"新航段要求: {req.comments}")
        
        # 3. 检查宵禁限制（使用真实数据）
        if new_departure_airport:
            dep_curfew_violations = self._check_airport_curfew_real_data(
                new_departure_airport, flight.scheduled_departure, "DEPARTURE"
            )
            if dep_curfew_violations:
                violations.extend([f"新出发机场 {v}" for v in dep_curfew_violations])
        
        if new_arrival_airport:
            arr_curfew_violations = self._check_airport_curfew_real_data(
                new_arrival_airport, flight.scheduled_arrival, "ARRIVAL"
            )
            if arr_curfew_violations:
                violations.extend([f"新到达机场 {v}" for v in arr_curfew_violations])
        
        # 4. 保留原有的基础检查
        if not self._check_traffic_rights(new_dep, new_arr):
            violations.append("航权不满足")
        
        aircraft = self.aircrafts.get(flight.aircraft_registration)
        if aircraft:
            if new_departure_airport and not self._check_ground_service_capability(new_departure_airport, aircraft.aircraft_type):
                violations.append("新出发机场地面服务能力不足")
            if new_arrival_airport and not self._check_ground_service_capability(new_arrival_airport, aircraft.aircraft_type):
                violations.append("新到达机场地面服务能力不足")
        
        return len(violations) == 0, violations
    
    def _check_airport_curfew_real_data(self, airport_code: str, check_time: datetime, operation_type: str = "BOTH") -> List[str]:
        """使用真实数据检查机场宵禁"""
        violations = []
        
        # 获取机场宵禁限制
        curfew_restrictions = self.data_loader.get_airport_curfew_restrictions(airport_code, check_time)
        
        for restriction in curfew_restrictions:
            if restriction.is_curfew_violation(check_time, airport_code, operation_type):
                start_time = restriction.start_time_of_day.strftime("%H:%M")
                end_time = restriction.end_time_of_day.strftime("%H:%M")
                violations.append(f"宵禁时间冲突 ({start_time}-{end_time}): {restriction.remarks}")
        
        return violations
    
    def _check_crew_duty_limits(self, crew_id: str, departure_time: datetime, flight_duration: timedelta):
        """检查机组值勤期限（保留原有逻辑）"""
        crew = self.crews.get(crew_id)
        if not crew:
            return False
        
        # 检查机组是否可用
        if not crew.is_available(departure_time, ""):
            return False
        
        # 检查值勤时间限制
        duty_end = departure_time + flight_duration
        if crew.captain.duty_start:
            duty_duration = duty_end - crew.captain.duty_start
            if duty_duration.total_seconds() / 3600 > crew.captain.max_duty_hours:
                return False
        
        return True
    
    def _check_customs_hours(self, airport_code: str, time_dt: datetime):
        """检查海关工作时间（保留原有逻辑）"""
        airport = self.airports.get(airport_code)
        if not airport:
            return False
        
        time_str = time_dt.strftime("%H:%M")
        start, end = airport.customs_hours
        return start <= time_str <= end
    
    def _check_aircraft_availability(self, aircraft: Aircraft, departure_time: datetime):
        """检查飞机可用性"""
        return aircraft.is_available(departure_time)
    
    def _check_passenger_accommodation(self, flight: Flight, aircraft: Aircraft):
        """检查座位配置"""
        return aircraft.seat_capacity >= flight.passenger_count
    
    def _check_traffic_rights(self, dep_airport: str, arr_airport: str):
        """检查航权（简化实现）"""
        # 国内航线通常没有航权问题
        domestic_airports = ["PEK", "PVG", "CAN", "CTU", "XIY", "KMG", "WUH", "TAO", "DLC", "SHE"]
        if dep_airport in domestic_airports and arr_airport in domestic_airports:
            return True
        return True  # 简化处理，假设都有航权
    
    def _check_ground_service_capability(self, airport_code: str, aircraft_type: str):
        """检查地面服务能力（简化实现）"""
        # 大型机场通常支持所有常见机型
        major_airports = ["PEK", "PVG", "CAN", "CTU", "XIY", "KMG"]
        if airport_code in major_airports:
            return True
        
        # 中小型机场可能不支持大型机
        if aircraft_type in ["B777", "B787", "A330"] and airport_code not in major_airports:
            return False
        
        return True
    
    def get_constraint_summary(self, flight: Flight, check_time: datetime):
        """获取航班约束摘要信息"""
        flight_no = flight.flight_no.replace("CA", "")
        
        summary = {
            "航班号": flight.flight_no,
            "航段": f"{flight.departure_airport}-{flight.arrival_airport}",
            "检查时间": check_time.strftime("%Y-%m-%d %H:%M"),
            "约束统计": {}
        }
        
        # 统计各类约束数量
        airport_special_reqs_dep = self.data_loader.get_airport_special_requirements(
            flight.departure_airport, check_time
        )
        airport_special_reqs_arr = self.data_loader.get_airport_special_requirements(
            flight.arrival_airport, check_time
        )
        
        flight_restrictions = self.data_loader.get_flight_restrictions(
            flight_no, "CA", flight.departure_airport, flight.arrival_airport, check_time
        )
        
        sector_reqs = self.data_loader.get_sector_special_requirements(
            flight.departure_airport, flight.arrival_airport, "CA", check_time
        )
        
        flight_special_reqs = self.data_loader.get_flight_special_requirements(
            flight_no, "CA", flight.departure_airport, flight.arrival_airport, check_time
        )
        
        curfew_restrictions_dep = self.data_loader.get_airport_curfew_restrictions(
            flight.departure_airport, check_time
        )
        curfew_restrictions_arr = self.data_loader.get_airport_curfew_restrictions(
            flight.arrival_airport, check_time
        )
        
        summary["约束统计"] = {
            "机场特殊要求": len(airport_special_reqs_dep) + len(airport_special_reqs_arr),
            "航班限制": len(flight_restrictions),
            "扇区特殊要求": len(sector_reqs),
            "航班特殊要求": len(flight_special_reqs),
            "宵禁限制": len(curfew_restrictions_dep) + len(curfew_restrictions_arr)
        }
        
        # 统计MUST级别约束
        must_constraints = []
        for req in airport_special_reqs_dep + airport_special_reqs_arr:
            if req.priority == Priority.MUST:
                must_constraints.append(f"机场要求: {req.comments[:50]}...")
        
        for restriction in flight_restrictions:
            if restriction.priority == Priority.MUST:
                must_constraints.append(f"航班限制: {restriction.remarks[:50]}...")
        
        for req in sector_reqs:
            if req.priority == Priority.MUST:
                must_constraints.append(f"扇区要求: {req.comments[:50]}...")
        
        for req in flight_special_reqs:
            if req.priority == Priority.MUST:
                must_constraints.append(f"航班要求: {req.comments[:50]}...")
        
        summary["强制约束"] = must_constraints[:10]  # 只显示前10个
        
        return summary 