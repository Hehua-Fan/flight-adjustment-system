"""
约束数据加载器 - 包含约束数据加载和解析功能
"""

import pandas as pd
import json
import numpy as np
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class ConstraintDataLoader:
    """约束数据加载器类 - 负责从不同来源加载约束数据"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化约束数据加载器
        
        Args:
            data_dir: 约束数据文件目录，如果为None则自动确定
        """
        if data_dir is None:
            # 自动确定数据目录位置
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            data_dir = project_root / "assets" / "restriction"
        self.data_dir = Path(data_dir)
        self.constraint_files = {
            'airport_restriction': 'airport_restriction.csv',
            'airport_special_requirement': 'airport_special_requirement.csv', 
            'flight_restriction': 'flight_restriction.csv',
            'flight_special_requirement': 'flight_special_requirement.csv',
            'sector_special_requirement': 'sector_special_requirement.csv'
        }
    
    def load_constraint_data(self, constraint_dir_path: str = None, filter_active: bool = True):
        """
        加载所有5种约束数据文件，可选择是否过滤有效约束
        
        Args:
            constraint_dir_path: 约束文件所在目录路径，如果为None则使用默认目录
            filter_active: 是否过滤出当前有效的约束条件，默认为True
            
        Returns:
            dict: 包含所有约束数据的字典
        """
        if constraint_dir_path is None:
            constraint_dir_path = self.data_dir
        else:
            constraint_dir_path = Path(constraint_dir_path)
            
        print(f"[ConstraintDataLoader]: 正在从 {constraint_dir_path} 加载所有约束数据...")

        constraint_data = {}
        
        for key, filename in self.constraint_files.items():
            file_path = constraint_dir_path / filename
            try:
                df = pd.read_csv(file_path)
                constraint_data[key] = df
                print(f"  ✓ 成功加载: {filename} ({len(df)} 条记录)")
            except FileNotFoundError:
                print(f"  ⚠ 约束文件未找到，将忽略: {filename}")
                constraint_data[key] = pd.DataFrame()
            except Exception as e:
                print(f"  ✗ 加载失败: {filename} - {e}")
                constraint_data[key] = pd.DataFrame()
        
        # 如果需要过滤有效约束
        if filter_active:
            constraint_data = self._filter_active_constraints(constraint_data, datetime.now())
        
        print("[ConstraintDataLoader]: 约束数据加载完毕。")
        return constraint_data
    
    def _filter_active_constraints(self, constraint_data: dict, current_date: datetime = None):
        """
        过滤出当前有效的约束条件（私有方法）
        
        Args:
            constraint_data: 约束数据字典
            current_date: 当前日期，默认为今天
            
        Returns:
            dict: 过滤后的约束数据
        """
        if current_date is None:
            current_date = datetime.now()
        
        print("[ConstraintDataLoader]: 正在过滤有效约束条件...")
        filtered_data = {}
        
        for constraint_type, df in constraint_data.items():
            if df.empty:
                filtered_data[constraint_type] = df
                continue
            
            # 过滤有效期内的约束
            active_df = df.copy()
            
            # 检查开始日期和结束日期
            if 'START_DATE' in df.columns:
                active_df['START_DATE'] = pd.to_datetime(active_df['START_DATE'], errors='coerce')
                active_df = active_df[
                    (active_df['START_DATE'].isna()) | 
                    (active_df['START_DATE'] <= current_date)
                ]
            
            if 'END_DATE' in df.columns:
                active_df['END_DATE'] = pd.to_datetime(active_df['END_DATE'], errors='coerce')
                active_df = active_df[
                    (active_df['END_DATE'].isna()) | 
                    (active_df['END_DATE'] >= current_date)
                ]
            
            filtered_data[constraint_type] = active_df
            
            if len(active_df) < len(df):
                print(f"  [ConstraintDataLoader]: {constraint_type} 过滤后有效约束: {len(active_df)}/{len(df)}")
        
        return filtered_data

    def _clean_data(self, data: Any) -> Any:
        """清理数据中的NaN值，使其可以JSON序列化"""
        if isinstance(data, dict):
            return {k: self._clean_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_data(item) for item in data]
        elif isinstance(data, float) and (pd.isna(data) or np.isnan(data)):
            return None
        elif pd.isna(data):
            return None
        else:
            return data
        
    def parse_airport_restrictions(self) -> List[Dict[str, Any]]:
        """解析机场限制条件"""
        file_path = self.data_dir / self.constraint_files['airport_restriction']
        df = pd.read_csv(file_path)
        
        restrictions = []
        for _, row in df.iterrows():
            restriction = {
                'id': str(row['AIRPORT_RESTRICTION_ID']),
                'name': f"{row['AIRPORT_CODE']} 机场限制",
                'airport_code': row['AIRPORT_CODE'],
                'priority': row['PRIORITY'],
                'category': row['CATEGORY'],
                'restriction_type': row.get('RESTRICTION_TYPE', ''),
                'curfew_type': row.get('CURFEW_AIRPORT_RST_TYPE', ''),
                'description': row.get('COMMENTS', ''),
                'remarks': row.get('REMARKS', ''),
                'time_period': {
                    'continuous': bool(row.get('CONTINUOUS_TIME_PERIOD', 0)),
                    'start_date': row.get('START_DATE', ''),
                    'end_date': row.get('END_DATE', ''),
                    'start_time': row.get('START_TIME_OF_DAY', ''),
                    'end_time': row.get('END_TIME_OF_DAY', ''),
                    'days_of_week': row.get('DISCONT_DAYS_OF_WEEK', '')
                },
                'scope': row.get('RESTRICTION_SCOPE', ''),
                'owner': row.get('RESTRICTION_OWNER', ''),
                'source': row.get('SOURCE', ''),
                'last_modified': row.get('LAST_MODIFIED_TIME_STAMP', '')
            }
            restrictions.append(restriction)
        
        return self._clean_data(restrictions)
    
    def parse_airport_special_requirements(self) -> List[Dict[str, Any]]:
        """解析机场特殊要求"""
        file_path = self.data_dir / self.constraint_files['airport_special_requirement']
        df = pd.read_csv(file_path)
        
        requirements = []
        for _, row in df.iterrows():
            requirement = {
                'id': str(row['AIRPORT_SPECIAL_REQUIREMENT_ID']),
                'name': f"{row.get('AIRPORT_CODE', '通用')} 特殊要求",
                'airport_code': row.get('AIRPORT_CODE', ''),
                'requirement_type': row['REQUIREMENT_TYPE'],
                'priority': row['PRIORITY'],
                'category': row['CATEGORY'],
                'description': row.get('COMMENTS', ''),
                'remarks': row.get('REMARKS', ''),
                'time_period': {
                    'continuous': bool(row.get('CONTINUOUS_TIME_PERIOD', 0)),
                    'start_date': row.get('START_DATE', ''),
                    'end_date': row.get('END_DATE', ''),
                    'start_time': row.get('START_TIME_OF_DAY', ''),
                    'end_time': row.get('END_TIME_OF_DAY', ''),
                    'days_of_week': row.get('DISCONT_DAYS_OF_WEEK', '')
                },
                'scope': row.get('R_SCOPE', ''),
                'owner': row.get('R_OWNER', ''),
                'source': row.get('SOURCE', ''),
                'last_modified': row.get('LAST_MODIFIED_TIME_STAMP', '')
            }
            requirements.append(requirement)
        
        return self._clean_data(requirements)
    
    def parse_flight_restrictions(self) -> List[Dict[str, Any]]:
        """解析航班限制条件"""
        file_path = self.data_dir / self.constraint_files['flight_restriction']
        df = pd.read_csv(file_path)
        
        restrictions = []
        for _, row in df.iterrows():
            restriction = {
                'id': str(row['FLIGHT_LEG_RESTRICTION_ID']),
                'name': f"{row.get('CARRIER_CODE', '')}{row.get('FLIGHT_NUMBER', '')} 航班限制",
                'departure_airport': row.get('DEPARTURE_AIRPORT_CODE', ''),
                'arrival_airport': row.get('ARRIVAL_AIRPORT_CODE', ''),
                'carrier_code': row.get('CARRIER_CODE', ''),
                'flight_number': row.get('FLIGHT_NUMBER', ''),
                'priority': row['PRIORITY'],
                'restriction_type': row['RESTRICTION_TYPE'],
                'category': row['CATEGORY'],
                'description': row.get('COMMENTS', ''),
                'remarks': row.get('REMARKS', ''),
                'time_period': {
                    'continuous': bool(row.get('CONTINUOUS_TIME_PERIOD', 0)),
                    'start_date': row.get('START_DATE', ''),
                    'end_date': row.get('END_DATE', ''),
                    'start_time': row.get('START_TIME', ''),
                    'end_time': row.get('END_TIME', ''),
                    'days_of_week': row.get('DAY_OF_WEEK', '')
                },
                'scope': row.get('RESTRICTION_SCOPE', ''),
                'owner': row.get('RESTRICTION_OWNER', ''),
                'match_by_date': row.get('MATCH_BY_DATE', ''),
                'source': row.get('SOURCE', ''),
                'last_modified': row.get('LAST_MODIFIED_TIME_STAMP', '')
            }
            restrictions.append(restriction)
        
        return self._clean_data(restrictions)
    
    def parse_flight_special_requirements(self) -> List[Dict[str, Any]]:
        """解析航班特殊要求"""
        file_path = self.data_dir / self.constraint_files['flight_special_requirement']
        df = pd.read_csv(file_path)
        
        requirements = []
        for _, row in df.iterrows():
            requirement = {
                'id': str(row['FLIGHT_LEG_SPECIAL_RQRMNT_ID']),
                'name': f"{row.get('CARRIER_CODE', '')}{row.get('REF_FLIGHT_NUMBER', '')} 特殊要求",
                'departure_airport': row.get('DEPARTURE_AIRPORT_CODE', ''),
                'arrival_airport': row.get('ARRIVAL_AIRPORT_CODE', ''),
                'carrier_code': row.get('CARRIER_CODE', ''),
                'ref_flight_number': row.get('REF_FLIGHT_NUMBER', ''),
                'requirement_type': row['REQUIREMENT_TYPE'],
                'priority': row['PRIORITY'],
                'category': row['CATEGORY'],
                'description': row.get('COMMENTS', ''),
                'remarks': row.get('REMARKS', ''),
                'time_period': {
                    'continuous': bool(row.get('CONTINUOUS_TIME_PERIOD', 0)),
                    'start_date': row.get('START_DATE', ''),
                    'end_date': row.get('END_DATE', ''),
                    'start_time': row.get('START_TIME_OF_DAY', ''),
                    'end_time': row.get('END_TIME_OF_DAY', ''),
                    'days_of_week': row.get('DISCONT_DAYS_OF_WEEK', '')
                },
                'scope': row.get('R_SCOPE', ''),
                'owner': row.get('R_OWNER', ''),
                'match_by_date': row.get('MATCH_BY_DATE', ''),
                'source': row.get('SOURCE', ''),
                'last_modified': row.get('LAST_MODIFIED_TIME_STAMP', '')
            }
            requirements.append(requirement)
        
        return self._clean_data(requirements)
    
    def parse_sector_special_requirements(self) -> List[Dict[str, Any]]:
        """解析航路特殊要求"""
        file_path = self.data_dir / self.constraint_files['sector_special_requirement']
        df = pd.read_csv(file_path)
        
        requirements = []
        for _, row in df.iterrows():
            requirement = {
                'id': str(row['SECTOR_SPECIAL_REQUIREMENT_ID']),
                'name': f"{row.get('DEPARTURE_AIRPORT_CODE', '')}-{row.get('ARRIVAL_AIRPORT_CODE', '')} 航路要求",
                'departure_airport': row.get('DEPARTURE_AIRPORT_CODE', ''),
                'arrival_airport': row.get('ARRIVAL_AIRPORT_CODE', ''),
                'carrier_code': row.get('CARRIER_CODE', ''),
                'requirement_type': row['REQUIREMENT_TYPE'],
                'priority': row['PRIORITY'],
                'category': row['CATEGORY'],
                'description': row.get('COMMENTS', ''),
                'remarks': row.get('REMARKS', ''),
                'time_period': {
                    'continuous': bool(row.get('CONTINUOUS_TIME_PERIOD', 0)),
                    'start_date': row.get('START_DATE', ''),
                    'end_date': row.get('END_DATE', ''),
                    'start_time': row.get('START_TIME_OF_DAY', ''),
                    'end_time': row.get('END_TIME_OF_DAY', ''),
                    'days_of_week': row.get('DISCONT_DAYS_OF_WEEK', '')
                },
                'scope': row.get('R_SCOPE', ''),
                'owner': row.get('R_OWNER', ''),
                'source': row.get('SOURCE', ''),
                'last_modified': row.get('LAST_MODIFIED_TIME_STAMP', '')
            }
            requirements.append(requirement)
        
        return self._clean_data(requirements)
    
    def get_all_constraints(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有约束条件数据"""
        return {
            'airport_restrictions': self.parse_airport_restrictions(),
            'airport_special_requirements': self.parse_airport_special_requirements(),
            'flight_restrictions': self.parse_flight_restrictions(),
            'flight_special_requirements': self.parse_flight_special_requirements(),
            'sector_special_requirements': self.parse_sector_special_requirements()
        }
    
    def get_constraint_summary(self) -> Dict[str, Any]:
        """获取约束条件统计摘要"""
        all_constraints = self.get_all_constraints()
        
        summary = {
            'total_count': sum(len(constraints) for constraints in all_constraints.values()),
            'categories': {}
        }
        
        for category, constraints in all_constraints.items():
            priority_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MUST': 0}
            active_count = 0
            
            for constraint in constraints:
                priority = constraint.get('priority', 'MEDIUM')
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
                
                # 检查是否在有效期内
                try:
                    start_date = constraint['time_period'].get('start_date', '')
                    end_date = constraint['time_period'].get('end_date', '')
                    if start_date and end_date:
                        start = datetime.strptime(start_date.split()[0], '%Y/%m/%d')
                        end = datetime.strptime(end_date.split()[0], '%Y/%m/%d')
                        now = datetime.now()
                        if start <= now <= end:
                            active_count += 1
                except:
                    pass
            
            summary['categories'][category] = {
                'total': len(constraints),
                'active': active_count,
                'priority_distribution': priority_counts
            }
        
        return summary

# 保持向后兼容性的别名
ConstraintParser = ConstraintDataLoader

if __name__ == "__main__":
    # 测试加载器
    loader = ConstraintDataLoader()
    summary = loader.get_constraint_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
