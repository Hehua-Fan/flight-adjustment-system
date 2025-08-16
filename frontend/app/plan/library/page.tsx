"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Search,
  Filter,
  BookOpen,
  Edit,
  Copy,
  Trash2,
  Play,
  Calendar,
  User,
  TrendingUp,
  Clock,
  Plane,
  AlertCircle,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { AppLayout } from '@/components/AppLayout';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

// 方案数据类型
interface PlanData {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'generated' | 'executed' | 'archived';
  createdBy: string;
  createdAt: string;
  lastModified: string;
  metrics?: {
    totalCost: number;
    cancelledFlights: number;
    delayMinutes: number;
    aircraftChanges: number;
    affectedPassengers: number;
  };
  tags: string[];
}

export default function PlanLibraryPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedPlans, setSelectedPlans] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // 模拟方案数据
  const mockPlans: PlanData[] = [
    {
      id: '1',
      name: '天气延误应急方案',
      description: '应对恶劣天气导致的大面积航班延误',
      status: 'generated',
      createdBy: '张三',
      createdAt: '2024-01-15',
      lastModified: '2024-01-16',
      metrics: {
        totalCost: 2850000,
        cancelledFlights: 12,
        delayMinutes: 4560,
        aircraftChanges: 8,
        affectedPassengers: 2340
      },
      tags: ['天气', '应急', '大面积延误']
    },
    {
      id: '2',
      name: '春运运力优化方案',
      description: '春运期间运力重新配置和优化',
      status: 'executed',
      createdBy: '李四',
      createdAt: '2024-01-10',
      lastModified: '2024-01-12',
      metrics: {
        totalCost: 1250000,
        cancelledFlights: 3,
        delayMinutes: 1200,
        aircraftChanges: 15,
        affectedPassengers: 890
      },
      tags: ['春运', '运力优化', '节假日']
    },
    {
      id: '3',
      name: '机场关闭备用方案',
      description: '主要机场临时关闭时的应急调整方案',
      status: 'draft',
      createdBy: '王五',
      createdAt: '2024-01-20',
      lastModified: '2024-01-20',
      tags: ['应急', '机场关闭', '备用方案']
    },
    {
      id: '4',
      name: '维护期调整方案',
      description: '大型维护期间的航班调整和重新安排',
      status: 'generated',
      createdBy: '赵六',
      createdAt: '2024-01-18',
      lastModified: '2024-01-19',
      metrics: {
        totalCost: 950000,
        cancelledFlights: 8,
        delayMinutes: 3200,
        aircraftChanges: 12,
        affectedPassengers: 1560
      },
      tags: ['维护', '计划调整', '定期维护']
    }
  ];

  const [plans] = useState<PlanData[]>(mockPlans);

  // 筛选和搜索逻辑
  const filteredPlans = plans.filter(plan => {
    const matchesSearch = plan.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         plan.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         plan.createdBy.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || plan.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // 分页逻辑
  const totalPages = Math.ceil(filteredPlans.length / itemsPerPage);
  const paginatedPlans = filteredPlans.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handleSelectPlan = (planId: string, checked: boolean) => {
    setSelectedPlans(prev => {
      const newSelected = new Set(prev);
      if (checked) {
        newSelected.add(planId);
      } else {
        newSelected.delete(planId);
      }
      return newSelected;
    });
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedPlans(new Set(paginatedPlans.map(p => p.id)));
    } else {
      setSelectedPlans(new Set());
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      generated: 'bg-blue-100 text-blue-800',
      executed: 'bg-green-100 text-green-800',
      archived: 'bg-yellow-100 text-yellow-800'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getStatusLabel = (status: string) => {
    const labels = {
      draft: '草稿',
      generated: '已生成',
      executed: '已执行',
      archived: '已归档'
    };
    return labels[status as keyof typeof labels] || '未知';
  };

  const handleEdit = (planId: string) => {
    toast.success(`编辑方案 ${planId}`);
  };

  const handleCopy = (planId: string) => {
    toast.success(`复制方案 ${planId}`);
  };

  const handleDelete = (planId: string) => {
    toast.success(`删除方案 ${planId}`);
  };

  const handleExecute = (planId: string) => {
    toast.success(`执行方案 ${planId}`);
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const isAllSelected = paginatedPlans.length > 0 && selectedPlans.size === paginatedPlans.length;
  const isPartiallySelected = selectedPlans.size > 0 && selectedPlans.size < paginatedPlans.length;

  return (
    <AppLayout>
      <div className="p-6">
        {/* Header区域 */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[120px] bg-white">
                <SelectValue placeholder="状态筛选" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有状态</SelectItem>
                <SelectItem value="draft">草稿</SelectItem>
                <SelectItem value="generated">已生成</SelectItem>
                <SelectItem value="executed">已执行</SelectItem>
                <SelectItem value="archived">已归档</SelectItem>
              </SelectContent>
            </Select>

            <Button variant="outline" size="sm" onClick={() => {
              setSearchTerm('');
              setStatusFilter('all');
              setSelectedPlans(new Set());
            }}>
              <Filter className="h-4 w-4 mr-2" />
              重置筛选
            </Button>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* 搜索框 */}
            <div className="relative w-[300px]">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="搜索方案名称、描述、创建人..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-white"
              />
            </div>

            <div className="text-sm text-gray-500">
              共 {filteredPlans.length} 个方案
            </div>
          </div>
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: '草稿', count: plans.filter(p => p.status === 'draft').length, color: 'bg-gray-500' },
            { label: '已生成', count: plans.filter(p => p.status === 'generated').length, color: 'bg-blue-500' },
            { label: '已执行', count: plans.filter(p => p.status === 'executed').length, color: 'bg-green-500' },
            { label: '已归档', count: plans.filter(p => p.status === 'archived').length, color: 'bg-yellow-500' }
          ].map((stat, index) => (
            <Card key={index} className="p-4">
              <div className="flex items-center space-x-3">
                <div className={`w-4 h-4 rounded-full ${stat.color}`} />
                <div>
                  <p className="text-sm text-gray-600">{stat.label}</p>
                  <p className="text-2xl font-bold">{stat.count}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* 方案列表 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <BookOpen className="h-5 w-5" />
                <span>方案列表</span>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-500">
                  {paginatedPlans.length} 个方案 • {selectedPlans.size} 个已选择
                </div>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-gray-200 bg-black">
                    <th className="px-3 py-2 text-left text-xs font-medium text-white uppercase tracking-wider w-12">
                      <Checkbox
                        checked={isAllSelected}
                        ref={(el) => {
                          if (el) {
                            // @ts-expect-error - indeterminate property exists on input element
                            el.indeterminate = isPartiallySelected;
                          }
                        }}
                        onCheckedChange={handleSelectAll}
                      />
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-white uppercase tracking-wider w-48">方案名称</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-white uppercase tracking-wider w-24">状态</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-white uppercase tracking-wider w-32">核心指标</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-white uppercase tracking-wider w-20">创建人</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-white uppercase tracking-wider w-32">创建时间</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-white uppercase tracking-wider w-32">操作</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {paginatedPlans.map((plan) => (
                    <tr
                      key={plan.id}
                      className={cn(
                        "hover:bg-gray-50 transition-colors",
                        selectedPlans.has(plan.id) && "bg-blue-50"
                      )}
                    >
                      {/* 选择框 */}
                      <td className="px-3 py-2">
                        <Checkbox
                          checked={selectedPlans.has(plan.id)}
                          onCheckedChange={(checked) => handleSelectPlan(plan.id, checked as boolean)}
                        />
                      </td>

                      {/* 方案名称 */}
                      <td className="px-3 py-2">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{plan.name}</div>
                          <div className="text-sm text-gray-600 truncate max-w-64" title={plan.description}>
                            {plan.description}
                          </div>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {plan.tags.map((tag, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </td>

                      {/* 状态 */}
                      <td className="px-3 py-2">
                        <Badge className={getStatusColor(plan.status)}>
                          {getStatusLabel(plan.status)}
                        </Badge>
                      </td>

                      {/* 核心指标 */}
                      <td className="px-3 py-2">
                        {plan.metrics ? (
                          <div className="text-xs space-y-1">
                            <div className="flex items-center">
                              <TrendingUp className="h-3 w-3 mr-1 text-red-500" />
                              <span>成本: ¥{formatNumber(plan.metrics.totalCost)}</span>
                            </div>
                            <div className="flex items-center">
                              <Plane className="h-3 w-3 mr-1 text-orange-500" />
                              <span>取消: {plan.metrics.cancelledFlights}班</span>
                            </div>
                            <div className="flex items-center">
                              <Clock className="h-3 w-3 mr-1 text-blue-500" />
                              <span>延误: {formatNumber(plan.metrics.delayMinutes)}分钟</span>
                            </div>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-400">无数据</span>
                        )}
                      </td>

                      {/* 创建人 */}
                      <td className="px-3 py-2 text-sm text-gray-900">
                        <div className="flex items-center">
                          <User className="h-3 w-3 mr-1" />
                          {plan.createdBy}
                        </div>
                      </td>

                      {/* 创建时间 */}
                      <td className="px-3 py-2 text-sm text-gray-500">
                        <div className="flex items-center">
                          <Calendar className="h-3 w-3 mr-1" />
                          {plan.createdAt}
                        </div>
                      </td>

                      {/* 操作 */}
                      <td className="px-3 py-2">
                        <div className="flex items-center space-x-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEdit(plan.id)}
                            className="h-7 w-7 p-0"
                            title="编辑"
                          >
                            <Edit className="h-3 w-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleCopy(plan.id)}
                            className="h-7 w-7 p-0"
                            title="复制"
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                          {plan.status === 'generated' && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleExecute(plan.id)}
                              className="h-7 w-7 p-0 text-green-600"
                              title="执行"
                            >
                              <Play className="h-3 w-3" />
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDelete(plan.id)}
                            className="h-7 w-7 p-0 text-red-600"
                            title="删除"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 空状态 */}
            {paginatedPlans.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <BookOpen className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p>没有找到匹配的方案</p>
              </div>
            )}

            {/* 分页控制 */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
                <div className="flex-1 flex justify-between sm:hidden">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                  >
                    上一页
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                  >
                    下一页
                  </Button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      显示第 <span className="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span> 到{' '}
                      <span className="font-medium">
                        {Math.min(currentPage * itemsPerPage, filteredPlans.length)}
                      </span>{' '}
                      条，共 <span className="font-medium">{filteredPlans.length}</span> 条
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                        disabled={currentPage === 1}
                        className="rounded-l-md"
                      >
                        <ChevronLeft className="h-4 w-4" />
                        上一页
                      </Button>
                      {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                        const page = currentPage <= 3 ? i + 1 : currentPage - 2 + i;
                        return page <= totalPages ? (
                          <Button
                            key={page}
                            variant={page === currentPage ? "default" : "outline"}
                            size="sm"
                            onClick={() => setCurrentPage(page)}
                            className="rounded-none"
                          >
                            {page}
                          </Button>
                        ) : null;
                      })}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                        disabled={currentPage === totalPages}
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
            {selectedPlans.size > 0 && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <span className="text-sm font-medium text-blue-900">
                      已选择 {selectedPlans.size} 个方案
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        toast.success(`批量导出 ${selectedPlans.size} 个方案`);
                      }}
                    >
                      批量导出
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        toast.success(`批量归档 ${selectedPlans.size} 个方案`);
                      }}
                    >
                      批量归档
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        toast.error(`批量删除 ${selectedPlans.size} 个方案`);
                      }}
                      className="text-red-600 hover:text-red-700"
                    >
                      批量删除
                    </Button>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSelectedPlans(new Set())}
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
