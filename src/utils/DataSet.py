"""
数据集基类和具体实现
参考 PyTorch 的 DataSet 设计思路，提供通用的数据集接口
"""

import pandas as pd
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime, time
from ..types.constraint_models import (
    AirportSpecialRequirement, AirportRestriction, FlightRestriction,
    FlightSpecialRequirement, SectorSpecialRequirement,
    Priority, RequirementType, Category, RestrictionType
)


class DataSet(ABC):
    """数据集基类"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data: pd.DataFrame = pd.DataFrame()
        self.items: List[Any] = []
        
    @abstractmethod
    def load_data(self) -> None:
        """加载数据文件"""
        pass
        
    @abstractmethod
    def parse_item(self, row: pd.Series) -> Any:
        """解析单个数据项"""
        pass
        
    @abstractmethod
    def get_data_type(self) -> Type:
        """获取数据类型"""
        pass
        
    def __len__(self) -> int:
        """获取数据集大小"""
        return len(self.items)
        
    def __getitem__(self, index: int) -> Any:
        """获取指定索引的数据项"""
        return self.items[index]
        
    def get_all_items(self) -> List[Any]:
        """获取所有数据项"""
        return self.items
        
    def filter_by_condition(self, condition_func) -> List[Any]:
        """根据条件筛选数据"""
        return [item for item in self.items if condition_func(item)]
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        return {
            "总数": len(self.items),
            "数据类型": self.get_data_type().__name__
        }
    
    # 通用解析方法 - 所有子类都可以使用
    def _safe_parse_category(self, category_str: str) -> Category:
        """安全解析 Category 值"""
        if pd.isna(category_str) or str(category_str).strip() == "":
            return Category.EMPTY
        try:
            return Category(str(category_str))
        except ValueError:
            return Category.OTHER
            
    def _safe_parse_restriction_type(self, restriction_type_str: str) -> RestrictionType:
        """安全解析 RestrictionType 值"""
        if pd.isna(restriction_type_str) or str(restriction_type_str).strip() == "":
            return RestrictionType.EMPTY
        try:
            return RestrictionType(str(restriction_type_str))
        except ValueError:
            return RestrictionType.EMPTY
            
    def _parse_date(self, date_str: str) -> datetime:
        """解析日期字符串，使用 pandas 的强大解析能力"""
        if pd.isna(date_str):
            return datetime(2024, 1, 1)
        try:
            return pd.to_datetime(date_str).to_pydatetime()
        except:
            return datetime(2024, 1, 1)
            
    def _parse_time(self, time_str: str) -> time:
        """解析时间字符串"""
        if pd.isna(time_str):
            return time(0, 0)
        try:
            return pd.to_datetime(time_str, format="%H:%M").time()
        except:
            return time(0, 0)
            
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """解析日期时间字符串，使用 pandas 的智能解析"""
        if pd.isna(datetime_str):
            return datetime(2024, 1, 1, 0, 0, 0)
        try:
            return pd.to_datetime(datetime_str).to_pydatetime()
        except:
            return datetime(2024, 1, 1, 0, 0, 0)
    
    def _safe_parse_priority(self, priority_str: str) -> Priority:
        """安全解析 Priority 值"""
        if pd.isna(priority_str) or str(priority_str).strip() == "":
            return Priority.NORMAL
        try:
            return Priority(str(priority_str))
        except ValueError:
            return Priority.NORMAL
            
    def _safe_parse_requirement_type(self, req_type_str: str) -> RequirementType:
        """安全解析 RequirementType 值"""
        if pd.isna(req_type_str) or str(req_type_str).strip() == "":
            return RequirementType.MANDATORY
        try:
            return RequirementType(str(req_type_str))
        except ValueError:
            return RequirementType.MANDATORY
    
    def _safe_parse_bool(self, bool_str: str) -> bool:
        """安全解析布尔值"""
        if pd.isna(bool_str):
            return False
        try:
            if isinstance(bool_str, (bool, int)):
                return bool(bool_str)
            str_val = str(bool_str).strip().lower()
            return str_val in ('1', 'true', 'yes', 'on', 't', 'y')
        except:
            return False
    
    def _safe_parse_int(self, int_str: str, default: int = 0) -> int:
        """安全解析整数值"""
        if pd.isna(int_str):
            return default
        try:
            return int(float(str(int_str)))  # 先转float再转int，处理"1.0"这种情况
        except:
            return default
    
    def _safe_parse_float(self, float_str: str, default: float = 0.0) -> float:
        """安全解析浮点数值"""
        if pd.isna(float_str):
            return default
        try:
            return float(str(float_str))
        except:
            return default
    
    def _safe_parse_str(self, str_val: str, default: str = "") -> str:
        """安全解析字符串值"""
        if pd.isna(str_val):
            return default
        return str(str_val).strip()


class AirportSpecialRequirementDataSet(DataSet):
    """机场特殊要求数据集"""
    
    def load_data(self) -> None:
        """加载机场特殊要求数据"""
        try:
            self.data = pd.read_csv(self.file_path, encoding='utf-8-sig')
            self.items = []
            
            for _, row in self.data.iterrows():
                try:
                    item = self.parse_item(row)
                    self.items.append(item)
                except Exception as e:
                    print(f"警告: 跳过无效的机场特殊要求记录 {row.get('AIRPORT_SPECIAL_REQUIREMENT_ID', 'Unknown')}: {e}")
                    
        except Exception as e:
            print(f"❌ 加载机场特殊要求数据失败: {e}")
            raise
            
    def parse_item(self, row: pd.Series) -> AirportSpecialRequirement:
        """解析机场特殊要求数据项"""
        return AirportSpecialRequirement(
            id=self._safe_parse_str(row['AIRPORT_SPECIAL_REQUIREMENT_ID']),
            version=self._safe_parse_int(row['LATEST_VERSION'], 1),
            requirement_type=self._safe_parse_requirement_type(row['REQUIREMENT_TYPE']),
            priority=self._safe_parse_priority(row['PRIORITY']),
            comments=self._safe_parse_str(row['COMMENTS']),
            remarks=self._safe_parse_str(row['REMARKS']),
            category=self._safe_parse_category(row['CATEGORY']),
            continuous_time_period=self._safe_parse_bool(row['CONTINUOUS_TIME_PERIOD']),
            start_date=self._parse_date(row['START_DATE']),
            end_date=self._parse_date(row['END_DATE']),
            start_time_of_day=self._parse_time(row['START_TIME_OF_DAY']),
            end_time_of_day=self._parse_time(row['END_TIME_OF_DAY']),
            days_of_week=self._safe_parse_str(row['DISCONT_DAYS_OF_WEEK']),
            airport_code=self._safe_parse_str(row['AIRPORT_CODE']) or None,
            airports_group_id=self._safe_parse_str(row['AIRPORTS_GROUP_ID']) or None,
            airport_type=self._safe_parse_str(row['AIRPORT_TYPE']),
            scope=self._safe_parse_str(row['R_SCOPE']),
            owner=self._safe_parse_str(row['R_OWNER']),
            constraint_id=self._safe_parse_str(row['CONSTRAINT_ID']),
            source=self._safe_parse_str(row['SOURCE']),
            last_modified=self._parse_datetime(row['LAST_MODIFIED_TIME_STAMP'])
        )
        
    def get_data_type(self) -> Type:
        return AirportSpecialRequirement


class AirportRestrictionDataSet(DataSet):
    """机场限制数据集"""
    
    def load_data(self) -> None:
        """加载机场限制数据"""
        try:
            self.data = pd.read_csv(self.file_path, encoding='utf-8-sig')
            self.items = []
            
            for _, row in self.data.iterrows():
                try:
                    item = self.parse_item(row)
                    self.items.append(item)
                except Exception as e:
                    print(f"警告: 跳过无效的机场限制记录 {row.get('AIRPORT_RESTRICTION_ID', 'Unknown')}: {e}")
                    
        except Exception as e:
            print(f"❌ 加载机场限制数据失败: {e}")
            raise
            
    def parse_item(self, row: pd.Series) -> AirportRestriction:
        """解析机场限制数据项"""
        return AirportRestriction(
            id=self._safe_parse_str(row['AIRPORT_RESTRICTION_ID']),
            version=self._safe_parse_int(row['LATEST_VERSION'], 1),
            priority=self._safe_parse_priority(row['PRIORITY']),
            comments=self._safe_parse_str(row['COMMENTS']),
            remarks=self._safe_parse_str(row['REMARKS']),
            category=self._safe_parse_category(row['CATEGORY']),
            continuous_time_period=self._safe_parse_bool(row['CONTINUOUS_TIME_PERIOD']),
            start_date=self._parse_date(row['START_DATE']),
            end_date=self._parse_date(row['END_DATE']),
            start_time_of_day=self._parse_time(row['START_TIME_OF_DAY']),
            end_time_of_day=self._parse_time(row['END_TIME_OF_DAY']),
            days_of_week=self._safe_parse_str(row['DISCONT_DAYS_OF_WEEK']),
            curfew_type=self._safe_parse_str(row['CURFEW_AIRPORT_RST_TYPE']),
            constraint_type=self._safe_parse_str(row['CONSTRAINT_TYPE']),
            constraint_value=self._safe_parse_str(row['CONSTRAINT_VALUE']),
            restriction_type=self._safe_parse_restriction_type(row['RESTRICTION_TYPE']),
            airport_code=self._safe_parse_str(row['AIRPORT_CODE']),
            airport_type=self._safe_parse_str(row['AIRPORT_TYPE']),
            scope=self._safe_parse_str(row['RESTRICTION_SCOPE']),
            owner=self._safe_parse_str(row['RESTRICTION_OWNER']),
            airports_group_id=self._safe_parse_str(row['AIRPORTS_GROUP_ID']) or None,
            constraint_id=self._safe_parse_str(row['CONSTRAINT_ID']),
            source=self._safe_parse_str(row['SOURCE']),
            required=self._safe_parse_bool(row['REQUIRED']),
            last_modified=self._parse_datetime(row['LAST_MODIFIED_TIME_STAMP'])
        )
        
    def get_data_type(self) -> Type:
        return AirportRestriction


class FlightRestrictionDataSet(DataSet):
    """航班限制数据集"""
    
    def load_data(self) -> None:
        """加载航班限制数据"""
        try:
            self.data = pd.read_csv(self.file_path, encoding='utf-8-sig')
            self.items = []
            
            for _, row in self.data.iterrows():
                try:
                    item = self.parse_item(row)
                    self.items.append(item)
                except Exception as e:
                    print(f"警告: 跳过无效的航班限制记录 {row.get('FLIGHT_LEG_RESTRICTION_ID', 'Unknown')}: {e}")
                    
        except Exception as e:
            print(f"❌ 加载航班限制数据失败: {e}")
            raise
            
    def parse_item(self, row: pd.Series) -> FlightRestriction:
        """解析航班限制数据项"""
        return FlightRestriction(
            id=self._safe_parse_str(row['FLIGHT_LEG_RESTRICTION_ID']),
            version=self._safe_parse_int(row['LATEST_VERSION'], 1),
            priority=self._safe_parse_priority(row['PRIORITY']),
            departure_airport=self._safe_parse_str(row['DEPARTURE_AIRPORT_CODE']) or None,
            arrival_airport=self._safe_parse_str(row['ARRIVAL_AIRPORT_CODE']) or None,
            carrier_code=self._safe_parse_str(row['SECTOR_CARRIER_CODE']),
            restriction_type=self._safe_parse_str(row['RESTRICTION_TYPE']),
            continuous_time_period=self._safe_parse_bool(row['CONTINUOUS_TIME_PERIOD']),
            start_date=self._parse_date(row['START_DATE']),
            end_date=self._parse_date(row['END_DATE']),
            start_time=self._parse_time(row['START_TIME']),
            end_time=self._parse_time(row['END_TIME']),
            days_of_week=self._safe_parse_str(row['DAY_OF_WEEK']),
            category=self._safe_parse_category(row['CATEGORY']),
            remarks=self._safe_parse_str(row['REMARKS']),
            comments=self._safe_parse_str(row['COMMENTS']),
            flight_carrier_code=self._safe_parse_str(row['CARRIER_CODE']),
            flight_number=self._safe_parse_str(row['FLIGHT_NUMBER']),
            op_suffix=self._safe_parse_str(row['OP_SUFFIX']),
            scope=self._safe_parse_str(row['RESTRICTION_SCOPE']),
            owner=self._safe_parse_str(row['RESTRICTION_OWNER']),
            match_by_date=self._safe_parse_str(row['MATCH_BY_DATE']),
            constraint_id=self._safe_parse_str(row['CONSTRAINT_ID']),
            source=self._safe_parse_str(row['SOURCE']),
            required=self._safe_parse_bool(row['REQUIRED']),
            last_modified=self._parse_datetime(row['LAST_MODIFIED_TIME_STAMP'])
        )
        
    def get_data_type(self) -> Type:
        return FlightRestriction


class FlightSpecialRequirementDataSet(DataSet):
    """航班特殊要求数据集"""
    
    def load_data(self) -> None:
        """加载航班特殊要求数据"""
        try:
            self.data = pd.read_csv(self.file_path, encoding='utf-8-sig')
            self.items = []
            
            for _, row in self.data.iterrows():
                try:
                    item = self.parse_item(row)
                    self.items.append(item)
                except Exception as e:
                    print(f"警告: 跳过无效的航班特殊要求记录 {row.get('FLIGHT_LEG_SPECIAL_RQRMNT_ID', 'Unknown')}: {e}")
                    
        except Exception as e:
            print(f"❌ 加载航班特殊要求数据失败: {e}")
            raise
            
    def parse_item(self, row: pd.Series) -> FlightSpecialRequirement:
        """解析航班特殊要求数据项"""
        return FlightSpecialRequirement(
            id=self._safe_parse_str(row['FLIGHT_LEG_SPECIAL_RQRMNT_ID']),
            version=self._safe_parse_int(row['LATEST_VERSION'], 1),
            requirement_type=self._safe_parse_requirement_type(row['REQUIREMENT_TYPE']),
            priority=self._safe_parse_priority(row['PRIORITY']),
            comments=self._safe_parse_str(row['COMMENTS']),
            remarks=self._safe_parse_str(row['REMARKS']),
            category=self._safe_parse_category(row['CATEGORY']),
            continuous_time_period=self._safe_parse_bool(row['CONTINUOUS_TIME_PERIOD']),
            start_date=self._parse_date(row['START_DATE']),
            end_date=self._parse_date(row['END_DATE']),
            start_time_of_day=self._parse_time(row['START_TIME_OF_DAY']),
            end_time_of_day=self._parse_time(row['END_TIME_OF_DAY']),
            days_of_week=self._safe_parse_str(row['DISCONT_DAYS_OF_WEEK']),
            departure_airport=self._safe_parse_str(row['DEPARTURE_AIRPORT_CODE']),
            arrival_airport=self._safe_parse_str(row['ARRIVAL_AIRPORT_CODE']),
            carrier_code=self._safe_parse_str(row['CARRIER_CODE']),
            ref_carrier_code=self._safe_parse_str(row['REF_CARRIER_CODE']),
            ref_flight_number=self._safe_parse_str(row['REF_FLIGHT_NUMBER']),
            ref_op_suffix=self._safe_parse_str(row['REF_OP_SUFFIX']),
            scope=self._safe_parse_str(row['R_SCOPE']),
            owner=self._safe_parse_str(row['R_OWNER']),
            match_by_date=self._safe_parse_str(row['MATCH_BY_DATE']),
            constraint_id=self._safe_parse_str(row['CONSTRAINT_ID']),
            source=self._safe_parse_str(row['SOURCE']),
            last_modified=self._parse_datetime(row['LAST_MODIFIED_TIME_STAMP'])
        )
        
    def get_data_type(self) -> Type:
        return FlightSpecialRequirement


class SectorSpecialRequirementDataSet(DataSet):
    """航段特殊要求数据集"""
    
    def load_data(self) -> None:
        """加载航段特殊要求数据"""
        try:
            self.data = pd.read_csv(self.file_path, encoding='utf-8-sig')
            self.items = []
            
            for _, row in self.data.iterrows():
                try:
                    item = self.parse_item(row)
                    self.items.append(item)
                except Exception as e:
                    print(f"警告: 跳过无效的航段特殊要求记录 {row.get('SECTOR_SPECIAL_REQUIREMENT_ID', 'Unknown')}: {e}")
                    
        except Exception as e:
            print(f"❌ 加载航段特殊要求数据失败: {e}")
            raise
            
    def parse_item(self, row: pd.Series) -> SectorSpecialRequirement:
        """解析航段特殊要求数据项"""
        return SectorSpecialRequirement(
            id=self._safe_parse_str(row['SECTOR_SPECIAL_REQUIREMENT_ID']),
            version=self._safe_parse_int(row['LATEST_VERSION'], 1),
            requirement_type=self._safe_parse_requirement_type(row['REQUIREMENT_TYPE']),
            priority=self._safe_parse_priority(row['PRIORITY']),
            comments=self._safe_parse_str(row['COMMENTS']),
            remarks=self._safe_parse_str(row['REMARKS']),
            category=self._safe_parse_category(row['CATEGORY']),
            continuous_time_period=self._safe_parse_bool(row['CONTINUOUS_TIME_PERIOD']),
            start_date=self._parse_date(row['START_DATE']),
            end_date=self._parse_date(row['END_DATE']),
            start_time_of_day=self._parse_time(row['START_TIME_OF_DAY']),
            end_time_of_day=self._parse_time(row['END_TIME_OF_DAY']),
            days_of_week=self._safe_parse_str(row['DISCONT_DAYS_OF_WEEK']),
            departure_airport=self._safe_parse_str(row['DEPARTURE_AIRPORT_CODE']),
            arrival_airport=self._safe_parse_str(row['ARRIVAL_AIRPORT_CODE']),
            carrier_code=self._safe_parse_str(row['CARRIER_CODE']),
            scope=self._safe_parse_str(row['R_SCOPE']),
            owner=self._safe_parse_str(row['R_OWNER']),
            constraint_id=self._safe_parse_str(row['CONSTRAINT_ID']),
            source=self._safe_parse_str(row['SOURCE']),
            last_modified=self._parse_datetime(row['LAST_MODIFIED_TIME_STAMP'])
        )
        
    def get_data_type(self) -> Type:
        return SectorSpecialRequirement 
