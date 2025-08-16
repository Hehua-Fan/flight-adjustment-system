import pandas as pd
from datetime import datetime, timedelta

class CDMDataLoader:
    """CDM数据加载器类 - 负责从CDM文件加载航班数据"""
    
    def __init__(self):
        """初始化CDM数据加载器"""
        pass
    
    def load_cdm_data(self, file_path: str, test_mode: bool = False, limit_rows: int = 1000):
        """
        加载并预处理CDM数据文件
        
        Args:
            file_path: CDM数据文件路径
            test_mode: 是否启用测试模式
            limit_rows: 测试模式下限制的行数，默认100行
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
        
        # 2. 测试模式：限制数据行数
        original_rows = len(flights_df)
        if test_mode and original_rows > limit_rows:
            flights_df = flights_df.head(limit_rows)
            print(f"⚡ 测试模式：数据已限制为前{limit_rows}行（原始数据: {original_rows}行）")
        
        # 3. 时间格式转换（使用原列名）
        time_cols = ['计划起飞时间', '预计起飞时间', 'CTOT', '预计落地时间']
        for col in time_cols:
            if col in flights_df.columns:
                flights_df[col] = pd.to_datetime(flights_df[col], errors='coerce')
        
        # 4. 标准化机场列名
        if '计划起飞机场' in flights_df.columns:
            flights_df['departure_airport'] = flights_df['计划起飞机场']
        if '计划落地机场' in flights_df.columns:
            flights_df['arrival_airport'] = flights_df['计划落地机场']
        
        # 5. 提取航空公司代码（如果需要用于约束匹配）
        if '航班号' in flights_df.columns:
            flights_df['carrier_code'] = flights_df['航班号'].str.extract(r'^([A-Z]{1,3})', expand=False)
            flights_df['carrier_code'] = flights_df['carrier_code'].fillna('CA')

        # 6. 计算飞行时长（如果相关列存在）
        if '预计落地时间' in flights_df.columns and '预计起飞时间' in flights_df.columns:
            flights_df['flight_duration_minutes'] = (flights_df['预计落地时间'] - flights_df['预计起飞时间']).dt.total_seconds() / 60
            # 对缺失值用平均值填充
            mean_duration = flights_df['flight_duration_minutes'].mean()
            if pd.notna(mean_duration):
                flights_df['flight_duration_minutes'] = flights_df['flight_duration_minutes'].fillna(mean_duration)
            else:
                flights_df['flight_duration_minutes'] = flights_df['flight_duration_minutes'].fillna(120)  # 默认2小时
        elif '计划飞行时长(分钟)' in flights_df.columns:
            flights_df['flight_duration_minutes'] = flights_df['计划飞行时长(分钟)'].fillna(120)
        else:
            flights_df['flight_duration_minutes'] = 120  # 默认2小时

        # 7. 估算航班收入（如果旅客数据存在）
        if '旅客人数(订座)' in flights_df.columns:
            AVG_TICKET_PRICE = 500 
            flights_df['revenue'] = flights_df['旅客人数(订座)'] * AVG_TICKET_PRICE
        else:
            flights_df['revenue'] = 75000  # 默认收入
        
        # 8. 确定目标起飞时间
        def get_target_departure_time(row):
            if 'CTOT' in flights_df.columns and pd.notna(row.get('CTOT')):
                return row['CTOT']
            if '预计起飞时间' in flights_df.columns and pd.notna(row.get('预计起飞时间')):
                return row['预计起飞时间']
            if '计划起飞时间' in flights_df.columns and pd.notna(row.get('计划起飞时间')):
                return row['计划起飞时间']
            return pd.NaT

        flights_df['target_departure_time'] = flights_df.apply(get_target_departure_time, axis=1)

        # 9. 计算目标到达时间
        def get_target_arrival_time(row):
            if pd.notna(row.get('target_departure_time')) and pd.notna(row.get('flight_duration_minutes')):
                return row['target_departure_time'] + timedelta(minutes=row['flight_duration_minutes'])
            elif '预计落地时间' in flights_df.columns and pd.notna(row.get('预计落地时间')):
                return row['预计落地时间']
            return pd.NaT
        
        flights_df['target_arrival_time'] = flights_df.apply(get_target_arrival_time, axis=1)
        
        # 10. 清理无效数据
        before_clean = len(flights_df)
        flights_df = flights_df.dropna(subset=['target_departure_time'])
        after_clean = len(flights_df)
        
        if before_clean != after_clean:
            print(f"清理无效数据: {before_clean} -> {after_clean} 条记录")
        
        print("CDM数据加载和预处理完毕。")
        print(flights_df.head())
        return flights_df
