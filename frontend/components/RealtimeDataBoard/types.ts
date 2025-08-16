// 航班状态类型定义
export interface FlightStatus {
  id: string;
  flightNumber: string;
  aircraft: string;
  route: string;
  departureTime: string;
  arrivalTime: string;
  actualDeparture?: string;
  actualArrival?: string;
  status: 'on-time' | 'slightly-late' | 'very-late' | 'delayed' | 'cancelled';
  delayReason?: string;
  gate?: string;
  passengers: number;
  progress: number; // 0-100
  crew?: string; // 机组
  runway?: string; // 跑道
  selected?: boolean; // 是否被选中
  priority?: 'high' | 'medium' | 'low'; // 优先级
  decisionStatus?: 'pending' | 'approved' | 'rejected' | 'auto'; // 决策状态
}

// 甘特图时间槽类型
export interface TimeSlot {
  time: string;
  hour: number;
}

// 拖拽类型定义
export type DragType = 'move' | 'resize-start' | 'resize-end' | 'vertical';

// 拖拽状态
export interface DragState {
  draggedItem: FlightStatus | null;
  dragType: DragType | null;
  originalPosition: { left: string; width: string } | null;
  previewPosition: { left: string; width: string } | null;
  conflicts: string[];
  // 拖拽反馈信息
  dragFeedback?: {
    minutesMoved: number;
    direction: 'forward' | 'backward' | 'none';
    dragType: DragType;
  };
}

// 资源行类型
export interface ResourceRow {
  id: string;
  type: 'crew' | 'runway' | 'gate';
  name: string;
  flights: FlightStatus[];
}

// 历史状态类型（用于撤销/重做）
export interface HistoryState {
  flights: FlightStatus[];
  timestamp: number;
}

// 列表视图的列定义
export interface ColumnConfig {
  key: string;
  title: string;
  width?: string;
  sortable?: boolean;
  filterable?: boolean;
}

// 警报和解决方案系统
export interface FlightAlert {
  id: string;
  flightId: string;
  type: 'delay' | 'crew_timeout' | 'resource_conflict' | 'weather' | 'maintenance';
  severity: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  predictedDelay: number; // 预测延误分钟数
  timestamp: number;
  solutions: Solution[];
}

export interface Solution {
  id: string;
  type: 'crew_change' | 'time_adjust' | 'route_change' | 'cancel' | 'resource_swap';
  title: string;
  description: string;
  timeSaved: number; // 节省的分钟数
  costImpact: 'low' | 'medium' | 'high';
  riskLevel: 'low' | 'medium' | 'high';
  details: string[];
  estimatedCost?: string;
  affectedPassengers?: number;
}

export interface AlertCardState {
  activeAlert: FlightAlert | null;
  showSolutions: boolean;
  selectedSolutions: Set<string>;
  compareMode: boolean;
}
