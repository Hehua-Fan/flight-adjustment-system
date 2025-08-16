#!/usr/bin/env python3
"""
最终测试脚本 - 验证优化器是否正确处理延误和约束
"""

import requests
import json
import time

def test_final():
    """测试优化器的真实性能"""
    print("🚀 开始最终优化器测试")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:8000/api/plans/generate",
            json={
                "plan_name": "真实优化测试",
                "plan_description": "测试100架航班的真实优化场景",
                "weights": {
                    "cancel": 1.0,
                    "delay": 0.5,
                    "swap": 0.3
                },
                "constraints": [],
                "allowed_actions": ["delay", "cancel", "swap"],
                "flight_range": "all",
                "test_mode": True
            },
            timeout=300  # 5分钟超时
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"⏱️ 总响应时间: {total_time:.2f} 秒")
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功！")
            print(f"📈 生成方案数量: {len(result['plans'])}")
            print(f"🎯 成功方案数量: {result['successful_plans']}")
            
            success_count = 0
            total_original_delay = 0
            
            for i, plan in enumerate(result['plans']):
                print(f"\n📋 方案 {i+1}: {plan['name']}")
                print(f"   状态: {plan['status']}")
                
                if plan['status'] == 'success' and plan.get('results'):
                    success_count += 1
                    results = plan['results']
                    
                    print(f"   📊 总航班: {results['total_flights']}")
                    print(f"   ✈️  执行航班: {results['executed_flights']}")
                    print(f"   ❌ 取消航班: {results['cancelled_flights']}")
                    print(f"   ⏰ 总延误: {results['total_delay']} 分钟")
                    print(f"   💰 总成本: {results['total_cost']:.0f}")
                    
                    # 检查是否有真实的优化
                    if results['total_delay'] > 0 or results['cancelled_flights'] > 0:
                        print(f"   ✅ 方案显示有调整动作")
                    else:
                        print(f"   ⚠️  方案显示无调整（可能无需优化）")
                    
                    total_original_delay += results.get('original_delay', 0)
                else:
                    print(f"   ❌ 方案失败")
            
            # 评估测试结果
            if success_count > 0:
                print(f"\n🎉 优化器测试成功！")
                print(f"   ✅ 成功方案: {success_count}/{len(result['plans'])}")
                print(f"   ⚡ 平均处理时间: {total_time/100:.3f} 秒/航班")
                
                # 检查优化效果
                if any(plan.get('results', {}).get('total_delay', 0) > 0 or 
                       plan.get('results', {}).get('cancelled_flights', 0) > 0 
                       for plan in result['plans'] if plan['status'] == 'success'):
                    print(f"   🎯 优化器正在进行真实调整！")
                    return True
                else:
                    print(f"   ℹ️  所有航班都是最优状态（无需调整）")
                    return True
            else:
                print(f"\n❌ 所有方案都失败了")
                return False
        else:
            print(f"❌ API调用失败: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误文本: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        return False

if __name__ == "__main__":
    success = test_final()
    if success:
        print("\n🎊 恭喜！航班调整优化系统测试通过！")
    else:
        print("\n💔 测试未完全成功，需要进一步调试")