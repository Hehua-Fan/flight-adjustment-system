import pandas as pd
from datetime import datetime, timedelta
import os

class DataLoader:
    """数据加载器类 - 负责从不同来源加载数据"""
    
    def __init__(self):
        """初始化数据加载器"""
        pass
    
    def load_cdm_data(self, file_path: str):
        """
        加载并预处理CDM数据文件
        """
        
        # 1.读取数据
        try:
            if file_path.endswith('.csv'):
                flights_df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                flights_df = pd.read_excel(file_path)
            else:
                print(f"错误：不支持的文件类型 {file_path}。请确保文件是csv, xlsx, xls格式。")
                return None
        except FileNotFoundError:
            print(f"错误：无法找到文件 {file_path}。请确保文件名正确且文件与脚本在同一目录下。")
            return None
        
        # 3. 时间格式转换（使用原列名）
        time_cols = ['计划起飞时间', '预计起飞时间', 'CTOT', '预计落地时间']
        for col in time_cols:
            if col in flights_df.columns:
                flights_df[col] = pd.to_datetime(flights_df[col], errors='coerce')
        
        # 4. 提取航空公司代码（如果需要用于约束匹配）
        if '航班号' in flights_df.columns:
            flights_df['carrier_code'] = flights_df['航班号'].str.extract(r'^([A-Z]{1,3})', expand=False)
            flights_df['carrier_code'] = flights_df['carrier_code'].fillna('CA')

        # 5. 计算飞行时长（如果相关列存在）
        if '预计落地时间' in flights_df.columns and '预计起飞时间' in flights_df.columns:
            flights_df['flight_duration_minutes'] = (flights_df['预计落地时间'] - flights_df['预计起飞时间']).dt.total_seconds() / 60
            # 对缺失值用平均值填充
            mean_duration = flights_df['flight_duration_minutes'].mean()
            if pd.notna(mean_duration):
                flights_df['flight_duration_minutes'] = flights_df['flight_duration_minutes'].fillna(mean_duration)
            else:
                flights_df['flight_duration_minutes'] = flights_df['flight_duration_minutes'].fillna(120)  # 默认2小时

        # 6. 估算航班收入（如果旅客数据存在）
        if '旅客人数(订座)' in flights_df.columns:
            AVG_TICKET_PRICE = 500 
            flights_df['revenue'] = flights_df['旅客人数(订座)'] * AVG_TICKET_PRICE
        else:
            flights_df['revenue'] = 75000  # 默认收入
        
        # 7. 确定目标起飞时间
        def get_target_departure_time(row):
            if 'CTOT' in flights_df.columns and pd.notna(row.get('CTOT')):
                return row['CTOT']
            if '预计起飞时间' in flights_df.columns and pd.notna(row.get('预计起飞时间')):
                return row['预计起飞时间']
            if '计划起飞时间' in flights_df.columns and pd.notna(row.get('计划起飞时间')):
                return row['计划起飞时间']
            return pd.NaT

        flights_df['target_departure_time'] = flights_df.apply(get_target_departure_time, axis=1)

        # 8. 计算目标到达时间
        def get_target_arrival_time(row):
            if pd.notna(row.get('target_departure_time')) and pd.notna(row.get('flight_duration_minutes')):
                return row['target_departure_time'] + timedelta(minutes=row['flight_duration_minutes'])
            elif '预计落地时间' in flights_df.columns and pd.notna(row.get('预计落地时间')):
                return row['预计落地时间']
            return pd.NaT
        
        flights_df['target_arrival_time'] = flights_df.apply(get_target_arrival_time, axis=1)
        
        # 9. 清理无效数据
        before_clean = len(flights_df)
        flights_df = flights_df.dropna(subset=['target_departure_time'])
        after_clean = len(flights_df)
        
        if before_clean != after_clean:
            print(f"清理无效数据: {before_clean} -> {after_clean} 条记录")
        
        print("CDM数据加载和预处理完毕。")
        print(flights_df.head())
        return flights_df
    
    def load_constraint_data(self, constraint_dir_path: str, filter_active: bool = True):
        """
        加载所有5种约束数据文件，可选择是否过滤有效约束
        
        Args:
            constraint_dir_path: 约束文件所在目录路径
            filter_active: 是否过滤出当前有效的约束条件，默认为True
            current_date: 当前日期，默认为今天（仅在filter_active=True时使用）
            
        Returns:
            dict: 包含所有约束数据的字典
        """
        print(f"[DataLoader]: 正在从 {constraint_dir_path} 加载所有约束数据...")

        constraint_files = {
            "airport_restriction": "airport_restriction.csv",
            "airport_special_requirement": "airport_special_requirement.csv", 
            "flight_restriction": "flight_restriction.csv",
            "flight_special_requirement": "flight_special_requirement.csv",
            "sector_special_requirement": "sector_special_requirement.csv"
        }
        
        constraint_data = {}
        
        for key, filename in constraint_files.items():
            file_path = os.path.join(constraint_dir_path, filename)
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
        
        print("[DataLoader]: 约束数据加载完毕。")
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
        
        print("[DataLoader]: 正在过滤有效约束条件...")
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
                print(f"  [DataLoader]: {constraint_type} 过滤后有效约束: {len(active_df)}/{len(df)}")
        
        return filtered_data