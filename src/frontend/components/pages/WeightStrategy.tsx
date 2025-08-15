"use client";

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Settings, CheckCircle, AlertTriangle } from 'lucide-react';
import { WeightStrategyPreview } from '@/components/WeightStrategyPreview';

interface WeightStrategyProps {
  processSteps: any[];
  analysisResult: any;
  onWeightsConfirmed: (weights: any) => void;
  testMode: boolean;
  onTestModeChange: (testMode: boolean) => void;
  weightConfirmation: any;
}

export function WeightStrategy({
  processSteps,
  analysisResult,
  onWeightsConfirmed,
  testMode,
  onTestModeChange,
  weightConfirmation
}: WeightStrategyProps) {
  
  const stepData = processSteps.find(step => step.id === 2) || processSteps[1];
  const isCompleted = stepData?.status === 'completed';
  const isReady = analysisResult && weightConfirmation.show;

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-6 border border-purple-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
            <Settings className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800">权重策略</h1>
            <p className="text-sm text-slate-600">生成优化权重配置方案</p>
          </div>
        </div>
        
        {/* 状态指示 */}
        {isCompleted ? (
          <div className="bg-white rounded-lg p-4 border border-emerald-200">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-500" />
              <span className="font-medium text-emerald-700">权重策略已确认</span>
              <span className="text-sm text-slate-500">
                - 已配置 {Object.keys(stepData.result?.weights || {}).length} 个权重方案
              </span>
            </div>
          </div>
        ) : !isReady ? (
          <div className="bg-white rounded-lg p-4 border border-amber-200">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <span className="font-medium text-amber-700">等待事件分析完成</span>
              <span className="text-sm text-slate-500">- 请先完成事件分析步骤</span>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg p-4 border border-blue-200">
            <div className="flex items-center gap-2">
              <Settings className="w-5 h-5 text-blue-500" />
              <span className="font-medium text-blue-700">权重策略配置中</span>
              <span className="text-sm text-slate-500">- 请配置权重参数并确认</span>
            </div>
          </div>
        )}
      </div>

      {/* 权重策略配置 */}
      {isReady ? (
        <WeightStrategyPreview 
          stepData={stepData}
          analysisResult={analysisResult}
          onWeightsConfirmed={onWeightsConfirmed}
          testMode={testMode}
          onTestModeChange={onTestModeChange}
        />
      ) : (
        <Card>
          <CardContent className="p-12 text-center">
            <Settings className="w-16 h-16 mx-auto text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-700 mb-2">权重策略配置</h3>
            <p className="text-slate-500 mb-6">
              {!analysisResult 
                ? '请先在事件分析页面完成事件分析，系统将自动生成权重策略方案'
                : '正在准备权重策略配置界面...'}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
