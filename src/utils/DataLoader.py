"""
智能数据加载器
参考 PyTorch 的 DataLoader 设计思路，提供智能的数据加载和自动类型识别功能
"""

import os
import pandas as pd
from typing import Dict, List, Optional, Any, Type, Union
from datetime import datetime
from .DataSet import (
    DataSet, AirportSpecialRequirementDataSet, AirportRestrictionDataSet,
    FlightRestrictionDataSet, FlightSpecialRequirementDataSet, 
    SectorSpecialRequirementDataSet
)
from ..types.constraint_models import (
    AirportSpecialRequirement, AirportRestriction, FlightRestriction,
    FlightSpecialRequirement, SectorSpecialRequirement,
    RestrictionType
)


class DatasetFactory:
    """数据集工厂类，用于根据文件名自动选择合适的 DataSet"""
    
    # 文件名到 DataSet 类的映射
    _dataset_mapping = {
        'airport_special_requirement': AirportSpecialRequirementDataSet,
        'airport_restriction': AirportRestrictionDataSet,
        'flight_restriction': FlightRestrictionDataSet,
        'flight_special_requirement': FlightSpecialRequirementDataSet,
        'sector_special_requirement': SectorSpecialRequirementDataSet,
    }
    
    @classmethod
    def create_dataset(cls, file_path: str):
        """
        根据文件路径自动创建对应的 DataSet
        
        Args:
            file_path: 文件路径
            
        Returns:
            对应的 DataSet 实例，如果无法识别则返回 None
        """
        file_name = os.path.basename(file_path).lower()
        
        # 去除文件扩展名
        if '.' in file_name:
            file_name = file_name.rsplit('.', 1)[0]
            
        # 查找匹配的数据集类型
        for key, dataset_class in cls._dataset_mapping.items():
            if key == file_name:  # 精确匹配
                return dataset_class(file_path)
                
        print(f"警告: 无法识别文件类型: {file_path} (文件名: {file_name})")
        return None
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的文件类型列表"""
        return list(cls._dataset_mapping.keys())


class DataLoader:
    """智能数据加载器"""
    
    def __init__(self, data_dir: str = "运行优化数据", auto_load: bool = True):
        """
        初始化数据加载器
        
        Args:
            data_dir: CSV文件所在目录，默认为"运行优化数据"
            auto_load: 是否自动加载所有数据，默认为 True
        """
        self.data_dir = data_dir
        self.datasets: Dict[str, DataSet] = {}
        self._cache: Dict[str, List[Any]] = {}
        
        if auto_load:
            self.auto_discover_and_load()
    
    def auto_discover_and_load(self) -> None:
        """自动发现并加载数据目录中的所有支持的文件"""
        if not os.path.exists(self.data_dir):
            print(f"❌ 数据目录不存在: {self.data_dir}")
            return
            
        print("🔍 自动发现数据文件...")
        
        # 扫描目录中的 CSV 文件
        csv_files = []
        for file_name in os.listdir(self.data_dir):
            if file_name.lower().endswith('.csv'):
                file_path = os.path.join(self.data_dir, file_name)
                csv_files.append(file_path)
        
        if not csv_files:
            print(f"❌ 在目录 {self.data_dir} 中未找到 CSV 文件")
            return
            
        print(f"📁 发现 {len(csv_files)} 个 CSV 文件")
        
                 # 自动加载每个文件
        loaded_count = 0
        for file_path in csv_files:
            dataset = DatasetFactory.create_dataset(file_path)
            if dataset is not None:
                try:
                    dataset.load_data()
                    dataset_key = self._get_dataset_key(dataset)
                    self.datasets[dataset_key] = dataset
                    loaded_count += 1
                    print(f"✅ 已加载: {os.path.basename(file_path)} ({len(dataset)} 条记录)")
                except Exception as e:
                    print(f"❌ 加载失败: {os.path.basename(file_path)} - {e}")
                    import traceback
                    traceback.print_exc()  # 显示详细错误信息
            else:
                print(f"⚠️  跳过未识别的文件: {os.path.basename(file_path)}")
        
        print(f"🎉 成功加载 {loaded_count} 个数据集")
        self._update_cache()
    
    def _get_dataset_key(self, dataset: DataSet) -> str:
        """根据数据集类型生成键名"""
        type_mapping = {
            'AirportSpecialRequirementDataSet': 'airport_special_requirements',
            'AirportRestrictionDataSet': 'airport_restrictions',
            'FlightRestrictionDataSet': 'flight_restrictions',
            'FlightSpecialRequirementDataSet': 'flight_special_requirements',
            'SectorSpecialRequirementDataSet': 'sector_special_requirements',
        }
        return type_mapping.get(dataset.__class__.__name__, 'unknown')
    
    def _update_cache(self) -> None:
        """更新缓存，提供向后兼容的接口"""
        self._cache.clear()
        for key, dataset in self.datasets.items():
            self._cache[key] = dataset.get_all_items()
    
    # 向后兼容的属性访问
    @property
    def airport_special_requirements(self) -> List[AirportSpecialRequirement]:
        return self._cache.get('airport_special_requirements', [])
    
    @property
    def airport_restrictions(self) -> List[AirportRestriction]:
        return self._cache.get('airport_restrictions', [])
    
    @property
    def flight_restrictions(self) -> List[FlightRestriction]:
        return self._cache.get('flight_restrictions', [])
    
    @property
    def flight_special_requirements(self) -> List[FlightSpecialRequirement]:
        return self._cache.get('flight_special_requirements', [])
    
    @property
    def sector_special_requirements(self) -> List[SectorSpecialRequirement]:
        return self._cache.get('sector_special_requirements', [])
        
    def load_all_data(self) -> None:
        """加载所有CSV数据（向后兼容方法）"""
        if not self.datasets:
            self.auto_discover_and_load()
        else:
            total_count = sum(len(dataset) for dataset in self.datasets.values())
            print(f"✅ 数据加载完成！总计加载 {total_count} 条约束记录")
            print(f"   ├── 机场特殊要求: {len(self.airport_special_requirements)} 条")
            print(f"   ├── 机场限制: {len(self.airport_restrictions)} 条")
            print(f"   ├── 航班限制: {len(self.flight_restrictions)} 条")
            print(f"   ├── 航班特殊要求: {len(self.flight_special_requirements)} 条")
            print(f"   └── 航段特殊要求: {len(self.sector_special_requirements)} 条")
    
    def load_specific_dataset(self, file_path: str) -> Optional[DataSet]:
        """
        加载指定的数据文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            加载的数据集，如果失败则返回 None
        """
        dataset = DatasetFactory.create_dataset(file_path)
        if dataset:
            try:
                dataset.load_data()
                dataset_key = self._get_dataset_key(dataset)
                self.datasets[dataset_key] = dataset
                self._update_cache()
                print(f"✅ 成功加载: {os.path.basename(file_path)} ({len(dataset)} 条记录)")
                return dataset
            except Exception as e:
                print(f"❌ 加载失败: {os.path.basename(file_path)} - {e}")
        return None
    
    def get_dataset(self, dataset_type: str) -> Optional[DataSet]:
        """
        获取指定类型的数据集
        
        Args:
            dataset_type: 数据集类型
            
        Returns:
            对应的数据集
        """
        return self.datasets.get(dataset_type)
    
    def get_all_datasets(self) -> Dict[str, DataSet]:
        """获取所有数据集"""
        return self.datasets.copy()
    
    def filter_data(self, dataset_type: str, condition_func) -> List[Any]:
        """
        根据条件筛选指定类型的数据
        
        Args:
            dataset_type: 数据集类型
            condition_func: 筛选条件函数
            
        Returns:
            筛选后的数据列表
        """
        dataset = self.datasets.get(dataset_type)
        if dataset:
            return dataset.filter_by_condition(condition_func)
        return []

    # 向后兼容的加载方法 - 这些方法现在通过 auto_discover_and_load 自动处理
    def load_airport_special_requirements(self) -> None:
        """加载机场特殊要求数据（向后兼容）"""
        file_path = os.path.join(self.data_dir, "airport_special_requirement.csv")
        if os.path.exists(file_path):
            self.load_specific_dataset(file_path)

    def load_airport_restrictions(self) -> None:
        """加载机场限制数据（向后兼容）"""
        file_path = os.path.join(self.data_dir, "airport_restriction.csv")
        if os.path.exists(file_path):
            self.load_specific_dataset(file_path)

    def load_flight_restrictions(self) -> None:
        """加载航班限制数据（向后兼容）"""
        file_path = os.path.join(self.data_dir, "flight_restriction.csv")
        if os.path.exists(file_path):
            self.load_specific_dataset(file_path)

    def load_flight_special_requirements(self) -> None:
        """加载航班特殊要求数据（向后兼容）"""
        file_path = os.path.join(self.data_dir, "flight_special_requirement.csv")
        if os.path.exists(file_path):
            self.load_specific_dataset(file_path)

    def load_sector_special_requirements(self) -> None:
        """加载航段特殊要求数据（向后兼容）"""
        file_path = os.path.join(self.data_dir, "sector_special_requirement.csv")
        if os.path.exists(file_path):
            self.load_specific_dataset(file_path)

    def get_airport_curfew_restrictions(self, airport_code: str, check_time: datetime) -> List[AirportRestriction]:
        """获取指定机场在指定时间的宵禁限制"""
        restrictions = []
        for restriction in self.airport_restrictions:
            if (restriction.restriction_type == RestrictionType.AIRPORT_CURFEW and 
                restriction.airport_code == airport_code and 
                restriction.is_active(check_time)):
                restrictions.append(restriction)
        return restrictions

    def get_flight_restrictions(self, flight_no: str, carrier_code: str, 
                              dep_airport: str, arr_airport: Optional[str], 
                              check_time: datetime) -> List[FlightRestriction]:
        """获取指定航班的限制"""
        restrictions = []
        for restriction in self.flight_restrictions:
            if restriction.applies_to_flight(flight_no, carrier_code, dep_airport, arr_airport, check_time):
                restrictions.append(restriction)
        return restrictions

    def get_airport_special_requirements(self, airport_code: str, check_time: datetime) -> List[AirportSpecialRequirement]:
        """获取指定机场的特殊要求"""
        requirements = []
        for req in self.airport_special_requirements:
            if req.is_active(check_time, airport_code):
                requirements.append(req)
        return requirements

    def get_sector_special_requirements(self, dep_airport: str, arr_airport: str, 
                                      carrier_code: str, check_time: datetime) -> List[SectorSpecialRequirement]:
        """获取指定航段的特殊要求"""
        requirements = []
        for req in self.sector_special_requirements:
            if req.applies_to_sector(dep_airport, arr_airport, carrier_code, check_time):
                requirements.append(req)
        return requirements

    def get_flight_special_requirements(self, flight_no: str, carrier_code: str, 
                                      dep_airport: str, arr_airport: str, 
                                      check_time: datetime) -> List[FlightSpecialRequirement]:
        """获取指定航班的特殊要求"""
        requirements = []
        for req in self.flight_special_requirements:
            if req.applies_to_flight(flight_no, carrier_code, dep_airport, arr_airport, check_time):
                requirements.append(req)
        return requirements

    def get_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        # 基础统计
        stats = {
            "总约束数": sum(len(dataset) for dataset in self.datasets.values()),
            "机场特殊要求": len(self.airport_special_requirements),
            "机场限制": len(self.airport_restrictions),
            "航班限制": len(self.flight_restrictions),
            "航班特殊要求": len(self.flight_special_requirements),
            "航段特殊要求": len(self.sector_special_requirements),
            "数据集详情": {}
        }
        
        # 添加每个数据集的详细统计
        for key, dataset in self.datasets.items():
            dataset_stats = dataset.get_statistics()
            stats["数据集详情"][key] = dataset_stats
        
        # 计算优先级分布
        priority_dist = {}
        all_constraints = (
            self.airport_special_requirements + 
            self.airport_restrictions + 
            self.flight_restrictions + 
            self.flight_special_requirements + 
            self.sector_special_requirements
        )
        
        for constraint in all_constraints:
            if hasattr(constraint, 'priority'):
                priority_name = constraint.priority.value if hasattr(constraint.priority, 'value') else str(constraint.priority)
                priority_dist[priority_name] = priority_dist.get(priority_name, 0) + 1
        
        stats["优先级分布"] = priority_dist
        
        # 计算分类分布  
        category_dist = {}
        for constraint in all_constraints:
            if hasattr(constraint, 'category'):
                category_name = constraint.category.value if hasattr(constraint.category, 'value') else str(constraint.category)
                category_dist[category_name] = category_dist.get(category_name, 0) + 1
            elif hasattr(constraint, 'restriction_type'):
                # 对于没有category的约束，使用restriction_type
                type_name = constraint.restriction_type.value if hasattr(constraint.restriction_type, 'value') else str(constraint.restriction_type)
                category_dist[type_name] = category_dist.get(type_name, 0) + 1
        
        stats["分类分布"] = category_dist
            
        return stats
    
    def get_supported_file_types(self) -> List[str]:
        """获取支持的文件类型"""
        return DatasetFactory.get_supported_types()
    
    def reload_data(self) -> None:
        """重新加载所有数据"""
        self.datasets.clear()
        self._cache.clear()
        self.auto_discover_and_load()
    
    def add_custom_dataset(self, key: str, dataset: DataSet) -> None:
        """
        添加自定义数据集
        
        Args:
            key: 数据集键名
            dataset: 数据集实例
        """
        self.datasets[key] = dataset
        self._update_cache()
    
    def export_to_pandas(self, dataset_type: str) -> Optional[pd.DataFrame]:
        """
        将指定数据集导出为 pandas DataFrame
        
        Args:
            dataset_type: 数据集类型
            
        Returns:
            pandas DataFrame，如果数据集不存在则返回 None
        """
        dataset = self.datasets.get(dataset_type)
        if dataset and hasattr(dataset, 'data'):
            return dataset.data.copy()
        return None
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """获取所有数据集的基本信息"""
        info = {}
        for key, dataset in self.datasets.items():
            info[key] = {
                "类型": dataset.get_data_type().__name__,
                "文件路径": dataset.file_path,
                "记录数": len(dataset),
                "统计信息": dataset.get_statistics()
            }
        return info 