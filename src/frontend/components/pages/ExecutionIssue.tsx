"use client";

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  FileText, 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  Download, 
  Send, 
  Plane, 
  Users, 
  Settings, 
  Calendar,
  Bell,
  CheckSquare,
  Mail
} from 'lucide-react';

interface ExecutionIssueProps {
  stepData: any;
  finalResult: any;
  selectedPlan: any;
}

export function ExecutionIssue({
  stepData,
  finalResult,
  selectedPlan
}: ExecutionIssueProps) {
  
  const [activeTab, setActiveTab] = useState('instructions');
  const [notificationsSent, setNotificationsSent] = useState(false);
  
  const isCompleted = stepData?.status === 'completed';
  const isRunning = stepData?.status === 'running';
  const isReady = stepData?.status !== 'pending';

  // 模拟执行指令数据
  const executionInstructions = {
    flightChanges: [
      {
        flightNumber: 'CA1234',
        originalTime: '14:30',
        newTime: '16:45',
        action: 'delay',
        reason: '天气原因',
        gate: 'A12 → A15',
        aircraft: 'B737-800',
        crew: '机组A-03',
        passengerCount: 156
      },
      {
        flightNumber: 'MU5678',
        originalTime: '15:15',
        newTime: '取消',
        action: 'cancel',
        reason: '机械故障',
        gate: 'B08',
        aircraft: 'A320',
        crew: '机组B-07',
        passengerCount: 142
      },
      {
        flightNumber: 'CZ9012',
        originalTime: '16:00',
        newTime: '15:30',
        action: 'advance',
        reason: '时刻调整',
        gate: 'C05 → C03',
        aircraft: 'B737-300 → A321',
        crew: '机组C-12',
        passengerCount: 189
      }
    ],
    resourceAllocations: {
      gates: [
        { gate: 'A15', flight: 'CA1234', time: '16:45', status: 'allocated' },
        { gate: 'C03', flight: 'CZ9012', time: '15:30', status: 'allocated' },
        { gate: 'B08', flight: '-', time: '-', status: 'released' }
      ],
      aircraft: [
        { aircraft: 'B737-800', flight: 'CA1234', status: 'reassigned' },
        { aircraft: 'A321', flight: 'CZ9012', status: 'reassigned' },
        { aircraft: 'A320', flight: '-', status: 'maintenance' }
      ],
      crew: [
        { crew: '机组A-03', flight: 'CA1234', shift: '延长2小时', status: 'confirmed' },
        { crew: '机组C-12', flight: 'CZ9012', shift: '提前30分钟', status: 'confirmed' },
        { crew: '机组B-07', flight: '-', shift: '待命', status: 'standby' }
      ]
    },
    notifications: [
      { type: 'passenger', count: 487, channel: '短信+APP推送', status: 'ready' },
      { type: 'crew', count: 23, channel: '内部通讯系统', status: 'ready' },
      { type: 'ground', count: 15, channel: '运控系统', status: 'ready' },
      { type: 'external', count: 8, channel: '合作伙伴API', status: 'ready' }
    ]
  };

  const handleSendNotifications = () => {
    setNotificationsSent(true);
    // 这里可以调用实际的通知发送API
  };

  const getActionBadge = (action: string) => {
    switch (action) {
      case 'delay':
        return <Badge className="bg-amber-100 text-amber-800 border-amber-300">延误</Badge>;
      case 'cancel':
        return <Badge className="bg-red-100 text-red-800 border-red-300">取消</Badge>;
      case 'advance':
        return <Badge className="bg-blue-100 text-blue-800 border-blue-300">提前</Badge>;
      default:
        return <Badge className="bg-slate-100 text-slate-800 border-slate-300">正常</Badge>;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'allocated':
      case 'reassigned':
      case 'confirmed':
      case 'ready':
        return 'text-emerald-600 bg-emerald-50';
      case 'released':
      case 'standby':
        return 'text-amber-600 bg-amber-50';
      case 'maintenance':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-slate-600 bg-slate-50';
    }
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="bg-gradient-to-r from-emerald-50 to-green-50 rounded-lg p-6 border border-emerald-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-lg flex items-center justify-center">
            <FileText className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800">执行下发</h1>
            <p className="text-sm text-slate-600">生成执行指令和报告</p>
          </div>
        </div>
        
        {/* 状态指示 */}
        {isCompleted ? (
          <div className="bg-white rounded-lg p-4 border border-emerald-200">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-500" />
              <span className="font-medium text-emerald-700">执行指令已下发</span>
              <span className="text-sm text-slate-500">
                - 所有相关方已收到通知
              </span>
            </div>
          </div>
        ) : isRunning ? (
          <div className="bg-white rounded-lg p-4 border border-blue-200">
            <div className="flex items-center gap-2">
              <Send className="w-5 h-5 text-blue-500 animate-pulse" />
              <span className="font-medium text-blue-700">正在生成执行指令</span>
              <span className="text-sm text-slate-500">- 准备下发执行通知</span>
            </div>
          </div>
        ) : !isReady ? (
          <div className="bg-white rounded-lg p-4 border border-amber-200">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <span className="font-medium text-amber-700">等待方案决策完成</span>
              <span className="text-sm text-slate-500">- 请先完成方案决策步骤</span>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg p-4 border border-slate-200">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-slate-500" />
              <span className="font-medium text-slate-700">等待执行</span>
              <span className="text-sm text-slate-500">- 准备生成执行指令</span>
            </div>
          </div>
        )}
      </div>

      {/* 执行内容 */}
      {(isRunning || isCompleted) && (
        <Card>
          <CardContent className="p-6">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="instructions" className="flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  执行指令
                </TabsTrigger>
                <TabsTrigger value="resources" className="flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  资源调配
                </TabsTrigger>
                <TabsTrigger value="notifications" className="flex items-center gap-2">
                  <Bell className="w-4 h-4" />
                  通知下发
                </TabsTrigger>
                <TabsTrigger value="reports" className="flex items-center gap-2">
                  <Download className="w-4 h-4" />
                  报告下载
                </TabsTrigger>
              </TabsList>

              {/* 执行指令 */}
              <TabsContent value="instructions" className="space-y-4">
                <h3 className="text-lg font-semibold text-slate-800">航班调整指令</h3>
                
                <div className="space-y-3">
                  {executionInstructions.flightChanges.map((flight, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-slate-50">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <Plane className="w-5 h-5 text-blue-600" />
                          <span className="font-semibold text-slate-800">{flight.flightNumber}</span>
                          {getActionBadge(flight.action)}
                        </div>
                        <Badge variant="outline" className="text-slate-600">
                          {flight.passengerCount}名旅客
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-slate-500">时间调整:</span>
                          <div className="font-medium">
                            {flight.originalTime} → {flight.newTime}
                          </div>
                        </div>
                        <div>
                          <span className="text-slate-500">登机口:</span>
                          <div className="font-medium">{flight.gate}</div>
                        </div>
                        <div>
                          <span className="text-slate-500">机型/机组:</span>
                          <div className="font-medium">{flight.aircraft}</div>
                          <div className="text-xs text-slate-400">{flight.crew}</div>
                        </div>
                        <div>
                          <span className="text-slate-500">调整原因:</span>
                          <div className="font-medium">{flight.reason}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </TabsContent>

              {/* 资源调配 */}
              <TabsContent value="resources" className="space-y-6">
                <h3 className="text-lg font-semibold text-slate-800">资源重新分配</h3>
                
                {/* 登机口分配 */}
                <div>
                  <h4 className="font-medium text-slate-800 mb-3 flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    登机口分配
                  </h4>
                  <div className="space-y-2">
                    {executionInstructions.resourceAllocations.gates.map((gate, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded border">
                        <div className="flex items-center gap-4">
                          <span className="font-medium text-slate-800">{gate.gate}</span>
                          <span className="text-slate-600">{gate.flight}</span>
                          <span className="text-sm text-slate-500">{gate.time}</span>
                        </div>
                        <Badge className={getStatusColor(gate.status)}>
                          {gate.status === 'allocated' ? '已分配' : 
                           gate.status === 'released' ? '已释放' : gate.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 飞机调配 */}
                <div>
                  <h4 className="font-medium text-slate-800 mb-3 flex items-center gap-2">
                    <Plane className="w-4 h-4" />
                    飞机调配
                  </h4>
                  <div className="space-y-2">
                    {executionInstructions.resourceAllocations.aircraft.map((aircraft, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded border">
                        <div className="flex items-center gap-4">
                          <span className="font-medium text-slate-800">{aircraft.aircraft}</span>
                          <span className="text-slate-600">{aircraft.flight}</span>
                        </div>
                        <Badge className={getStatusColor(aircraft.status)}>
                          {aircraft.status === 'reassigned' ? '重新分配' : 
                           aircraft.status === 'maintenance' ? '维护' : aircraft.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 机组调配 */}
                <div>
                  <h4 className="font-medium text-slate-800 mb-3 flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    机组调配
                  </h4>
                  <div className="space-y-2">
                    {executionInstructions.resourceAllocations.crew.map((crew, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded border">
                        <div className="flex items-center gap-4">
                          <span className="font-medium text-slate-800">{crew.crew}</span>
                          <span className="text-slate-600">{crew.flight}</span>
                          <span className="text-sm text-slate-500">{crew.shift}</span>
                        </div>
                        <Badge className={getStatusColor(crew.status)}>
                          {crew.status === 'confirmed' ? '已确认' : 
                           crew.status === 'standby' ? '待命' : crew.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </TabsContent>

              {/* 通知下发 */}
              <TabsContent value="notifications" className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-slate-800">通知下发状态</h3>
                  <Button 
                    onClick={handleSendNotifications}
                    disabled={notificationsSent}
                    className="bg-blue-500 hover:bg-blue-600"
                  >
                    {notificationsSent ? (
                      <>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        已发送
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        发送通知
                      </>
                    )}
                  </Button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {executionInstructions.notifications.map((notification, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-slate-50">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          {notification.type === 'passenger' && <Users className="w-5 h-5 text-blue-600" />}
                          {notification.type === 'crew' && <Users className="w-5 h-5 text-green-600" />}
                          {notification.type === 'ground' && <Settings className="w-5 h-5 text-orange-600" />}
                          {notification.type === 'external' && <Mail className="w-5 h-5 text-purple-600" />}
                          <span className="font-medium text-slate-800">
                            {notification.type === 'passenger' ? '旅客通知' :
                             notification.type === 'crew' ? '机组通知' :
                             notification.type === 'ground' ? '地面服务' : '外部合作方'}
                          </span>
                        </div>
                        <Badge className={`${notificationsSent ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
                          {notificationsSent ? '已发送' : '待发送'}
                        </Badge>
                      </div>
                      <div className="text-sm text-slate-600">
                        <div>接收对象: {notification.count} 个</div>
                        <div>发送渠道: {notification.channel}</div>
                      </div>
                    </div>
                  ))}
                </div>

                {notificationsSent && (
                  <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-emerald-600" />
                      <span className="font-medium text-emerald-800">通知发送完成</span>
                    </div>
                    <div className="text-sm text-emerald-700 mt-1">
                      所有相关方已收到调整通知，执行指令正式生效
                    </div>
                  </div>
                )}
              </TabsContent>

              {/* 报告下载 */}
              <TabsContent value="reports" className="space-y-4">
                <h3 className="text-lg font-semibold text-slate-800">执行报告</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { name: '航班调整执行报告', type: '详细记录所有航班变更信息', format: 'PDF', size: '2.3MB' },
                    { name: '资源重分配清单', type: '登机口、飞机、机组分配详情', format: 'Excel', size: '1.8MB' },
                    { name: '旅客影响统计', type: '受影响旅客统计和补偿方案', format: 'PDF', size: '1.5MB' },
                    { name: '成本效益分析', type: '本次调整的成本收益分析', format: 'Excel', size: '2.1MB' },
                    { name: '执行时间轴', type: '完整的执行时间线和关键节点', format: 'PDF', size: '1.2MB' },
                    { name: '系统日志', type: '完整的系统操作和决策日志', format: 'TXT', size: '0.8MB' }
                  ].map((report, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-white hover:bg-slate-50 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium text-slate-800 mb-1">{report.name}</h4>
                          <p className="text-sm text-slate-600 mb-2">{report.type}</p>
                          <div className="flex items-center gap-4 text-xs text-slate-500">
                            <span>格式: {report.format}</span>
                            <span>大小: {report.size}</span>
                          </div>
                        </div>
                        <Button variant="outline" size="sm" className="ml-4">
                          <Download className="w-4 h-4 mr-1" />
                          下载
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="w-5 h-5 text-blue-600" />
                    <span className="font-medium text-blue-800">批量下载</span>
                  </div>
                  <div className="text-sm text-blue-700 mb-3">
                    下载包含所有执行相关文档的完整报告包
                  </div>
                  <Button className="bg-blue-500 hover:bg-blue-600">
                    <Download className="w-4 h-4 mr-2" />
                    下载完整报告包 (ZIP, 8.7MB)
                  </Button>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* 等待状态 */}
      {!isReady && (
        <Card>
          <CardContent className="p-12 text-center">
            <FileText className="w-16 h-16 mx-auto text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-700 mb-2">等待执行下发</h3>
            <p className="text-slate-500">
              请先完成前置步骤，系统将自动生成执行指令
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
