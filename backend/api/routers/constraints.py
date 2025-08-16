"""
约束条件相关的API路由 - 简化版本
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

try:
    from tools import ConstraintDataLoader
    constraint_parser = ConstraintDataLoader()
except ImportError:
    print("[约束路由警告]: 无法导入约束数据加载器，约束API将不可用")
    constraint_parser = None

router = APIRouter(prefix="/constraints", tags=["constraints"])

def flatten_constraints():
    """将所有约束条件扁平化为统一格式"""
    if constraint_parser is None:
        return []
    
    try:
        all_constraints = constraint_parser.get_all_constraints()
        flattened = []
        
        for category_key, constraints in all_constraints.items():
            # 映射类别名称
            category_map = {
                'airport_restrictions': '机场限制',
                'airport_special_requirements': '机场特殊要求',
                'flight_restrictions': '航班限制', 
                'flight_special_requirements': '航班特殊要求',
                'sector_special_requirements': '航路特殊要求'
            }
            
            category_name = category_map.get(category_key, category_key)
            
            for constraint in constraints:
                flattened_item = {
                    'id': constraint.get('id'),
                    'name': constraint.get('name', ''),
                    'category': category_name,
                    'category_key': category_key,
                    'priority': constraint.get('priority', ''),
                    'description': constraint.get('description', ''),
                    'remarks': constraint.get('remarks', ''),
                    'airport_code': constraint.get('airport_code', ''),
                    'carrier_code': constraint.get('carrier_code', ''),
                    'flight_number': constraint.get('flight_number', ''),
                    'time_period': constraint.get('time_period', {}),
                    'last_modified': constraint.get('last_modified', '')
                }
                flattened.append(flattened_item)
        
        return flattened
    except Exception as e:
        print(f"扁平化约束条件时出错: {e}")
        return []

@router.get("")
async def get_constraints(
    category: Optional[str] = Query(None, description="约束类别: 机场限制, 机场特殊要求, 航班限制, 航班特殊要求, 航路特殊要求"),
    priority: Optional[str] = Query(None, description="优先级: HIGH, MEDIUM, LOW, MUST"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量")
):
    """获取约束条件列表"""
    if constraint_parser is None:
        raise HTTPException(status_code=503, detail="约束解析器不可用")
    
    try:
        # 获取扁平化的约束条件
        all_constraints = flatten_constraints()
        
        # 应用筛选
        filtered_constraints = all_constraints
        
        if category:
            filtered_constraints = [c for c in filtered_constraints if c['category'] == category]
        
        if priority:
            filtered_constraints = [c for c in filtered_constraints if c['priority'].upper() == priority.upper()]
        
        if search:
            search_lower = search.lower()
            filtered_constraints = [
                c for c in filtered_constraints 
                if (search_lower in c['name'].lower() or
                    search_lower in c['description'].lower() or 
                    search_lower in c['remarks'].lower() or
                    search_lower in (c['airport_code'] or '').lower() or
                    search_lower in (c['carrier_code'] or '').lower() or
                    search_lower in (c['flight_number'] or '').lower())
            ]
        
        # 分页
        total = len(filtered_constraints)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_constraints = filtered_constraints[start_idx:end_idx]
        
        return {
            "data": paginated_constraints,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取约束条件失败: {str(e)}")

@router.get("/categories")
async def get_categories():
    """获取约束条件类别统计"""
    if constraint_parser is None:
        raise HTTPException(status_code=503, detail="约束解析器不可用")
    
    try:
        all_constraints = flatten_constraints()
        
        # 统计各类别数量
        category_stats = {}
        for constraint in all_constraints:
            category = constraint['category']
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1
        
        # 统计优先级分布
        priority_stats = {}
        for constraint in all_constraints:
            priority = constraint['priority']
            if priority not in priority_stats:
                priority_stats[priority] = 0
            priority_stats[priority] += 1
        
        return {
            "total": len(all_constraints),
            "categories": category_stats,
            "priorities": priority_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取类别统计失败: {str(e)}")
