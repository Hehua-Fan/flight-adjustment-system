"use client";

import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { List, Users, Check, X, ChevronLeft, ChevronRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

import { FlightStatus, ColumnConfig } from './types';
import { 
  decisionStatusColors,
  decisionStatusLabels
} from './mockData';

// 列配置
const columns: ColumnConfig[] = [
  { key: 'select', title: '', width: 'w-12' },
  { key: 'day', title: 'Day', width: 'w-16' },
  { key: 'flightNumber', title: 'Flight #', width: 'w-24', sortable: true },
  { key: 'status', title: 'Status', width: 'w-20' },
  { key: 'plots', title: 'Plots', width: 'w-16' },
  { key: 'crew', title: 'Crew', width: 'w-20' },
  { key: 'passengers', title: 'Pax', width: 'w-16' },
  { key: 'registration', title: 'Reg', width: 'w-20' },
  { key: 'edto', title: 'EDTO', width: 'w-16' },
  { key: 'desk', title: 'Desk', width: 'w-16' },
  { key: 'decisionStatus', title: 'Filing Status', width: 'w-32' }
];

interface ResourceListViewProps {
  flights: FlightStatus[];
  selectedFlights: Set<string>;
  setSelectedFlights: React.Dispatch<React.SetStateAction<Set<string>>>;
  setFlights: React.Dispatch<React.SetStateAction<FlightStatus[]>>;
  saveToHistory: (flights: FlightStatus[]) => void;
}

export function ResourceListView({ 
  flights, 
  selectedFlights, 
  setSelectedFlights, 
  setFlights, 
  saveToHistory 
}: ResourceListViewProps) {
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // 排序逻辑
  const sortedFlights = useMemo(() => {
    if (!sortConfig) return flights;

    return [...flights].sort((a, b) => {
      const aValue = a[sortConfig.key as keyof FlightStatus] || '';
      const bValue = b[sortConfig.key as keyof FlightStatus] || '';

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [flights, sortConfig]);

  // 分页逻辑
  const totalPages = Math.ceil(sortedFlights.length / itemsPerPage);
  const paginatedFlights = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return sortedFlights.slice(startIndex, startIndex + itemsPerPage);
  }, [sortedFlights, currentPage, itemsPerPage]);

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
  const handleSelectFlight = (flightId: string, checked: boolean) => {
    setSelectedFlights(prev => {
      const newSelected = new Set(prev);
      if (checked) {
        newSelected.add(flightId);
      } else {
        newSelected.delete(flightId);
      }
      return newSelected;
    });
  };

  // 全选/取消全选
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedFlights(new Set(flights.map(f => f.id)));
    } else {
      setSelectedFlights(new Set());
    }
  };

  // 处理决策状态变更
  const handleDecisionStatusChange = (flightId: string, newStatus: 'approved' | 'rejected') => {
    const newFlights = flights.map(flight =>
      flight.id === flightId
        ? { ...flight, decisionStatus: newStatus }
        : flight
    );
    
    saveToHistory(newFlights);
    setFlights(newFlights);
    
    const flight = flights.find(f => f.id === flightId);
    toast.success(`航班 ${flight?.flightNumber} 决策状态已更新为 ${decisionStatusLabels[newStatus]}`);
  };

  // 获取状态图标
  const getStatusIcon = (status: FlightStatus['status']) => {
    switch (status) {
      case 'on-time':
        return <div className="w-3 h-3 bg-green-500 rounded-full" />;
      case 'slightly-late':
        return <div className="w-3 h-3 bg-yellow-500 rounded-full" />;
      case 'very-late':
        return <div className="w-3 h-3 bg-red-500 rounded-full" />;
      case 'delayed':
        return <div className="w-3 h-3 bg-orange-500 rounded-full" />;
      case 'cancelled':
        return <div className="w-3 h-3 bg-gray-500 rounded-full" />;
      default:
        return <div className="w-3 h-3 bg-gray-300 rounded-full" />;
    }
  };

  // 获取决策状态组件
  const getDecisionStatusComponent = (flight: FlightStatus) => {
    const status = flight.decisionStatus || 'pending';
    
    if (status === 'pending') {
      return (
        <div className="flex items-center space-x-2">
          <Button
            size="sm"
            variant="outline"
            className="h-6 w-6 p-0 text-green-600 hover:bg-green-50"
            onClick={() => handleDecisionStatusChange(flight.id, 'approved')}
            title="批准"
          >
            <Check className="h-3 w-3" />
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-6 w-6 p-0 text-red-600 hover:bg-red-50"
            onClick={() => handleDecisionStatusChange(flight.id, 'rejected')}
            title="拒绝"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      );
    }

    return (
      <Badge className={cn("text-xs", decisionStatusColors[status])}>
        {decisionStatusLabels[status]}
      </Badge>
    );
  };

  const isAllSelected = flights.length > 0 && selectedFlights.size === flights.length;
  const isPartiallySelected = selectedFlights.size > 0 && selectedFlights.size < flights.length;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <List className="h-5 w-5" />
            <span>航班列表视图</span>
          </div>
          <div className="text-sm text-gray-500">
            {flights.length} 个航班 • {selectedFlights.size} 个已选择
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-900">
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
                        checked={isAllSelected}
                        ref={(el) => {
                          if (el) {
                            // @ts-expect-error - indeterminate property exists on input element
                            el.indeterminate = isPartiallySelected;
                          }
                        }}
                        onCheckedChange={handleSelectAll}
                      />
                    ) : (
                      <div
                        className={cn(
                          "flex items-center space-x-1",
                          column.sortable && "cursor-pointer hover:text-gray-700"
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
              {paginatedFlights.map((flight) => (
                <tr
                  key={flight.id}
                  className={cn(
                    "hover:bg-gray-50 transition-colors",
                    selectedFlights.has(flight.id) && "bg-blue-50"
                  )}
                >
                  {/* 选择框 */}
                  <td className="px-3 py-2">
                    <Checkbox
                      checked={selectedFlights.has(flight.id)}
                      onCheckedChange={(checked) => handleSelectFlight(flight.id, checked as boolean)}
                    />
                  </td>

                  {/* Day */}
                  <td className="px-3 py-2 text-sm text-gray-900">01</td>

                  {/* Flight Number */}
                  <td className="px-3 py-2">
                    <div className="text-sm font-medium text-gray-900">{flight.flightNumber}</div>
                  </td>

                  {/* Status */}
                  <td className="px-3 py-2">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(flight.status)}
                      <div className="flex space-x-1">
                        <Check className="h-3 w-3 text-green-500" />
                        <Check className="h-3 w-3 text-green-500" />
                      </div>
                    </div>
                  </td>

                  {/* Plots */}
                  <td className="px-3 py-2">
                    <Users className="h-4 w-4 text-gray-400" />
                  </td>

                  {/* Crew */}
                  <td className="px-3 py-2 text-sm text-gray-900">{flight.crew}</td>

                  {/* Passengers */}
                  <td className="px-3 py-2 text-sm text-gray-900">{flight.passengers}</td>

                  {/* Registration */}
                  <td className="px-3 py-2 text-sm text-gray-900">{flight.crew}</td>

                  {/* EDTO */}
                  <td className="px-3 py-2">
                    {flight.priority === 'high' && (
                      <Check className="h-4 w-4 text-green-500" />
                    )}
                  </td>

                  {/* Desk */}
                  <td className="px-3 py-2 text-sm text-gray-900">
                    {flight.crew?.includes('AME') ? 'AME' : ''}
                  </td>

                  {/* Filing Status */}
                  <td className="px-3 py-2">
                    {getDecisionStatusComponent(flight)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

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
                    {Math.min(currentPage * itemsPerPage, sortedFlights.length)}
                  </span>{' '}
                  条，共 <span className="font-medium">{sortedFlights.length}</span> 条
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
        {selectedFlights.size > 0 && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <span className="text-sm font-medium text-blue-900">
                  已选择 {selectedFlights.size} 个航班
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    const selectedFlightsList = flights.filter(f => selectedFlights.has(f.id));
                    const pendingFlights = selectedFlightsList.filter(f => f.decisionStatus === 'pending');
                    
                    if (pendingFlights.length === 0) {
                      toast.warning('没有待决策的航班');
                      return;
                    }

                    const newFlights = flights.map(flight =>
                      selectedFlights.has(flight.id) && flight.decisionStatus === 'pending'
                        ? { ...flight, decisionStatus: 'approved' as const }
                        : flight
                    );

                    saveToHistory(newFlights);
                    setFlights(newFlights);
                    toast.success(`${pendingFlights.length} 个航班已批量批准`);
                  }}
                >
                  <Check className="h-4 w-4 mr-2" />
                  批量批准
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    const selectedFlightsList = flights.filter(f => selectedFlights.has(f.id));
                    const pendingFlights = selectedFlightsList.filter(f => f.decisionStatus === 'pending');
                    
                    if (pendingFlights.length === 0) {
                      toast.warning('没有待决策的航班');
                      return;
                    }

                    const newFlights = flights.map(flight =>
                      selectedFlights.has(flight.id) && flight.decisionStatus === 'pending'
                        ? { ...flight, decisionStatus: 'rejected' as const }
                        : flight
                    );

                    saveToHistory(newFlights);
                    setFlights(newFlights);
                    toast.success(`${pendingFlights.length} 个航班已批量拒绝`);
                  }}
                >
                  <X className="h-4 w-4 mr-2" />
                  批量拒绝
                </Button>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setSelectedFlights(new Set())}
              >
                清除选择
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
