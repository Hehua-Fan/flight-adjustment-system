import { FlightStatus, ResourceRow } from './types';

// 状态颜色映射
export const statusColors = {
  'on-time': 'bg-green-500',
  'slightly-late': 'bg-yellow-500', 
  'very-late': 'bg-red-500',
  'delayed': 'bg-orange-500',
  'cancelled': 'bg-gray-500'
};

export const statusLabels = {
  'on-time': '准点',
  'slightly-late': '轻微延误',
  'very-late': '严重延误', 
  'delayed': '预计延误',
  'cancelled': '取消'
};

// 决策状态颜色和标签
export const decisionStatusColors = {
  'pending': 'bg-yellow-100 text-yellow-800',
  'approved': 'bg-green-100 text-green-800',
  'rejected': 'bg-red-100 text-red-800',
  'auto': 'bg-blue-100 text-blue-800'
};

export const decisionStatusLabels = {
  'pending': '待决策',
  'approved': '已批准',
  'rejected': '已拒绝',
  'auto': '自动处理'
};

// Mock数据
export const mockFlights: FlightStatus[] = [
  {
    id: 'BYT985',
    flightNumber: 'BYT985',
    aircraft: 'B738',
    route: 'ZGGG-ZSPD',
    departureTime: '07:00',
    arrivalTime: '09:30',
    actualDeparture: '07:05',
    actualArrival: '09:35',
    status: 'on-time',
    gate: 'A12',
    passengers: 168,
    progress: 100,
    crew: 'GTSTB',
    runway: '01L',
    priority: 'medium',
    decisionStatus: 'approved'
  },
  {
    id: 'MSR004',
    flightNumber: 'MSR004',
    aircraft: 'A320',
    route: 'ZSPD-ZBAA',
    departureTime: '08:15',
    arrivalTime: '11:00',
    actualDeparture: '08:20',
    status: 'slightly-late',
    gate: 'B15',
    passengers: 145,
    progress: 75,
    crew: 'GBYTZ',
    runway: '01R',
    priority: 'high',
    decisionStatus: 'pending'
  },
  {
    id: 'BYT987',
    flightNumber: 'BYT987',
    aircraft: 'B777',
    route: 'ZBAA-EGCC',
    departureTime: '09:30',
    arrivalTime: '15:45',
    status: 'delayed',
    delayReason: '流控',
    gate: 'T2-15',
    passengers: 280,
    progress: 30,
    crew: 'GTSTB',
    runway: '02L',
    priority: 'high',
    decisionStatus: 'approved'
  },
  {
    id: 'FQ111',
    flightNumber: 'FQ111',
    aircraft: 'A330',
    route: 'ZBAA-RJAA',
    departureTime: '10:20',
    arrivalTime: '15:30',
    actualDeparture: '11:45',
    status: 'very-late',
    delayReason: '机械故障',
    gate: 'C08',
    passengers: 210,
    progress: 60,
    crew: 'GTSTA',
    runway: '02R',
    priority: 'high',
    decisionStatus: 'rejected'
  },
  {
    id: 'FJ112',
    flightNumber: 'FJ112',
    aircraft: 'B787',
    route: 'ZBAA-EGLL',
    departureTime: '11:15',
    arrivalTime: '16:30',
    status: 'on-time',
    gate: 'T3-25',
    passengers: 295,
    progress: 45,
    crew: 'GTSTB',
    runway: '03L',
    priority: 'medium',
    decisionStatus: 'auto'
  },
  {
    id: 'KAL283',
    flightNumber: 'KAL283',
    aircraft: 'A321',
    route: 'ZBAA-RKSI',
    departureTime: '12:00',
    arrivalTime: '15:20',
    status: 'slightly-late',
    gate: 'B22',
    passengers: 180,
    progress: 20,
    crew: 'HL7624',
    runway: '03R',
    priority: 'low',
    decisionStatus: 'pending'
  },
  {
    id: 'DCM002',
    flightNumber: 'DCM002',
    aircraft: 'A350',
    route: 'ZBAA-LFPG',
    departureTime: '13:30',
    arrivalTime: '18:45',
    status: 'delayed',
    delayReason: '天气原因',
    gate: 'T3-12',
    passengers: 320,
    progress: 15,
    crew: 'GTSTA',
    runway: '01L',
    priority: 'high',
    decisionStatus: 'pending'
  },
  {
    id: 'ASL78K',
    flightNumber: 'ASL78K',
    aircraft: 'B777',
    route: 'ZBAA-KJFK',
    departureTime: '14:00',
    arrivalTime: '19:30',
    status: 'on-time',
    gate: 'T2-08',
    passengers: 350,
    progress: 25,
    crew: 'YRURS',
    runway: '02L',
    priority: 'medium',
    decisionStatus: 'auto'
  },
  {
    id: 'BYTEST',
    flightNumber: 'BYTEST',
    aircraft: 'A320',
    route: 'ZBAA-ZSSS',
    departureTime: '15:15',
    arrivalTime: '17:45',
    status: 'slightly-late',
    gate: 'A05',
    passengers: 160,
    progress: 10,
    crew: 'GTSTA',
    runway: '01R',
    priority: 'low',
    decisionStatus: 'approved'
  },
  {
    id: 'BYT006',
    flightNumber: 'BYT006',
    aircraft: 'B738',
    route: 'ZBAA-ZGGG',
    departureTime: '16:00',
    arrivalTime: '18:30',
    status: 'delayed',
    delayReason: '前序航班延误',
    gate: 'B18',
    passengers: 175,
    progress: 5,
    crew: 'GBYJ',
    runway: '03L',
    priority: 'medium',
    decisionStatus: 'pending'
  },
  {
    id: 'KAL032',
    flightNumber: 'KAL032',
    aircraft: 'A330',
    route: 'ZBAA-RKSI',
    departureTime: '17:30',
    arrivalTime: '20:00',
    status: 'on-time',
    gate: 'T2-20',
    passengers: 250,
    progress: 0,
    crew: 'HL8064',
    runway: '02R',
    priority: 'medium',
    decisionStatus: 'approved'
  },
  {
    id: 'RCL747',
    flightNumber: 'RCL747',
    aircraft: 'B787',
    route: 'ZBAA-VHHH',
    departureTime: '18:45',
    arrivalTime: '21:15',
    status: 'delayed',
    delayReason: '机场拥堵',
    gate: 'T3-30',
    passengers: 290,
    progress: 0,
    crew: 'GBYTI',
    runway: '03R',
    priority: 'high',
    decisionStatus: 'pending'
  }
];

// Mock资源数据
export const mockResources: ResourceRow[] = [
  { id: 'crew-gtstb', type: 'crew', name: 'GTSTB', flights: [] },
  { id: 'crew-gbytz', type: 'crew', name: 'GBYTZ', flights: [] },
  { id: 'crew-gtsta', type: 'crew', name: 'GTSTA', flights: [] },
  { id: 'crew-hl7624', type: 'crew', name: 'HL7624', flights: [] },
  { id: 'crew-yrurs', type: 'crew', name: 'YRURS', flights: [] },
  { id: 'crew-gbyj', type: 'crew', name: 'GBYJ', flights: [] },
  { id: 'runway-01l', type: 'runway', name: '01L', flights: [] },
  { id: 'runway-01r', type: 'runway', name: '01R', flights: [] },
  { id: 'runway-02l', type: 'runway', name: '02L', flights: [] },
  { id: 'runway-02r', type: 'runway', name: '02R', flights: [] },
  { id: 'runway-03l', type: 'runway', name: '03L', flights: [] },
  { id: 'runway-03r', type: 'runway', name: '03R', flights: [] },
];

// 模拟警报数据
import { FlightAlert } from './types';

export const mockAlerts: FlightAlert[] = [
  {
    id: 'ALT001',
    flightId: 'F001',
    type: 'crew_timeout',
    severity: 'high',
    title: '机组即将超时',
    description: '机组CA123当班时间即将达到最大限制，预计延误40分钟',
    predictedDelay: 40,
    timestamp: Date.now(),
    solutions: [
      {
        id: 'SOL001',
        type: 'crew_change',
        title: '更换备用机组',
        description: '调用备用机组CA-BACKUP-01执行航班',
        timeSaved: 25,
        costImpact: 'medium',
        riskLevel: 'low',
        details: ['备用机组已就位', '预计15分钟内完成交接', '机组资质符合要求'],
        estimatedCost: '¥15,000',
        affectedPassengers: 0
      },
      {
        id: 'SOL002',
        type: 'time_adjust',
        title: '调整起飞时间',
        description: '延后起飞时间至机组休息完毕',
        timeSaved: -40,
        costImpact: 'low',
        riskLevel: 'medium',
        details: ['机组休息2小时后执行', '需协调后续航班时刻', '可能影响连接航班'],
        estimatedCost: '¥5,000',
        affectedPassengers: 156
      },
      {
        id: 'SOL003',
        type: 'route_change',
        title: '优化航路减少飞行时间',
        description: '申请直飞航路，减少15分钟飞行时间',
        timeSaved: 15,
        costImpact: 'low',
        riskLevel: 'low',
        details: ['申请A593直飞航路', '燃油消耗略增', '空管协调中'],
        estimatedCost: '¥2,000',
        affectedPassengers: 0
      }
    ]
  },
  {
    id: 'ALT002',
    flightId: 'F002',
    type: 'weather',
    severity: 'medium',
    title: '目的地雷暴天气',
    description: '目的地机场出现雷暴，预计延误30分钟',
    predictedDelay: 30,
    timestamp: Date.now() - 300000,
    solutions: [
      {
        id: 'SOL004',
        type: 'time_adjust',
        title: '延后起飞等待天气好转',
        description: '等待雷暴过境后起飞',
        timeSaved: 0,
        costImpact: 'low',
        riskLevel: 'low',
        details: ['预计1小时后天气好转', '无额外成本', '安全优先'],
        estimatedCost: '¥0',
        affectedPassengers: 89
      },
      {
        id: 'SOL005',
        type: 'route_change',
        title: '备降附近机场',
        description: '备降至临近机场，待天气好转后继续',
        timeSaved: 45,
        costImpact: 'high',
        riskLevel: 'medium',
        details: ['备降杭州机场', '需安排地面交通', '增加运营成本'],
        estimatedCost: '¥50,000',
        affectedPassengers: 89
      }
    ]
  }
];
