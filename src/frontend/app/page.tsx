"use client";

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Plane, 
  Brain, 
  CheckCircle,
  AlertTriangle,
  Sparkles
} from 'lucide-react';

// API配置
const API_BASE_URL = 'http://localhost:8000';

interface ProcessStep {
  id: number;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  description: string;
  result?: {
    event_type?: string;
    severity?: string;
    confidence?: number;
  };
}

interface FlightAdjustment {
  flight_number: string;
  adjustment_action: string;
  status: string;
  additional_delay_minutes: number;
  reason: string;
}

export default function HomePage() {
  const [eventDescription, setEventDescription] = useState('');
  const [selectedPreset, setSelectedPreset] = useState('');
  const [presetEvents, setPresetEvents] = useState<Array<{id: string; name: string; description: string; severity: string}>>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [processSteps, setProcessSteps] = useState<ProcessStep[]>([
    { id: 1, name: '事件分析', status: 'pending', description: 'AI智能分析事件类型和严重程度' },
    { id: 2, name: '权重策略', status: 'pending', description: '生成优化权重配置方案' },
    { id: 3, name: '数据处理', status: 'pending', description: '加载航班数据和约束条件' },
    { id: 4, name: '优化计算', status: 'pending', description: '生成多种调整方案' },
    { id: 5, name: '方案决策', status: 'pending', description: '智能选择最优方案' },
    { id: 6, name: '执行下发', status: 'pending', description: '生成执行指令和报告' }
  ]);
  const [finalResult, setFinalResult] = useState<{
    chosen_plan_name: string;
    summary: {
      total_flights: number;
      normal_flights: number;
      delayed_flights: number;
      cancelled_flights: number;
      cost_saving: number;
    };
    solutions: Record<string, FlightAdjustment[]>;
  } | null>(null);

  // 加载预设事件
  useEffect(() => {
    const loadPresets = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/events/presets`);
        const events = await response.json();
        setPresetEvents(events);
      } catch (error) {
        console.error('Failed to load presets:', error);
      }
    };
    loadPresets();
  }, []);

  const updateStepStatus = (stepId: number, status: ProcessStep['status'], result?: ProcessStep['result']) => {
    setProcessSteps(prev => prev.map(step => 
      step.id === stepId ? { ...step, status, result } : step
    ));
  };

  const startProcess = async () => {
    if (!eventDescription.trim()) {
      alert('请输入事件描述或选择预设事件');
      return;
    }

    setIsProcessing(true);
    setCurrentStep(1);
    setFinalResult(null);

    try {
      // 步骤1: 事件分析
      updateStepStatus(1, 'running');
      await new Promise(resolve => setTimeout(resolve, 800));
      
      const analysisResponse = await fetch(`${API_BASE_URL}/api/events/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: eventDescription })
      });
      const analysisResult = await analysisResponse.json();
      updateStepStatus(1, 'completed', analysisResult);
      setCurrentStep(2);

      // 步骤2-6: 权重策略 -> 执行下发
      for (let step = 2; step <= 6; step++) {
        await new Promise(resolve => setTimeout(resolve, 600));
        updateStepStatus(step, 'running');
        setCurrentStep(step);
        
        if (step === 6) {
          // 最后一步：运行完整优化
          const optimizationResponse = await fetch(`${API_BASE_URL}/api/optimization/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              event_description: eventDescription,
              weights: analysisResult.weights
            })
          });
          const optimizationResult = await optimizationResponse.json();
          updateStepStatus(step, 'completed', optimizationResult);
          setFinalResult(optimizationResult);
        } else {
          updateStepStatus(step, 'completed');
        }
      }

            } catch (error) {
          console.error('Process failed:', error);
          updateStepStatus(currentStep, 'error');
          alert(`处理失败: ${error instanceof Error ? error.message : '未知错误'}`);
        } finally {
      setIsProcessing(false);
    }
  };

  const resetProcess = () => {
    setProcessSteps(prev => prev.map(step => ({ ...step, status: 'pending', result: undefined })));
    setCurrentStep(0);
    setFinalResult(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-6 py-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center">
              <Plane className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">智能航班调整系统</h1>
              <p className="text-gray-500 text-sm">AI-Powered Flight Adjustment Platform</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Event Input Section */}
        <Card className="mb-8">
          <CardContent className="p-8">
            <div className="text-center mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">描述航空运营事件</h2>
              <p className="text-gray-500">详细描述遇到的事件情况，AI将智能分析并生成最优调整方案</p>
            </div>

            <div className="space-y-6">
              {/* Preset Events */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">预设事件</label>
                <Select 
                  value={selectedPreset} 
                  onValueChange={(value) => {
                    setSelectedPreset(value);
                    const event = presetEvents.find((e) => e.id === value);
                    if (event) {
                      setEventDescription(event.description);
                    }
                  }}
                >
                  <SelectTrigger className="h-12">
                    <SelectValue placeholder="选择常见事件类型（可选）" />
                  </SelectTrigger>
                  <SelectContent>
                    {presetEvents.map((event) => (
                      <SelectItem key={event.id} value={event.id}>
                        <div className="flex items-center gap-2">
                          <span>{event.name}</span>
                          <Badge variant="outline" className="text-xs">{event.severity}</Badge>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Custom Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">事件描述</label>
                <Textarea
                  placeholder="请详细描述遇到的航空运营事件，例如：上海区域因雷雨天气实施流量控制，预计影响2小时，涉及进出港航班约200架次..."
                  value={eventDescription}
                  onChange={(e) => setEventDescription(e.target.value)}
                  rows={4}
                  className="resize-none"
                />
              </div>

              {/* Action Button */}
              <div className="flex justify-center pt-4">
                {!isProcessing ? (
                  <Button 
                    onClick={startProcess}
                    size="lg" 
                    className="h-12 px-8 bg-blue-500 hover:bg-blue-600"
                    disabled={!eventDescription.trim()}
                  >
                    <Brain className="w-5 h-5 mr-2" />
                    开始智能分析
                  </Button>
                ) : (
                  <Button 
                    size="lg" 
                    className="h-12 px-8" 
                    disabled
                  >
                    <Sparkles className="w-5 h-5 mr-2 animate-spin" />
                    处理中...
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Process Steps */}
        {(isProcessing || currentStep > 0) && (
          <Card className="mb-8">
            <CardContent className="p-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">处理进度</h3>
                {!isProcessing && (
                  <Button variant="outline" size="sm" onClick={resetProcess}>
                    重新开始
                  </Button>
                )}
              </div>

              <div className="space-y-4">
                {processSteps.map((step) => (
                  <div key={step.id} className="flex items-start gap-4">
                    {/* Step Icon */}
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
                      step.status === 'completed' ? 'bg-green-100 text-green-600' :
                      step.status === 'running' ? 'bg-blue-100 text-blue-600' :
                      step.status === 'error' ? 'bg-red-100 text-red-600' :
                      'bg-gray-100 text-gray-400'
                    }`}>
                      {step.status === 'completed' ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : step.status === 'running' ? (
                        <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                      ) : step.status === 'error' ? (
                        <AlertTriangle className="w-5 h-5" />
                      ) : (
                        <span className="text-sm font-medium">{step.id}</span>
                      )}
                    </div>

                    {/* Step Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className={`font-medium ${
                          step.status === 'running' ? 'text-blue-600' : 'text-gray-900'
                        }`}>
                          {step.name}
                        </h4>
                        {step.status === 'running' && (
                          <Badge variant="secondary" className="bg-blue-50 text-blue-600">
                            进行中
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mb-2">{step.description}</p>
                      
                      {/* Step Result */}
                      {step.result && step.id === 1 && (
                        <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <span className="text-gray-500">事件类型:</span>
                              <div className="font-medium">{step.result.event_type}</div>
                            </div>
                            <div>
                              <span className="text-gray-500">严重程度:</span>
                              <div className="font-medium">{step.result.severity}</div>
                            </div>
                            <div>
                              <span className="text-gray-500">置信度:</span>
                              <div className="font-medium">{step.result.confidence}%</div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Final Results */}
        {finalResult && (
          <Card>
            <CardContent className="p-8">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">处理完成</h3>
                <p className="text-gray-500">AI已生成最优航班调整方案</p>
              </div>

              {/* Summary Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="text-center p-4 bg-blue-50 rounded-xl">
                  <div className="text-2xl font-bold text-blue-600">{finalResult.summary.total_flights}</div>
                  <div className="text-sm text-blue-600">处理航班</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-xl">
                  <div className="text-2xl font-bold text-green-600">{finalResult.summary.normal_flights}</div>
                  <div className="text-sm text-green-600">正常执行</div>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-xl">
                  <div className="text-2xl font-bold text-yellow-600">{finalResult.summary.delayed_flights}</div>
                  <div className="text-sm text-yellow-600">延误调整</div>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-xl">
                  <div className="text-2xl font-bold text-red-600">{finalResult.summary.cancelled_flights}</div>
                  <div className="text-sm text-red-600">取消航班</div>
                </div>
              </div>

              {/* Action Results */}
              <div className="space-y-3">
                <h4 className="font-semibold text-gray-900">调整方案详情</h4>
                {Object.entries(finalResult.solutions).map(([planName, flights]) => (
                  <div key={planName} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h5 className="font-medium text-gray-900">{planName}</h5>
                      <Badge className="bg-blue-100 text-blue-800">{flights.length} 个航班</Badge>
                    </div>
                    <div className="space-y-2">
                      {flights.slice(0, 5).map((flight, index) => (
                        <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                          <div className="flex items-center gap-3">
                            <span className="font-mono text-sm font-medium">{flight.flight_number}</span>
                            <Badge variant="outline" className="text-xs">
                              {flight.adjustment_action}
                            </Badge>
                          </div>
                          <div className="text-sm text-gray-500">
                            {flight.additional_delay_minutes > 0 && `+${flight.additional_delay_minutes}min`}
                            {flight.reason}
                          </div>
                        </div>
                      ))}
                      {flights.length > 5 && (
                        <div className="text-center py-2 text-sm text-gray-500">
                          还有 {flights.length - 5} 个航班...
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Cost Savings */}
              <div className="mt-6 p-4 bg-green-50 rounded-xl text-center">
                <div className="text-lg font-semibold text-green-700">
                  预计节省成本: ¥{(finalResult.summary.cost_saving / 10000).toFixed(1)}万
                </div>
                <div className="text-sm text-green-600 mt-1">
                  相比传统人工调度方案
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}