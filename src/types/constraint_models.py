"""
约束模型数据类
用于表示从CSV文件加载的各种约束条件
"""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional, List
from enum import Enum


class Priority(Enum):
    """约束优先级"""
    MUST = "MUST"
    HIGH = "HIGH" 
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RequirementType(Enum):
    """要求类型"""
    AIRCRAFT = "AIRCRAFT"


class Category(Enum):
    """约束分类"""
    ACEQUIPMENT = "ACequipment"
    COUNTRY = "COUNTRY"
    HAAP = "HAAP"
    APU = "APU"
    OPSLIMIT = "OPSLIMIT"
    NOISELIMIT = "NOISELIMIT"
    WETLEASE = "WETLEASE"
    AIRCRAFTPERFORMANCE = "AIRCRAFTPERFORMANCE"
    WATERCROSS = "WATERCROSS"
    PBN = "PBN"
    CURFEW = "CURFEW"
    OXYGEN = "OXYGEN"
    TANKLIMIT = "TANKLIMIT"
    ADSB = "ADSB"
    ETOPS = "ETOPS"
    POLAR = "POLAR"
    AIROPS = "AIROPS"
    COMMERCAIL = "COMMERCAIL"  # 保持原始拼写错误
    CUSTOM = "CUSTOM"
    OTHER = "OTHER"
    EMPTY = ""  # 空值情况


class RestrictionType(Enum):
    """限制类型"""
    AIRPORT_CURFEW = "AIRPORT_CURFEW"
    AIRCRAFT = "AIRCRAFT"
    AIRCRAFT_TYPE = "AIRCRAFT_TYPE"
    AIRPORT_FLOW_RATE = "AIRPORT_FLOW_RATE"
    EMPTY = ""  # 空值情况


@dataclass
class AirportSpecialRequirement:
    """机场特殊要求"""
    id: str
    version: int
    requirement_type: RequirementType
    priority: Priority
    comments: str
    remarks: str
    category: Category
    continuous_time_period: bool
    start_date: datetime
    end_date: datetime
    start_time_of_day: time
    end_time_of_day: time
    days_of_week: str
    airport_code: Optional[str]
    airports_group_id: Optional[str]
    airport_type: str
    scope: str
    owner: str
    constraint_id: str
    source: str
    last_modified: datetime

    def is_active(self, check_time: datetime, airport_code: str) -> bool:
        """检查约束在指定时间和机场是否生效"""
        # 检查日期范围
        if not (self.start_date.date() <= check_time.date() <= self.end_date.date()):
            return False
        
        # 检查机场匹配
        if self.airport_code and self.airport_code != airport_code:
            return False
            
        # 检查星期几
        weekday = str(check_time.weekday() + 1)  # Python weekday: 0=Monday, 转换为1=Monday
        if weekday not in self.days_of_week:
            return False
            
        # 检查时间段
        if not self.continuous_time_period:
            check_time_only = check_time.time()
            if self.start_time_of_day <= self.end_time_of_day:
                return self.start_time_of_day <= check_time_only <= self.end_time_of_day
            else:  # 跨日时间段
                return check_time_only >= self.start_time_of_day or check_time_only <= self.end_time_of_day
        
        return True

    def applies_to_country(self, country_group_id: str) -> bool:
        """检查是否适用于指定国家/地区"""
        return self.airports_group_id == country_group_id if self.airports_group_id else False


@dataclass
class AirportRestriction:
    """机场限制"""
    id: str
    version: int
    priority: Priority
    comments: str
    remarks: str
    category: Category
    continuous_time_period: bool
    start_date: datetime
    end_date: datetime
    start_time_of_day: time
    end_time_of_day: time
    days_of_week: str
    curfew_type: str
    constraint_type: str
    constraint_value: str
    restriction_type: RestrictionType
    airport_code: str
    airport_type: str
    scope: str
    owner: str
    airports_group_id: Optional[str]
    constraint_id: str
    source: str
    required: bool
    last_modified: datetime

    def is_curfew_violation(self, check_time: datetime, airport_code: str, operation_type: str = "BOTH"):
        """检查是否违反宵禁"""
        if self.restriction_type != RestrictionType.AIRPORT_CURFEW:
            return False
            
        if self.airport_code != airport_code:
            return False
            
        if self.airport_type not in ["BOTH", operation_type]:
            return False
            
        if not self.is_active(check_time):
            return False
            
        # 在宵禁时间段内则违反宵禁
        check_time_only = check_time.time()
        if self.start_time_of_day <= self.end_time_of_day:
            return self.start_time_of_day <= check_time_only <= self.end_time_of_day
        else:  # 跨日宵禁
            return check_time_only >= self.start_time_of_day or check_time_only <= self.end_time_of_day

    def is_active(self, check_time: datetime) -> bool:
        """检查限制在指定时间是否生效"""
        # 检查日期范围
        if not (self.start_date.date() <= check_time.date() <= self.end_date.date()):
            return False
            
        # 检查星期几
        weekday = str(check_time.weekday() + 1)
        if weekday not in self.days_of_week:
            return False
            
        return True


@dataclass
class FlightRestriction:
    """航班限制"""
    id: str
    version: int
    priority: Priority
    departure_airport: Optional[str]
    arrival_airport: Optional[str]
    carrier_code: str
    restriction_type: str
    continuous_time_period: bool
    start_date: datetime
    end_date: datetime
    start_time: time
    end_time: time
    days_of_week: str
    category: Category
    remarks: str
    comments: str
    flight_carrier_code: str
    flight_number: str
    op_suffix: str
    scope: str
    owner: str
    match_by_date: str
    constraint_id: str
    source: str
    required: bool
    last_modified: datetime

    def applies_to_flight(self, flight_no: str, carrier_code: str, dep_airport: str, 
                         arr_airport: Optional[str], check_time: datetime) -> bool:
        """检查是否适用于指定航班"""
        # 检查航班号
        if self.flight_number != flight_no.lstrip('0'):  # 去掉前导0比较
            return False
            
        # 检查承运人
        if self.flight_carrier_code != carrier_code:
            return False
            
        # 检查机场
        if self.departure_airport and self.departure_airport != dep_airport:
            return False
        if self.arrival_airport and arr_airport and self.arrival_airport != arr_airport:
            return False
            
        return self.is_active(check_time)

    def is_active(self, check_time: datetime) -> bool:
        """检查限制在指定时间是否生效"""
        # 检查日期范围
        if not (self.start_date.date() <= check_time.date() <= self.end_date.date()):
            return False
            
        # 检查星期几
        weekday = str(check_time.weekday() + 1)
        if weekday not in self.days_of_week:
            return False
            
        # 检查时间段
        if not self.continuous_time_period:
            check_time_only = check_time.time()
            if self.start_time <= self.end_time:
                return self.start_time <= check_time_only <= self.end_time
            else:  # 跨日时间段
                return check_time_only >= self.start_time or check_time_only <= self.end_time
                
        return True


@dataclass
class FlightSpecialRequirement:
    """航班特殊要求"""
    id: str
    version: int
    requirement_type: RequirementType
    priority: Priority
    comments: str
    remarks: str
    category: Category
    continuous_time_period: bool
    start_date: datetime
    end_date: datetime
    start_time_of_day: time
    end_time_of_day: time
    days_of_week: str
    departure_airport: str
    arrival_airport: str
    carrier_code: str
    ref_carrier_code: str
    ref_flight_number: str
    ref_op_suffix: str
    scope: str
    owner: str
    match_by_date: str
    constraint_id: str
    source: str
    last_modified: datetime

    def applies_to_flight(self, flight_no: str, carrier_code: str, dep_airport: str, 
                         arr_airport: str, check_time: datetime) -> bool:
        """检查是否适用于指定航班"""
        # 检查航班号
        if self.ref_flight_number != flight_no.lstrip('0'):
            return False
            
        # 检查承运人
        if self.ref_carrier_code != carrier_code:
            return False
            
        # 检查航段
        if self.departure_airport != dep_airport or self.arrival_airport != arr_airport:
            return False
            
        return self.is_active(check_time)

    def is_active(self, check_time: datetime) -> bool:
        """检查要求在指定时间是否生效"""
        # 检查日期范围
        if not (self.start_date.date() <= check_time.date() <= self.end_date.date()):
            return False
            
        # 检查星期几
        weekday = str(check_time.weekday() + 1)
        if weekday not in self.days_of_week:
            return False
            
        return True


@dataclass
class SectorSpecialRequirement:
    """航段特殊要求"""
    id: str
    version: int
    requirement_type: RequirementType
    priority: Priority
    comments: str
    remarks: str
    category: Category
    continuous_time_period: bool
    start_date: datetime
    end_date: datetime
    start_time_of_day: time
    end_time_of_day: time
    days_of_week: str
    departure_airport: str
    arrival_airport: str
    carrier_code: str
    scope: str
    owner: str
    constraint_id: str
    source: str
    last_modified: datetime

    def applies_to_sector(self, dep_airport: str, arr_airport: str, 
                         carrier_code: str, check_time: datetime):
        """检查是否适用于指定航段"""
        # 检查航段
        if self.departure_airport != dep_airport or self.arrival_airport != arr_airport:
            return False
            
        # 检查承运人
        if self.carrier_code != carrier_code:
            return False
            
        return self.is_active(check_time)

    def is_active(self, check_time: datetime):
        """检查要求在指定时间是否生效"""
        # 检查日期范围
        if not (self.start_date.date() <= check_time.date() <= self.end_date.date()):
            return False
            
        # 检查星期几
        weekday = str(check_time.weekday() + 1)
        if weekday not in self.days_of_week:
            return False
            
        return True

    def is_extended_overwater(self):
        """是否为延伸跨水运行要求"""
        return self.category == Category.WATERCROSS

    def requires_special_performance(self):
        """是否需要特殊性能"""
        return self.category == Category.AIRCRAFTPERFORMANCE 