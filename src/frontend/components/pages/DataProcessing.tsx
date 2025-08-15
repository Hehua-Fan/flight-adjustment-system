"use client";

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Upload, CheckCircle, Clock, AlertTriangle } from 'lucide-react';

interface DataProcessingProps {
  stepData: any;
  analysisResult: any;
  dataStatistics: any;
}

export function DataProcessing({
  stepData,
  analysisResult,
  dataStatistics
}: DataProcessingProps) {
  
  const isCompleted = stepData?.status === 'completed';
  const isRunning = stepData?.status === 'running';
  const isReady = analysisResult && stepData?.status !== 'pending';

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center">
            <Upload className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800">数据处理</h1>
            <p className="text-sm text-slate-600">加载航班数据和约束条件</p>
          </div>
        </div>
        
        {/* 状态指示 */}
        {isCompleted ? (
          <div className="bg-white rounded-lg p-4 border border-emerald-200">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-500" />
              <span className="font-medium text-emerald-700">数据处理完成</span>
              <span className="text-sm text-slate-500">
                {dataStatistics?.total_flights 
                  ? `- 已加载 ${dataStatistics.total_flights} 个航班数据`
                  : '- 数据处理完成'}
              </span>
            </div>
          </div>
        ) : isRunning ? (
          <div className="bg-white rounded-lg p-4 border border-blue-200">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-500 animate-spin" />
              <span className="font-medium text-blue-700">数据处理中</span>
              <span className="text-sm text-slate-500">- 正在加载和验证数据</span>
            </div>
          </div>
        ) : !isReady ? (
          <div className="bg-white rounded-lg p-4 border border-amber-200">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <span className="font-medium text-amber-700">等待权重策略确认</span>
              <span className="text-sm text-slate-500">- 请先完成权重策略配置</span>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg p-4 border border-slate-200">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-slate-500" />
              <span className="font-medium text-slate-700">等待执行</span>
              <span className="text-sm text-slate-500">- 准备进行数据处理</span>
            </div>
          </div>
        )}
      </div>

      {/* 数据处理详情 */}
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">处理详情</h2>
          
          {isCompleted && dataStatistics ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <div className="text-blue-600 text-sm font-medium">航班总数</div>
                <div className="text-2xl font-bold text-blue-800">
                  {dataStatistics.total_flights}
                </div>
              </div>
              <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-200">
                <div className="text-emerald-600 text-sm font-medium">正常航班</div>
                <div className="text-2xl font-bold text-emerald-800">
                  {dataStatistics.normal_flights}
                </div>
              </div>
              <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
                <div className="text-amber-600 text-sm font-medium">受影响航班</div>
                <div className="text-2xl font-bold text-amber-800">
                  {dataStatistics.affected_flights}
                </div>
              </div>
            </div>
          ) : isCompleted && !dataStatistics ? (
            <div className="text-center py-8">
              <AlertTriangle className="w-16 h-16 mx-auto text-amber-300 mb-4" />
              <h3 className="text-lg font-medium text-slate-700 mb-2">数据统计信息不可用</h3>
              <p className="text-slate-500">
                数据处理已完成，但统计信息未从后端获取到
              </p>
            </div>
          ) : isRunning ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <Upload className="w-4 h-4 text-blue-600" />
                </div>
                <div>
                  <div className="font-medium text-slate-800">加载CDM航班数据</div>
                  <div className="text-sm text-slate-500">正在读取和解析航班数据...</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
                <div>
                  <div className="font-medium text-slate-800">验证约束条件</div>
                  <div className="text-sm text-slate-500">已验证所有约束条件文件</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center animate-pulse">
                  <Clock className="w-4 h-4 text-amber-600" />
                </div>
                <div>
                  <div className="font-medium text-slate-800">数据预处理</div>
                  <div className="text-sm text-slate-500">正在清洗和标准化数据格式...</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <Upload className="w-16 h-16 mx-auto text-slate-300 mb-4" />
              <h3 className="text-lg font-medium text-slate-700 mb-2">等待数据处理</h3>
              <p className="text-slate-500">
                {!isReady 
                  ? '请先完成前置步骤，系统将自动开始数据处理'
                  : '数据处理将在权重策略确认后自动开始'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 数据概览 */}
      {isCompleted && (
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">数据概览</h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">处理时间:</span>
                <span className="font-medium">
                  {stepData?.result?.timestamp 
                    ? new Date(stepData.result.timestamp).toLocaleString()
                    : new Date().toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">数据来源:</span>
                <span className="font-medium">
                  {stepData?.result?.data_source || 'CDM航班数据 + 约束条件文件'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">处理状态:</span>
                <span className="font-medium text-emerald-600">成功</span>
              </div>
              {dataStatistics?.total_flights && (
                <div className="flex justify-between">
                  <span className="text-slate-600">数据记录数:</span>
                  <span className="font-medium">
                    {dataStatistics.total_flights.toLocaleString()} 条航班记录
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
