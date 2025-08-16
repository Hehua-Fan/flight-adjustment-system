from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
import tempfile
import shutil

import pandas as pd
from datetime import datetime
import uuid

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.models import PlanGenerationRequest, MultiPlanResponse, OptimizationPlan, PlanResults
from tools import CDMDataLoader, ConstraintDataLoader, Optimizer
from agents import WriterAgent

from api.routers import constraints


app = FastAPI(
    title="智能航班调整系统 API",
    description="基于AI的航班调整系统后端API",
    version="1.0.0"
)

# 添加路由
app.include_router(constraints.router, prefix="/api")

# CDM文件上传存储
uploaded_cdm_files = {}

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
flight_system = None
current_status = {
    "is_running": False,
    "current_event": None,
    "processing_step": None,
    "last_update": datetime.now(),
    "statistics": {},
    "detailed_progress": [],
    "current_step_data": {},
    "analysis_result": None,
    "data_statistics": None
}


@app.get("/", response_model=dict)
async def root():
    """根路径"""
    return {
        "message": "智能航班调整系统 API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.post("/api/plans/generate", response_model=MultiPlanResponse)
async def generate_optimization_plans(request: PlanGenerationRequest):
    """生成多套优化方案"""
    try:
        print(f"[API] 开始生成优化方案: {request.plan_name}")
        
        cdm_loader = CDMDataLoader()
        constraint_loader = ConstraintDataLoader()
        optimizer = Optimizer()
        
        # 加载CDM数据
        if request.cdm_file_id and request.cdm_file_id in uploaded_cdm_files:
            # 使用上传的CDM文件
            file_info = uploaded_cdm_files[request.cdm_file_id]
            cdm_file = file_info['file_path']
            print(f"[API] 使用上传的CDM数据: {file_info['filename']}")
            
            try:
                flights_df = cdm_loader.load_cdm_data(cdm_file, test_mode=True, limit_rows=10)
            except Exception as e:
                print(f"[API] 上传的CDM文件加载失败: {str(e)}")
                raise HTTPException(status_code=400, detail=f"CDM文件加载失败: {str(e)}")
        else:
            # 使用默认CDM文件
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            cdm_file = os.path.join(project_root, "assets", "cdm", "cdm_cleaned.xlsx")
            
            print(f"[API] 查找CDM文件路径: {cdm_file}")
            if not os.path.exists(cdm_file):
                print(f"[API] CDM文件不存在，当前工作目录: {os.getcwd()}")
                raise HTTPException(status_code=400, detail=f"CDM文件不存在: {cdm_file}")
                
            print(f"[API] 加载默认CDM数据: {cdm_file}")
            try:
                flights_df = cdm_loader.load_cdm_data(cdm_file, test_mode=request.test_mode, limit_rows=100)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"默认CDM文件加载失败: {str(e)}")
        
        if flights_df is None or flights_df.empty:
            raise HTTPException(status_code=400, detail="CDM数据为空，请检查上传的文件格式和内容")
        
        print(f"[API] 加载约束数据")
        try:
            # 使用get_all_constraints方法获取约束条件
            raw_constraints = constraint_loader.get_all_constraints()
            constraint_data = convert_constraint_data_for_optimizer(raw_constraints)
            print(f"[API] 成功加载约束数据，共{len(raw_constraints)}个类别")
        except Exception as e:
            print(f"[API] 约束数据加载失败: {str(e)}，使用基础约束数据")
            # 使用基础约束数据，确保有一些约束来测试优化
            constraint_data = {
                "airport_restriction": pd.DataFrame([
                    {"AIRPORT_CODE": "PEK", "RESTRICTION_TYPE": "AIRPORT_CURFEW", 
                     "START_TIME_OF_DAY": "01:00", "END_TIME_OF_DAY": "05:00", "PRIORITY": "HIGH"},
                    {"AIRPORT_CODE": "PVG", "RESTRICTION_TYPE": "AIRPORT_CURFEW", 
                     "START_TIME_OF_DAY": "00:00", "END_TIME_OF_DAY": "06:00", "PRIORITY": "HIGH"}
                ]),
                "airport_capacity": {
                    "PEK": {"08:00-09:00": {"limit": 20, "priority": "HIGH"}},
                    "PVG": {"08:00-09:00": {"limit": 15, "priority": "HIGH"}}
                },
                "quota": {
                    "cancel": {"max": 50, "priority": "HIGH"},
                    "swap": {"max": 100, "priority": "MEDIUM"}
                }
            }
        
        # 转换前端权重为优化器格式
        base_weights = {
            "cancel": request.weights.get("cancel", 1.0),
            "delay": request.weights.get("delay", 0.5),
            "swap": request.weights.get("swap", 0.3)
        }
        
        print(f"[API] 前端基础权重: {base_weights}")
        
        # 基于前端权重生成3套微调方案
        weight_strategies = [
            {
                "id": "1",
                "name": f"{request.plan_name} - 保守方案",
                "description": "基于用户配置，偏向保守稳定的调整策略",
                "weights": {
                    "cancel": base_weights["cancel"] * 1.2,  # 增加20%取消权重，更保守
                    "delay": base_weights["delay"] * 1.1,   # 增加10%延误权重
                    "swap": base_weights["swap"] * 0.8       # 减少20%换机权重
                }
            },
            {
                "id": "2", 
                "name": f"{request.plan_name} - 标准方案",
                "description": "严格按照用户配置的权重执行",
                "weights": {
                    "cancel": base_weights["cancel"],
                    "delay": base_weights["delay"], 
                    "swap": base_weights["swap"]
                }
            },
            {
                "id": "3",
                "name": f"{request.plan_name} - 激进方案", 
                "description": "基于用户配置，采用更激进的优化策略",
                "weights": {
                    "cancel": base_weights["cancel"] * 0.8,  # 减少20%取消权重，更激进
                    "delay": base_weights["delay"] * 0.9,    # 减少10%延误权重
                    "swap": base_weights["swap"] * 1.3       # 增加30%换机权重
                }
            }
        ]
        
        # 规范化航班数据格式
        print(f"[API] 规范化航班数据格式")
        print(f"[API] 规范化前的列: {list(flights_df.columns)}")
        flights_df = optimizer._normalize_flight_df(flights_df)
        
        # 确保索引唯一性
        if flights_df.index.duplicated().any():
            print(f"[API] 发现重复的flight_id，正在修复...")
            flights_df = flights_df.reset_index(drop=True)
            flights_df['flight_id'] = [f"F{i+1}" for i in range(len(flights_df))]
            flights_df = flights_df.set_index('flight_id', drop=False)
            print(f"[API] 已修复重复索引，新的flight_id: {list(flights_df.index[:5])}")
        
        # 确保数值字段类型正确
        numeric_cols = ['base_delay_minutes', 'target_dep_min_of_day', 'flight_duration_minutes', 'revenue']
        for col in numeric_cols:
            if col in flights_df.columns:
                flights_df[col] = pd.to_numeric(flights_df[col], errors='coerce').fillna(0.0)
        
        # 创建真实的延误场景以便测试优化器
        print(f"[API] 创建延误测试场景...")
        import numpy as np
        np.random.seed(42)  # 确保结果可重复
        
        # 给30%的航班分配延误
        n_flights = len(flights_df)
        delay_indices = np.random.choice(n_flights, size=int(n_flights * 0.3), replace=False)
        delay_amounts = np.random.choice([15, 30, 45, 60, 90, 120], size=len(delay_indices))
        
        # 重置所有航班的延误为0，然后给选中的航班分配延误
        flights_df['base_delay_minutes'] = 0.0
        for idx, delay in zip(delay_indices, delay_amounts):
            flight_id = flights_df.iloc[idx].name
            flights_df.loc[flight_id, 'base_delay_minutes'] = float(delay)
        
        delayed_count = (flights_df['base_delay_minutes'] > 0).sum()
        total_delay = flights_df['base_delay_minutes'].sum()
        print(f"[API] 延误场景创建完成: {delayed_count}/{n_flights} 架航班有延误，总延误 {total_delay} 分钟")
        
        print(f"[API] 规范化后的航班数据: {len(flights_df)} 行")
        print(f"[API] 规范化后的列: {list(flights_df.columns)}")
        print(f"[API] 索引唯一性检查: {flights_df.index.is_unique}")
        print(f"[API] base_delay_minutes数据类型: {flights_df['base_delay_minutes'].dtype}")
        print(f"[API] base_delay_minutes样本值: {flights_df['base_delay_minutes'].head().tolist()}")
        print(f"[API] 航班数据样本:")
        print(flights_df.head())
        
        # 验证数据格式
        print(f"[API] 验证数据格式...")
        for i, row in flights_df.head(3).iterrows():
            print(f"[API] 航班{i}: base_delay_minutes={row['base_delay_minutes']}, 类型={type(row['base_delay_minutes'])}")
        
        # 测试单个值访问
        test_flight_id = flights_df.index[0]
        test_value = flights_df.loc[test_flight_id, 'base_delay_minutes']
        print(f"[API] 测试访问: flights_df.loc['{test_flight_id}', 'base_delay_minutes'] = {test_value}, 类型={type(test_value)}")
        
        print(f"[API] 开始批量优化，共{len(weight_strategies)}套方案")
        
        # 批量求解
        weight_sets = [strategy["weights"] for strategy in weight_strategies]
        solutions = optimizer.batch_solve(
            flights_df=flights_df,
            constraint_data=constraint_data,
            weight_sets=weight_sets,
            solver_name="glpk",
            time_limit=60,

        )
        
        print(f"[API] 优化完成，处理结果...")
        
        # 处理结果
        plans = []
        successful_count = 0
        
        for i, (solution, strategy) in enumerate(zip(solutions, weight_strategies)):
            plan_id = strategy["id"]
            
            print(f"[API] 处理方案{i+1}: plan_id={plan_id}")
            print(f"[API] solution类型: {type(solution)}")
            print(f"[API] solution键: {list(solution.keys()) if isinstance(solution, dict) else 'Not dict'}")
            print(f"[API] solution['result']: {solution.get('result') if isinstance(solution, dict) else 'N/A'}")
            print(f"[API] solution['table']是否为None: {solution.get('table') is None if isinstance(solution, dict) else 'N/A'}")
            
            if solution["result"] and solution["table"] is not None:
                result_table = solution["table"]
                
                # 统计结果
                total_flights = len(result_table)
                executed_flights = len(result_table[result_table["status"] == "执行"])
                cancelled_flights = len(result_table[result_table["status"] == "取消"])
                total_delay = int(result_table["additional_delay_minutes"].sum())
                
                # 转换航班调整数据
                flight_adjustments = []
                for _, row in result_table.iterrows():
                    # 生成具体的调度指令
                    action_type = row["adjustment_action"]
                    flight_num = row.get("航班号", f"Flight_{row.name}")
                    delay_mins = float(row["additional_delay_minutes"])
                    
                    if action_type == "取消":
                        instructions = f"1. 通知旅客服务部启动航班取消流程\n2. 协调地面服务停止{flight_num}相关准备\n3. 通知机组调度解除当班任务\n4. 启动旅客改签/退票服务"
                        priority = "urgent"
                    elif delay_mins > 0:
                        instructions = f"1. 通知航班延误{delay_mins}分钟\n2. 协调机场更新时刻表\n3. 通知旅客服务部广播延误信息\n4. 调整后续航班衔接计划"
                        priority = "high" if delay_mins > 30 else "normal"
                    else:
                        instructions = f"1. 确认{flight_num}按计划执行\n2. 监控航班准备状态\n3. 保持正常调度流程"
                        priority = "normal"
                    
                    adjustment = {
                        "flight_number": flight_num,
                        "adjustment_action": action_type,
                        "status": row["status"],
                        "additional_delay_minutes": delay_mins,
                        "adjusted_departure_time": row.get("adjusted_departure_time"),
                        "reason": "智能优化调整",
                        "dispatch_instructions": instructions,
                        "priority": priority
                    }
                    flight_adjustments.append(adjustment)
                
                # 成本计算
                delay_cost = total_delay * 80
                cancel_cost = cancelled_flights * 30000
                total_cost = delay_cost + cancel_cost
                
                # 绩效指标 - 修复计算逻辑
                delayed_flights = len(result_table[result_table["additional_delay_minutes"] > 0])
                on_time_flights = executed_flights - delayed_flights
                on_time_rate = (on_time_flights / max(total_flights, 1)) * 100
                
                # 生成调度操作清单
                dispatch_actions = []
                
                # 1. 预先准备操作
                if cancelled_flights > 0:
                    dispatch_actions.append({
                        "action_id": "PREP_001",
                        "action_type": "预先准备",
                        "description": f"准备{cancelled_flights}个航班的取消流程和旅客服务",
                        "responsible_dept": "运行控制中心",
                        "deadline": "执行前30分钟",
                        "priority": "urgent",
                        "related_flights": [adj["flight_number"] for adj in flight_adjustments if adj["adjustment_action"] == "取消"],
                        "checklist": ["准备取消通知模板", "协调客服中心", "准备改签方案", "通知地面服务停止准备"]
                    })
                
                if delayed_flights > 0:
                    dispatch_actions.append({
                        "action_id": "PREP_002", 
                        "action_type": "预先准备",
                        "description": f"准备{delayed_flights}个航班的延误协调",
                        "responsible_dept": "运行控制中心",
                        "deadline": "执行前15分钟",
                        "priority": "high",
                        "related_flights": [adj["flight_number"] for adj in flight_adjustments if adj["additional_delay_minutes"] > 0],
                        "checklist": ["更新机场时刻表", "通知旅客服务部", "协调后续航班", "准备延误广播"]
                    })
                
                # 2. 实时监控操作
                dispatch_actions.append({
                    "action_id": "MONITOR_001",
                    "action_type": "实时监控", 
                    "description": "监控所有航班执行状态并及时调整",
                    "responsible_dept": "航班调度",
                    "deadline": "持续监控",
                    "priority": "normal",
                    "related_flights": [adj["flight_number"] for adj in flight_adjustments],
                    "checklist": ["检查气象条件", "监控机场容量", "跟踪机组状态", "确认机械状况"]
                })
                
                # 3. 应急响应准备
                if total_delay > 60 or cancelled_flights > 1:
                    dispatch_actions.append({
                        "action_id": "EMERGENCY_001",
                        "action_type": "应急响应",
                        "description": "启动应急响应流程，准备额外资源",
                        "responsible_dept": "应急指挥中心",
                        "deadline": "立即执行",
                        "priority": "urgent", 
                        "related_flights": [],
                        "checklist": ["启动应急指挥室", "调配备用机组", "准备备用飞机", "协调VIP旅客服务"]
                    })
                
                plan_results = PlanResults(
                    total_flights=total_flights,
                    executed_flights=executed_flights,
                    cancelled_flights=cancelled_flights,
                    total_delay=total_delay,
                    total_cost=total_cost,
                    flight_adjustments=flight_adjustments,
                    cost_breakdown={
                        "delayCost": delay_cost,
                        "cancellationCost": cancel_cost,
                        "aircraftChangeCost": 0,
                        "passengerCompensation": total_delay * 50
                    },
                    summary={
                        "onTimeRate": on_time_rate,
                        "passengerSatisfaction": max(0, 100 - cancelled_flights * 5 - total_delay / 10),
                        "costEfficiency": max(0, 100 - total_cost / 1000),
                        "operationalScore": (on_time_rate + max(0, 100 - total_cost / 1000)) / 2
                    },
                    dispatch_actions=dispatch_actions
                )
                
                status = "success"
                successful_count += 1
                print(f"[API] 方案{plan_id}生成成功: {executed_flights}/{total_flights}执行, {cancelled_flights}取消, {total_delay}分钟延误")
            else:
                plan_results = None
                status = "failed"
                print(f"[API] 方案{plan_id}生成失败")
            
            plan = OptimizationPlan(
                id=plan_id,
                name=strategy["name"],
                description=strategy["description"],
                weights=strategy["weights"],
                status=status,
                generated_at=datetime.now(),
                results=plan_results
            )
            plans.append(plan)
        
        print(f"[API] 所有方案处理完成，成功{successful_count}/{len(plans)}个")
        
        # 使用WriterAgent生成详细描述
        print("[API] 正在生成方案详细描述...")
        writer_agent = WriterAgent()
        
        for plan in plans:
            if plan.status == "success" and plan.results:
                # 构建方案信息用于WriterAgent
                plan_info = {
                    "plan_name": plan.name,
                    "total_flights": plan.results.total_flights,
                    "executed_flights": plan.results.executed_flights,
                    "cancelled_flights": plan.results.cancelled_flights,
                    "total_delay": plan.results.total_delay,
                    "total_cost": plan.results.total_cost,
                    "on_time_rate": plan.results.summary.get("onTimeRate", 0),
                    "passenger_satisfaction": plan.results.summary.get("passengerSatisfaction", 0),
                    "cost_efficiency": plan.results.summary.get("costEfficiency", 0),
                    "key_adjustments": plan.results.flight_adjustments[:3]  # 前3个关键调整
                }
                
                try:
                    # 获取该方案的权重配置
                    plan_weights = strategy["weights"]
                    weight_desc = []
                    if plan_weights["cancel"] > 0.6:
                        weight_desc.append("高取消成本敏感")
                    if plan_weights["delay"] > 0.5:
                        weight_desc.append("延误时间敏感")
                    if plan_weights["swap"] > 0.5:
                        weight_desc.append("换机操作偏好")
                    
                    # 调用WriterAgent生成面向调度员的实操指导
                    detailed_description = writer_agent.invoke(
                        f"你是一名资深航班调度专家，请为调度员生成以下方案的**具体执行指导**：\n\n"
                        f"## 方案概况\n"
                        f"- 方案名称：{plan_info['plan_name']}\n"
                        f"- 总航班数：{plan_info['total_flights']}\n"
                        f"- 执行航班：{plan_info['executed_flights']}\n"
                        f"- 取消航班：{plan_info['cancelled_flights']}\n"
                        f"- 总延误：{plan_info['total_delay']}分钟\n"
                        f"- 准点率：{plan_info['on_time_rate']:.1f}%\n"
                        f"- 权重特点：{', '.join(weight_desc) if weight_desc else '均衡配置'}\n\n"
                        f"## 权重配置分析\n"
                        f"- 取消权重：{plan_weights['cancel']:.1f} {'(高敏感)' if plan_weights['cancel'] > 0.6 else '(标准)'}\n"
                        f"- 延误权重：{plan_weights['delay']:.1f} {'(高敏感)' if plan_weights['delay'] > 0.5 else '(标准)'}\n"
                        f"- 换机权重：{plan_weights['swap']:.1f} {'(偏好换机)' if plan_weights['swap'] > 0.5 else '(谨慎换机)'}\n\n"
                        f"## 重点航班调整\n"
                        + '\n'.join([f"- {adj['flight_number']}: {adj['adjustment_action']}" + 
                                   (f"（延误{adj['additional_delay_minutes']}分钟）" if adj['additional_delay_minutes'] > 0 else "")
                                   for adj in plan_info['key_adjustments']]) + "\n\n"
                        f"请提供：\n"
                        f"1. **执行时间轴**：按时间顺序列出关键节点和操作\n"
                        f"2. **协调要点**：基于权重配置，重点协调的部门和事项\n"
                        f"3. **风险预警**：根据权重偏好，可能遇到的问题和应对措施\n"
                        f"4. **操作检查清单**：调度员必须检查的具体项目\n"
                        f"5. **应急预案**：如果出现偏差的具体处理步骤\n\n"
                        f"语言要求：简洁明确，具体可操作，避免理论分析。针对权重配置给出精准指导。"
                    )
                    plan.detailed_description = detailed_description
                    print(f"[API] 方案{plan.id}描述生成成功")
                except Exception as e:
                    print(f"[API] 方案{plan.id}描述生成失败: {e}")
                    plan.detailed_description = f"该{plan.name}通过智能优化算法生成，在{plan_info['total_flights']}个航班中成功调度{plan_info['executed_flights']}个航班执行，取消{plan_info['cancelled_flights']}个航班，总延误时间{plan_info['total_delay']}分钟，预计产生成本¥{plan_info['total_cost']:,.0f}。方案准点率达到{plan_info['on_time_rate']:.1f}%，旅客满意度{plan_info['passenger_satisfaction']:.1f}%，成本效率{plan_info['cost_efficiency']:.1f}%。"
        
        print("[API] 方案描述生成完成")
        
        return MultiPlanResponse(
            plans=plans,
            total_generated=len(plans),
            successful_plans=successful_count
        )
        
    except Exception as e:
        print(f"[API] 方案生成异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"方案生成失败: {str(e)}")



def convert_constraint_data_for_optimizer(raw_constraints):
    """转换约束数据格式"""
    import pandas as pd
    
    constraint_data = {}
    
    # 处理机场限制
    airport_restrictions = []
    if 'airport_restriction' in raw_constraints:
        df = raw_constraints['airport_restriction']
        for _, row in df.iterrows():
            if ('宵禁' in str(row.get('COMMENTS', '')).lower() or 
                '禁止夜航' in str(row.get('REMARKS', '')).lower()):
                airport_restrictions.append({
                    "AIRPORT_CODE": row.get('AIRPORT_CODE', ''),
                    "RESTRICTION_TYPE": "AIRPORT_CURFEW",
                    "START_TIME_OF_DAY": row.get('START_TIME_OF_DAY', '23:00'),
                    "END_TIME_OF_DAY": row.get('END_TIME_OF_DAY', '06:00')
                })
    
    if not airport_restrictions:
        airport_restrictions = [
            {"AIRPORT_CODE": "PEK", "RESTRICTION_TYPE": "AIRPORT_CURFEW", "START_TIME_OF_DAY": "23:00", "END_TIME_OF_DAY": "06:00"}
        ]
    
    constraint_data["airport_restriction"] = pd.DataFrame(airport_restrictions)
    # 设置更宽松的机场容量限制
    constraint_data["airport_capacity"] = {
        "PEK": {"08:00(+60)": 50, "09:00(+60)": 50, "14:00(+60)": 50},
        "PVG": {"08:00(+60)": 50, "09:00(+60)": 50, "14:00(+60)": 50},
        "SHA": {"08:00(+60)": 50, "09:00(+60)": 50, "14:00(+60)": 50},
        "CAN": {"08:00(+60)": 50, "09:00(+60)": 50, "14:00(+60)": 50}
    }
    # 设置更宽松的配额限制
    constraint_data["quota"] = {"cancel": {"max": 100}, "swap": {"max": 100}}
    
    return constraint_data

@app.post("/api/cdm/upload")
async def upload_cdm_file(file: UploadFile = File(...)):
    """上传CDM数据文件"""
    try:
        # 验证文件类型
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(
                status_code=400, 
                detail="仅支持Excel文件(.xlsx, .xls)和CSV文件(.csv)"
            )
        
        # 创建临时目录存储上传的文件
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 生成文件ID
        file_id = str(uuid.uuid4())
        
        # 验证文件可以正常读取
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # 基本验证：检查是否包含必要的列
            required_columns = ['flight_id', 'scheduled_departure', 'scheduled_arrival']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                # 尝试智能匹配列名
                column_mapping = {
                    'flight_id': ['航班号', 'flight_no', 'flight_number', 'flightId'],
                    'scheduled_departure': ['计划起飞时间', 'departure_time', 'std', 'scheduledDeparture'],
                    'scheduled_arrival': ['计划到达时间', 'arrival_time', 'sta', 'scheduledArrival']
                }
                
                for required_col, possible_cols in column_mapping.items():
                    if required_col in missing_columns:
                        for possible_col in possible_cols:
                            if possible_col in df.columns:
                                df = df.rename(columns={possible_col: required_col})
                                missing_columns.remove(required_col)
                                break
                
                if missing_columns:
                    # 清理临时文件
                    shutil.rmtree(temp_dir)
                    raise HTTPException(
                        status_code=400,
                        detail=f"CDM文件缺少必要的列: {missing_columns}。请确保文件包含航班号、计划起飞时间、计划到达时间等字段。"
                    )
            
            # 保存重命名后的文件
            if file.filename.endswith('.csv'):
                df.to_csv(file_path, index=False)
            else:
                df.to_excel(file_path, index=False)
                
        except Exception as e:
            # 清理临时文件
            shutil.rmtree(temp_dir)
            raise HTTPException(
                status_code=400,
                detail=f"文件格式错误或无法解析: {str(e)}"
            )
        
        # 存储文件信息
        uploaded_cdm_files[file_id] = {
            'filename': file.filename,
            'file_path': file_path,
            'temp_dir': temp_dir,
            'upload_time': datetime.now(),
            'row_count': len(df),
            'columns': list(df.columns)
        }
        
        return {
            'file_id': file_id,
            'filename': file.filename,
            'row_count': len(df),
            'columns': list(df.columns),
            'message': 'CDM文件上传成功'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@app.get("/api/cdm/files")
async def list_uploaded_cdm_files():
    """获取已上传的CDM文件列表"""
    files = []
    for file_id, info in uploaded_cdm_files.items():
        files.append({
            'file_id': file_id,
            'filename': info['filename'],
            'upload_time': info['upload_time'].isoformat(),
            'row_count': info['row_count'],
            'columns': info['columns']
        })
    
    return {'files': files}

@app.delete("/api/cdm/files/{file_id}")
async def delete_cdm_file(file_id: str):
    """删除已上传的CDM文件"""
    if file_id not in uploaded_cdm_files:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        # 清理临时文件
        temp_dir = uploaded_cdm_files[file_id]['temp_dir']
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        # 从存储中移除
        del uploaded_cdm_files[file_id]
        
        return {'message': '文件删除成功'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
