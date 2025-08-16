"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Settings, 
  Plane, 
  Save, 
  Play,
  AlertTriangle,
  Users,
  TrendingUp,
  Clock,
  DollarSign,
  CheckCircle,
  XCircle,
  Eye,
  ArrowLeft,
  BarChart3,
  Loader2
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AppLayout } from '@/components/AppLayout';
import toast from 'react-hot-toast';

// 权重配置类型
interface WeightConfig {
  cancellation: number;
  delay: number;
  aircraftChange: number;
  passengerImpact: number;
  costImpact: number;
}

// 约束条件类型
interface ConstraintConfig {
  id: string;
  name: string;
  enabled: boolean;
  priority: 'HIGH' | 'MEDIUM' | 'LOW' | 'MUST';
  category?: string;
  description?: string;
  remarks?: string;
}

// 航班数据类型
interface FlightData {
  id: string;
  flightNumber: string;
  route: string;
  departureTime: string;
  arrivalTime: string;
  aircraft: string;
  passengers: number;
  selected: boolean;
}

// 可选动作类型
interface ActionConfig {
  cancel: boolean;
  delay: boolean;
  reschedule: boolean;
  aircraftChange: boolean;
  routeChange: boolean;
}

// 优化方案类型
interface OptimizationPlan {
  id: string;
  name: string;
  description: string;
  detailedDescription?: string;
  weights: WeightConfig;
  status: 'success' | 'failed' | 'generating';
  generatedAt: string;
  results?: PlanResults;
}

// 方案结果类型
interface PlanResults {
  totalFlights: number;
  executedFlights: number;
  cancelledFlights: number;
  totalDelay: number;
  totalCost: number;
  flightAdjustments: FlightAdjustment[];
  costBreakdown: CostBreakdown;
  summary: ResultSummary;
  dispatchActions?: DispatchAction[];
}

// 航班调整详情
interface FlightAdjustment {
  flightId: string;
  flightNumber: string;
  originalDeparture: string;
  adjustedDeparture: string;
  action: 'normal' | 'delay' | 'cancel' | 'reschedule' | 'aircraftChange';
  delayMinutes: number;
  status: 'executed' | 'cancelled';
  reason: string;
  dispatchInstructions?: string;
  priority?: string;
}

// 调度操作
interface DispatchAction {
  actionId: string;
  actionType: string;
  description: string;
  responsibleDept: string;
  deadline: string;
  priority: string;
  relatedFlights: string[];
  checklist: string[];
}

// 成本分解
interface CostBreakdown {
  delayCost: number;
  cancellationCost: number;
  aircraftChangeCost: number;
  passengerCompensation: number;
}

// 结果摘要
interface ResultSummary {
  onTimeRate: number;
  passengerSatisfaction: number;
  costEfficiency: number;
  operationalScore: number;
}

// CDM文件信息
interface CDMFileInfo {
  file_id: string;
  filename: string;
  upload_time: string;
  row_count: number;
  columns: string[];
}

export default function CreatePlanPage() {
  const [planName, setPlanName] = useState('');
  const [planDescription, setPlanDescription] = useState('');
  const [weights, setWeights] = useState<WeightConfig>({
    cancellation: 80,
    delay: 60,
    aircraftChange: 40,
    passengerImpact: 70,
    costImpact: 90
  });


  
  // 方案生成相关状态
  const [currentStep, setCurrentStep] = useState<'config' | 'results'>('config');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedPlans, setGeneratedPlans] = useState<OptimizationPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<OptimizationPlan | null>(null);

  // CDM文件上传相关状态
  const [uploadedFiles, setUploadedFiles] = useState<CDMFileInfo[]>([]);
  const [selectedCDMFile, setSelectedCDMFile] = useState<string | null>(null);
  const [isUploadingCDM, setIsUploadingCDM] = useState(false);

  // 简化的调整动作配置
  const [allowedActions, setAllowedActions] = useState<ActionConfig>({
    cancel: true,
    delay: true,
    reschedule: true,
    aircraftChange: true,
    routeChange: false
  });

  const handleWeightChange = (key: keyof WeightConfig, value: number[]) => {
    setWeights(prev => ({
      ...prev,
      [key]: value[0]
    }));
  };

  // CDM文件上传处理函数
  const handleCDMFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // 验证文件类型
    const allowedTypes = ['.xlsx', '.xls', '.csv'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
      toast.error('仅支持Excel文件(.xlsx, .xls)和CSV文件(.csv)');
      return;
    }

    setIsUploadingCDM(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/api/cdm/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '文件上传失败');
      }

      const result = await response.json();
      
      // 刷新文件列表
      await loadUploadedFiles();
      
      // 自动选择刚上传的文件
      setSelectedCDMFile(result.file_id);
      
      toast.success(`CDM文件上传成功！包含 ${result.row_count} 行数据`);
      
    } catch (error) {
      console.error('CDM文件上传失败:', error);
      toast.error(error instanceof Error ? error.message : '文件上传失败');
    } finally {
      setIsUploadingCDM(false);
      // 清空input值，允许重新上传相同文件
      event.target.value = '';
    }
  };

  // 加载已上传的文件列表
  const loadUploadedFiles = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/cdm/files');
      if (response.ok) {
        const data = await response.json();
        setUploadedFiles(data.files);
      }
    } catch (error) {
      console.error('加载文件列表失败:', error);
    }
  };

  // 删除CDM文件
  const handleDeleteCDMFile = async (fileId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/cdm/files/${fileId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await loadUploadedFiles();
        if (selectedCDMFile === fileId) {
          setSelectedCDMFile(null);
        }
        toast.success('文件删除成功');
      } else {
        throw new Error('删除失败');
      }
    } catch (error) {
      console.error('删除文件失败:', error);
      toast.error('文件删除失败');
    }
  };

  // 组件加载时获取文件列表
  React.useEffect(() => {
    loadUploadedFiles();
  }, []);

  const handleActionToggle = (action: keyof ActionConfig) => {
    setAllowedActions(prev => ({
      ...prev,
      [action]: !prev[action]
    }));
  };

  const handleBackToConfig = () => {
    setCurrentStep('config');
    setSelectedPlan(null);
  };

  const handleSaveDraft = () => {
    toast.success('草稿已保存');
  };

  const handleViewPlanDetails = (plan: OptimizationPlan) => {
    setSelectedPlan(plan);
  };

  const handleGeneratePlan = async () => {
    if (!planName.trim()) {
      toast.error('请输入方案名称');
      return;
    }

    setIsGenerating(true);
    const loadingToast = toast.loading('正在生成调整方案...');
    
    try {
      // 准备API请求数据
      const requestData = {
        plan_name: planName,
        plan_description: planDescription,
        weights: weights,
        constraints: [],
        allowed_actions: Object.entries(allowedActions).filter(([_, enabled]) => enabled).map(([action, _]) => action),
        flight_range: 'all',
        selected_flights: [],
        test_mode: true,
        cdm_file_id: selectedCDMFile
      };

      console.log('发送API请求:', requestData);

      // 调用后端API
      const response = await fetch('http://localhost:8000/api/plans/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '网络错误' }));
        const errorMessage = errorData.detail || `HTTP ${response.status}`;
        
        // 特殊处理CDM文件相关的错误
        if (errorMessage.includes('请先上传CDM数据文件') || errorMessage.includes('CDM文件')) {
          throw new Error(`${errorMessage}\n\n请在上方"CDM数据文件"部分上传您的数据文件。`);
        }
        
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log('API响应:', data);

      // 转换API响应数据格式
      const convertedPlans: OptimizationPlan[] = data.plans.map((apiPlan: any) => ({
        id: apiPlan.id,
        name: apiPlan.name,
        description: apiPlan.description,
        detailedDescription: apiPlan.detailed_description,
        weights: apiPlan.weights,
        status: apiPlan.status,
        generatedAt: apiPlan.generated_at,
        results: apiPlan.results ? {
          totalFlights: apiPlan.results.total_flights,
          executedFlights: apiPlan.results.executed_flights,
          cancelledFlights: apiPlan.results.cancelled_flights,
          totalDelay: apiPlan.results.total_delay,
          totalCost: apiPlan.results.total_cost,
          flightAdjustments: apiPlan.results.flight_adjustments.map((adj: any) => ({
            flightId: adj.flight_number,
            flightNumber: adj.flight_number,
            originalDeparture: 'N/A',
            adjustedDeparture: adj.adjusted_departure_time || 'N/A',
            action: adj.adjustment_action === 'normal' ? 'normal' : 
                   adj.adjustment_action === 'cancel' ? 'cancel' : 'delay',
            delayMinutes: adj.additional_delay_minutes,
            status: adj.status === '执行' ? 'executed' : 'cancelled',
            reason: adj.reason || '优化调整',
            dispatchInstructions: adj.dispatch_instructions || '',
            priority: adj.priority || 'normal'
          })),
          costBreakdown: apiPlan.results.cost_breakdown,
          summary: apiPlan.results.summary,
          dispatchActions: apiPlan.results.dispatch_actions?.map((action: any) => ({
            actionId: action.action_id,
            actionType: action.action_type,
            description: action.description,
            responsibleDept: action.responsible_dept,
            deadline: action.deadline,
            priority: action.priority,
            relatedFlights: action.related_flights || [],
            checklist: action.checklist || []
          })) || []
        } : undefined
      }));
      
      setGeneratedPlans(convertedPlans);
      setCurrentStep('results');
      toast.dismiss(loadingToast);
      toast.success(`成功生成 ${convertedPlans.length} 套优化方案！共 ${data.successful_plans} 个成功`, {
        duration: 4000,
      });
      
    } catch (error: any) {
      console.error('方案生成失败:', error);
      toast.dismiss(loadingToast);
      toast.error(`方案生成失败: ${error.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const getActionColor = (action: string) => {
    const colors = {
      'normal': 'bg-green-100 text-green-800',
      'delay': 'bg-yellow-100 text-yellow-800', 
      'cancel': 'bg-red-100 text-red-800',
      'reschedule': 'bg-blue-100 text-blue-800',
      'aircraftChange': 'bg-purple-100 text-purple-800'
    };
    return colors[action as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getActionLabel = (action: string) => {
    const labels = {
      'normal': '正常执行',
      'delay': '延误',
      'cancel': '取消',
      'reschedule': '改期',
      'aircraftChange': '换机'
    };
    return labels[action as keyof typeof labels] || action;
  };

  const formatCurrency = (amount: number) => {
    return `¥${amount.toLocaleString()}`;
  };

  const formatTime = (timeString: string) => {
    return new Date(timeString).toLocaleString('zh-CN');
  };

  const getWeightLabel = (key: keyof WeightConfig) => {
    const labels = {
      cancellation: '取消权重',
      delay: '延误权重',
      aircraftChange: '换机权重',
      passengerImpact: '旅客影响权重',
      costImpact: '成本影响权重'
    };
    return labels[key];
  };

  const getActionLabelForConfig = (key: keyof ActionConfig) => {
    const labels = {
      cancel: '取消航班',
      delay: '延误',
      reschedule: '改期',
      aircraftChange: '换机',
      routeChange: '改航线'
    };
    return labels[key];
  };

  // 如果正在查看具体方案详情
  if (selectedPlan) {
    return (
      <AppLayout>
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <Button 
                variant="outline" 
                onClick={() => setSelectedPlan(null)}
                className="flex items-center"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                返回方案列表
              </Button>
              <div>
                <h1 className="text-3xl font-bold">{selectedPlan.name}</h1>
                <p className="text-gray-600 mt-1">{selectedPlan.description}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Badge variant="outline" className="bg-green-50 text-green-700">
                <CheckCircle className="h-3 w-3 mr-1" />
                生成成功
              </Badge>
              <span className="text-sm text-gray-500">
                {formatTime(selectedPlan.generatedAt)}
              </span>
            </div>
          </div>

                                  {selectedPlan.results && (
            <>
              {/* 方案概览统计 - 置于顶部 */}
              <div className="grid grid-cols-4 gap-4 mb-6">
                <Card className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Plane className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">执行航班</p>
                      <p className="text-2xl font-bold">{selectedPlan.results.executedFlights}/{selectedPlan.results.totalFlights}</p>
                    </div>
                  </div>
                </Card>
                
                <Card className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                      <XCircle className="h-5 w-5 text-red-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">取消航班</p>
                      <p className="text-2xl font-bold">{selectedPlan.results.cancelledFlights}</p>
                    </div>
                  </div>
                </Card>
                
                <Card className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                      <Clock className="h-5 w-5 text-yellow-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">总延误</p>
                      <p className="text-2xl font-bold">{selectedPlan.results.totalDelay}分钟</p>
                    </div>
                  </div>
                </Card>
                
                <Card className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                      <DollarSign className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">总成本</p>
                      <p className="text-2xl font-bold">{formatCurrency(selectedPlan.results.totalCost)}</p>
                    </div>
                  </div>
                </Card>
              </div>

              {/* 左右分栏：航班调整详情 & 方案详细分析 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 左侧：航班调整详情 */}
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <BarChart3 className="h-5 w-5 mr-2" />
                        航班调整详情
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {selectedPlan.results.flightAdjustments.map((adjustment) => (
                          <div key={adjustment.flightId} className="p-3 border rounded-lg space-y-2">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-3">
                                <div>
                                  <div className="font-medium">{adjustment.flightNumber}</div>
                                  <div className="text-sm text-gray-500">
                                    {adjustment.originalDeparture} → {adjustment.adjustedDeparture}
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center space-x-2">
                                <Badge 
                                  className={
                                    adjustment.priority === 'urgent' ? 'bg-red-100 text-red-800' :
                                    adjustment.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                                    'bg-blue-100 text-blue-800'
                                  }
                                >
                                  {adjustment.priority === 'urgent' ? '紧急' :
                                   adjustment.priority === 'high' ? '高优先级' : '正常'}
                                </Badge>
                                <Badge className={getActionColor(adjustment.action)}>
                                  {getActionLabel(adjustment.action)}
                                </Badge>
                                {adjustment.delayMinutes > 0 && (
                                  <Badge variant="outline">
                                    +{adjustment.delayMinutes}分钟
                                  </Badge>
                                )}
                              </div>
                            </div>
                            {adjustment.dispatchInstructions && (
                              <div className="bg-blue-50 p-2 rounded text-sm">
                                <div className="font-medium text-blue-800 mb-1">调度指令：</div>
                                <div className="text-blue-700 whitespace-pre-line">
                                  {adjustment.dispatchInstructions}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* 成本分解 */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <DollarSign className="h-5 w-5 mr-2" />
                        成本分解
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">延误成本</span>
                          <span className="font-medium">{formatCurrency(selectedPlan.results.costBreakdown.delayCost)}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">取消成本</span>
                          <span className="font-medium">{formatCurrency(selectedPlan.results.costBreakdown.cancellationCost)}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">换机成本</span>
                          <span className="font-medium">{formatCurrency(selectedPlan.results.costBreakdown.aircraftChangeCost)}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">旅客补偿</span>
                          <span className="font-medium">{formatCurrency(selectedPlan.results.costBreakdown.passengerCompensation)}</span>
                        </div>
                        <div className="border-t pt-4">
                          <div className="flex justify-between items-center font-bold">
                            <span>总计</span>
                            <span>{formatCurrency(selectedPlan.results.totalCost)}</span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* 右侧：方案详细分析 */}
                <div>
                  {selectedPlan.detailedDescription && (
                    <Card className="h-full">
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Eye className="h-5 w-5 mr-2" />
                          方案详细分析
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="prose prose-sm max-w-none max-h-[600px] overflow-y-auto">
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                              // 自定义样式
                              h3: ({node, ...props}) => <h3 className="text-lg font-semibold mt-4 mb-2 text-blue-700" {...props} />,
                              h4: ({node, ...props}) => <h4 className="text-base font-medium mt-3 mb-2 text-gray-800" {...props} />,
                              p: ({node, ...props}) => <p className="mb-3 leading-relaxed text-gray-700" {...props} />,
                              ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-3 space-y-1" {...props} />,
                              li: ({node, ...props}) => <li className="text-gray-700" {...props} />,
                              table: ({node, ...props}) => <table className="w-full border-collapse border border-gray-300 my-4" {...props} />,
                              th: ({node, ...props}) => <th className="border border-gray-300 px-3 py-2 bg-gray-100 font-medium text-left" {...props} />,
                              td: ({node, ...props}) => <td className="border border-gray-300 px-3 py-2" {...props} />,
                              strong: ({node, ...props}) => <strong className="font-semibold text-gray-900" {...props} />,
                              em: ({node, ...props}) => <em className="italic text-blue-600" {...props} />,
                              blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-blue-500 pl-4 my-4 italic text-gray-600 bg-blue-50 py-2" {...props} />,
                              hr: ({node, ...props}) => <hr className="my-6 border-gray-300" {...props} />
                            }}
                          >
                            {selectedPlan.detailedDescription}
                          </ReactMarkdown>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </div>

              {/* 调度操作清单 */}
              {selectedPlan.results.dispatchActions && selectedPlan.results.dispatchActions.length > 0 && (
                <Card className="mt-6">
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <CheckCircle className="h-5 w-5 mr-2" />
                      调度操作清单
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {selectedPlan.results.dispatchActions.map((action) => (
                        <div key={action.actionId} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-3">
                              <Badge className={
                                action.priority === 'urgent' ? 'bg-red-100 text-red-800' :
                                action.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                                'bg-blue-100 text-blue-800'
                              }>
                                {action.actionType}
                              </Badge>
                              <span className="font-medium">{action.description}</span>
                            </div>
                            <div className="text-sm text-gray-500">{action.deadline}</div>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3 text-sm">
                            <div>
                              <div className="font-medium text-gray-700">负责部门：</div>
                              <div className="text-gray-600">{action.responsibleDept}</div>
                            </div>
                            {action.relatedFlights.length > 0 && (
                              <div>
                                <div className="font-medium text-gray-700">相关航班：</div>
                                <div className="text-gray-600">{action.relatedFlights.join(', ')}</div>
                              </div>
                            )}
                          </div>

                          {action.checklist.length > 0 && (
                            <div className="mt-3">
                              <div className="font-medium text-gray-700 mb-2">检查清单：</div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-1">
                                {action.checklist.map((item, index) => (
                                  <div key={index} className="flex items-center space-x-2 text-sm">
                                    <input type="checkbox" className="rounded" />
                                    <span className="text-gray-600">{item}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* 绩效指标 - 置于底部 */}
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <TrendingUp className="h-5 w-5 mr-2" />
                    绩效指标
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-4 gap-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{selectedPlan.results.summary.onTimeRate}%</div>
                      <div className="text-sm text-gray-600">准点率</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{selectedPlan.results.summary.passengerSatisfaction}%</div>
                      <div className="text-sm text-gray-600">旅客满意度</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">{selectedPlan.results.summary.costEfficiency}%</div>
                      <div className="text-sm text-gray-600">成本效率</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">{selectedPlan.results.summary.operationalScore}%</div>
                      <div className="text-sm text-gray-600">运营评分</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="p-6">
        {currentStep === 'config' ? (
          <>
            {/* 配置页面 Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-3xl font-bold">创建调整方案</h1>
                <p className="text-gray-600 mt-1">配置权重、约束条件和航班范围，生成最优调整方案</p>
              </div>
              <div className="flex items-center space-x-3">
                <Button variant="outline" onClick={handleSaveDraft}>
                  <Save className="h-4 w-4 mr-2" />
                  保存草稿
                </Button>
                <Button 
                  onClick={handleGeneratePlan}
                  disabled={isGenerating}
                  className="relative"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      生成中...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      生成方案
                    </>
                  )}
                </Button>
              </div>
            </div>
          </>
        ) : (
          <>
            {/* 结果页面 Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-4">
                <Button 
                  variant="outline" 
                  onClick={handleBackToConfig}
                  className="flex items-center"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  返回配置
                </Button>
                <div>
                  <h1 className="text-3xl font-bold">优化方案结果</h1>
                  <p className="text-gray-600 mt-1">已生成 {generatedPlans.length} 套优化方案，请选择查看详情</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Badge variant="outline" className="bg-green-50 text-green-700">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  生成完成
                </Badge>
                <Button variant="outline" onClick={handleGeneratePlan}>
                  <Play className="h-4 w-4 mr-2" />
                  重新生成
                </Button>
              </div>
            </div>

            {/* 方案概览统计 */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <Card className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <BarChart3 className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">生成方案</p>
                    <p className="text-2xl font-bold">{generatedPlans.length}</p>
                  </div>
                </div>
              </Card>
              
              <Card className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">成功方案</p>
                    <p className="text-2xl font-bold">{generatedPlans.filter(p => p.status === 'success').length}</p>
                  </div>
                </div>
              </Card>
              
              <Card className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <Clock className="h-5 w-5 text-yellow-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">平均延误</p>
                    <p className="text-2xl font-bold">
                      {Math.round(generatedPlans.reduce((acc, plan) => 
                        acc + (plan.results?.totalDelay || 0), 0) / Math.max(generatedPlans.length, 1))}分钟
                    </p>
                  </div>
                </div>
              </Card>
              
              <Card className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <DollarSign className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">平均成本</p>
                    <p className="text-2xl font-bold">
                      {formatCurrency(Math.round(generatedPlans.reduce((acc, plan) => 
                        acc + (plan.results?.totalCost || 0), 0) / Math.max(generatedPlans.length, 1)))}
                    </p>
                  </div>
                </div>
              </Card>
            </div>

            {/* 方案列表 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2" />
                  优化方案列表
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {generatedPlans.map((plan) => (
                    <div key={plan.id} className="border rounded-lg p-6 hover:shadow-lg transition-shadow">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
                            {plan.id}
                          </div>
                          <div>
                            <h3 className="text-lg font-semibold">{plan.name}</h3>
                            <p className="text-gray-600 text-sm">{plan.description}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <Badge variant={plan.status === 'success' ? 'default' : 'destructive'}>
                            {plan.status === 'success' ? '生成成功' : '生成失败'}
                          </Badge>
                          <Button 
                            onClick={() => handleViewPlanDetails(plan)}
                            size="sm"
                            disabled={!plan.results}
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            查看详情
                          </Button>
                        </div>
                      </div>
                      
                      {plan.results && (
                        <div className="grid grid-cols-4 gap-4 bg-gray-50 rounded-lg p-4">
                          <div className="text-center">
                            <div className="text-xl font-bold text-blue-600">{plan.results.executedFlights}/{plan.results.totalFlights}</div>
                            <div className="text-xs text-gray-600">执行航班</div>
                          </div>
                          <div className="text-center">
                            <div className="text-xl font-bold text-red-600">{plan.results.cancelledFlights}</div>
                            <div className="text-xs text-gray-600">取消航班</div>
                          </div>
                          <div className="text-center">
                            <div className="text-xl font-bold text-yellow-600">{plan.results.totalDelay}分钟</div>
                            <div className="text-xs text-gray-600">总延误</div>
                          </div>
                          <div className="text-center">
                            <div className="text-xl font-bold text-green-600">{formatCurrency(plan.results.totalCost)}</div>
                            <div className="text-xs text-gray-600">总成本</div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {currentStep === 'config' && (
          <div className="max-w-4xl mx-auto space-y-6">
            {/* 基本信息 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Settings className="h-5 w-5 mr-2" />
                  基本信息
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="planName">方案名称</Label>
                  <Input
                    id="planName"
                    value={planName}
                    onChange={(e) => setPlanName(e.target.value)}
                    placeholder="请输入方案名称"
                  />
                </div>
                <div>
                  <Label htmlFor="planDescription">方案描述</Label>
                  <Textarea
                    id="planDescription"
                    value={planDescription}
                    onChange={(e) => setPlanDescription(e.target.value)}
                    placeholder="请输入方案描述（可选）"
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>

            {/* CDM文件上传 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Plane className="h-5 w-5 mr-2" />
                  CDM数据文件
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* 文件上传 */}
                <div className="space-y-2">
                  <Label>上传CDM文件</Label>
                  <div className="flex items-center space-x-2">
                    <Input
                      type="file"
                      accept=".xlsx,.xls,.csv"
                      onChange={handleCDMFileUpload}
                      disabled={isUploadingCDM}
                      className="flex-1"
                    />
                    {isUploadingCDM && (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    )}
                  </div>
                  <p className="text-sm text-gray-500">
                    支持Excel文件(.xlsx, .xls)和CSV文件(.csv)
                  </p>
                </div>

                {/* 已上传文件列表 */}
                {uploadedFiles.length > 0 && (
                  <div className="space-y-2">
                    <Label>已上传的文件</Label>
                    <div className="space-y-2 max-h-32 overflow-y-auto">
                      {uploadedFiles.map((file) => (
                        <div
                          key={file.file_id}
                          className={`flex items-center justify-between p-2 rounded border ${
                            selectedCDMFile === file.file_id
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200'
                          }`}
                        >
                          <div className="flex items-center space-x-2 flex-1">
                            <Checkbox
                              checked={selectedCDMFile === file.file_id}
                              onCheckedChange={(checked) => {
                                setSelectedCDMFile(checked ? file.file_id : null);
                              }}
                            />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium truncate">
                                {file.filename}
                              </p>
                              <p className="text-xs text-gray-500">
                                {file.row_count} 行数据 • {new Date(file.upload_time).toLocaleString()}
                              </p>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteCDMFile(file.file_id)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <XCircle className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 文件状态提示 */}
                <div className="text-sm">
                  {selectedCDMFile ? (
                    <div className="flex items-center text-green-600">
                      <CheckCircle className="h-4 w-4 mr-1" />
                      已选择CDM文件
                    </div>
                  ) : (
                    <div className="flex items-center text-amber-600">
                      <AlertTriangle className="h-4 w-4 mr-1" />
                      未选择CDM文件，将使用系统默认数据
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* 权重配置 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Settings className="h-5 w-5 mr-2" />
                  权重配置
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {Object.entries(weights).map(([key, value]) => (
                  <div key={key} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>{getWeightLabel(key as keyof WeightConfig)}</Label>
                      <div className="flex items-center space-x-2">
                        <Input
                          type="number"
                          value={value}
                          onChange={(e) => handleWeightChange(key as keyof WeightConfig, [parseInt(e.target.value) || 0])}
                          className="w-16 h-8"
                          min="0"
                          max="100"
                        />
                        <span className="text-sm text-gray-500">%</span>
                      </div>
                    </div>
                    <Slider
                      value={[value]}
                      onValueChange={(value) => handleWeightChange(key as keyof WeightConfig, value)}
                      max={100}
                      step={1}
                      className="w-full"
                    />
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* 可选动作集 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Plane className="h-5 w-5 mr-2" />
                  可选动作集
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(allowedActions).map(([key, enabled]) => (
                    <div key={key} className="flex items-center space-x-2">
                      <Checkbox
                        id={key}
                        checked={enabled}
                        onCheckedChange={() => handleActionToggle(key as keyof ActionConfig)}
                      />
                      <Label htmlFor={key} className="text-sm">
                        {getActionLabelForConfig(key as keyof ActionConfig)}
                      </Label>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
