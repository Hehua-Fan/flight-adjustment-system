"""
真实数据演示示例
展示如何使用CSV中的真实约束数据替代mock数据进行航班调整
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from src.types.flight_models import (
    Flight, Aircraft, Crew, Airport, OperationalContext, 
    CrewMember, FlightStatus, AdjustmentAction
)
from src.modules.Engine import *
from src.modules.Checker import ConstraintChecker
from src.utils.DataLoader import DataLoader
import json


def create_sample_data():
    """创建示例数据"""
    # 创建机场
    airports = {
        "PEK": Airport(code="PEK", name="北京首都国际机场", timezone="Asia/Shanghai", 
                      is_high_altitude=False,
                      curfew_start="00:00", curfew_end="06:00",
                      customs_hours=("07:00", "23:00")),
        "PVG": Airport(code="PVG", name="上海浦东国际机场", timezone="Asia/Shanghai",
                      is_high_altitude=False,
                      curfew_start="00:00", curfew_end="06:00",
                      customs_hours=("06:00", "24:00")),
        "CAN": Airport(code="CAN", name="广州白云国际机场", timezone="Asia/Shanghai",
                      is_high_altitude=False,
                      curfew_start="01:00", curfew_end="06:00",
                      customs_hours=("06:30", "23:30")),
        "URC": Airport(code="URC", name="乌鲁木齐地窝堡国际机场", timezone="Asia/Shanghai",
                      is_high_altitude=False,
                      curfew_start="02:00", curfew_end="07:00",
                      customs_hours=("08:00", "22:00")),
        "KGT": Airport(code="KGT", name="康定机场", timezone="Asia/Shanghai",
                      is_high_altitude=True,
                      curfew_start="22:00", curfew_end="07:00",
                      customs_hours=("08:00", "18:00"))
    }
    
    # 创建飞机
    aircrafts = {
        "B-1234": Aircraft(registration="B-1234", aircraft_type="A320", 
                          seat_capacity=180, fuel_capacity=24500.0, current_airport="PEK",
                          special_config={"high_altitude": False, "life_raft": False},
                          fault_reserves=[]),
        "B-5678": Aircraft(registration="B-5678", aircraft_type="A330", 
                          seat_capacity=250, fuel_capacity=139090.0, current_airport="PEK",
                          special_config={"high_altitude": True, "life_raft": True},
                          fault_reserves=[]),
        "B-9999": Aircraft(registration="B-9999", aircraft_type="B737", 
                          seat_capacity=160, fuel_capacity=20700.0, current_airport="PEK",
                          special_config={"high_altitude": True, "life_raft": False},
                          fault_reserves=["APU故障"])
    }
    
    # 创建机组
    captain = CrewMember(crew_id="CAPT001", name="张机长", position="机长", 
                        current_location="PEK",
                        max_duty_hours=14, duty_start=datetime.now() - timedelta(hours=2))
    copilot = CrewMember(crew_id="FO001", name="李副驾驶", position="副驾驶", 
                        current_location="PEK",
                        max_duty_hours=14, duty_start=datetime.now() - timedelta(hours=2))
    
    crews = {
        "CREW001": Crew(crew_id="CREW001", captain=captain, first_officer=copilot, 
                       cabin_crew=[], qualified_aircraft_types=["A320", "A330"])
    }
    
    return airports, aircrafts, crews


def demo_real_data_constraints():
    """演示使用真实数据进行约束检查"""
    print("🛫 航班调整引擎 - 真实数据约束检查演示")
    print("=" * 60)
    
    # 1. 加载真实数据
    print("\n📊 第一步：加载真实约束数据")
    print("-" * 40)
    
    data_loader = DataLoader("assets/运行优化数据")
    try:
        data_loader.load_all_data()
        
        # 显示数据统计
        stats = data_loader.get_statistics()
        print(f"\n📈 数据统计:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for k, v in value.items():
                    print(f"     └── {k}: {v}")
            else:
                print(f"   └── {key}: {value}")
                
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        print("📝 提示: 请确保 '运行优化数据' 目录中有所需的CSV文件")
        return
    
    # 2. 创建基础数据
    print(f"\n🏗️ 第二步：创建基础数据（机场、飞机、机组）")
    print("-" * 40)
    
    airports, aircrafts, crews = create_sample_data()
    print(f"✅ 创建了 {len(airports)} 个机场、{len(aircrafts)} 架飞机、{len(crews)} 个机组")
    
    # 3. 创建真实数据约束检查器
    print(f"\n🔍 第三步：创建真实数据约束检查器")
    print("-" * 40)
    
    real_checker = ConstraintChecker(airports, aircrafts, crews, data_loader)
    print("✅ 真实数据约束检查器创建完成")
    
    # 4. 创建测试航班
    print(f"\n✈️ 第四步：创建测试航班")
    print("-" * 40)
    
    # 测试多个真实航段
    test_flights = [
        {
            "flight_number": "CA123",
            "departure_airport": "PEK",
            "arrival_airport": "PVG", 
            "departure_time": datetime.now() + timedelta(hours=2),
            "description": "北京-上海 常规航线"
        },
        {
            "flight_number": "CA456", 
            "departure_airport": "PEK",
            "arrival_airport": "URC",
            "departure_time": datetime.now() + timedelta(hours=1),
            "description": "北京-乌鲁木齐 特殊要求航线"
        },
        {
            "flight_number": "CA789",
            "departure_airport": "CTU", 
            "arrival_airport": "KGT",
            "departure_time": datetime.now() + timedelta(hours=3),
            "description": "成都-康定 高原机场"
        }
    ]
    
    # 5. 逐一测试航班约束
    for i, flight_info in enumerate(test_flights, 1):
        print(f"\n🧪 测试 {i}: {flight_info['description']}")
        print("-" * 40)
        
        # 创建航班对象
        flight = Flight(
            flight_no=flight_info["flight_number"],
            departure_airport=flight_info["departure_airport"],
            arrival_airport=flight_info["arrival_airport"],
            scheduled_departure=flight_info["departure_time"],
            scheduled_arrival=flight_info["departure_time"] + timedelta(hours=2),
            aircraft_registration="B-1234",
            crew_id="CREW001",
            aircraft_type="A320",
            passenger_count=150,
            status=FlightStatus.SCHEDULED,
            is_international=False
        )
        
        print(f"   航班: {flight.flight_no}")
        print(f"   航段: {flight.departure_airport} → {flight.arrival_airport}")
        print(f"   时间: {flight.scheduled_departure.strftime('%H:%M')}")
        
        # 获取约束摘要
        constraint_summary = real_checker.get_constraint_summary(flight, flight.scheduled_departure)
        
        print(f"\n📋 约束摘要:")
        print(f"   └── 约束统计: {constraint_summary['约束统计']}")
        
        if constraint_summary['强制约束']:
            print(f"   └── 强制约束 (前5个):")
            for constraint in constraint_summary['强制约束'][:5]:
                print(f"       • {constraint}")
        else:
            print(f"   └── 强制约束: 无")
        
        # 测试时间变更约束检查
        print(f"\n⏰ 测试时间变更约束 (延误30分钟):")
        new_departure = flight.scheduled_departure + timedelta(minutes=30)
        
        context = OperationalContext(
            current_time=datetime.now(),
            weather_conditions={"visibility": "5000", "wind_speed": "15"},
            atc_restrictions={"flow_control": False, "slot_available": True},
            airport_closures=[],
            runway_closures={},
            flow_control={}
        )
        
        is_valid, violations = real_checker.check_time_change_constraints(flight, new_departure, context)
        
        print(f"   结果: {'✅ 通过' if is_valid else '❌ 违反约束'}")
        if violations:
            print(f"   违反的约束:")
            for violation in violations[:3]:  # 只显示前3个
                print(f"     • {violation}")
            if len(violations) > 3:
                print(f"     • ... 还有 {len(violations) - 3} 个约束")
        
        # 测试飞机变更约束检查
        print(f"\n🛩️ 测试飞机变更约束 (B-1234 → B-5678):")
        is_valid, violations = real_checker.check_aircraft_change_constraints(flight, "B-5678", context)
        
        print(f"   结果: {'✅ 通过' if is_valid else '❌ 违反约束'}")
        if violations:
            print(f"   违反的约束:")
            for violation in violations[:3]:
                print(f"     • {violation}")
            if len(violations) > 3:
                print(f"     • ... 还有 {len(violations) - 3} 个约束")
    
    # 6. 对比Mock数据和真实数据
    print(f"\n📊 第六步：Mock数据 vs 真实数据对比")
    print("=" * 60)
    
    print("🔹 Mock数据特点:")
    print("   • 硬编码约束规则")
    print("   • 简化的宵禁检查")
    print("   • 假设性的机型限制")
    print("   • 静态的约束条件")
    
    print("\n🔸 真实数据优势:")
    print("   • 2,389条真实约束记录")
    print("   • 实际的机场宵禁时间")
    print("   • 真实的航班特殊要求")
    print("   • 动态的时间范围检查")
    print("   • 优先级分级管理")
    print("   • 详细的约束分类")
    
    # 7. 数据质量报告
    print(f"\n📈 第七步：数据质量报告")
    print("-" * 40)
    
    stats = data_loader.get_statistics()
    priority_dist = stats["优先级分布"]
    category_dist = stats["分类分布"]
    
    print("📊 优先级分布:")
    for priority, count in priority_dist.items():
        percentage = (count / stats["总约束数"]) * 100
        print(f"   └── {priority}: {count} 条 ({percentage:.1f}%)")
    
    print("\n📊 分类分布 (Top 5):")
    sorted_categories = sorted(category_dist.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_categories[:5]:
        percentage = (count / stats["总约束数"]) * 100
        print(f"   └── {category}: {count} 条 ({percentage:.1f}%)")
    
    print(f"\n🎯 总结:")
    print(f"✅ 成功加载并使用了 {stats['总约束数']} 条真实约束数据")
    print(f"✅ 替代了原有的Mock数据，提升了约束检查的准确性")
    print(f"✅ 支持动态时间范围检查和优先级管理")
    print(f"✅ 提供了详细的约束分类和说明信息")
    
    return data_loader, real_checker


def demonstrate_specific_constraints():
    """演示特定的真实约束案例"""
    print(f"\n🔍 特定约束案例演示")
    print("=" * 60)
    
    # 重新加载数据
    data_loader = DataLoader("assets/运行优化数据")
    data_loader.load_all_data()
    
    # 1. 乌鲁木齐机场冬季特殊要求
    print("📍 案例1: 乌鲁木齐机场冬季运行限制")
    print("-" * 40)
    
    check_time = datetime(2024, 12, 15, 14, 30)  # 冬季时间
    urc_requirements = data_loader.get_airport_special_requirements("URC", check_time)
    
    print(f"时间: {check_time.strftime('%Y年%m月%d日 %H:%M')}")
    print(f"找到 {len(urc_requirements)} 条URC机场特殊要求:")
    
    for req in urc_requirements[:3]:  # 显示前3条
        print(f"   • 优先级: {req.priority.value}")
        print(f"     要求: {req.comments}")
        print(f"     生效期: {req.start_date.strftime('%Y/%m/%d')} - {req.end_date.strftime('%Y/%m/%d')}")
        print()
    
    # 2. 机场宵禁限制
    print("📍 案例2: 机场宵禁限制检查")
    print("-" * 40)
    
    # 测试深夜时间的宵禁
    night_time = datetime(2024, 12, 15, 1, 30)  # 凌晨1:30
    
    airports_to_check = ["BPX", "LZY", "DDR"]
    for airport in airports_to_check:
        curfew_restrictions = data_loader.get_airport_curfew_restrictions(airport, night_time)
        if curfew_restrictions:
            print(f"   {airport} 机场宵禁:")
            for restriction in curfew_restrictions[:1]:  # 只显示第一条
                start_time = restriction.start_time_of_day.strftime("%H:%M")
                end_time = restriction.end_time_of_day.strftime("%H:%M")
                print(f"     • 时间: {start_time} - {end_time}")
                print(f"     • 说明: {restriction.remarks}")
        else:
            print(f"   {airport} 机场: 无宵禁限制")
    
    # 3. 航班特殊要求
    print(f"\n📍 案例3: 航班特殊要求 (湿租航班)")
    print("-" * 40)
    
    # CA1201 湿租航班要求
    check_time = datetime(2024, 12, 15, 10, 0)
    flight_reqs = data_loader.get_flight_special_requirements("1201", "CA", "PEK", "XIY", check_time)
    
    if flight_reqs:
        print(f"CA1201 航班特殊要求:")
        for req in flight_reqs:
            print(f"   • 分类: {req.category.value}")
            print(f"   • 要求: {req.comments}")
            print(f"   • 备注: {req.remarks}")
    else:
        print("未找到CA1201航班的特殊要求")
    
    # 4. 扇区跨水运行要求
    print(f"\n📍 案例4: 扇区跨水运行要求")
    print("-" * 40)
    
    # 查找跨水运行要求
    all_sector_reqs = data_loader.sector_special_requirements
    watercross_reqs = [req for req in all_sector_reqs if req.category.value == "WATERCROSS"]
    
    print(f"找到 {len(watercross_reqs)} 条跨水运行要求:")
    for req in watercross_reqs[:3]:  # 显示前3条
        print(f"   • 航段: {req.departure_airport} → {req.arrival_airport}")
        print(f"   • 要求: {req.comments}")
        print()


if __name__ == "__main__":
    # 运行主演示
    data_loader, real_checker = demo_real_data_constraints()
    
    # 运行特定案例演示
    demonstrate_specific_constraints()
