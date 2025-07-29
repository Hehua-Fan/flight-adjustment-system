#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外部系统集成接口模块
负责与MMIS、Ameco、气象、空管等外部系统的数据交互
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import logging
from ..types.integration_models import SystemConnection





class ExternalSystemConnector(ABC):
    """外部系统连接器基类"""
    
    def __init__(self, connection: SystemConnection):
        self.connection = connection
        self.logger = logging.getLogger(f"{__name__}.{connection.system_name}")
        self.session = requests.Session()
        
        # 设置认证
        if connection.api_key:
            self.session.headers.update({"Authorization": f"Bearer {connection.api_key}"})
        elif connection.username and connection.password:
            self.session.auth = (connection.username, connection.password)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """发起HTTP请求"""
        url = f"{self.connection.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.connection.retry_attempts):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.connection.timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.connection.retry_attempts}): {e}")
                if attempt == self.connection.retry_attempts - 1:
                    self.logger.error(f"请求最终失败: {url}")
                    return None
        
        return None


class MMISConnector(ExternalSystemConnector):
    """MMIS系统连接器"""
    
    def test_connection(self) -> bool:
        """测试MMIS连接"""
        result = self._make_request("GET", "/api/health")
        return result is not None
    
    def get_aircraft_status(self, aircraft_reg: str = None) -> Dict[str, Any]:
        """获取飞机状态"""
        endpoint = "/api/aircraft/status"
        params = {}
        
        if aircraft_reg:
            params["registration"] = aircraft_reg
        
        result = self._make_request("GET", endpoint, params=params)
        
        if result:
            return result
        
        # 模拟数据作为fallback
        return self._get_mock_aircraft_status(aircraft_reg)
    
    def get_flight_plan(self, flight_no: str, date: datetime) -> Dict[str, Any]:
        """获取航班计划"""
        endpoint = f"/api/flights/{flight_no}/plan"
        params = {"date": date.strftime("%Y-%m-%d")}
        
        result = self._make_request("GET", endpoint, params=params)
        
        if result:
            return result
        
        # 模拟数据作为fallback
        return self._get_mock_flight_plan(flight_no, date)
    
    def update_flight_plan(self, adjustment_plan: Dict[str, Any]) -> bool:
        """更新航班计划"""
        endpoint = "/api/flights/plan/update"
        
        # 转换调整方案为MMIS格式
        mmis_data = self._convert_to_mmis_format(adjustment_plan)
        
        result = self._make_request("POST", endpoint, json=mmis_data)
        
        if result:
            self.logger.info(f"航班计划更新成功: {adjustment_plan.get('flight_no')}")
            return True
        else:
            self.logger.error(f"航班计划更新失败: {adjustment_plan.get('flight_no')}")
            return False
    
    def get_crew_availability(self, crew_id: str, date: datetime) -> Dict[str, Any]:
        """获取机组可用性"""
        endpoint = f"/api/crew/{crew_id}/availability"
        params = {"date": date.strftime("%Y-%m-%d")}
        
        result = self._make_request("GET", endpoint, params=params)
        
        if result:
            return result
        
        # 模拟数据作为fallback
        return self._get_mock_crew_availability(crew_id, date)
    
    def _get_mock_aircraft_status(self, aircraft_reg: str = None) -> Dict[str, Any]:
        """模拟飞机状态数据"""
        mock_data = {
            "B-1234": {
                "registration": "B-1234",
                "aircraft_type": "A330",
                "status": "available",
                "location": "PEK",
                "next_maintenance": "2024-02-15T10:00:00",
                "fuel_level": 0.8,
                "technical_status": "serviceable"
            },
            "B-5678": {
                "registration": "B-5678",
                "aircraft_type": "A320",
                "status": "in_flight",
                "location": "en_route",
                "next_maintenance": "2024-02-20T14:00:00",
                "fuel_level": 0.6,
                "technical_status": "serviceable"
            }
        }
        
        if aircraft_reg:
            return mock_data.get(aircraft_reg, {})
        
        return {"aircraft_list": list(mock_data.values())}
    
    def _get_mock_flight_plan(self, flight_no: str, date: datetime) -> Dict[str, Any]:
        """模拟航班计划数据"""
        return {
            "flight_no": flight_no,
            "date": date.strftime("%Y-%m-%d"),
            "departure_airport": "PEK",
            "arrival_airport": "PVG",
            "scheduled_departure": "14:00",
            "scheduled_arrival": "16:30",
            "aircraft_registration": "B-1234",
            "aircraft_type": "A330",
            "crew_id": "CREW001",
            "passenger_count": 250,
            "cargo_weight": 5000
        }
    
    def _get_mock_crew_availability(self, crew_id: str, date: datetime) -> Dict[str, Any]:
        """模拟机组可用性数据"""
        return {
            "crew_id": crew_id,
            "date": date.strftime("%Y-%m-%d"),
            "status": "available",
            "duty_start": "06:00",
            "duty_end": "18:00",
            "current_duty_hours": 4.5,
            "max_duty_hours": 14,
            "qualifications": ["A330", "A320"],
            "base_station": "PEK"
        }
    
    def _convert_to_mmis_format(self, adjustment_plan: Dict[str, Any]) -> Dict[str, Any]:
        """转换调整方案为MMIS格式"""
        return {
            "flight_no": adjustment_plan.get("flight_no"),
            "action": adjustment_plan.get("action"),
            "details": adjustment_plan.get("details", {}),
            "timestamp": datetime.now().isoformat(),
            "operator": "flight_adjustment_system"
        }


class AmecoConnector(ExternalSystemConnector):
    """Ameco维修系统连接器"""
    
    def test_connection(self) -> bool:
        """测试Ameco连接"""
        result = self._make_request("GET", "/api/status")
        return result is not None
    
    def get_maintenance_status(self, aircraft_reg: str = None) -> Dict[str, Any]:
        """获取维修状态"""
        endpoint = "/api/maintenance/status"
        params = {}
        
        if aircraft_reg:
            params["aircraft"] = aircraft_reg
        
        result = self._make_request("GET", endpoint, params=params)
        
        if result:
            return result
        
        # 模拟数据作为fallback
        return self._get_mock_maintenance_status(aircraft_reg)
    
    def get_maintenance_schedule(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """获取维修计划"""
        endpoint = "/api/maintenance/schedule"
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
        
        result = self._make_request("GET", endpoint, params=params)
        
        if result:
            return result
        
        # 模拟数据作为fallback
        return self._get_mock_maintenance_schedule(start_date, end_date)
    
    def report_technical_issue(self, aircraft_reg: str, issue_description: str) -> bool:
        """报告技术问题"""
        endpoint = "/api/maintenance/issues/report"
        data = {
            "aircraft_registration": aircraft_reg,
            "issue_description": issue_description,
            "report_time": datetime.now().isoformat(),
            "reporter": "flight_adjustment_system"
        }
        
        result = self._make_request("POST", endpoint, json=data)
        return result is not None
    
    def _get_mock_maintenance_status(self, aircraft_reg: str = None) -> Dict[str, Any]:
        """模拟维修状态数据"""
        mock_data = {
            "B-1234": {
                "aircraft_registration": "B-1234",
                "maintenance_status": "serviceable",
                "next_a_check": "2024-03-01T08:00:00",
                "next_c_check": "2024-06-15T08:00:00",
                "outstanding_defects": 0,
                "grounded": False
            },
            "B-5678": {
                "aircraft_registration": "B-5678",
                "maintenance_status": "minor_defect",
                "next_a_check": "2024-02-28T10:00:00",
                "next_c_check": "2024-08-20T08:00:00",
                "outstanding_defects": 1,
                "grounded": False
            }
        }
        
        if aircraft_reg:
            return mock_data.get(aircraft_reg, {})
        
        return {"maintenance_status": list(mock_data.values())}
    
    def _get_mock_maintenance_schedule(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """模拟维修计划数据"""
        schedule = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() == 6:  # 周日安排维修
                schedule.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "aircraft_registration": "B-1234",
                    "maintenance_type": "A_CHECK",
                    "duration_hours": 8,
                    "start_time": "08:00",
                    "end_time": "16:00"
                })
            current_date += timedelta(days=1)
        
        return {"maintenance_schedule": schedule}


class WeatherConnector(ExternalSystemConnector):
    """气象系统连接器"""
    
    def test_connection(self) -> bool:
        """测试气象系统连接"""
        result = self._make_request("GET", "/api/weather/status")
        return result is not None
    
    def get_current_conditions(self, airport_codes: List[str] = None) -> Dict[str, Any]:
        """获取当前天气条件"""
        endpoint = "/api/weather/current"
        params = {}
        
        if airport_codes:
            params["airports"] = ",".join(airport_codes)
        
        result = self._make_request("GET", endpoint, params=params)
        
        if result:
            return result
        
        # 模拟数据作为fallback
        return self._get_mock_weather_conditions(airport_codes)
    
    def get_forecast(self, airport_code: str, hours: int = 24) -> Dict[str, Any]:
        """获取天气预报"""
        endpoint = f"/api/weather/forecast/{airport_code}"
        params = {"hours": hours}
        
        result = self._make_request("GET", endpoint, params=params)
        
        if result:
            return result
        
        # 模拟数据作为fallback
        return self._get_mock_weather_forecast(airport_code, hours)
    
    def _get_mock_weather_conditions(self, airport_codes: List[str] = None) -> Dict[str, Any]:
        """模拟天气条件数据"""
        default_airports = ["PEK", "PVG", "CAN", "CTU", "KMG"]
        airports = airport_codes or default_airports
        
        weather_data = {}
        for airport in airports:
            if airport == "PEK":
                weather_data[airport] = "light_rain"
            elif airport == "CAN":
                weather_data[airport] = "thunderstorm"
            elif airport == "CTU":
                weather_data[airport] = "fog"
            else:
                weather_data[airport] = "clear"
        
        return {"weather_conditions": weather_data}
    
    def _get_mock_weather_forecast(self, airport_code: str, hours: int) -> Dict[str, Any]:
        """模拟天气预报数据"""
        forecast = []
        current_time = datetime.now()
        
        for i in range(0, hours, 3):  # 每3小时一个预报
            forecast_time = current_time + timedelta(hours=i)
            
            # 简单的模拟逻辑
            if airport_code == "CAN":
                condition = "thunderstorm" if i < 6 else "heavy_rain"
            elif airport_code == "CTU":
                condition = "fog" if i < 12 else "clear"
            else:
                condition = "clear"
            
            forecast.append({
                "time": forecast_time.isoformat(),
                "condition": condition,
                "visibility": 10000 if condition == "clear" else 1000,
                "wind_speed": 5 if condition == "clear" else 15,
                "temperature": 20
            })
        
        return {
            "airport_code": airport_code,
            "forecast": forecast
        }


class ATCConnector(ExternalSystemConnector):
    """空管系统连接器"""
    
    def test_connection(self) -> bool:
        """测试空管系统连接"""
        result = self._make_request("GET", "/api/atc/status")
        return result is not None
    
    def get_flow_control(self, airport_codes: List[str] = None) -> Dict[str, Any]:
        """获取流量控制信息"""
        endpoint = "/api/atc/flow_control"
        params = {}
        
        if airport_codes:
            params["airports"] = ",".join(airport_codes)
        
        result = self._make_request("GET", endpoint, params=params)
        
        if result:
            return result
        
        # 模拟数据作为fallback
        return self._get_mock_flow_control(airport_codes)
    
    def get_slot_availability(self, airport_code: str, date: datetime) -> Dict[str, Any]:
        """获取时刻可用性"""
        endpoint = f"/api/atc/slots/{airport_code}"
        params = {"date": date.strftime("%Y-%m-%d")}
        
        result = self._make_request("GET", endpoint, params=params)
        
        if result:
            return result
        
        # 模拟数据作为fallback
        return self._get_mock_slot_availability(airport_code, date)
    
    def request_slot_change(self, flight_no: str, new_time: datetime) -> Dict[str, Any]:
        """申请时刻变更"""
        endpoint = "/api/atc/slots/change_request"
        data = {
            "flight_no": flight_no,
            "new_departure_time": new_time.isoformat(),
            "request_time": datetime.now().isoformat(),
            "reason": "operational_adjustment"
        }
        
        result = self._make_request("POST", endpoint, json=data)
        
        if result:
            return result
        
        # 模拟响应
        return {
            "request_id": str(hash(flight_no + new_time.isoformat())),
            "status": "approved",
            "approved_time": new_time.isoformat()
        }
    
    def _get_mock_flow_control(self, airport_codes: List[str] = None) -> Dict[str, Any]:
        """模拟流量控制数据"""
        default_airports = ["PEK", "PVG", "CAN", "CTU"]
        airports = airport_codes or default_airports
        
        flow_control_data = {}
        for airport in airports:
            if airport in ["PEK", "CAN"]:
                flow_control_data[airport] = {
                    "flow_control": True,
                    "rate": "12/hour" if airport == "PEK" else "8/hour",
                    "start_time": "08:00",
                    "end_time": "20:00",
                    "reason": "weather"
                }
            else:
                flow_control_data[airport] = {
                    "flow_control": False
                }
        
        return {"flow_control": flow_control_data}
    
    def _get_mock_slot_availability(self, airport_code: str, date: datetime) -> Dict[str, Any]:
        """模拟时刻可用性数据"""
        slots = []
        start_hour = 6
        end_hour = 23
        
        for hour in range(start_hour, end_hour + 1):
            for minute in [0, 15, 30, 45]:
                slot_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # 模拟部分时刻已被占用
                is_available = not (hour == 8 and minute in [0, 15])  # 8:00-8:15 占用
                
                slots.append({
                    "time": slot_time.isoformat(),
                    "available": is_available,
                    "flight_no": "CA1001" if not is_available else None
                })
        
        return {
            "airport_code": airport_code,
            "date": date.strftime("%Y-%m-%d"),
            "slots": slots
        }


class CustomsConnector(ExternalSystemConnector):
    """海关系统连接器"""
    
    def test_connection(self) -> bool:
        """测试海关系统连接"""
        result = self._make_request("GET", "/api/customs/status")
        return result is not None
    
    def get_working_hours(self, airport_code: str, date: datetime) -> Dict[str, Any]:
        """获取海关工作时间"""
        endpoint = f"/api/customs/working_hours/{airport_code}"
        params = {"date": date.strftime("%Y-%m-%d")}
        
        result = self._make_request("GET", endpoint, params=params)
        
        if result:
            return result
        
        # 模拟数据作为fallback
        return self._get_mock_working_hours(airport_code, date)
    
    def check_clearance_requirements(self, flight_no: str, passenger_count: int) -> Dict[str, Any]:
        """检查通关要求"""
        endpoint = "/api/customs/clearance_requirements"
        params = {
            "flight_no": flight_no,
            "passenger_count": passenger_count
        }
        
        result = self._make_request("GET", endpoint, params=params)
        
        if result:
            return result
        
        # 模拟数据作为fallback
        return self._get_mock_clearance_requirements(flight_no, passenger_count)
    
    def _get_mock_working_hours(self, airport_code: str, date: datetime) -> Dict[str, Any]:
        """模拟海关工作时间数据"""
        # 大部分国际机场24小时工作
        if airport_code in ["PEK", "PVG", "CAN"]:
            return {
                "airport_code": airport_code,
                "date": date.strftime("%Y-%m-%d"),
                "working_hours": {
                    "start": "00:00",
                    "end": "23:59",
                    "24_hour": True
                }
            }
        else:
            # 小机场限时工作
            return {
                "airport_code": airport_code,
                "date": date.strftime("%Y-%m-%d"),
                "working_hours": {
                    "start": "06:00",
                    "end": "22:00",
                    "24_hour": False
                }
            }
    
    def _get_mock_clearance_requirements(self, flight_no: str, passenger_count: int) -> Dict[str, Any]:
        """模拟通关要求数据"""
        return {
            "flight_no": flight_no,
            "passenger_count": passenger_count,
            "estimated_clearance_time": max(20, passenger_count * 0.5),  # 分钟
            "special_requirements": [],
            "customs_channel": "green" if passenger_count < 100 else "red"
        }


class ExternalSystemsIntegration:
    """外部系统集成管理器"""
    
    def __init__(self, config: Dict[str, Dict[str, Any]] = None):
        self.config = config or {}
        self.connectors = {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化连接器
        self._initialize_connectors()
    
    def _initialize_connectors(self):
        """初始化所有连接器"""
        
        # MMIS连接器
        mmis_config = self.config.get("mmis", {})
        mmis_connection = SystemConnection(
            system_name="MMIS",
            base_url=mmis_config.get("base_url", "http://mmis.airline.com/api"),
            api_key=mmis_config.get("api_key"),
            timeout=mmis_config.get("timeout", 30)
        )
        self.connectors["mmis"] = MMISConnector(mmis_connection)
        
        # Ameco连接器
        ameco_config = self.config.get("ameco", {})
        ameco_connection = SystemConnection(
            system_name="Ameco",
            base_url=ameco_config.get("base_url", "http://ameco.airline.com/api"),
            username=ameco_config.get("username"),
            password=ameco_config.get("password"),
            timeout=ameco_config.get("timeout", 30)
        )
        self.connectors["ameco"] = AmecoConnector(ameco_connection)
        
        # 气象系统连接器
        weather_config = self.config.get("weather", {})
        weather_connection = SystemConnection(
            system_name="Weather",
            base_url=weather_config.get("base_url", "http://weather.caac.gov.cn/api"),
            api_key=weather_config.get("api_key"),
            timeout=weather_config.get("timeout", 15)
        )
        self.connectors["weather"] = WeatherConnector(weather_connection)
        
        # 空管系统连接器
        atc_config = self.config.get("atc", {})
        atc_connection = SystemConnection(
            system_name="ATC",
            base_url=atc_config.get("base_url", "http://atc.caac.gov.cn/api"),
            api_key=atc_config.get("api_key"),
            timeout=atc_config.get("timeout", 20)
        )
        self.connectors["atc"] = ATCConnector(atc_connection)
        
        # 海关系统连接器
        customs_config = self.config.get("customs", {})
        customs_connection = SystemConnection(
            system_name="Customs",
            base_url=customs_config.get("base_url", "http://customs.gov.cn/api"),
            api_key=customs_config.get("api_key"),
            timeout=customs_config.get("timeout", 25)
        )
        self.connectors["customs"] = CustomsConnector(customs_connection)
    
    def test_all_connections(self) -> Dict[str, bool]:
        """测试所有系统连接"""
        results = {}
        
        for system_name, connector in self.connectors.items():
            try:
                results[system_name] = connector.test_connection()
                status = "✅ 连接成功" if results[system_name] else "❌ 连接失败"
                self.logger.info(f"{system_name}: {status}")
            except Exception as e:
                results[system_name] = False
                self.logger.error(f"{system_name}: ❌ 连接异常 - {e}")
        
        return results
    
    def sync_all_data(self):
        """同步所有外部系统数据"""
        sync_results = {
            "aircraft_data": {},
            "weather_data": {},
            "atc_data": {},
            "maintenance_data": {},
            "customs_data": {},
            "sync_timestamp": datetime.now().isoformat()
        }
        
        try:
            # 同步飞机数据
            if "mmis" in self.connectors:
                sync_results["aircraft_data"] = self.connectors["mmis"].get_aircraft_status()
            
            # 同步天气数据
            if "weather" in self.connectors:
                sync_results["weather_data"] = self.connectors["weather"].get_current_conditions()
            
            # 同步空管数据
            if "atc" in self.connectors:
                sync_results["atc_data"] = self.connectors["atc"].get_flow_control()
            
            # 同步维修数据
            if "ameco" in self.connectors:
                sync_results["maintenance_data"] = self.connectors["ameco"].get_maintenance_status()
            
            # 同步海关数据（示例）
            if "customs" in self.connectors:
                sync_results["customs_data"] = self.connectors["customs"].get_working_hours("PEK", datetime.now())
        
        except Exception as e:
            self.logger.error(f"数据同步异常: {e}")
            sync_results["error"] = str(e)
        
        return sync_results
    
    def push_adjustment_to_downstream(self, adjustment_plan: Dict[str, Any]):
        """将调整方案推送到下游系统"""
        push_results = {}
        
        # 推送到MMIS
        if "mmis" in self.connectors:
            try:
                push_results["mmis"] = self.connectors["mmis"].update_flight_plan(adjustment_plan)
            except Exception as e:
                self.logger.error(f"推送到MMIS失败: {e}")
                push_results["mmis"] = False
        
        # 如果是时刻变更，推送到空管系统
        if adjustment_plan.get("action") == "CHANGE_TIME" and "atc" in self.connectors:
            try:
                new_departure = datetime.fromisoformat(
                    adjustment_plan.get("details", {}).get("new_departure", "")
                )
                flight_no = adjustment_plan.get("flight_no")
                
                result = self.connectors["atc"].request_slot_change(flight_no, new_departure)
                push_results["atc"] = result.get("status") == "approved"
            except Exception as e:
                self.logger.error(f"推送到空管系统失败: {e}")
                push_results["atc"] = False
        
        # 如果涉及维修问题，通知Ameco
        if ("aircraft" in adjustment_plan.get("reason", "").lower() and 
            "ameco" in self.connectors):
            try:
                aircraft_reg = adjustment_plan.get("details", {}).get("aircraft_registration", "")
                issue_description = f"航班调整相关: {adjustment_plan.get('reason', '')}"
                
                push_results["ameco"] = self.connectors["ameco"].report_technical_issue(
                    aircraft_reg, issue_description
                )
            except Exception as e:
                self.logger.error(f"推送到Ameco失败: {e}")
                push_results["ameco"] = False
        
        return push_results
    
    def get_integration_status(self):
        """获取集成状态"""
        connection_status = self.test_all_connections()
        
        total_systems = len(self.connectors)
        connected_systems = sum(1 for status in connection_status.values() if status)
        
        return {
            "total_systems": total_systems,
            "connected_systems": connected_systems,
            "connection_rate": connected_systems / total_systems if total_systems > 0 else 0,
            "system_status": connection_status,
            "last_check": datetime.now().isoformat()
        }
    
    def get_real_time_context(self):
        """获取实时运行环境上下文"""
        context = {
            "current_time": datetime.now().isoformat(),
            "weather_conditions": {},
            "atc_restrictions": {},
            "airport_closures": [],
            "runway_closures": {},
            "flow_control": {}
        }
        
        try:
            # 获取天气信息
            if "weather" in self.connectors:
                weather_data = self.connectors["weather"].get_current_conditions()
                context["weather_conditions"] = weather_data.get("weather_conditions", {})
            
            # 获取空管限制
            if "atc" in self.connectors:
                atc_data = self.connectors["atc"].get_flow_control()
                context["atc_restrictions"] = atc_data.get("flow_control", {})
                context["flow_control"] = atc_data.get("flow_control", {})
        
        except Exception as e:
            self.logger.error(f"获取实时上下文失败: {e}")
            context["error"] = str(e)
        
        return context 