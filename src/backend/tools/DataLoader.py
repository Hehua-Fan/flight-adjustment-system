import pandas as pd
from datetime import datetime, timedelta
import os

class FlightDataLoader:
    """航班数据加载和预处理类"""
    
    def __init__(self):
        self.flights_df = None
        self.airport_res_df = None
        self.airport_special_req_df = None
        self.flight_restriction_df = None
        self.flight_special_req_df = None
        self.sector_special_req_df = None
        
        # 约束文件路径
        self.constraints_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets', 'restriction')


    def load_constraint_files(self):
        """加载所有约束文件"""
        print("正在加载约束文件...")
        
        try:
            # 1. 加载机场限制文件
            airport_restriction_path = os.path.join(self.constraints_path, 'airport_restriction.csv')
            self.airport_res_df = pd.read_csv(airport_restriction_path)
            print(f"✓ 机场限制: {len(self.airport_res_df)} 条记录")
            
            # 2. 加载机场特殊要求文件
            airport_special_path = os.path.join(self.constraints_path, 'airport_special_requirement.csv')
            self.airport_special_req_df = pd.read_csv(airport_special_path)
            print(f"✓ 机场特殊要求: {len(self.airport_special_req_df)} 条记录")
            
            # 3. 加载航班限制文件
            flight_restriction_path = os.path.join(self.constraints_path, 'flight_restriction.csv')
            self.flight_restriction_df = pd.read_csv(flight_restriction_path)
            print(f"✓ 航班限制: {len(self.flight_restriction_df)} 条记录")
            
            # 4. 加载航班特殊要求文件
            flight_special_path = os.path.join(self.constraints_path, 'flight_special_requirement.csv')
            self.flight_special_req_df = pd.read_csv(flight_special_path)
            print(f"✓ 航班特殊要求: {len(self.flight_special_req_df)} 条记录")
            
            # 5. 加载航段特殊要求文件
            sector_special_path = os.path.join(self.constraints_path, 'sector_special_requirement.csv')
            self.sector_special_req_df = pd.read_csv(sector_special_path)
            print(f"✓ 航段特殊要求: {len(self.sector_special_req_df)} 条记录")
            
        except FileNotFoundError as e:
            print(f"❌ 约束文件未找到: {e}")
            raise
        except Exception as e:
            print(f"❌ 读取约束文件出错: {e}")
            raise

    def preprocess_constraint_data(self):
        """预处理约束数据"""
        print("正在预处理约束数据...")
        
        # 预处理机场限制数据
        if self.airport_res_df is not None and not self.airport_res_df.empty:
            # 转换日期时间列
            for col in ['START_DATE', 'END_DATE']:
                if col in self.airport_res_df.columns:
                    self.airport_res_df[col] = pd.to_datetime(self.airport_res_df[col], format='%Y/%m/%d', errors='coerce')
            
            # 过滤当前有效的限制
            current_date = datetime.now().date()
            valid_restrictions = self.airport_res_df[
                (pd.to_datetime(self.airport_res_df['START_DATE']).dt.date <= current_date) &
                (pd.to_datetime(self.airport_res_df['END_DATE']).dt.date >= current_date)
            ]
            print(f"  过滤后当前有效的机场限制: {len(valid_restrictions)} 条")
            
        # 预处理航班限制数据
        if self.flight_restriction_df is not None and not self.flight_restriction_df.empty:
            for col in ['START_DATE', 'END_DATE']:
                if col in self.flight_restriction_df.columns:
                    self.flight_restriction_df[col] = pd.to_datetime(self.flight_restriction_df[col], format='%Y/%m/%d', errors='coerce')
        
        # 预处理其他约束数据的日期时间
        for df_name, df in [
            ('airport_special_req_df', self.airport_special_req_df),
            ('flight_special_req_df', self.flight_special_req_df),
            ('sector_special_req_df', self.sector_special_req_df)
        ]:
            if df is not None and not df.empty:
                for col in ['START_DATE', 'END_DATE']:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], format='%Y/%m/%d', errors='coerce')
        
        print("约束数据预处理完成")

    def load_flight_data(self):
        """加载航班数据"""
        print("正在加载航班数据...")
        
        # 尝试从多个位置加载航班数据
        flight_data_paths = [
            'flights_schedule.csv',  # 当前目录
            os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets', '航班调整记录', 'cdm数据.csv'),
        ]
        
        for path in flight_data_paths:
            if os.path.exists(path):
                try:
                    print(f"尝试加载航班数据: {path}")
                    self.flights_df = pd.read_csv(path)
                    print(f"✓ 航班数据加载成功: {len(self.flights_df)} 条记录")
                    break
                except Exception as e:
                    print(f"⚠️ 加载 {path} 失败: {e}")
                    continue
        
        if self.flights_df is None:
            print("❌ 未找到可用的航班数据文件")
            raise FileNotFoundError("未找到航班数据文件")

    def preprocess_flight_data(self):
        """预处理航班数据"""
        if self.flights_df is None:
            return
            
        print("正在预处理航班数据...")
        
        # 将字符串时间转换为datetime对象
        time_columns = ['planned_departure_time', 'planned_arrival_time']
        for col in time_columns:
            if col in self.flights_df.columns:
                self.flights_df[col] = pd.to_datetime(self.flights_df[col], errors='coerce')
        
        # 计算计划飞行时长（分钟）
        if 'planned_departure_time' in self.flights_df.columns and 'planned_arrival_time' in self.flights_df.columns:
            self.flights_df['flight_duration_minutes'] = (
                self.flights_df['planned_arrival_time'] - self.flights_df['planned_departure_time']
            ).dt.total_seconds() / 60
        
        # 清理无效数据
        self.flights_df = self.flights_df.dropna(subset=['planned_departure_time', 'planned_arrival_time'])
        
        print(f"✓ 航班数据预处理完成: {len(self.flights_df)} 条有效记录")

    def load_and_preprocess_data(self):
        """加载所有数据文件并进行预处理"""
        print("正在加载和预处理数据...")
        
        # 加载约束文件
        self.load_constraint_files()
        
        # 预处理约束数据
        self.preprocess_constraint_data()
        
        # 加载航班数据
        self.load_flight_data()
        
        # 预处理航班数据
        self.preprocess_flight_data()
        
        print("所有数据加载和预处理完成")
        
        return self.flights_df, self.airport_res_df

    def get_weight_strategies(self):
        """获取预定义的权重策略"""
        return {
            'cost_focused': {
                'cancel': 1.0,      # 取消权重最高
                'delay': 0.1,       # 延误权重较低
                'late_pax': 0.5,    # 旅客影响权重中等
                'revenue': 1.0      # 商委损失权重最高
            },
            'ops_focused': {
                'cancel': 0.5,      # 取消权重中等
                'delay': 1.0,       # 延误权重最高
                'late_pax': 1.0,    # 旅客影响权重最高
                'revenue': 0.2      # 商委损失权重较低
            },
            'balanced': {
                'cancel': 0.7,      # 取消权重较高
                'delay': 0.6,       # 延误权重中等
                'late_pax': 0.7,    # 旅客影响权重较高
                'revenue': 0.6      # 商委损失权重中等
            }
        }

    def get_weights_for_strategy(self, strategy='balanced'):
        """根据策略名称获取对应的权重配置"""
        strategies = self.get_weight_strategies()
        return strategies.get(strategy, strategies['balanced'])

    def process_optimization_results(self, model, result, flights_df):
        """
        处理优化求解结果并返回调整方案
        
        Args:
            model: 已求解的优化模型
            result: 求解器结果  
            flights_df: 航班数据DataFrame
            
        Returns:
            pandas.DataFrame: 航班调整结果，如果求解失败返回None
        """
        import pyomo.environ as pyo
        
        print("--- 处理求解结果 ---")
        
        if result is None:
            print("❌ 无法处理空的求解结果")
            return None
            
        if result.solver.termination_condition == pyo.TerminationCondition.optimal:
            print("✓ 找到最优解，正在提取结果...")
            
            # 创建结果DataFrame副本，避免修改原数据
            result_df = flights_df.copy()
            
            # 提取决策变量值
            result_df['is_operated'] = [pyo.value(model.x[f]) for f in model.flights]
            result_df['delay_minutes'] = [pyo.value(model.d[f]) for f in model.flights]
            result_df['is_late (>120min)'] = [pyo.value(model.l[f]) for f in model.flights]
            
            # 计算调整后的状态和时间
            result_df['status'] = result_df['is_operated'].apply(lambda x: '执行' if x > 0.5 else '取消')
            result_df['adjusted_departure_time'] = result_df.apply(
                lambda row: row['planned_departure_time'] + timedelta(minutes=row['delay_minutes']) if row['status'] == '执行' else pd.NaT,
                axis=1
            )
            result_df['adjusted_arrival_time'] = result_df.apply(
                lambda row: row['planned_arrival_time'] + timedelta(minutes=row['delay_minutes']) if row['status'] == '执行' else pd.NaT,
                axis=1
            )
            
            # 返回关键结果列
            final_result = result_df[['flight_number', 'status', 'delay_minutes', 'is_late (>120min)', 'adjusted_departure_time', 'adjusted_arrival_time']]
            
            print(f"✓ 结果处理完成，共{len(final_result)}个航班")
            return final_result
        else:
            print("❌ 未能找到最优解")
            return None

    def load_data(self):
        """
        加载数据的便捷方法
        
        Returns:
            tuple: (flights_df, airport_res_df)
        """
        return self.load_and_preprocess_data()

    def get_all_constraints(self):
        """获取所有约束数据"""
        return {
            'airport_restrictions': self.airport_res_df,
            'airport_special_requirements': self.airport_special_req_df,
            'flight_restrictions': self.flight_restriction_df,
            'flight_special_requirements': self.flight_special_req_df,
            'sector_special_requirements': self.sector_special_req_df
        }

    def get_active_airport_restrictions(self, airport_code=None):
        """获取活跃的机场限制
        
        Args:
            airport_code: 机场代码，如果指定则只返回该机场的限制
            
        Returns:
            DataFrame: 活跃的机场限制数据
        """
        if self.airport_res_df is None or self.airport_res_df.empty:
            return pd.DataFrame()
        
        # 过滤当前有效的限制
        current_date = datetime.now().date()
        valid_restrictions = self.airport_res_df[
            (pd.to_datetime(self.airport_res_df['START_DATE']).dt.date <= current_date) &
            (pd.to_datetime(self.airport_res_df['END_DATE']).dt.date >= current_date)
        ]
        
        if airport_code:
            valid_restrictions = valid_restrictions[valid_restrictions['AIRPORT_CODE'] == airport_code]
        
        return valid_restrictions

    def get_flight_specific_constraints(self, flight_number=None, departure_airport=None, arrival_airport=None):
        """获取特定航班相关的约束
        
        Args:
            flight_number: 航班号
            departure_airport: 出发机场
            arrival_airport: 到达机场
            
        Returns:
            dict: 相关约束数据
        """
        constraints = {}
        
        # 航班限制
        if self.flight_restriction_df is not None and not self.flight_restriction_df.empty:
            flight_restrictions = self.flight_restriction_df.copy()
            if flight_number:
                flight_restrictions = flight_restrictions[
                    flight_restrictions['FLIGHT_NUMBER'].astype(str).str.contains(str(flight_number), na=False)
                ]
            if departure_airport:
                flight_restrictions = flight_restrictions[
                    flight_restrictions['DEPARTURE_AIRPORT_CODE'] == departure_airport
                ]
            constraints['flight_restrictions'] = flight_restrictions
        
        # 航段特殊要求
        if self.sector_special_req_df is not None and not self.sector_special_req_df.empty:
            sector_special = self.sector_special_req_df.copy()
            if departure_airport and arrival_airport:
                sector_special = sector_special[
                    (sector_special['DEPARTURE_AIRPORT_CODE'] == departure_airport) &
                    (sector_special['ARRIVAL_AIRPORT_CODE'] == arrival_airport)
                ]
            constraints['sector_special_requirements'] = sector_special
        
        return constraints
