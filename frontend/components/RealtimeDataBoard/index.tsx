"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar as CalendarComponent } from '@/components/ui/calendar';
import { Calendar, Search, RefreshCw, ChevronDown, Undo2, Redo2, List, BarChart3 } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

import { GanttView } from './GanttView';
import { ResourceListView } from './ResourceListView';
import { 
  FlightStatus, 
  DragState, 
  HistoryState
} from './types';
import { 
  mockFlights, 
  statusColors, 
  statusLabels 
} from './mockData';

export function RealtimeDataBoard() {
  const [flights, setFlights] = useState<FlightStatus[]>(mockFlights);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [viewMode, setViewMode] = useState<'timeline' | 'resource'>('timeline');
  const [selectedFlights, setSelectedFlights] = useState<Set<string>>(new Set());
  const [datePickerOpen, setDatePickerOpen] = useState(false);
  const [timeFilter, setTimeFilter] = useState<'24h' | '48h' | '72h'>('24h');
  
  // 拖拽相关状态
  const [dragState, setDragState] = useState<DragState>({
    draggedItem: null,
    dragType: null,
    originalPosition: null,
    previewPosition: null,
    conflicts: []
  });
  
  // 历史状态管理（撤销/重做）
  const [history, setHistory] = useState<HistoryState[]>([{ flights: mockFlights, timestamp: Date.now() }]);
  const [historyIndex, setHistoryIndex] = useState(0);
  
  // 过滤航班
  const filteredFlights = flights.filter(flight => {
    const matchesSearch = flight.flightNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         flight.route.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || flight.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // 保存历史状态
  const saveToHistory = useCallback((newFlights: FlightStatus[]) => {
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push({ flights: newFlights, timestamp: Date.now() });
    if (newHistory.length > 50) {
      newHistory.shift();
    } else {
      setHistoryIndex(historyIndex + 1);
    }
    setHistory(newHistory);
  }, [history, historyIndex]);

  // 撤销操作
  const undo = useCallback(() => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      setFlights(history[newIndex].flights);
      toast.success('已撤销操作');
    }
  }, [historyIndex, history]);

  // 重做操作
  const redo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      setFlights(history[newIndex].flights);
      toast.success('已重做操作');
    }
  }, [historyIndex, history]);

  // 自动刷新逻辑
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      setFlights(prev => prev.map(flight => ({
        ...flight,
        progress: Math.min(100, flight.progress + Math.random() * 10)
      })));
      setLastUpdate(new Date());
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        if (e.key === 'z' && !e.shiftKey) {
          e.preventDefault();
          undo();
        } else if ((e.key === 'y') || (e.key === 'z' && e.shiftKey)) {
          e.preventDefault();
          redo();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [undo, redo]);

  // 手动刷新
  const handleRefresh = () => {
    setLastUpdate(new Date());
    toast.success('数据已刷新');
  };

  return (
    <div className="p-6">
      {/* Header区域 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">          
          {/* 日期选择器 */}
          <Popover open={datePickerOpen} onOpenChange={setDatePickerOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className="w-[200px] justify-start text-left font-normal"
              >
                <Calendar className="mr-2 h-4 w-4" />
                {selectedDate ? format(selectedDate, 'yyyy年MM月dd日') : "选择日期"}
                <ChevronDown className="ml-auto h-4 w-4 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <CalendarComponent
                mode="single"
                selected={selectedDate}
                onSelect={(date) => {
                  setSelectedDate(date || new Date());
                  setDatePickerOpen(false);
                }}
                initialFocus
              />
            </PopoverContent>
          </Popover>

          {/* 时间筛选器 */}
          <div className="flex items-center space-x-1 border border-gray-200 rounded-md p-1 bg-white">
            {['24h', '48h', '72h'].map((period) => (
              <Button
                key={period}
                variant={timeFilter === period ? "default" : "ghost"}
                size="sm"
                className="px-3 py-1 text-xs"
                onClick={() => setTimeFilter(period as '24h' | '48h' | '72h')}
              >
                {period}
              </Button>
            ))}
          </div>

          {/* 撤销/重做按钮 */}
          <div className="flex items-center space-x-1">
            <Button
              variant="outline"
              size="sm"
              onClick={undo}
              disabled={historyIndex <= 0}
              title="撤销 (Ctrl+Z)"
            >
              <Undo2 className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={redo}
              disabled={historyIndex >= history.length - 1}
              title="重做 (Ctrl+Y)"
            >
              <Redo2 className="h-4 w-4" />
            </Button>
          </div>
          
          {/* 视图模式切换 */}
          <div className="flex items-center space-x-2">
            <Button
              variant={viewMode === 'timeline' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('timeline')}
              className="flex items-center space-x-2"
            >
              <BarChart3 className="h-4 w-4" />
              <span>甘特图</span>
            </Button>
            <Button
              variant={viewMode === 'resource' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('resource')}
              className="flex items-center space-x-2"
            >
              <List className="h-4 w-4" />
              <span>列表</span>
            </Button>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* 搜索框 */}
          <div className="relative w-[300px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="搜索航班号或航线..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-white"
            />
          </div>

          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[120px] bg-white">
              <SelectValue placeholder="状态筛选" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有状态</SelectItem>
              <SelectItem value="on-time">准点</SelectItem>
              <SelectItem value="slightly-late">轻微延误</SelectItem>
              <SelectItem value="very-late">严重延误</SelectItem>
              <SelectItem value="delayed">预计延误</SelectItem>
              <SelectItem value="cancelled">取消</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            自动刷新
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
          >
            手动刷新
          </Button>
          
          <p className="text-gray-500 text-sm">最后更新: {lastUpdate.toLocaleTimeString()}</p>
        </div>
      </div>

      {/* 状态统计 */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        {Object.entries(statusLabels).map(([status, label]) => {
          const count = filteredFlights.filter(f => f.status === status).length;
          return (
            <Card key={status} className="p-4">
              <div className="flex items-center space-x-3">
                <div className={`w-4 h-4 rounded-full ${statusColors[status as keyof typeof statusColors]}`} />
                <div>
                  <p className="text-sm text-gray-600">{String(label)}</p>
                  <p className="text-2xl font-bold">{count}</p>
                </div>
              </div>
            </Card>
          );
        })}
      </div>



      {/* 主要内容区域 */}
      {viewMode === 'timeline' ? (
        <GanttView 
          flights={filteredFlights}
          dragState={dragState}
          setDragState={setDragState}
          selectedFlights={selectedFlights}
          setSelectedFlights={setSelectedFlights}
          setFlights={setFlights}
          saveToHistory={saveToHistory}
        />
      ) : (
        <ResourceListView 
          flights={filteredFlights}
          selectedFlights={selectedFlights}
          setSelectedFlights={setSelectedFlights}
          setFlights={setFlights}
          saveToHistory={saveToHistory}
        />
      )}

      {/* 拖拽提示工具栏 */}
      {dragState.draggedItem && (
        <div className="fixed bottom-4 right-4 bg-white shadow-lg rounded-lg p-4 border max-w-sm">
          <div className="text-sm space-y-2">
            <div className="font-medium">拖拽提示</div>
            <div>航班: {dragState.draggedItem.flightNumber}</div>
            <div>操作: {
              dragState.dragType === 'move' ? '整体移动' : 
              dragState.dragType === 'resize-start' ? '调整起飞时间' : 
              dragState.dragType === 'resize-end' ? '调整到达时间' : '垂直移动'
            }</div>
            {dragState.conflicts.length > 0 && (
              <div className="text-red-600 text-xs">
                ⚠️ 存在时间冲突
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
