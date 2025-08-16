"use client";

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Search,
  Filter,
  Clock,
  Loader2,
  RefreshCw,
  List,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';
import { AppLayout } from '@/components/AppLayout';

// 约束条件类型定义（简化版）
interface ConstraintItem {
  id: string;
  name: string;
  category: string;
  category_key: string;
  priority: string;
  description: string;
  remarks: string;
  airport_code?: string;
  carrier_code?: string;
  flight_number?: string;
  time_period: string | null;
  last_modified: string;
}

// API响应类型
interface ConstraintResponse {
  data: ConstraintItem[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

// 类别统计类型
interface CategoryStats {
  total: number;
  categories: { [key: string]: number };
  priorities: { [key: string]: number };
}

// API基础URL
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// 约束类别选项
const CATEGORIES = [
  '机场限制',
  '机场特殊要求', 
  '航班限制',
  '航班特殊要求',
  '航路特殊要求'
];

// 优先级选项
const PRIORITIES = ['HIGH', 'MEDIUM', 'LOW', 'MUST'];

// 机场选项（示例）
const AIRPORTS = [
  'PEK', 'PVG', 'CAN', 'CTU', 'KMG', 'XIY', 'WUH', 'CSX', 'TSN', 'NKG',
  'HGH', 'SJW', 'TAO', 'DLC', 'SHE', 'HAK', 'XMN', 'FOC', 'HFE', 'NNG'
];

// 列配置接口
interface ColumnConfig {
  key: string;
  title: string;
  width: string;
  sortable?: boolean;
}

// 列配置
const columns: ColumnConfig[] = [
  { key: 'select', title: '', width: 'w-12' },
  { key: 'name', title: '约束名称', width: 'w-48', sortable: true },
  { key: 'category', title: '类别', width: 'w-32', sortable: true },
  { key: 'priority', title: '优先级', width: 'w-24', sortable: true },
  { key: 'description', title: '描述', width: 'w-64' },
  { key: 'airport_code', title: '机场', width: 'w-20' },
  { key: 'carrier_code', title: '航司', width: 'w-20' },
  { key: 'flight_number', title: '航班号', width: 'w-24' },
  { key: 'last_modified', title: '最后修改', width: 'w-32' }
];

export default function ConstraintPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [airportFilter, setAirportFilter] = useState<string>('all');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<CategoryStats | null>(null);
  const [constraints, setConstraints] = useState<ConstraintItem[]>([]);
  const [selectedConstraints, setSelectedConstraints] = useState<Set<string>>(new Set());
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0
  });

  // 排序逻辑
  const sortedConstraints = useMemo(() => {
    if (!sortConfig) return constraints;

    return [...constraints].sort((a, b) => {
      const aValue = a[sortConfig.key as keyof ConstraintItem] || '';
      const bValue = b[sortConfig.key as keyof ConstraintItem] || '';

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [constraints, sortConfig]);

  // 处理排序
  const handleSort = (key: string) => {
    setSortConfig(prevConfig => {
      if (prevConfig?.key === key) {
        return {
          key,
          direction: prevConfig.direction === 'asc' ? 'desc' : 'asc'
        };
      }
      return { key, direction: 'asc' };
    });
  };

  // 处理选择
  const handleSelectConstraint = (constraintId: string, checked: boolean) => {
    setSelectedConstraints(prev => {
      const newSelected = new Set(prev);
      if (checked) {
        newSelected.add(constraintId);
      } else {
        newSelected.delete(constraintId);
      }
      return newSelected;
    });
  };

  // 全选/取消全选
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedConstraints(new Set(sortedConstraints.map(c => c.id)));
    } else {
      setSelectedConstraints(new Set());
    }
  };

  // 获取类别统计
  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/constraints/categories`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        throw new Error(`API请求失败: ${response.status}`);
      }
    } catch (error) {
      console.error('获取统计信息失败:', error);
      toast.error('获取统计信息失败，请检查后端服务是否启动');
    }
  };

  // 获取约束条件列表
  const fetchConstraints = useCallback(async (page: number = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '20'
      });
      
      if (categoryFilter && categoryFilter !== 'all') {
        params.append('category', categoryFilter);
      }
      
      if (priorityFilter && priorityFilter !== 'all') {
        params.append('priority', priorityFilter);
      }
      
      if (airportFilter && airportFilter !== 'all') {
        params.append('airport', airportFilter);
      }
      
      if (searchTerm.trim()) {
        params.append('search', searchTerm.trim());
      }

      const response = await fetch(`${API_BASE_URL}/constraints?${params}`);
      if (response.ok) {
        const data: ConstraintResponse = await response.json();
        setConstraints(data.data);
        setPagination(data.pagination);
      } else {
        throw new Error(`API请求失败: ${response.status}`);
      }
    } catch (error) {
      console.error('获取约束条件失败:', error);
      toast.error('获取约束条件失败，请检查后端服务是否启动');
      setConstraints([]);
      setPagination({
        page: 1,
        page_size: 20,
        total: 0,
        total_pages: 0
      });
    } finally {
      setLoading(false);
    }
  }, [categoryFilter, priorityFilter, airportFilter, searchTerm]);

  // 初始化加载数据
  useEffect(() => {
    fetchStats();
    fetchConstraints(1);
  }, [fetchConstraints]);

  // 当筛选条件变化时重新加载数据
  useEffect(() => {
    fetchConstraints(1);
  }, [fetchConstraints]);

  // 处理分页
  const handlePageChange = (page: number) => {
    fetchConstraints(page);
  };

  // 重置筛选
  const handleReset = () => {
    setSearchTerm('');
    setCategoryFilter('all');
    setPriorityFilter('all');
    setAirportFilter('all');
    setSelectedConstraints(new Set());
    setSortConfig(null);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'MUST': return 'bg-red-100 text-red-800';
      case 'HIGH': return 'bg-orange-100 text-orange-800';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800';
      case 'LOW': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityLabel = (priority: string) => {
    switch (priority) {
      case 'MUST': return '必须';
      case 'HIGH': return '高';
      case 'MEDIUM': return '中';
      case 'LOW': return '低';
      default: return '未知';
    }
  };

  return (
    <AppLayout>
      <div className="p-6">
          {/* Header区域 */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              {/* 机场筛选 */}
              <Select value={airportFilter} onValueChange={setAirportFilter}>
                <SelectTrigger className="w-[120px] bg-white">
                  <SelectValue placeholder="机场筛选" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有机场</SelectItem>
                  {AIRPORTS.map((airport) => (
                    <SelectItem key={airport} value={airport}>
                      {airport}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* 类别筛选 */}
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-[140px] bg-white">
                  <SelectValue placeholder="类别筛选" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有类别</SelectItem>
                  {CATEGORIES.map((category) => (
                    <SelectItem key={category} value={category}>
                      {category}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* 优先级筛选 */}
              <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                <SelectTrigger className="w-[120px] bg-white">
                  <SelectValue placeholder="优先级" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有优先级</SelectItem>
                  {PRIORITIES.map((priority) => (
                    <SelectItem key={priority} value={priority}>
                      {getPriorityLabel(priority)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button variant="outline" size="sm" onClick={handleReset}>
                <RefreshCw className="h-4 w-4 mr-2" />
                重置筛选
              </Button>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* 搜索框 */}
              <div className="relative w-[300px]">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="搜索约束名称、描述、机场代码等..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-white"
                />
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  fetchStats();
                  fetchConstraints(1);
                  toast.success('数据已刷新');
                }}
              >
                手动刷新
              </Button>
              
              {stats && (
                <p className="text-gray-500 text-sm">共 {stats.total} 条约束条件</p>
              )}
            </div>
          </div>

          {/* 统计卡片 */}
          <div className="grid grid-cols-5 gap-4 mb-6">
            {CATEGORIES.map((category, index) => {
              const count = stats?.categories[category] || 0;
              const colors = [
                'bg-blue-500',
                'bg-green-500', 
                'bg-yellow-500',
                'bg-purple-500',
                'bg-red-500'
              ];
              return (
                <Card key={category} className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className={`w-4 h-4 rounded-full ${colors[index % colors.length]}`} />
                    <div>
                      <p className="text-sm text-gray-600">{category}</p>
                      <p className="text-2xl font-bold">{count}</p>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>

          {/* 约束条件列表 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <List className="h-5 w-5" />
                  <span>约束条件列表</span>
                </div>
                <div className="flex items-center space-x-4">
                  {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                  <div className="text-sm text-gray-500">
                    {sortedConstraints.length} 条约束 • {selectedConstraints.size} 个已选择
                  </div>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-gray-200 bg-black">
                      {columns.map((column) => (
                        <th
                          key={column.key}
                          className={cn(
                            "px-3 py-2 text-left text-xs font-medium text-white uppercase tracking-wider",
                            column.width
                          )}
                        >
                          {column.key === 'select' ? (
                            <Checkbox
                              checked={sortedConstraints.length > 0 && selectedConstraints.size === sortedConstraints.length}
                              ref={(el) => {
                                if (el) {
                                  // @ts-expect-error - indeterminate property exists on input element
                                  el.indeterminate = selectedConstraints.size > 0 && selectedConstraints.size < sortedConstraints.length;
                                }
                              }}
                              onCheckedChange={handleSelectAll}
                            />
                          ) : (
                            <div
                              className={cn(
                                "flex items-center space-x-1",
                                column.sortable && "cursor-pointer hover:text-gray-200"
                              )}
                              onClick={() => column.sortable && handleSort(column.key)}
                            >
                              <span>{column.title}</span>
                              {column.sortable && sortConfig?.key === column.key && (
                                <span className="text-xs">
                                  {sortConfig.direction === 'asc' ? '↑' : '↓'}
                                </span>
                              )}
                            </div>
                          )}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {sortedConstraints.map((constraint) => (
                      <tr
                        key={constraint.id}
                        className={cn(
                          "hover:bg-gray-50 transition-colors",
                          selectedConstraints.has(constraint.id) && "bg-blue-50"
                        )}
                      >
                        {/* 选择框 */}
                        <td className="px-3 py-2">
                          <Checkbox
                            checked={selectedConstraints.has(constraint.id)}
                            onCheckedChange={(checked) => handleSelectConstraint(constraint.id, checked as boolean)}
                          />
                        </td>

                        {/* 约束名称 */}
                        <td className="px-3 py-2">
                          <div className="text-sm font-medium text-gray-900">{constraint.name}</div>
                        </td>

                        {/* 类别 */}
                        <td className="px-3 py-2">
                          <Badge variant="outline">{constraint.category}</Badge>
                        </td>

                        {/* 优先级 */}
                        <td className="px-3 py-2">
                          <Badge className={getPriorityColor(constraint.priority)}>
                            {getPriorityLabel(constraint.priority)}
                          </Badge>
                        </td>

                        {/* 描述 */}
                        <td className="px-3 py-2">
                          <div className="text-sm text-gray-600 truncate max-w-64" title={constraint.description || constraint.remarks || '暂无描述'}>
                            {constraint.description || constraint.remarks || '暂无描述'}
                          </div>
                        </td>

                        {/* 机场 */}
                        <td className="px-3 py-2 text-sm text-gray-900">
                          {constraint.airport_code || '-'}
                        </td>

                        {/* 航司 */}
                        <td className="px-3 py-2 text-sm text-gray-900">
                          {constraint.carrier_code || '-'}
                        </td>

                        {/* 航班号 */}
                        <td className="px-3 py-2 text-sm text-gray-900">
                          {constraint.flight_number || '-'}
                        </td>

                        {/* 最后修改 */}
                        <td className="px-3 py-2 text-sm text-gray-500">
                          {constraint.last_modified ? (
                            <div className="flex items-center">
                              <Clock className="h-3 w-3 mr-1" />
                              {constraint.last_modified}
                            </div>
                          ) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* 空状态 */}
              {!loading && sortedConstraints.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Filter className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                  <p>没有找到匹配的约束条件</p>
                </div>
              )}
              
              {loading && sortedConstraints.length === 0 && (
                <div className="text-center py-8">
                  <Loader2 className="h-8 w-8 mx-auto animate-spin text-blue-500" />
                  <p className="text-gray-500 mt-2">正在加载约束条件...</p>
                </div>
              )}

              {/* 分页控制 */}
              {pagination.total_pages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
                  <div className="flex-1 flex justify-between sm:hidden">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(Math.max(1, pagination.page - 1))}
                      disabled={pagination.page === 1}
                    >
                      上一页
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(Math.min(pagination.total_pages, pagination.page + 1))}
                      disabled={pagination.page === pagination.total_pages}
                    >
                      下一页
                    </Button>
                  </div>
                  <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm text-gray-700">
                        显示第 <span className="font-medium">{(pagination.page - 1) * pagination.page_size + 1}</span> 到{' '}
                        <span className="font-medium">
                          {Math.min(pagination.page * pagination.page_size, pagination.total)}
                        </span>{' '}
                        条，共 <span className="font-medium">{pagination.total}</span> 条
                      </p>
                    </div>
                    <div>
                      <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handlePageChange(Math.max(1, pagination.page - 1))}
                          disabled={pagination.page === 1}
                          className="rounded-l-md"
                        >
                          <ChevronLeft className="h-4 w-4" />
                          上一页
                        </Button>
                        {Array.from({ length: Math.min(pagination.total_pages, 5) }, (_, i) => {
                          const page = pagination.page <= 3 ? i + 1 : pagination.page - 2 + i;
                          return page <= pagination.total_pages ? (
                            <Button
                              key={page}
                              variant={page === pagination.page ? "default" : "outline"}
                              size="sm"
                              onClick={() => handlePageChange(page)}
                              className="rounded-none"
                            >
                              {page}
                            </Button>
                          ) : null;
                        })}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handlePageChange(Math.min(pagination.total_pages, pagination.page + 1))}
                          disabled={pagination.page === pagination.total_pages}
                          className="rounded-r-md"
                        >
                          下一页
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      </nav>
                    </div>
                  </div>
                </div>
              )}

              {/* 批量操作栏 */}
              {selectedConstraints.size > 0 && (
                <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <span className="text-sm font-medium text-blue-900">
                        已选择 {selectedConstraints.size} 个约束条件
                      </span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          const selectedList = sortedConstraints.filter(c => selectedConstraints.has(c.id));
                          toast.success(`已导出 ${selectedList.length} 个约束条件\n约束条件信息已复制到剪贴板`);
                        }}
                      >
                        导出选中
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          const selectedList = sortedConstraints.filter(c => selectedConstraints.has(c.id));
                          toast.success(`${selectedList.length} 个约束条件已标记为已审核`);
                        }}
                      >
                        标记已审核
                      </Button>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setSelectedConstraints(new Set())}
                    >
                      清除选择
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
    </AppLayout>
  );
}
