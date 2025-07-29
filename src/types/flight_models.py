from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class FlightStatus(Enum):
    """航班状态"""
    SCHEDULED = "SCHEDULED"  # 计划中
    DELAYED = "DELAYED"      # 延误
    CANCELLED = "CANCELLED"  # 取消
    DEPARTED = "DEPARTED"    # 已起飞
    ARRIVED = "ARRIVED"      # 已到达


class AdjustmentAction(Enum):
    """调整动作类型"""
    CHANGE_TIME = "CHANGE_TIME"           # 变更时刻
    CHANGE_AIRCRAFT = "CHANGE_AIRCRAFT"   # 更换飞机
    CANCEL_FLIGHT = "CANCEL_FLIGHT"       # 取消航班
    CHANGE_AIRPORT = "CHANGE_AIRPORT"     # 变更起降机场
    CHANGE_NATURE = "CHANGE_NATURE"       # 变更航班性质
    ADD_FLIGHT = "ADD_FLIGHT"             # 新增航班


@dataclass
class Airport:
    """机场信息"""
    code: str                           # 机场代码
    name: str                           # 机场名称
    timezone: str                       # 时区
    curfew_start: Optional[str] = None  # 宵禁开始时间 "23:00"
    curfew_end: Optional[str] = None    # 宵禁结束时间 "06:00"
    runway_status: bool = True          # 跑道状态
    customs_hours: tuple = ("06:00", "24:00")  # 海关工作时间
    is_high_altitude: bool = False      # 是否高原机场
    capacity_limit: int = 100           # 容量限制


@dataclass
class Aircraft:
    """飞机信息"""
    registration: str                   # 机号
    aircraft_type: str                  # 机型 如"A330"
    seat_capacity: int                  # 座位数
    fuel_capacity: float               # 燃油容量
    current_airport: str               # 当前位置
    maintenance_status: str = "NORMAL"  # 维修状态
    fault_reserves: List[str] = field(default_factory=list)  # 故障保留
    special_config: Dict[str, Any] = field(default_factory=dict)  # 特殊配置
    next_maintenance: Optional[datetime] = None  # 下次检修时间
    
    def is_available(self, departure_time: datetime) -> bool:
        """检查飞机在指定时间是否可用"""
        if self.maintenance_status != "NORMAL":
            return False
        if self.next_maintenance and departure_time >= self.next_maintenance:
            return False
        return True


@dataclass
class CrewMember:
    """机组成员"""
    crew_id: str                        # 机组ID
    name: str                           # 姓名
    position: str                       # 职位 "CAPTAIN", "FIRST_OFFICER", "CABIN_CREW"
    current_location: str               # 当前位置
    duty_start: Optional[datetime] = None    # 值勤开始时间
    duty_end: Optional[datetime] = None      # 值勤结束时间
    rest_required: timedelta = timedelta(hours=12)  # 最小休息时间
    max_duty_hours: int = 14            # 最大值勤时间


@dataclass
class Crew:
    """完整机组"""
    crew_id: str                        # 机组ID
    captain: CrewMember                 # 机长
    first_officer: CrewMember          # 副驾驶
    cabin_crew: List[CrewMember]       # 乘务员
    qualified_aircraft_types: List[str] = field(default_factory=list)  # 机型资质
    
    def is_available(self, departure_time: datetime, aircraft_type: str) -> bool:
        """检查机组是否可用"""
        if aircraft_type not in self.qualified_aircraft_types:
            return False
        
        # 检查所有成员是否可用
        all_members = [self.captain, self.first_officer] + self.cabin_crew
        for member in all_members:
            if member.duty_end and departure_time < member.duty_end + member.rest_required:
                return False
        return True


@dataclass
class Flight:
    """航班信息"""
    flight_no: str                      # 航班号
    departure_airport: str              # 出发机场
    arrival_airport: str                # 到达机场
    scheduled_departure: datetime       # 计划起飞时间
    scheduled_arrival: datetime         # 计划到达时间
    aircraft_registration: str          # 机号
    crew_id: str                        # 机组ID
    aircraft_type: str                  # 机型
    status: FlightStatus = FlightStatus.SCHEDULED
    
    # 航班属性
    is_international: bool = False      # 是否国际航班
    is_cargo: bool = False             # 是否货机
    is_vip: bool = False               # 是否重保航班
    passenger_count: int = 0           # 旅客数量
    
    # 实际时间
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    
    # 调整历史
    adjustment_history: List[Dict] = field(default_factory=list)
    
    def get_flight_duration(self) -> timedelta:
        """获取飞行时长"""
        return self.scheduled_arrival - self.scheduled_departure
    
    def get_current_delay(self) -> timedelta:
        """获取当前延误时长"""
        if self.actual_departure:
            return self.actual_departure - self.scheduled_departure
        return timedelta(0)


@dataclass
class OperationalConstraint:
    """运行约束"""
    min_turnaround_time: Dict[str, int] = field(default_factory=lambda: {
        "domestic": 45,      # 国内航班最小过站时间(分钟)
        "international": 90  # 国际航班最小过站时间(分钟)
    })
    max_delay_threshold: Dict[str, int] = field(default_factory=lambda: {
        "domestic": 240,     # 国内航班最大延误阈值(分钟)
        "international": 120 # 国际航班最大延误阈值(分钟)
    })
    crew_duty_limits: Dict[str, int] = field(default_factory=lambda: {
        "single_day": 14,    # 单日最大值勤时间(小时)
        "rest_period": 12    # 最小休息时间(小时)
    })


@dataclass
class AdjustmentOption:
    """调整方案"""
    action: AdjustmentAction            # 调整动作
    flight_no: str                      # 航班号
    reason: str                         # 调整原因
    score: float                        # 评分
    details: Dict[str, Any]             # 详细信息
    extra: Dict[str, Any] = field(default_factory=dict)  # 额外信息
    
    # 约束违反情况
    constraint_violations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'action': self.action.value,
            'flight_no': self.flight_no,
            'reason': self.reason,
            'score': self.score,
            'details': self.details,
            'extra': self.extra,
            'constraint_violations': self.constraint_violations
        }


@dataclass
class OperationalContext:
    """运行环境上下文"""
    current_time: datetime              # 当前时间
    weather_conditions: Dict[str, str] = field(default_factory=dict)  # 天气情况
    atc_restrictions: Dict[str, Any] = field(default_factory=dict)    # 空管限制
    airport_closures: List[str] = field(default_factory=list)        # 机场关闭
    runway_closures: Dict[str, List[str]] = field(default_factory=dict)  # 跑道关闭
    flow_control: Dict[str, Dict] = field(default_factory=dict)      # 流量控制 