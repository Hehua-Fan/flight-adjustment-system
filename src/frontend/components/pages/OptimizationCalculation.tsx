"use client";

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { BarChart3, CheckCircle, Clock, AlertTriangle, Zap } from 'lucide-react';

interface OptimizationCalculationProps {
  stepData: any;
  detailedProgress: any[];
  isProcessing: boolean;
}

export function OptimizationCalculation({
  stepData,
  detailedProgress,
  isProcessing
}: OptimizationCalculationProps) {
  
  const isCompleted = stepData?.status === 'completed';
  const isRunning = stepData?.status === 'running';
  const isReady = stepData?.status !== 'pending';

  // 模拟优化进度数据
  const optimizationSteps = [
    { id: 1, name: '初始化优化模型', status: isCompleted ? 'completed' : isRunning ? 'running' : 'pending', progress: 100 },
    { id: 2, name: '载入约束条件', status: isCompleted ? 'completed' : isRunning ? 'completed' : 'pending', progress: 100 },
    { id: 3, name: '生成候选方案', status: isCompleted ? 'completed' : isRunning ? 'running' : 'pending', progress: isRunning ? 65 : isCompleted ? 100 : 0 },
    { id: 4, name: '评估方案质量', status: isCompleted ? 'completed' : 'pending', progress: isCompleted ? 100 : 0 },
    { id: 5, name: '优化排序', status: isCompleted ? 'completed' : 'pending', progress: isCompleted ? 100 : 0 }
  ];

  // 模拟优化结果数据
  const optimizationResults = {
    totalFlights: 1248,
    affectedFlights: 186,
    generatedPlans: 5,
    bestScore: 0.87,
    improvementRate: 0.23,
    executionTime: '2.3分钟'
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg p-6 border border-orange-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800">优化计算</h1>
            <p className="text-sm text-slate-600">生成多种调整方案</p>
          </div>
        </div>
        
        {/* 状态指示 */}
        {isCompleted ? (
          <div className="bg-white rounded-lg p-4 border border-emerald-200">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-500" />
              <span className="font-medium text-emerald-700">优化计算完成</span>
              <span className="text-sm text-slate-500">
                - 生成 {optimizationResults.generatedPlans} 个优化方案
              </span>
            </div>
          </div>
        ) : isRunning ? (
          <div className="bg-white rounded-lg p-4 border border-blue-200">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-blue-500 animate-pulse" />
              <span className="font-medium text-blue-700">优化计算中</span>
              <span className="text-sm text-slate-500">- 正在生成和评估方案</span>
            </div>
          </div>
        ) : !isReady ? (
          <div className="bg-white rounded-lg p-4 border border-amber-200">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <span className="font-medium text-amber-700">等待数据处理完成</span>
              <span className="text-sm text-slate-500">- 请先完成数据处理步骤</span>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg p-4 border border-slate-200">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-slate-500" />
              <span className="font-medium text-slate-700">等待执行</span>
              <span className="text-sm text-slate-500">- 准备进行优化计算</span>
            </div>
          </div>
        )}
      </div>

      {/* 优化进度 */}
      {(isRunning || isCompleted) && (
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">计算进度</h2>
            
            <div className="space-y-4">
              {optimizationSteps.map((step) => (
                <div key={step.id} className="flex items-center gap-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    step.status === 'completed' ? 'bg-emerald-100 text-emerald-600' :
                    step.status === 'running' ? 'bg-blue-100 text-blue-600' :
                    'bg-slate-100 text-slate-400'
                  }`}>
                    {step.status === 'completed' ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : step.status === 'running' ? (
                      <Clock className="w-4 h-4 animate-spin" />
                    ) : (
                      <span className="text-xs font-medium">{step.id}</span>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`font-medium ${
                        step.status === 'completed' ? 'text-emerald-700' :
                        step.status === 'running' ? 'text-blue-700' :
                        'text-slate-500'
                      }`}>
                        {step.name}
                      </span>
                      <span className="text-sm text-slate-500">{step.progress}%</span>
                    </div>
                    <Progress value={step.progress} className="h-2" />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 优化统计 */}
      {isCompleted && (
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">计算结果</h2>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <div className="text-blue-600 text-sm font-medium">总航班数</div>
                <div className="text-2xl font-bold text-blue-800">{optimizationResults.totalFlights}</div>
              </div>
              <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
                <div className="text-amber-600 text-sm font-medium">受影响航班</div>
                <div className="text-2xl font-bold text-amber-800">{optimizationResults.affectedFlights}</div>
              </div>
              <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-200">
                <div className="text-emerald-600 text-sm font-medium">生成方案</div>
                <div className="text-2xl font-bold text-emerald-800">{optimizationResults.generatedPlans}</div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                <div className="text-purple-600 text-sm font-medium">最佳方案评分</div>
                <div className="text-2xl font-bold text-purple-800">{optimizationResults.bestScore}</div>
                <div className="text-xs text-purple-600 mt-1">综合评分</div>
              </div>
              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                <div className="text-green-600 text-sm font-medium">预期改善率</div>
                <div className="text-2xl font-bold text-green-800">{(optimizationResults.improvementRate * 100).toFixed(1)}%</div>
                <div className="text-xs text-green-600 mt-1">相比基准方案</div>
              </div>
              <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
                <div className="text-indigo-600 text-sm font-medium">计算时间</div>
                <div className="text-2xl font-bold text-indigo-800">{optimizationResults.executionTime}</div>
                <div className="text-xs text-indigo-600 mt-1">总用时</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 方案预览 */}
      {isCompleted && (
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">生成方案预览</h2>
            
            <div className="space-y-3">
              {[
                { id: 1, name: '成本优先方案', score: 0.87, cost: '￥1,245,600', delay: '12分钟', satisfaction: '92%' },
                { id: 2, name: '时间优先方案', score: 0.84, cost: '￥1,389,200', delay: '8分钟', satisfaction: '95%' },
                { id: 3, name: '均衡优化方案', score: 0.85, cost: '￥1,312,800', delay: '10分钟', satisfaction: '93%' },
                { id: 4, name: '旅客优先方案', score: 0.82, cost: '￥1,456,300', delay: '6分钟', satisfaction: '97%' },
                { id: 5, name: '资源优化方案', score: 0.86, cost: '￥1,278,900', delay: '11分钟', satisfaction: '91%' }
              ].map((plan) => (
                <div key={plan.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200 hover:bg-slate-100 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center text-white font-bold">
                      {plan.id}
                    </div>
                    <div>
                      <div className="font-medium text-slate-800">{plan.name}</div>
                      <div className="text-sm text-slate-500">综合评分: {plan.score}</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-6 text-sm">
                    <div className="text-center">
                      <div className="text-slate-500">总成本</div>
                      <div className="font-medium">{plan.cost}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-slate-500">平均延误</div>
                      <div className="font-medium">{plan.delay}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-slate-500">旅客满意度</div>
                      <div className="font-medium">{plan.satisfaction}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 等待状态 */}
      {!isReady && (
        <Card>
          <CardContent className="p-12 text-center">
            <BarChart3 className="w-16 h-16 mx-auto text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-700 mb-2">等待优化计算</h3>
            <p className="text-slate-500">
              请先完成前置步骤，系统将自动开始优化计算
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
