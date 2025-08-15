"use client";

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, CheckCircle, Clock, AlertTriangle, Crown, Star, ThumbsUp, BarChart, DollarSign, Timer, Users } from 'lucide-react';

interface PlanDecisionProps {
  stepData: any;
  finalResult: any;
  onPlanSelected?: (planId: string) => void;
}

export function PlanDecision({
  stepData,
  finalResult,
  onPlanSelected
}: PlanDecisionProps) {
  
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  
  const isCompleted = stepData?.status === 'completed';
  const isRunning = stepData?.status === 'running';
  const isReady = stepData?.status !== 'pending';

  // 模拟方案数据
  const plans = [
    {
      id: 'plan-1',
      name: '成本优先方案',
      type: 'cost',
      recommended: true,
      score: 0.87,
      rank: 1,
      metrics: {
        totalCost: 1245600,
        avgDelay: 12,
        satisfaction: 92,
        efficiency: 89,
        riskLevel: 'low'
      },
      details: {
        canceledFlights: 8,
        delayedFlights: 42,
        rescheduledFlights: 136,
        passengerImpact: 2340,
        crewAdjustments: 23,
        aircraftChanges: 15
      },
      description: '优先控制总成本，在保证基本服务质量的前提下最小化运营支出'
    },
    {
      id: 'plan-2',
      name: '时间优先方案',
      type: 'time',
      recommended: false,
      score: 0.84,
      rank: 2,
      metrics: {
        totalCost: 1389200,
        avgDelay: 8,
        satisfaction: 95,
        efficiency: 92,
        riskLevel: 'medium'
      },
      details: {
        canceledFlights: 12,
        delayedFlights: 28,
        rescheduledFlights: 146,
        passengerImpact: 1980,
        crewAdjustments: 31,
        aircraftChanges: 22
      },
      description: '最小化延误时间，提高准点率和旅客满意度'
    },
    {
      id: 'plan-3',
      name: '均衡优化方案',
      type: 'balanced',
      recommended: false,
      score: 0.85,
      rank: 3,
      metrics: {
        totalCost: 1312800,
        avgDelay: 10,
        satisfaction: 93,
        efficiency: 90,
        riskLevel: 'low'
      },
      details: {
        canceledFlights: 10,
        delayedFlights: 35,
        rescheduledFlights: 141,
        passengerImpact: 2160,
        crewAdjustments: 27,
        aircraftChanges: 18
      },
      description: '在成本、时间和服务质量之间寻求最佳平衡'
    }
  ];

  const handlePlanSelect = (planId: string) => {
    setSelectedPlan(planId);
    onPlanSelected?.(planId);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'cost': return <DollarSign className="w-4 h-4" />;
      case 'time': return <Timer className="w-4 h-4" />;
      case 'balanced': return <BarChart className="w-4 h-4" />;
      default: return <Star className="w-4 h-4" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'cost': return 'text-emerald-600 bg-emerald-50 border-emerald-200';
      case 'time': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'balanced': return 'text-purple-600 bg-purple-50 border-purple-200';
      default: return 'text-slate-600 bg-slate-50 border-slate-200';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-emerald-600 bg-emerald-50';
      case 'medium': return 'text-amber-600 bg-amber-50';
      case 'high': return 'text-red-600 bg-red-50';
      default: return 'text-slate-600 bg-slate-50';
    }
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-lg p-6 border border-indigo-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800">方案决策</h1>
            <p className="text-sm text-slate-600">智能选择最优方案</p>
          </div>
        </div>
        
        {/* 状态指示 */}
        {isCompleted ? (
          <div className="bg-white rounded-lg p-4 border border-emerald-200">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-500" />
              <span className="font-medium text-emerald-700">方案决策完成</span>
              <span className="text-sm text-slate-500">
                - 已选择最优执行方案
              </span>
            </div>
          </div>
        ) : isRunning ? (
          <div className="bg-white rounded-lg p-4 border border-blue-200">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-500 animate-pulse" />
              <span className="font-medium text-blue-700">方案评估中</span>
              <span className="text-sm text-slate-500">- 正在分析和排序方案</span>
            </div>
          </div>
        ) : !isReady ? (
          <div className="bg-white rounded-lg p-4 border border-amber-200">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <span className="font-medium text-amber-700">等待优化计算完成</span>
              <span className="text-sm text-slate-500">- 请先完成优化计算步骤</span>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg p-4 border border-slate-200">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-slate-500" />
              <span className="font-medium text-slate-700">等待执行</span>
              <span className="text-sm text-slate-500">- 准备进行方案决策</span>
            </div>
          </div>
        )}
      </div>

      {/* AI推荐 */}
      {(isRunning || isCompleted) && (
        <Card className="border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <Crown className="w-6 h-6 text-amber-600" />
              <h2 className="text-lg font-semibold text-slate-800">AI智能推荐</h2>
            </div>
            
            <div className="bg-white rounded-lg p-4 border border-amber-200">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-amber-500 to-orange-500 rounded-lg flex items-center justify-center text-white font-bold text-lg">
                  1
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-slate-800">成本优先方案</h3>
                    <Badge className="bg-amber-100 text-amber-800 border-amber-300">
                      <Crown className="w-3 h-3 mr-1" />
                      AI推荐
                    </Badge>
                    <Badge variant="outline" className="text-emerald-600 border-emerald-300">
                      评分: 0.87
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-600 mb-3">
                    基于当前事件特征和历史数据分析，该方案在成本控制和风险管理方面表现最佳，
                    预计可减少运营成本23%，同时保持92%的旅客满意度。
                  </p>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-slate-500">总成本</div>
                      <div className="font-semibold text-emerald-600">￥124.6万</div>
                    </div>
                    <div className="text-center">
                      <div className="text-slate-500">平均延误</div>
                      <div className="font-semibold text-blue-600">12分钟</div>
                    </div>
                    <div className="text-center">
                      <div className="text-slate-500">旅客满意度</div>
                      <div className="font-semibold text-amber-600">92%</div>
                    </div>
                    <div className="text-center">
                      <div className="text-slate-500">风险等级</div>
                      <div className="font-semibold text-emerald-600">低</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 方案对比 */}
      {(isRunning || isCompleted) && (
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">方案对比与选择</h2>
            
            <div className="space-y-4">
              {plans.map((plan) => (
                <div 
                  key={plan.id} 
                  className={`border rounded-lg p-6 transition-all cursor-pointer hover:shadow-md ${
                    selectedPlan === plan.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : plan.recommended 
                        ? 'border-amber-300 bg-amber-50' 
                        : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                  onClick={() => handlePlanSelect(plan.id)}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-white ${
                        plan.rank === 1 ? 'bg-gradient-to-br from-amber-500 to-orange-500' :
                        plan.rank === 2 ? 'bg-gradient-to-br from-slate-400 to-slate-500' :
                        'bg-gradient-to-br from-amber-600 to-amber-700'
                      }`}>
                        {plan.rank}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-slate-800">{plan.name}</h3>
                          {plan.recommended && (
                            <Badge className="bg-amber-100 text-amber-800 border-amber-300">
                              <Crown className="w-3 h-3 mr-1" />
                              推荐
                            </Badge>
                          )}
                          <Badge variant="outline" className={getTypeColor(plan.type)}>
                            {getTypeIcon(plan.type)}
                            <span className="ml-1">
                              {plan.type === 'cost' ? '成本导向' : 
                               plan.type === 'time' ? '时间导向' : '均衡导向'}
                            </span>
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-600 mt-1">{plan.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-right">
                        <div className="text-sm text-slate-500">综合评分</div>
                        <div className="text-lg font-bold text-slate-800">{plan.score}</div>
                      </div>
                      {selectedPlan === plan.id && (
                        <CheckCircle className="w-6 h-6 text-blue-500" />
                      )}
                    </div>
                  </div>

                  {/* 关键指标 */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
                    <div className="text-center p-3 bg-white rounded border">
                      <DollarSign className="w-5 h-5 mx-auto text-emerald-600 mb-1" />
                      <div className="text-xs text-slate-500">总成本</div>
                      <div className="font-semibold text-emerald-600">￥{(plan.metrics.totalCost / 10000).toFixed(1)}万</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded border">
                      <Timer className="w-5 h-5 mx-auto text-blue-600 mb-1" />
                      <div className="text-xs text-slate-500">平均延误</div>
                      <div className="font-semibold text-blue-600">{plan.metrics.avgDelay}分钟</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded border">
                      <Users className="w-5 h-5 mx-auto text-purple-600 mb-1" />
                      <div className="text-xs text-slate-500">旅客满意度</div>
                      <div className="font-semibold text-purple-600">{plan.metrics.satisfaction}%</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded border">
                      <TrendingUp className="w-5 h-5 mx-auto text-indigo-600 mb-1" />
                      <div className="text-xs text-slate-500">运营效率</div>
                      <div className="font-semibold text-indigo-600">{plan.metrics.efficiency}%</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded border">
                      <AlertTriangle className="w-5 h-5 mx-auto text-slate-600 mb-1" />
                      <div className="text-xs text-slate-500">风险等级</div>
                      <div className={`font-semibold text-xs px-2 py-1 rounded ${getRiskColor(plan.metrics.riskLevel)}`}>
                        {plan.metrics.riskLevel === 'low' ? '低' : 
                         plan.metrics.riskLevel === 'medium' ? '中' : '高'}
                      </div>
                    </div>
                  </div>

                  {/* 详细数据 */}
                  <div className="bg-slate-50 rounded p-3">
                    <div className="grid grid-cols-3 md:grid-cols-6 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">取消航班:</span>
                        <span className="ml-1 font-medium">{plan.details.canceledFlights}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">延误航班:</span>
                        <span className="ml-1 font-medium">{plan.details.delayedFlights}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">改期航班:</span>
                        <span className="ml-1 font-medium">{plan.details.rescheduledFlights}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">影响旅客:</span>
                        <span className="ml-1 font-medium">{plan.details.passengerImpact}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">机组调整:</span>
                        <span className="ml-1 font-medium">{plan.details.crewAdjustments}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">机型更换:</span>
                        <span className="ml-1 font-medium">{plan.details.aircraftChanges}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* 确认按钮 */}
            {selectedPlan && (
              <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-blue-800">
                      已选择: {plans.find(p => p.id === selectedPlan)?.name}
                    </div>
                    <div className="text-sm text-blue-600">
                      确认后将进入执行下发阶段
                    </div>
                  </div>
                  <Button className="bg-blue-500 hover:bg-blue-600">
                    <CheckCircle className="w-4 h-4 mr-2" />
                    确认选择
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 等待状态 */}
      {!isReady && (
        <Card>
          <CardContent className="p-12 text-center">
            <TrendingUp className="w-16 h-16 mx-auto text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-700 mb-2">等待方案决策</h3>
            <p className="text-slate-500">
              请先完成前置步骤，系统将自动开始方案决策
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
