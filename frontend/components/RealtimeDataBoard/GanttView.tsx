"use client";

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Plane, AlertTriangle, Maximize, Minimize } from 'lucide-react';

import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

import { 
  FlightStatus, 
  DragState, 
  DragType, 
  TimeSlot
} from './types';
import { 
  statusColors, 
  statusLabels
} from './mockData';

// 生成时间槽 - 24小时完整视图
const generateTimeSlots = (): TimeSlot[] => {
  const slots: TimeSlot[] = [];
  for (let hour = 0; hour < 24; hour++) {
    slots.push({
      time: `${hour.toString().padStart(2, '0')}:00`,
      hour
    });
  }
  return slots;
};

// 计算航班在时间轴上的位置的辅助函数
function calculateFlightPosition(flight: FlightStatus) {
  const startHour = parseInt(flight.departureTime.split(':')[0]);
  const startMinute = parseInt(flight.departureTime.split(':')[1]);
  const endHour = parseInt(flight.arrivalTime.split(':')[0]);
  const endMinute = parseInt(flight.arrivalTime.split(':')[1]);
  
  // 计算相对于0:00的分钟数
  const startMinutesFromMidnight = startHour * 60 + startMinute;
  const endMinutesFromMidnight = endHour * 60 + endMinute;
  
  // 每个时间槽60px，每分钟1px (60px/60min)
  const pixelsPerMinute = 1;
  const left = startMinutesFromMidnight * pixelsPerMinute;
  const width = (endMinutesFromMidnight - startMinutesFromMidnight) * pixelsPerMinute;
  
  return { left: `${left}px`, width: `${width}px` };
}

// 时间转换辅助函数
function timeToMinutes(timeStr: string): number {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours * 60 + minutes;
}

function minutesToTime(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
}

// 检测冲突的辅助函数
function detectConflicts(flight: FlightStatus, otherFlights: FlightStatus[]): boolean {
  const flightStart = timeToMinutes(flight.departureTime);
  const flightEnd = timeToMinutes(flight.arrivalTime);
  
  return otherFlights.some(other => {
    if (other.id === flight.id) return false;
    if (flight.crew && other.crew === flight.crew) {
      const otherStart = timeToMinutes(other.departureTime);
      const otherEnd = timeToMinutes(other.arrivalTime);
      return !(flightEnd <= otherStart || flightStart >= otherEnd);
    }
    return false;
  });
}

// 可拖拽的航班条形组件
function DraggableFlightBar({ 
  flight, 
  onDragStart, 
  onDragMove, 
  onDragEnd,
  isSelected,
  onSelect,
  conflicts
}: { 
  flight: FlightStatus;
  onDragStart: (flight: FlightStatus, dragType: DragType) => void;
  onDragMove: (deltaX: number) => void;
  onDragEnd: () => void;
  isSelected: boolean;
  onSelect: (flight: FlightStatus, multi: boolean) => void;
  conflicts: string[];
}) {
  const position = calculateFlightPosition(flight);
  const [isDragging, setIsDragging] = useState(false);
  const [dragType, setDragType] = useState<DragType | null>(null);
  const [startPosition, setStartPosition] = useState({ x: 0, y: 0 });
  
  const hasConflict = conflicts.includes(flight.id);
  
  const handleMouseDown = (e: React.MouseEvent, type: DragType) => {
    e.preventDefault();
    setIsDragging(true);
    setDragType(type);
    setStartPosition({ x: e.clientX, y: e.clientY });
    onDragStart(flight, type);
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging && dragType) {
      const deltaX = e.clientX - startPosition.x;
      onDragMove(deltaX);
    }
  }, [isDragging, dragType, startPosition, onDragMove]);

  const handleMouseUp = useCallback(() => {
    if (isDragging) {
      setIsDragging(false);
      setDragType(null);
      onDragEnd();
    }
  }, [isDragging, onDragEnd]);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <div 
      className={cn(
        "absolute h-8 rounded-lg border-2 shadow-md transition-all duration-200 flex items-center text-white text-xs font-medium top-2 group",
        isSelected ? "border-blue-400 ring-2 ring-blue-200" : "border-white",
        hasConflict ? "bg-red-500 border-red-300" : statusColors[flight.status],
        isDragging ? "z-50 shadow-xl" : "hover:shadow-lg"
      )}
      style={{ 
        left: position.left, 
        width: position.width,
        minWidth: '100px',
        opacity: isDragging ? 0.8 : 1
      }}
      onClick={(e) => onSelect(flight, e.shiftKey || e.ctrlKey)}
    >
      {/* 左侧调整手柄 */}
      <div 
        className="absolute left-0 top-0 w-2 h-full bg-white/20 rounded-l-lg cursor-ew-resize opacity-0 group-hover:opacity-100 transition-opacity"
        onMouseDown={(e) => handleMouseDown(e, 'resize-start')}
      />
      
      {/* 主体内容 */}
      <div 
        className="flex-1 px-2 cursor-move"
        onMouseDown={(e) => handleMouseDown(e, 'move')}
      >
        <div className="flex items-center space-x-2 w-full">
          <span className="font-bold">{flight.flightNumber}</span>
          <span className="text-xs opacity-90">{flight.route}</span>
          {hasConflict && <AlertTriangle className="h-3 w-3" />}
        </div>
      </div>
      
      {/* 右侧调整手柄 */}
      <div 
        className="absolute right-0 top-0 w-2 h-full bg-white/20 rounded-r-lg cursor-ew-resize opacity-0 group-hover:opacity-100 transition-opacity"
        onMouseDown={(e) => handleMouseDown(e, 'resize-end')}
      />
      
      {/* 进度条 */}
      <div className="absolute bottom-0 left-0 h-1 bg-white/30 rounded-b-lg">
        <div 
          className="h-full bg-white rounded-b-lg transition-all duration-1000"
          style={{ width: `${flight.progress}%` }}
        />
      </div>
    </div>
  );
}



interface GanttViewProps {
  flights: FlightStatus[];
  dragState: DragState;
  setDragState: React.Dispatch<React.SetStateAction<DragState>>;
  selectedFlights: Set<string>;
  setSelectedFlights: React.Dispatch<React.SetStateAction<Set<string>>>;
  setFlights: React.Dispatch<React.SetStateAction<FlightStatus[]>>;
  saveToHistory: (flights: FlightStatus[]) => void;
}

export function GanttView({ 
  flights, 
  dragState, 
  setDragState, 
  selectedFlights, 
  setSelectedFlights, 
  setFlights, 
  saveToHistory 
}: GanttViewProps) {
  const timeSlots = generateTimeSlots();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // 全屏切换处理
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };
  
  // 航班选择处理
  const handleFlightSelect = useCallback((flight: FlightStatus, multi: boolean) => {
    setSelectedFlights(prev => {
      const newSelected = new Set(prev);
      if (multi) {
        if (newSelected.has(flight.id)) {
          newSelected.delete(flight.id);
        } else {
          newSelected.add(flight.id);
        }
      } else {
        newSelected.clear();
        newSelected.add(flight.id);
      }
      return newSelected;
    });
  }, [setSelectedFlights]);

  // 拖拽开始处理
  const handleDragStart = useCallback((flight: FlightStatus, dragType: DragType) => {
    const position = calculateFlightPosition(flight);
    setDragState({
      draggedItem: flight,
      dragType,
      originalPosition: position,
      previewPosition: position,
      conflicts: []
    });
  }, [setDragState]);

  // 拖拽移动处理
  const handleDragMove = useCallback((deltaX: number) => {
    if (!dragState.draggedItem || !dragState.originalPosition) return;

    const pixelsPerMinute = 1; // 每分钟对应的像素数
    const minutesDelta = deltaX / pixelsPerMinute;
    
    let newDepartureTime = dragState.draggedItem.departureTime;
    let newArrivalTime = dragState.draggedItem.arrivalTime;

    if (dragState.dragType === 'move') {
      // 整体移动
      const depMinutes = timeToMinutes(dragState.draggedItem.departureTime) + minutesDelta;
      const arrMinutes = timeToMinutes(dragState.draggedItem.arrivalTime) + minutesDelta;
      newDepartureTime = minutesToTime(Math.max(0, Math.min(1440, depMinutes))); // 0:00-24:00
      newArrivalTime = minutesToTime(Math.max(0, Math.min(1440, arrMinutes)));
    } else if (dragState.dragType === 'resize-start') {
      // 调整开始时间
      const depMinutes = timeToMinutes(dragState.draggedItem.departureTime) + minutesDelta;
      newDepartureTime = minutesToTime(Math.max(0, Math.min(1440, depMinutes)));
    } else if (dragState.dragType === 'resize-end') {
      // 调整结束时间
      const arrMinutes = timeToMinutes(dragState.draggedItem.arrivalTime) + minutesDelta;
      newArrivalTime = minutesToTime(Math.max(0, Math.min(1440, arrMinutes)));
    }

    // 创建临时航班对象用于冲突检测
    const tempFlight = {
      ...dragState.draggedItem,
      departureTime: newDepartureTime,
      arrivalTime: newArrivalTime
    };

    // 检测冲突
    const conflicts = detectConflicts(tempFlight, flights) ? [tempFlight.id] : [];
    
    // 更新预览位置
    const previewPosition = calculateFlightPosition(tempFlight);
    
    // 计算拖拽反馈信息
    const absoluteMinutesMoved = Math.abs(Math.round(minutesDelta));
    const direction = minutesDelta > 0 ? 'forward' : minutesDelta < 0 ? 'backward' : 'none';
    
    setDragState(prev => ({
      ...prev,
      previewPosition,
      conflicts,
      dragFeedback: {
        minutesMoved: absoluteMinutesMoved,
        direction,
        dragType: prev.dragType!
      }
    }));
  }, [dragState, flights, setDragState]);

  // 拖拽结束处理
  const handleDragEnd = useCallback(() => {
    if (!dragState.draggedItem || !dragState.previewPosition) {
      setDragState({
        draggedItem: null,
        dragType: null,
        originalPosition: null,
        previewPosition: null,
        conflicts: [],
        dragFeedback: undefined
      });
      return;
    }

    if (dragState.conflicts.length > 0) {
      toast.error('存在时间冲突，无法执行此操作');
      setDragState({
        draggedItem: null,
        dragType: null,
        originalPosition: null,
        previewPosition: null,
        conflicts: [],
        dragFeedback: undefined
      });
      return;
    }

    // 计算新的时间 - 使用像素单位
    const pixelsPerMinute = 1;
    const originalLeft = parseFloat(dragState.originalPosition!.left.replace('px', ''));
    const previewLeft = parseFloat(dragState.previewPosition.left.replace('px', ''));
    const originalWidth = parseFloat(dragState.originalPosition!.width.replace('px', ''));
    const previewWidth = parseFloat(dragState.previewPosition.width.replace('px', ''));
    
    const leftDelta = (previewLeft - originalLeft) / pixelsPerMinute; // 转换为分钟
    const widthDelta = (previewWidth - originalWidth) / pixelsPerMinute; // 转换为分钟

    let newDepartureTime = dragState.draggedItem.departureTime;
    let newArrivalTime = dragState.draggedItem.arrivalTime;

    if (dragState.dragType === 'move') {
      const depMinutes = timeToMinutes(dragState.draggedItem.departureTime) + leftDelta;
      const arrMinutes = timeToMinutes(dragState.draggedItem.arrivalTime) + leftDelta;
      newDepartureTime = minutesToTime(Math.max(0, Math.min(1440, depMinutes))); // 0:00-24:00
      newArrivalTime = minutesToTime(Math.max(0, Math.min(1440, arrMinutes)));
    } else if (dragState.dragType === 'resize-start') {
      const depMinutes = timeToMinutes(dragState.draggedItem.departureTime) + leftDelta;
      newDepartureTime = minutesToTime(Math.max(0, Math.min(1440, depMinutes)));
    } else if (dragState.dragType === 'resize-end') {
      const arrMinutes = timeToMinutes(dragState.draggedItem.arrivalTime) + leftDelta + widthDelta;
      newArrivalTime = minutesToTime(Math.max(0, Math.min(1440, arrMinutes)));
    }

    // 更新航班数据
    const newFlights = flights.map(flight => 
      flight.id === dragState.draggedItem!.id 
        ? { 
            ...flight, 
            departureTime: newDepartureTime, 
            arrivalTime: newArrivalTime 
          }
        : flight
    );

    saveToHistory(newFlights);
    setFlights(newFlights);
    
    // 显示反馈
    const timeDiff = timeToMinutes(newDepartureTime) - timeToMinutes(dragState.draggedItem.departureTime);
    if (timeDiff !== 0) {
      const direction = timeDiff > 0 ? '延后' : '提前';
      toast.success(`航班 ${dragState.draggedItem.flightNumber} ${direction} ${Math.abs(timeDiff)} 分钟`);
    }

    setDragState({
      draggedItem: null,
      dragType: null,
      originalPosition: null,
      previewPosition: null,
      conflicts: [],
      dragFeedback: undefined
    });
  }, [dragState, flights, saveToHistory, setFlights, setDragState]);

  return (
    <Card className={isFullscreen ? "fixed inset-0 z-50 overflow-auto bg-white" : ""}>
      <CardHeader>
        <CardTitle>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-2">
                <Plane className="h-5 w-5" />
                <span>航班甘特图视图</span>
              </div>
              <div className="text-sm text-gray-500">
                拖拽航班条进行调整 • 按住Shift多选 • Ctrl+Z撤销
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {selectedFlights.size > 0 && (
                <div className="text-sm text-blue-600 bg-blue-50 px-3 py-1 rounded-md">
                  已选择 {selectedFlights.size} 个航班，可批量延后或换机组
                </div>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={toggleFullscreen}
                className="flex items-center space-x-1"
              >
                {isFullscreen ? (
                  <>
                    <Minimize className="h-4 w-4" />
                    <span>退出全屏</span>
                  </>
                ) : (
                  <>
                    <Maximize className="h-4 w-4" />
                    <span>全屏</span>
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* 甘特图容器 */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          {/* 固定的航班信息和状态列 */}
          <div className="flex">
            {/* 左侧固定列 */}
            <div className="flex-shrink-0">
              {/* 固定列标题 */}
              <div className="flex bg-black border-b border-gray-200 h-12">
                <div className="w-32 px-4 border-r border-gray-200 flex items-center">
                  <div className="text-sm font-medium text-white">航班信息</div>
                </div>
                <div className="w-24 px-2 border-r border-gray-200 flex items-center justify-center">
                  <div className="text-sm font-medium text-white text-center">状态</div>
                </div>
              </div>
              
              {/* 固定列数据 */}
              <div className="divide-y divide-gray-200">
                {flights.map((flight) => (
                  <div key={`fixed-${flight.id}`} className="flex hover:bg-gray-50 h-12">
                    <div className="w-32 bg-white border-r border-gray-200 px-4 flex items-center">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{flight.flightNumber}</div>
                        <div className="text-xs text-gray-500">{flight.aircraft}</div>
                      </div>
                    </div>
                    <div className="w-24 bg-white border-r border-gray-200 px-2 flex items-center justify-center">
                      <Badge variant="outline" className={`${statusColors[flight.status]} text-white border-none text-xs`}>
                        {statusLabels[flight.status]}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* 右侧可滚动区域 */}
            <div className="flex-1 overflow-x-auto" ref={scrollContainerRef}>
              <div style={{ minWidth: '1440px' }}> {/* 24小时 * 60px = 1440px */}
                {/* 时间标尺 */}
                <div className="flex bg-black border-b border-gray-200">
                  {timeSlots.map((slot) => (
                    <div 
                      key={slot.time}
                      className="text-center text-sm font-medium text-white border-r border-gray-200 last:border-r-0 relative flex items-center justify-center h-12"
                      style={{ width: '60px', minWidth: '60px' }} // 每小时60px
                    >
                      {slot.time}
                    </div>
                  ))}
                </div>
                
                {/* 甘特图内容区域 */}
                <div className="relative">
                  {/* 当前时间虚线 - 贯穿整个甘特图 */}
                  {(() => {
                    const now = new Date();
                    const currentHour = now.getHours();
                    const currentMinute = now.getMinutes();
                    const currentMinutesFromMidnight = currentHour * 60 + currentMinute;
                    const position = currentMinutesFromMidnight; // 1px per minute
                    const timeString = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
                    
                    return (
                      <>
                        {/* 虚线 */}
                        <div 
                          className="absolute top-0 bottom-0 w-0.5 z-40 pointer-events-none"
                          style={{ 
                            left: `${position}px`,
                            background: 'repeating-linear-gradient(to bottom, red 0, red 6px, transparent 6px, transparent 12px)'
                          }}
                        />
                        {/* 时间标签 */}
                        <div 
                          className="absolute top-2 bg-red-500 text-white text-xs px-2 py-1 rounded-md shadow-lg z-50 whitespace-nowrap"
                          style={{ 
                            left: `${position + 4}px`,
                            transform: 'translateY(-50%)'
                          }}
                        >
                          {timeString}
                        </div>
                      </>
                    );
                  })()}
                  
                  {/* 航班条形图 */}
                  <div className="divide-y divide-gray-200">
                    {flights.map((flight) => (
                      <div key={flight.id} className="relative h-12 bg-gray-50 hover:bg-gray-100">
                        {/* 时间网格线 */}
                        {timeSlots.map((slot, index) => (
                          <div 
                            key={`grid-${flight.id}-${slot.time}`}
                            className="absolute top-0 bottom-0 border-r border-gray-200 last:border-r-0"
                            style={{ 
                              left: `${index * 60}px`, // 每小时60px
                              width: '60px'
                            }}
                          />
                        ))}
                        
                        <DraggableFlightBar
                          flight={flight}
                          onDragStart={handleDragStart}
                          onDragMove={handleDragMove}
                          onDragEnd={handleDragEnd}
                          isSelected={selectedFlights.has(flight.id)}
                          onSelect={handleFlightSelect}
                          conflicts={dragState.conflicts}
                        />
                        
                        {/* 拖拽预览 */}
                        {dragState.draggedItem?.id === flight.id && dragState.previewPosition && (
                          <>
                            <div 
                              className="absolute h-8 rounded-lg border-2 border-dashed border-blue-400 bg-blue-100/50 top-2 transition-all duration-200"
                              style={{ 
                                left: dragState.previewPosition.left, 
                                width: dragState.previewPosition.width,
                                minWidth: '30px'
                              }}
                            />
                            {/* 拖拽反馈提示 */}
                            {dragState.dragFeedback && dragState.dragFeedback.minutesMoved > 0 && (
                              <div 
                                className="absolute bg-gray-900 text-white text-xs px-2 py-1 rounded shadow-lg z-50 whitespace-nowrap"
                                style={{ 
                                  left: `calc(${dragState.previewPosition.left} + ${parseFloat(dragState.previewPosition.width.replace('px', '')) / 2}px)`,
                                  top: '-30px',
                                  transform: 'translateX(-50%)'
                                }}
                              >
                                {dragState.dragFeedback.direction === 'forward' ? '延后' : '提前'} {dragState.dragFeedback.minutesMoved} 分钟
                                {dragState.dragFeedback.dragType === 'resize-start' && ' (调整开始时间)'}
                                {dragState.dragFeedback.dragType === 'resize-end' && ' (调整结束时间)'}
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
