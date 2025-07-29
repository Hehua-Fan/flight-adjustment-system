import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import uuid
from ..types.flight_models import Flight, OperationalContext
from ..types.monitoring_models import AlertLevel, RiskType, Alert, MonitoringRule
from ..modules.Engine import FlightAdjustmentEngine


class RealTimeMonitoringSystem:
    """
    实时监控预警系统
    负责持续监控航班状态，主动发现问题并生成预警
    """
    
    def __init__(self, adjustment_engine: FlightAdjustmentEngine):
        self.engine = adjustment_engine
        self.is_running = False
        self.monitoring_thread = None
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable[[Alert], None]] = []
        
        # 监控配置
        self.monitoring_interval = 60  # 秒
        self.max_alerts_history = 1000
        
        # 预警阈值
        self.alert_thresholds = {
            RiskType.DELAY: {
                AlertLevel.WARNING: 15,    # 15分钟延误预警
                AlertLevel.HIGH: 30,       # 30分钟延误严重
                AlertLevel.CRITICAL: 60    # 60分钟延误紧急
            },
            RiskType.WEATHER: {
                AlertLevel.WARNING: 0.3,   # 30%恶劣天气概率
                AlertLevel.HIGH: 0.6,      # 60%恶劣天气概率
                AlertLevel.CRITICAL: 0.8   # 80%恶劣天气概率
            },
            RiskType.AIRCRAFT: {
                AlertLevel.WARNING: 0.3,   # 30%不可用概率
                AlertLevel.HIGH: 0.6,      # 60%不可用概率
                AlertLevel.CRITICAL: 1.0   # 完全不可用
            },
            RiskType.CREW: {
                AlertLevel.WARNING: 12,    # 值勤12小时预警
                AlertLevel.HIGH: 13,       # 值勤13小时严重
                AlertLevel.CRITICAL: 14    # 值勤14小时紧急
            }
        }
        
        # 初始化监控规则
        self.monitoring_rules = self._initialize_monitoring_rules()
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self):
        """启动实时监控"""
        if self.is_running:
            self.logger.warning("监控系统已在运行")
            return
        
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("实时监控系统已启动")
    
    def stop_monitoring(self):
        """停止实时监控"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("实时监控系统已停止")
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """添加预警处理器"""
        self.alert_handlers.append(handler)
    
    def get_active_alerts(self, level: AlertLevel = None) -> List[Alert]:
        """获取活跃预警"""
        active_alerts = [alert for alert in self.alerts if not alert.resolved]
        
        if level:
            active_alerts = [alert for alert in active_alerts if alert.level == level]
        
        # 按创建时间倒序排列
        active_alerts.sort(key=lambda a: a.created_at, reverse=True)
        return active_alerts
    
    def acknowledge_alert(self, alert_id: str, operator: str = "system") -> bool:
        """确认预警"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self.logger.info(f"预警 {alert_id} 已被 {operator} 确认")
                return True
        return False
    
    def resolve_alert(self, alert_id: str, resolution: str = "", operator: str = "system") -> bool:
        """解决预警"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                self.logger.info(f"预警 {alert_id} 已被 {operator} 解决: {resolution}")
                return True
        return False
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        active_alerts = self.get_active_alerts()
        
        stats = {
            "monitoring_status": "running" if self.is_running else "stopped",
            "total_alerts": len(self.alerts),
            "active_alerts": len(active_alerts),
            "alerts_by_level": self._group_alerts_by_level(active_alerts),
            "alerts_by_type": self._group_alerts_by_type(active_alerts),
            "monitoring_rules": len(self.monitoring_rules),
            "last_check": datetime.now().isoformat()
        }
        
        return stats
    
    # 私有方法
    def _monitoring_loop(self):
        """监控主循环"""
        while self.is_running:
            try:
                # 获取当前活跃航班
                active_flights = self._get_active_flights()
                current_context = self._get_current_context()
                
                # 对每个航班执行监控检查
                for flight in active_flights:
                    self._monitor_single_flight(flight, current_context)
                
                # 清理历史预警
                self._cleanup_old_alerts()
                
                # 等待下次检查
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                time.sleep(10)  # 异常时短暂休息
    
    def _monitor_single_flight(self, flight: Flight, context: OperationalContext):
        """监控单个航班"""
        # 应用所有监控规则
        for rule in self.monitoring_rules:
            if not rule.enabled:
                continue
            
            try:
                # 执行检查函数
                risk_value = self._execute_check_function(rule, flight, context)
                
                # 评估风险级别
                alert_level = self._evaluate_risk_level(rule, risk_value)
                
                # 如果风险超过阈值，生成预警
                if alert_level:
                    self._generate_alert(flight, rule, risk_value, alert_level, context)
                    
            except Exception as e:
                self.logger.error(f"执行监控规则 {rule.rule_id} 异常: {e}")
    
    def _execute_check_function(self, rule: MonitoringRule, flight: Flight, context: OperationalContext) -> float:
        """执行检查函数"""
        function_name = rule.check_function
        
        if function_name == "check_delay_risk":
            return self._check_delay_risk(flight, context, rule.parameters)
        elif function_name == "check_weather_risk":
            return self._check_weather_risk(flight, context, rule.parameters)
        elif function_name == "check_aircraft_risk":
            return self._check_aircraft_risk(flight, context, rule.parameters)
        elif function_name == "check_crew_risk":
            return self._check_crew_risk(flight, context, rule.parameters)
        elif function_name == "check_fuel_risk":
            return self._check_fuel_risk(flight, context, rule.parameters)
        elif function_name == "check_slot_risk":
            return self._check_slot_risk(flight, context, rule.parameters)
        else:
            self.logger.warning(f"未知检查函数: {function_name}")
            return 0.0
    
    def _check_delay_risk(self, flight: Flight, context: OperationalContext, params: Dict[str, Any]) -> float:
        """检查延误风险"""
        current_time = context.current_time
        scheduled_departure = flight.scheduled_departure
        
        # 如果航班已起飞，返回0
        if current_time > scheduled_departure:
            return 0.0
        
        # 计算预期延误时间
        predicted_delay = 0
        
        # 基于天气条件预测延误
        weather_delay = self._predict_weather_delay(flight, context)
        predicted_delay += weather_delay
        
        # 基于空管限制预测延误
        atc_delay = self._predict_atc_delay(flight, context)
        predicted_delay += atc_delay
        
        # 基于前序航班延误传播
        propagation_delay = self._predict_delay_propagation(flight, context)
        predicted_delay += propagation_delay
        
        return predicted_delay
    
    def _check_weather_risk(self, flight: Flight, context: OperationalContext, params: Dict[str, Any]) -> float:
        """检查天气风险"""
        weather_conditions = context.weather_conditions
        
        # 检查起降机场天气
        dep_weather = weather_conditions.get(flight.departure_airport, "clear")
        arr_weather = weather_conditions.get(flight.arrival_airport, "clear")
        
        # 计算天气风险分数
        risk_score = 0.0
        
        severe_conditions = {
            "thunderstorm": 0.8,
            "heavy_rain": 0.6,
            "snow": 0.7,
            "fog": 0.5,
            "strong_wind": 0.4
        }
        
        for condition, score in severe_conditions.items():
            if condition in dep_weather.lower() or condition in arr_weather.lower():
                risk_score = max(risk_score, score)
        
        return risk_score
    
    def _check_aircraft_risk(self, flight: Flight, context: OperationalContext, params: Dict[str, Any]) -> float:
        """检查飞机风险"""
        aircraft = self.engine.aircrafts.get(flight.aircraft_registration)
        
        if not aircraft:
            return 1.0  # 飞机不存在，风险最高
        
        # 检查飞机可用性
        if not aircraft.is_available(flight.scheduled_departure):
            return 1.0
        
        # 检查维修状态（简化实现）
        maintenance_risk = 0.0
        
        # 模拟维修风险评估
        current_time = context.current_time
        next_maintenance = getattr(aircraft, 'next_maintenance', current_time + timedelta(days=30))
        
        days_to_maintenance = (next_maintenance - current_time).days
        if days_to_maintenance < 1:
            maintenance_risk = 0.8
        elif days_to_maintenance < 3:
            maintenance_risk = 0.5
        elif days_to_maintenance < 7:
            maintenance_risk = 0.2
        
        return maintenance_risk
    
    def _check_crew_risk(self, flight: Flight, context: OperationalContext, params: Dict[str, Any]) -> float:
        """检查机组风险"""
        crew = self.engine.crews.get(flight.crew_id)
        
        if not crew:
            return 1.0  # 机组不存在，风险最高
        
        # 检查机组可用性
        if not crew.is_available(flight.scheduled_departure, flight.aircraft_type):
            return 1.0
        
        # 计算值勤时间风险
        duty_hours = self._calculate_crew_duty_hours(crew, flight, context)
        
        if duty_hours >= 14:
            return 1.0  # 超过法定值勤时间
        elif duty_hours >= 13:
            return 0.8  # 接近限制
        elif duty_hours >= 12:
            return 0.5  # 需要关注
        elif duty_hours >= 10:
            return 0.2  # 轻微风险
        
        return 0.0
    
    def _check_fuel_risk(self, flight: Flight, context: OperationalContext, params: Dict[str, Any]) -> float:
        """检查燃油风险"""
        # 简化实现：基于航班距离和天气条件
        base_fuel_risk = 0.0
        
        # 国际长航线风险高
        if flight.is_international:
            base_fuel_risk = 0.3
        
        # 恶劣天气增加燃油风险
        weather_risk = self._check_weather_risk(flight, context, params)
        fuel_weather_factor = weather_risk * 0.4
        
        return min(1.0, base_fuel_risk + fuel_weather_factor)
    
    def _check_slot_risk(self, flight: Flight, context: OperationalContext, params: Dict[str, Any]) -> float:
        """检查时刻风险"""
        # 检查空管限制
        atc_restrictions = context.atc_restrictions
        
        slot_risk = 0.0
        
        # 检查起降机场流控
        if flight.departure_airport in atc_restrictions:
            dep_restriction = atc_restrictions[flight.departure_airport]
            if dep_restriction.get("flow_control", False):
                slot_risk = max(slot_risk, 0.6)
        
        if flight.arrival_airport in atc_restrictions:
            arr_restriction = atc_restrictions[flight.arrival_airport]
            if arr_restriction.get("flow_control", False):
                slot_risk = max(slot_risk, 0.6)
        
        return slot_risk
    
    def _predict_weather_delay(self, flight: Flight, context: OperationalContext) -> float:
        """预测天气延误"""
        weather_risk = self._check_weather_risk(flight, context, {})
        
        # 将天气风险转换为延误分钟数
        if weather_risk >= 0.8:
            return 60  # 严重天气，预期延误60分钟
        elif weather_risk >= 0.6:
            return 30  # 恶劣天气，预期延误30分钟
        elif weather_risk >= 0.4:
            return 15  # 一般恶劣天气，预期延误15分钟
        
        return 0
    
    def _predict_atc_delay(self, flight: Flight, context: OperationalContext) -> float:
        """预测空管延误"""
        atc_restrictions = context.atc_restrictions
        
        delay = 0
        
        # 检查起降机场流控
        if flight.departure_airport in atc_restrictions:
            dep_flow = atc_restrictions[flight.departure_airport].get("flow_control", False)
            if dep_flow:
                delay += 20  # 流控延误20分钟
        
        if flight.arrival_airport in atc_restrictions:
            arr_flow = atc_restrictions[flight.arrival_airport].get("flow_control", False)
            if arr_flow:
                delay += 15  # 到达流控延误15分钟
        
        return delay
    
    def _predict_delay_propagation(self, flight: Flight, context: OperationalContext) -> float:
        """预测延误传播"""
        # 简化实现：检查同一飞机的前序航班
        aircraft_reg = flight.aircraft_registration
        
        # 模拟查找前序航班的延误
        # 在实际系统中，这里应该查询数据库
        prev_flight_delay = 0  # 假设前序航班延误
        
        # 如果前序航班延误，且过站时间不足，会传播延误
        min_turnaround = 45  # 最小过站时间45分钟
        
        if prev_flight_delay > min_turnaround:
            return prev_flight_delay - min_turnaround
        
        return 0
    
    def _calculate_crew_duty_hours(self, crew, flight: Flight, context: OperationalContext) -> float:
        """计算机组值勤时间"""
        # 简化实现：假设机组已值勤时间
        current_duty_hours = 8.0  # 假设已值勤8小时
        
        # 加上当前航班时间
        flight_duration = flight.get_flight_duration().total_seconds() / 3600
        
        return current_duty_hours + flight_duration
    
    def _evaluate_risk_level(self, rule: MonitoringRule, risk_value: float) -> Optional[AlertLevel]:
        """评估风险级别"""
        thresholds = self.alert_thresholds.get(rule.risk_type, {})
        
        if risk_value >= thresholds.get(AlertLevel.CRITICAL, float('inf')):
            return AlertLevel.CRITICAL
        elif risk_value >= thresholds.get(AlertLevel.HIGH, float('inf')):
            return AlertLevel.HIGH
        elif risk_value >= thresholds.get(AlertLevel.WARNING, float('inf')):
            return AlertLevel.WARNING
        
        return None
    
    def _generate_alert(self, flight: Flight, rule: MonitoringRule, risk_value: float, 
                       level: AlertLevel, context: OperationalContext):
        """生成预警"""
        # 检查是否已存在相同的活跃预警
        existing_alert = self._find_existing_alert(flight.flight_no, rule.risk_type)
        if existing_alert and not existing_alert.resolved:
            return  # 避免重复预警
        
        # 计算影响时间和决策时间
        time_to_impact = flight.scheduled_departure - context.current_time
        time_to_decision = max(timedelta(minutes=30), time_to_impact * 0.5)
        
        # 生成推荐动作
        recommended_actions = self._generate_recommended_actions(rule.risk_type, level, risk_value)
        
        # 创建预警
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            flight_no=flight.flight_no,
            risk_type=rule.risk_type,
            level=level,
            title=self._generate_alert_title(rule.risk_type, level),
            description=self._generate_alert_description(flight, rule, risk_value),
            current_value=risk_value,
            threshold_value=self.alert_thresholds[rule.risk_type][level],
            recommended_actions=recommended_actions,
            time_to_impact=time_to_impact,
            time_to_decision=time_to_decision
        )
        
        # 添加到预警列表
        self.alerts.append(alert)
        
        # 限制历史记录数量
        if len(self.alerts) > self.max_alerts_history:
            self.alerts = self.alerts[-self.max_alerts_history:]
        
        # 通知预警处理器
        self._notify_alert_handlers(alert)
        
        self.logger.warning(f"生成预警: {alert.title} - {alert.description}")
    
    def _find_existing_alert(self, flight_no: str, risk_type: RiskType) -> Optional[Alert]:
        """查找现有预警"""
        for alert in reversed(self.alerts):  # 从最新的开始查找
            if (alert.flight_no == flight_no and 
                alert.risk_type == risk_type and 
                not alert.resolved):
                return alert
        return None
    
    def _generate_alert_title(self, risk_type: RiskType, level: AlertLevel) -> str:
        """生成预警标题"""
        level_names = {
            AlertLevel.WARNING: "预警",
            AlertLevel.HIGH: "严重",
            AlertLevel.CRITICAL: "紧急"
        }
        
        type_names = {
            RiskType.DELAY: "延误",
            RiskType.WEATHER: "天气",
            RiskType.AIRCRAFT: "飞机",
            RiskType.CREW: "机组",
            RiskType.ATC: "空管",
            RiskType.FUEL: "燃油",
            RiskType.SLOT: "时刻"
        }
        
        return f"{type_names.get(risk_type, '未知')}{level_names.get(level, '警告')}"
    
    def _generate_alert_description(self, flight: Flight, rule: MonitoringRule, risk_value: float) -> str:
        """生成预警描述"""
        if rule.risk_type == RiskType.DELAY:
            return f"航班{flight.flight_no}预计延误{risk_value:.0f}分钟"
        elif rule.risk_type == RiskType.WEATHER:
            return f"航班{flight.flight_no}受恶劣天气影响，风险指数{risk_value:.1f}"
        elif rule.risk_type == RiskType.AIRCRAFT:
            return f"航班{flight.flight_no}飞机{flight.aircraft_registration}存在风险，指数{risk_value:.1f}"
        elif rule.risk_type == RiskType.CREW:
            return f"航班{flight.flight_no}机组{flight.crew_id}值勤时间风险，指数{risk_value:.1f}"
        else:
            return f"航班{flight.flight_no}存在{rule.risk_type.value}风险，指数{risk_value:.1f}"
    
    def _generate_recommended_actions(self, risk_type: RiskType, level: AlertLevel, risk_value: float) -> List[str]:
        """生成推荐动作"""
        actions = []
        
        if risk_type == RiskType.DELAY:
            if level == AlertLevel.CRITICAL:
                actions.extend(["立即联系机组", "考虑取消航班", "安排旅客改签"])
            elif level == AlertLevel.HIGH:
                actions.extend(["通知旅客延误", "调整后续航班", "准备延误处理"])
            else:
                actions.extend(["密切监控", "准备应急方案"])
        
        elif risk_type == RiskType.WEATHER:
            if level == AlertLevel.CRITICAL:
                actions.extend(["考虑备降", "申请绕飞", "延误等待"])
            else:
                actions.extend(["关注天气变化", "准备备用方案"])
        
        elif risk_type == RiskType.AIRCRAFT:
            if level == AlertLevel.CRITICAL:
                actions.extend(["立即更换飞机", "联系维修部门", "准备取消航班"])
            else:
                actions.extend(["检查飞机状态", "准备备用飞机"])
        
        elif risk_type == RiskType.CREW:
            if level == AlertLevel.CRITICAL:
                actions.extend(["立即更换机组", "申请值勤延长", "准备取消航班"])
            else:
                actions.extend(["关注机组状态", "准备备用机组"])
        
        return actions
    
    def _notify_alert_handlers(self, alert: Alert):
        """通知预警处理器"""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"预警处理器异常: {e}")
    
    def _get_active_flights(self) -> List[Flight]:
        """获取当前活跃航班"""
        # 这里应该从数据库或外部系统获取
        # 为演示目的，生成一些模拟数据
        current_time = datetime.now()
        flights = []
        
        for i in range(1, 21):  # 生成20个活跃航班
            flight_time = current_time + timedelta(hours=i//4, minutes=(i*15) % 60)
            
            flight = Flight(
                flight_no=f"CA{8000 + i}",
                departure_airport=["PEK", "PVG", "CAN", "CTU"][i % 4],
                arrival_airport=["PVG", "CAN", "CTU", "PEK"][i % 4],
                scheduled_departure=flight_time,
                scheduled_arrival=flight_time + timedelta(hours=2),
                aircraft_registration=f"B-{8000 + i}",
                crew_id=f"CREW{i:03d}",
                aircraft_type=["A320", "A330", "B737"][i % 3],
                passenger_count=150 + i * 5
            )
            flights.append(flight)
        
        return flights
    
    def _get_current_context(self) -> OperationalContext:
        """获取当前运行环境"""
        # 模拟运行环境数据
        return OperationalContext(
            current_time=datetime.now(),
            weather_conditions={
                "PEK": "light_rain",
                "PVG": "clear",
                "CAN": "thunderstorm",
                "CTU": "fog"
            },
            atc_restrictions={
                "PEK": {"flow_control": True, "rate": "12/hour"},
                "CAN": {"flow_control": True, "rate": "8/hour"}
            },
            airport_closures=[],
            runway_closures={},
            flow_control={}
        )
    
    def _initialize_monitoring_rules(self) -> List[MonitoringRule]:
        """初始化监控规则"""
        rules = [
            MonitoringRule(
                rule_id="delay_check",
                name="延误风险检查",
                risk_type=RiskType.DELAY,
                check_function="check_delay_risk",
                parameters={"prediction_window": 120},
                alert_thresholds=self.alert_thresholds[RiskType.DELAY],
                frequency_seconds=60
            ),
            MonitoringRule(
                rule_id="weather_check",
                name="天气风险检查",
                risk_type=RiskType.WEATHER,
                check_function="check_weather_risk",
                parameters={"forecast_horizon": 6},
                alert_thresholds=self.alert_thresholds[RiskType.WEATHER],
                frequency_seconds=300
            ),
            MonitoringRule(
                rule_id="aircraft_check",
                name="飞机状态检查",
                risk_type=RiskType.AIRCRAFT,
                check_function="check_aircraft_risk",
                parameters={"maintenance_buffer": 24},
                alert_thresholds=self.alert_thresholds[RiskType.AIRCRAFT],
                frequency_seconds=600
            ),
            MonitoringRule(
                rule_id="crew_check",
                name="机组状态检查",
                risk_type=RiskType.CREW,
                check_function="check_crew_risk",
                parameters={"duty_limit_hours": 14},
                alert_thresholds=self.alert_thresholds[RiskType.CREW],
                frequency_seconds=300
            ),
            MonitoringRule(
                rule_id="fuel_check",
                name="燃油风险检查",
                risk_type=RiskType.FUEL,
                check_function="check_fuel_risk",
                parameters={"safety_margin": 0.2},
                alert_thresholds={
                    AlertLevel.WARNING: 0.3,
                    AlertLevel.HIGH: 0.6,
                    AlertLevel.CRITICAL: 0.8
                },
                frequency_seconds=1800
            ),
            MonitoringRule(
                rule_id="slot_check",
                name="时刻风险检查",
                risk_type=RiskType.SLOT,
                check_function="check_slot_risk",
                parameters={"flow_control_threshold": 0.5},
                alert_thresholds={
                    AlertLevel.WARNING: 0.3,
                    AlertLevel.HIGH: 0.6,
                    AlertLevel.CRITICAL: 0.8
                },
                frequency_seconds=180
            )
        ]
        
        return rules
    
    def _cleanup_old_alerts(self):
        """清理历史预警"""
        # 保留最近24小时的预警
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.alerts = [alert for alert in self.alerts if alert.created_at > cutoff_time]
    
    def _group_alerts_by_level(self, alerts: List[Alert]) -> Dict[str, int]:
        """按级别分组预警"""
        groups = {}
        for alert in alerts:
            level = alert.level.value
            groups[level] = groups.get(level, 0) + 1
        return groups
    
    def _group_alerts_by_type(self, alerts: List[Alert]) -> Dict[str, int]:
        """按类型分组预警"""
        groups = {}
        for alert in alerts:
            risk_type = alert.risk_type.value
            groups[risk_type] = groups.get(risk_type, 0) + 1
        return groups


# 预警处理器示例
def console_alert_handler(alert: Alert):
    """控制台预警处理器"""
    level_colors = {
        AlertLevel.INFO: '\033[92m',      # 绿色
        AlertLevel.WARNING: '\033[93m',   # 黄色
        AlertLevel.HIGH: '\033[91m',      # 红色
        AlertLevel.CRITICAL: '\033[95m'   # 紫色
    }
    
    color = level_colors.get(alert.level, '\033[0m')
    reset_color = '\033[0m'
    
    print(f"{color}[{alert.level.value.upper()}] {alert.title}{reset_color}")
    print(f"航班: {alert.flight_no}")
    print(f"描述: {alert.description}")
    print(f"建议: {', '.join(alert.recommended_actions)}")
    print(f"影响时间: {alert.time_to_impact}")
    print("-" * 50)


def email_alert_handler(alert: Alert):
    """邮件预警处理器（模拟）"""
    if alert.level in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
        # 在真实系统中，这里会发送邮件
        print(f"📧 发送邮件预警: {alert.title} - {alert.flight_no}")


def sms_alert_handler(alert: Alert):
    """短信预警处理器（模拟）"""
    if alert.level == AlertLevel.CRITICAL:
        # 在真实系统中，这里会发送短信
        print(f"📱 发送短信预警: {alert.title} - {alert.flight_no}") 