"use client";

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Brain, Sparkles, CheckCircle, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

interface EventAnalysisProps {
  eventType: string;
  setEventType: (type: string) => void;
  eventDescription: string;
  setEventDescription: (description: string) => void;
  fileInfo: any;
  canStartAnalysis: () => boolean;
  handleAnalysis: () => Promise<void>;
  isProcessing: boolean;
  currentStep: number;
  weightConfirmation: any;
  onShowFileManager: () => void;
  analysisResult: any;
}

export function EventAnalysis({
  eventType,
  setEventType,
  eventDescription,
  setEventDescription,
  fileInfo,
  canStartAnalysis,
  handleAnalysis,
  isProcessing,
  currentStep,
  weightConfirmation,
  onShowFileManager,
  analysisResult
}: EventAnalysisProps) {
  
  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800">事件分析</h1>
            <p className="text-sm text-slate-600">AI智能分析事件类型和严重程度</p>
          </div>
        </div>
        
        {analysisResult && (
          <div className="bg-white rounded-lg p-4 border border-blue-200">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-5 h-5 text-emerald-500" />
              <span className="font-medium text-emerald-700">分析完成</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-slate-500">事件类型:</span>
                <span className="ml-1 font-medium">{analysisResult.event_type}</span>
              </div>
              <div>
                <span className="text-slate-500">严重程度:</span>
                <span className="ml-1 font-medium">{analysisResult.severity}</span>
              </div>
              <div>
                <span className="text-slate-500">置信度:</span>
                <span className="ml-1 font-medium">{analysisResult.confidence}%</span>
              </div>
              <div>
                <span className="text-slate-500">权重方案:</span>
                <span className="ml-1 font-medium">{Object.keys(analysisResult.weights || {}).length}个</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 数据源配置 */}
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">数据源配置</h2>
          
          {/* 数据状态概览 */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className={`w-4 h-4 rounded-full ${
                fileInfo?.cdm_files && fileInfo.cdm_files.length > 0 ? 'bg-blue-500' : 'bg-slate-300'
              }`}></div>
              <div>
                <div className="text-sm font-medium text-slate-700">CDM航班数据</div>
                <div className="text-xs text-slate-500">
                  {fileInfo?.cdm_files && fileInfo.cdm_files.length > 0 
                    ? `${fileInfo.cdm_files.length}个文件` 
                    : '未上传'}
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3 p-4 bg-emerald-50 rounded-lg border border-emerald-200">
              <div className={`w-4 h-4 rounded-full ${
                fileInfo?.constraint_files?.filter((f: any) => f.exists).length === 5 ? 'bg-emerald-500' : 'bg-slate-300'
              }`}></div>
              <div>
                <div className="text-sm font-medium text-slate-700">约束条件文件</div>
                <div className="text-xs text-slate-500">
                  {fileInfo?.constraint_files?.filter((f: any) => f.exists).length || 0}/5个
                </div>
              </div>
            </div>
          </div>

          {/* 详情按钮 */}
          <div className="text-center">
            <Button
              variant="outline"
              onClick={onShowFileManager}
              className="text-sm"
            >
              📁 数据管理详情
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 事件描述 */}
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">事件描述</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                选择事件类型
              </label>
              <Select value={eventType} onValueChange={setEventType}>
                <SelectTrigger>
                  <SelectValue placeholder="请选择事件类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="weather">天气 - 暴雨、雷电、大风、大雾等恶劣天气</SelectItem>
                  <SelectItem value="air_traffic_control">空管流控 - 航路拥堵、管制限制</SelectItem>
                  <SelectItem value="airport_operations">机场运行 - 跑道关闭、设备故障</SelectItem>
                  <SelectItem value="aircraft_malfunction">飞机故障 - 机械故障、技术问题</SelectItem>
                  <SelectItem value="crew_scheduling">机组调度 - 机组超时、人员调配</SelectItem>
                  <SelectItem value="other">其他 - 安全检查、政策变更等</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                详细描述事件情况
              </label>
              <Textarea
                value={eventDescription}
                onChange={(e) => setEventDescription(e.target.value)}
                placeholder="请详细描述遇到的事件情况，AI将智能分析并生成最优调整方案..."
                className="min-h-[120px] resize-none"
              />
            </div>

            <div className="pt-4">
              {!isProcessing ? (
                <Button 
                  onClick={handleAnalysis}
                  disabled={!canStartAnalysis() || !eventDescription.trim()}
                  className="w-full h-12 text-base"
                >
                  <Brain className="w-5 h-5 mr-2" />
                  开始AI智能分析
                </Button>
              ) : currentStep === 0 && !weightConfirmation.show ? (
                <Button 
                  disabled 
                  className="w-full h-12 text-base"
                >
                  <Sparkles className="w-5 h-5 mr-2 animate-spin" />
                  AI分析中...
                </Button>
              ) : weightConfirmation.show ? (
                <Button 
                  disabled 
                  className="w-full h-12 text-base"
                >
                  <Brain className="w-5 h-5 mr-2" />
                  等待权重确认...
                </Button>
              ) : (
                <Button 
                  disabled 
                  className="w-full h-12 text-base"
                >
                  <Sparkles className="w-5 h-5 mr-2 animate-spin" />
                  处理中...
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 处理状态 */}
      {isProcessing && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <Sparkles className="w-6 h-6 text-blue-500 animate-spin" />
              <div>
                <div className="font-medium text-blue-800">正在进行AI分析</div>
                <div className="text-sm text-blue-600">请稍候，系统正在分析事件并生成优化建议...</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
