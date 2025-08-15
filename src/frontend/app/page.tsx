"use client";

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import toast from 'react-hot-toast';
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
  result?: any;
  details?: any;
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
  const [testMode, setTestMode] = useState(true); // 默认启用测试模式
  const [expandedPlans, setExpandedPlans] = useState<Record<string, boolean>>({}); // 控制每个方案是否展开显示所有航班
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
      processed_flights?: number;
      normal_flights: number;
      delayed_flights: number;
      cancelled_flights: number;
      cost_saving: number;
    };
    solutions: Record<string, FlightAdjustment[]>;
  } | null>(null);
  const [detailedProgress, setDetailedProgress] = useState<any[]>([]);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [dataStatistics, setDataStatistics] = useState<any>(null);
  const [systemOutput, setSystemOutput] = useState<string>('');
  const [weightConfirmation, setWeightConfirmation] = useState<{
    show: boolean;
    weights: any;
    confirmed: boolean;
  }>({ show: false, weights: null, confirmed: false });
  const [editableWeights, setEditableWeights] = useState<any>(null);
  const [fileInfo, setFileInfo] = useState<any>(null);
  const [showFileManager, setShowFileManager] = useState(true);
  const [filePreview, setFilePreview] = useState<any>(null);
  const [selectedCdmFile, setSelectedCdmFile] = useState<string>('');

  // 加载预设事件和文件信息
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
    
    const loadFileInfo = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/files/info`);
        const info = await response.json();
        setFileInfo(info);
        // 设置默认选中的CDM文件
        if (info.cdm_files && info.cdm_files.length > 0) {
          setSelectedCdmFile(info.cdm_files[0].name);
        }
      } catch (error) {
        console.error('Failed to load file info:', error);
      }
    };
    
    loadPresets();
    loadFileInfo();
  }, []);

  const updateStepStatus = (stepId: number, status: ProcessStep['status'], result?: ProcessStep['result'], details?: any) => {
    setProcessSteps(prev => prev.map(step => 
      step.id === stepId ? { ...step, status, result, details } : step
    ));
  };

  // 获取详细进度信息
  const fetchDetailedProgress = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/system/detailed-progress`);
      const data = await response.json();
      
      if (data.detailed_progress) {
        setDetailedProgress(data.detailed_progress);
        
        // 更新步骤状态
        data.detailed_progress.forEach((progress: any) => {
          const stepMap: Record<string, number> = {
            '事件分析': 1,
            '数据处理': 3,
            '优化计算': 4,
            '方案决策': 5,
            '执行下发': 6
          };
          
          const stepId = stepMap[progress.step];
          if (stepId) {
            updateStepStatus(stepId, progress.status, progress.details, progress.details);
          }
        });
      }
      
      if (data.analysis_result) {
        setAnalysisResult(data.analysis_result);
      }
      
      if (data.data_statistics) {
        setDataStatistics(data.data_statistics);
        if (data.data_statistics.system_output) {
          setSystemOutput(data.data_statistics.system_output);
        }
      }
    } catch (error) {
      console.error('Failed to fetch detailed progress:', error);
    }
  };

  const startProcess = async () => {
    if (!eventDescription.trim()) {
      toast.error('请输入事件描述或选择预设事件');
      return;
    }

    if (!canStartAnalysis()) {
      toast.error('请先确保CDM数据和约束条件文件已准备就绪');
      return;
    }

    toast.loading('🚀 开始智能分析...', { id: 'main-process' });

    setIsProcessing(true);
    setCurrentStep(1);
    setFinalResult(null);
    setDetailedProgress([]);
    setAnalysisResult(null);
    setDataStatistics(null);
    setSystemOutput('');

    try {
      // 步骤1: 事件分析
      updateStepStatus(1, 'running');
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const analysisResponse = await fetch(`${API_BASE_URL}/api/events/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: eventDescription })
      });
      const analysisResult = await analysisResponse.json();
      updateStepStatus(1, 'completed', analysisResult);
      setAnalysisResult(analysisResult);
      setCurrentStep(2);
      
      toast.success('✅ 事件分析完成！AI已生成权重策略', { id: 'main-process' });

      // 步骤2: 权重策略 - 等待用户确认
      await new Promise(resolve => setTimeout(resolve, 500));
      updateStepStatus(2, 'running');
      
            // 显示权重确认界面
      setWeightConfirmation({
        show: true,
        weights: analysisResult.weights,
        confirmed: false
      });
      setEditableWeights(JSON.parse(JSON.stringify(analysisResult.weights)));

      // 更新步骤状态为等待用户确认
      updateStepStatus(2, 'pending', {
        message: "请确认或调整权重配置",
        strategies_generated: Object.keys(analysisResult.weights).length,
        primary_strategy: Object.keys(analysisResult.weights)[0]
      });

      toast('⚖️ 请确认权重策略后继续', {
        icon: '👆',
        duration: 4000,
      });
      
      // 停止自动进行，等待用户确认
      // 注意：这里不设置 setIsProcessing(false)，因为用户还需要确认权重
      return;

    } catch (error) {
      console.error('Process failed:', error);
      updateStepStatus(currentStep, 'error');
      toast.error(`❌ 处理失败: ${error instanceof Error ? error.message : '未知错误'}`, { id: 'main-process' });
      setIsProcessing(false);
    }
  };

  // 文件管理相关函数
  const handleFileUpload = async (file: File, type: 'cdm' | 'constraint') => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${API_BASE_URL}/api/files/upload/${type}`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
      }
      
      const result = await response.json();
      toast.success(`📁 文件上传成功: ${result.filename}`);
      
      // 重新加载文件信息
      const fileInfoResponse = await fetch(`${API_BASE_URL}/api/files/info`);
      const info = await fileInfoResponse.json();
      setFileInfo(info);
      
      return result;
    } catch (error) {
      toast.error(`❌ 文件上传失败: ${error instanceof Error ? error.message : '未知错误'}`);
      console.error('File upload error:', error);
    }
  };

  const handleFileDelete = async (filename: string, type: 'cdm' | 'constraint') => {
    if (!confirm(`确定要删除文件 ${filename} 吗？`)) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/files/${type}/${filename}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
      }
      
      toast.success(`🗑️ 文件删除成功: ${filename}`);
      
      // 重新加载文件信息
      const fileInfoResponse = await fetch(`${API_BASE_URL}/api/files/info`);
      const info = await fileInfoResponse.json();
      setFileInfo(info);
      
    } catch (error) {
      toast.error(`❌ 文件删除失败: ${error instanceof Error ? error.message : '未知错误'}`);
      console.error('File delete error:', error);
    }
  };

  const handleFilePreview = async (filename: string, type: 'cdm' | 'constraint') => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/files/preview/${type}/${filename}?rows=20`);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
      }
      
      const preview = await response.json();
      setFilePreview({ ...preview, filename, type });
      
    } catch (error) {
      toast.error(`❌ 文件预览失败: ${error instanceof Error ? error.message : '未知错误'}`);
      console.error('File preview error:', error);
    }
  };

  const canStartAnalysis = () => {
    // 检查是否有CDM文件和至少一个约束文件
    const hasCdmFile = fileInfo?.cdm_files && fileInfo.cdm_files.length > 0;
    const hasConstraintFiles = fileInfo?.constraint_files && fileInfo.constraint_files.some((f: any) => f.exists);
    const hasEventDescription = eventDescription.trim().length > 0;
    
    return hasCdmFile && hasConstraintFiles && hasEventDescription;
  };

  // 继续处理权重确认后的步骤
  const continueWithWeights = async (confirmedWeights: any) => {
    try {
      toast.loading('⚙️ 正在进行数据处理...', { id: 'optimization' });
      setIsProcessing(true);
      setWeightConfirmation(prev => ({ ...prev, confirmed: true, show: false }));
      
      // 标记权重策略步骤完成
      updateStepStatus(2, 'completed', {
        strategies_generated: Object.keys(confirmedWeights).length,
        primary_strategy: Object.keys(confirmedWeights)[0],
        user_confirmed: true
      });
      setCurrentStep(3);

      // 启动轮询以获取详细进度 (更频繁的轮询以获取实时状态)
      const progressInterval = setInterval(fetchDetailedProgress, 500);

      // 步骤3-6: 运行完整的系统处理
      updateStepStatus(3, 'running');
      
      const optimizationResponse = await fetch(`${API_BASE_URL}/api/optimization/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_description: eventDescription,
          weights: confirmedWeights,
          test_mode: testMode
        })
      });
      
      const optimizationResult = await optimizationResponse.json();
      
      // 停止轮询
      clearInterval(progressInterval);
      
      // 最后一次获取详细进度
      await fetchDetailedProgress();
      
      // 根据实际结果设置步骤状态，而不是强制标记为完成
      if (optimizationResult && !optimizationResult.error) {
        // 只有成功时才标记为完成
        updateStepStatus(5, 'completed');
        updateStepStatus(6, 'completed', optimizationResult);
        setFinalResult(optimizationResult);
        toast.success('🎉 优化计算完成！已生成最优调整方案', { id: 'optimization' });
      } else {
        // 失败时标记为错误
        updateStepStatus(5, 'error');
        updateStepStatus(6, 'error');
        console.error('Optimization failed:', optimizationResult);
        toast.error('❌ 优化计算失败，已使用模拟数据展示', { id: 'optimization' });
      }

    } catch (error) {
      console.error('Process failed:', error);
      updateStepStatus(currentStep, 'error');
      toast.error(`❌ 处理失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const resetProcess = () => {
    setProcessSteps(prev => prev.map(step => ({ ...step, status: 'pending', result: undefined, details: undefined })));
    setCurrentStep(0);
    setFinalResult(null);
    setDetailedProgress([]);
    setAnalysisResult(null);
    setDataStatistics(null);
    setSystemOutput('');
    setWeightConfirmation({ show: false, weights: null, confirmed: false });
    setEditableWeights(null);
    setFilePreview(null);
    setExpandedPlans({}); // 重置展开状态
    toast.success('🔄 已重置，可以开始新的分析');
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
          {/* Data File Management Section */}
          <Card className="mb-8">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">数据文件管理</h2>
                  <p className="text-sm text-gray-500">请确保上传CDM数据和约束条件文件后再开始分析</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowFileManager(!showFileManager)}
                >
                  {showFileManager ? '收起管理' : '展开管理'}
                </Button>
              </div>
              
              {/* 当前文件状态概览 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <h3 className="font-medium text-blue-900 mb-2">CDM航班数据</h3>
                  {fileInfo?.cdm_files && fileInfo.cdm_files.length > 0 ? (
                    <div className="text-sm">
                      <div className="text-blue-700 font-medium">{fileInfo.cdm_files.length} 个文件</div>
                      <div className="text-blue-600">当前: {selectedCdmFile || fileInfo.cdm_files[0]?.name}</div>
                    </div>
                  ) : (
                    <div className="text-sm text-red-600">⚠️ 未找到CDM文件</div>
                  )}
                </div>
                
                <div className="p-3 bg-green-50 rounded-lg">
                  <h3 className="font-medium text-green-900 mb-2">约束条件文件</h3>
                  <div className="text-sm">
                    <div className="text-green-700 font-medium">
                      {fileInfo?.constraint_files?.filter((f: any) => f.exists).length || 0}/5 个文件
                    </div>
                    <div className="text-green-600">
                      {fileInfo?.constraint_files?.filter((f: any) => f.exists).length === 5 ? '✓ 全部就绪' : '部分文件缺失'}
                    </div>
                  </div>
                </div>
                
                <div className="p-3 bg-gray-50 rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-2">系统状态</h3>
                  <div className="text-sm">
                    {canStartAnalysis() ? (
                      <div className="text-green-600 font-medium">✓ 可以开始分析</div>
                    ) : (
                      <div className="text-orange-600 font-medium">⚠️ 需要完善数据</div>
                    )}
                  </div>
                </div>
              </div>

              {/* 详细文件管理界面 */}
              {showFileManager && (
                <div className="border-t pt-4">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* CDM文件管理 */}
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-medium text-gray-900">CDM航班数据文件</h3>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setFilePreview(null)}
                        >
                          {filePreview ? '关闭预览' : ''}
                        </Button>
                      </div>
                      
                      <div className="space-y-2 mb-4">
                        {fileInfo?.cdm_files?.map((file: any, idx: number) => (
                          <div key={idx} className={`flex items-center justify-between p-3 rounded-lg border ${
                            selectedCdmFile === file.name ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-gray-50'
                          }`}>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <input
                                  type="radio"
                                  name="cdm-file"
                                  checked={selectedCdmFile === file.name}
                                  onChange={() => setSelectedCdmFile(file.name)}
                                  className="text-blue-600"
                                />
                                <span className="text-sm font-medium">{file.name}</span>
                              </div>
                              <div className="text-xs text-gray-500 ml-6">
                                {(file.size / 1024 / 1024).toFixed(1)}MB • {new Date(file.modified).toLocaleString()}
                              </div>
                            </div>
                            <div className="flex gap-1">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleFilePreview(file.name, 'cdm')}
                              >
                                预览
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleFileDelete(file.name, 'cdm')}
                                className="text-red-600 hover:text-red-700"
                              >
                                删除
                              </Button>
                            </div>
                          </div>
                        )) || <div className="text-sm text-gray-500 p-3 border border-dashed rounded">暂无CDM文件</div>}
                      </div>
                      
                      <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-blue-400 transition-colors">
                        <input
                          type="file"
                          accept=".csv,.xlsx,.xls"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) handleFileUpload(file, 'cdm');
                          }}
                          className="hidden"
                          id="cdm-upload"
                        />
                        <label htmlFor="cdm-upload" className="cursor-pointer">
                          <div className="text-sm text-gray-600">
                            📁 点击上传CDM文件
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            支持 .csv, .xlsx, .xls 格式
                          </div>
                        </label>
                      </div>
                    </div>

                    {/* 约束文件管理 */}
                    <div>
                      <h3 className="font-medium text-gray-900 mb-3">约束条件文件</h3>
                      <div className="space-y-2 mb-4">
                        {fileInfo?.constraint_files?.map((file: any, idx: number) => (
                          <div key={idx} className={`flex items-center justify-between p-3 rounded-lg border ${
                            file.exists ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                          }`}>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className={`w-2 h-2 rounded-full ${file.exists ? 'bg-green-500' : 'bg-red-500'}`}></span>
                                <span className="text-sm font-medium">{file.name}</span>
                              </div>
                              <div className="text-xs text-gray-500 ml-4">
                                {file.exists ? `${(file.size / 1024).toFixed(1)}KB • ${new Date(file.modified).toLocaleString()}` : '文件缺失'}
                              </div>
                            </div>
                            <div className="flex gap-1">
                              {file.exists && (
                                <>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleFilePreview(file.name, 'constraint')}
                                  >
                                    预览
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleFileDelete(file.name, 'constraint')}
                                    className="text-red-600 hover:text-red-700"
                                  >
                                    删除
                                  </Button>
                                </>
                              )}
                            </div>
                          </div>
                        )) || <div className="text-sm text-gray-500 p-3 border border-dashed rounded">暂无约束文件</div>}
                      </div>
                      
                      <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-green-400 transition-colors">
                        <input
                          type="file"
                          accept=".csv"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) handleFileUpload(file, 'constraint');
                          }}
                          className="hidden"
                          id="constraint-upload"
                        />
                        <label htmlFor="constraint-upload" className="cursor-pointer">
                          <div className="text-sm text-gray-600">
                            📋 点击上传约束文件
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            文件名需为预定义的约束类型 (.csv)
                          </div>
                        </label>
                      </div>
                    </div>
                  </div>
                  
                  {/* 文件预览 */}
                  {filePreview && (
                    <div className="mt-6 p-4 border rounded-lg bg-gray-50">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium text-gray-900">文件预览: {filePreview.filename}</h4>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setFilePreview(null)}
                        >
                          关闭
                        </Button>
                      </div>
                      <div className="text-sm text-gray-600 mb-2">
                        数据形状: {filePreview.shape[0]} 行 × {filePreview.shape[1]} 列 (显示前{filePreview.data.length}行)
                      </div>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-xs border border-gray-300">
                          <thead className="bg-gray-100">
                            <tr>
                              {filePreview.columns.map((col: string, idx: number) => (
                                <th key={idx} className="px-2 py-1 border-b border-gray-300 text-left font-medium">
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {filePreview.data.map((row: any, idx: number) => (
                              <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                                {filePreview.columns.map((col: string, colIdx: number) => (
                                  <td key={colIdx} className="px-2 py-1 border-b border-gray-200">
                                    {String(row[col] || '').substring(0, 50)}
                                    {String(row[col] || '').length > 50 && '...'}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

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
                {!isProcessing && !weightConfirmation.show ? (
                  <Button 
                    onClick={startProcess}
                    size="lg" 
                    className="h-12 px-8 bg-blue-500 hover:bg-blue-600"
                    disabled={!canStartAnalysis()}
                  >
                    <Brain className="w-5 h-5 mr-2" />
                    {!canStartAnalysis() ? '请先完善数据和事件描述' : '开始智能分析'}
                  </Button>
                ) : weightConfirmation.show ? (
                  <Button 
                    size="lg" 
                    className="h-12 px-8" 
                    disabled
                  >
                    <Brain className="w-5 h-5 mr-2" />
                    等待权重确认...
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
                          
                          {/* AI详细分析 */}
                          {analysisResult && analysisResult.ai_analysis_raw && (
                            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                              <span className="text-blue-700 text-sm font-medium">AI智能分析:</span>
                              <div className="text-sm mt-2 text-blue-800 whitespace-pre-line">
                                {analysisResult.ai_analysis_raw.split('\n').slice(0, 10).join('\n')}
                                {analysisResult.ai_analysis_raw.split('\n').length > 10 && '...'}
                              </div>
                            </div>
                          )}
                          
                          {step.result.recommendations && (
                            <div className="mt-3">
                              <span className="text-gray-500 text-sm">AI建议:</span>
                              <ul className="text-sm mt-1 space-y-1">
                                {step.result.recommendations.slice(0, 2).map((rec: string, idx: number) => (
                                  <li key={idx} className="text-gray-700">• {rec}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Step 2: 权重策略结果 */}
                      {step.result && step.id === 2 && (
                        <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-gray-500">生成策略数:</span>
                              <div className="font-medium">{step.result.strategies_generated} 套</div>
                            </div>
                            <div>
                              <span className="text-gray-500">主推策略:</span>
                              <div className="font-medium">{step.result.primary_strategy}</div>
                            </div>
                          </div>
                          {step.result.user_confirmed && (
                            <div className="mt-2 text-green-600 text-sm">
                              ✓ 权重配置已确认
                            </div>
                          )}
                          {step.result.message && (
                            <div className="mt-2 text-blue-600 text-sm">
                              {step.result.message}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Step 3: 数据处理详细进度 */}
                      {step.id === 3 && (
                        <div className="mt-3">
                          {/* 显示实时处理步骤 */}
                          {detailedProgress.filter(p => p.step === '数据处理').map((progress, idx) => (
                            <div key={idx} className="mb-2 p-2 bg-blue-50 rounded text-sm">
                              <div className="flex items-center gap-2">
                                {progress.status === 'completed' ? (
                                  <CheckCircle className="w-4 h-4 text-green-600" />
                                ) : progress.status === 'error' ? (
                                  <AlertTriangle className="w-4 h-4 text-red-600" />
                                ) : (
                                  <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                                )}
                                <span className={`font-medium ${
                                  progress.status === 'error' ? 'text-red-700' : 'text-blue-700'
                                }`}>
                                  {progress.details.substep || '处理中'}
                                </span>
                              </div>
                              <div className={`ml-6 mt-1 ${
                                progress.status === 'error' ? 'text-red-600' : 'text-blue-600'
                              }`}>
                                {progress.details.message}
                              </div>
                              {progress.status === 'completed' && idx === detailedProgress.filter(p => p.step === '数据处理').length - 1 && (
                                <div className="ml-6 mt-2 text-xs text-green-600">
                                  ✓ 数据处理完成
                                </div>
                              )}
                              {progress.status === 'error' && idx === detailedProgress.filter(p => p.step === '数据处理').length - 1 && (
                                <div className="ml-6 mt-2 text-xs text-red-600">
                                  ✗ 数据处理失败
                                </div>
                              )}
                            </div>
                          ))}
                          
                          {/* 数据处理完成后显示统计信息 */}
                          {dataStatistics && step.status === 'completed' && (
                            <div className="mt-3 p-3 bg-green-50 rounded-lg">
                              <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                  <span className="text-gray-500">航班数据:</span>
                                  <div className="font-medium">{dataStatistics.cdm_data?.total_flights?.toLocaleString()} 条记录</div>
                                </div>
                                <div>
                                  <span className="text-gray-500">机场覆盖:</span>
                                  <div className="font-medium">{dataStatistics.cdm_data?.departure_airports} 个起飞 / {dataStatistics.cdm_data?.arrival_airports} 个到达</div>
                                </div>
                              </div>
                              <div className="mt-2 text-sm">
                                <span className="text-gray-500">约束条件:</span>
                                <div className="grid grid-cols-2 gap-2 mt-1">
                                  {Object.entries(dataStatistics.constraints || {}).map(([key, value]: [string, any]) => (
                                    <div key={key} className="text-xs">
                                      <span className="text-gray-600">{key.replace(/_/g, ' ')}</span>: 
                                      <span className="font-medium ml-1">{value.active}/{value.total}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Step 4: 优化计算详细进度 */}
                      {step.id === 4 && (
                        <div className="mt-3">
                          {/* 显示实时优化步骤 */}
                          {detailedProgress.filter(p => p.step === '优化计算').map((progress, idx) => (
                            <div key={idx} className="mb-2 p-2 bg-yellow-50 rounded text-sm">
                              <div className="flex items-center gap-2">
                                {progress.status === 'completed' ? (
                                  <CheckCircle className="w-4 h-4 text-green-600" />
                                ) : progress.status === 'error' ? (
                                  <AlertTriangle className="w-4 h-4 text-red-600" />
                                ) : (
                                  <div className="w-4 h-4 border-2 border-yellow-600 border-t-transparent rounded-full animate-spin" />
                                )}
                                <span className={`font-medium ${
                                  progress.status === 'error' ? 'text-red-700' : 'text-yellow-700'
                                }`}>
                                  {progress.details.substep || '计算中'}
                                </span>
                              </div>
                              <div className={`ml-6 mt-1 ${
                                progress.status === 'error' ? 'text-red-600' : 'text-yellow-600'
                              }`}>
                                {progress.details.message}
                              </div>
                              {progress.status === 'completed' && idx === detailedProgress.filter(p => p.step === '优化计算').length - 1 && (
                                <div className="ml-6 mt-2 text-xs text-green-600">
                                  ✓ 优化计算完成
                                </div>
                              )}
                              {progress.status === 'error' && idx === detailedProgress.filter(p => p.step === '优化计算').length - 1 && (
                                <div className="ml-6 mt-2 text-xs text-red-600">
                                  ✗ 优化计算失败
                                </div>
                              )}
                            </div>
                          ))}
                          
                          {/* 优化计算完成后显示详细信息 */}
                          {step.status === 'completed' && dataStatistics?.system_output && (
                            <div className="mt-3 p-3 bg-green-50 rounded-lg">
                              <div className="text-sm">
                                <span className="text-green-700 font-medium">优化计算完成</span>
                                <div className="mt-2 space-y-1">
                                  {/* 显示约束应用统计 */}
                                  {dataStatistics.system_output.includes('约束应用统计') && (
                                    <div className="text-green-700">
                                      <div className="font-medium">约束应用情况:</div>
                                      {dataStatistics.system_output.match(/airport_curfew: (\d+) 个/)?.[1] && (
                                        <div>• 机场宵禁约束: {dataStatistics.system_output.match(/airport_curfew: (\d+) 个/)?.[1]} 个</div>
                                      )}
                                      {dataStatistics.system_output.match(/sector_requirements: (\d+) 个/)?.[1] && (
                                        <div>• 航段要求约束: {dataStatistics.system_output.match(/sector_requirements: (\d+) 个/)?.[1]} 个</div>
                                      )}
                                    </div>
                                  )}
                                  
                                  {/* 显示求解状态 */}
                                  {dataStatistics.system_output.includes('glpk') && (
                                    <div className="text-orange-600 mt-2">
                                      <div className="font-medium">⚠️ 求解器状态:</div>
                                      <div>GLPK求解器未安装，使用模拟结果</div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* 显示系统输出摘要 */}
                      {step.id >= 3 && step.status === 'completed' && dataStatistics?.system_output && (
                        <details className="mt-3">
                          <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                            查看详细日志 ↓
                          </summary>
                          <div className="mt-2 p-2 bg-gray-100 rounded text-xs font-mono whitespace-pre-line max-h-96 overflow-y-auto">
                            {dataStatistics.system_output}
                          </div>
                        </details>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Weight Confirmation Modal */}
        {weightConfirmation.show && (
          <Card className="mb-8">
            <CardContent className="p-8">
              <div className="text-center mb-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">权重策略确认</h3>
                <p className="text-gray-500">AI已生成权重配置方案，请确认或调整后继续</p>
              </div>

              {/* 快速预设选择 */}
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-medium text-gray-900">快速预设方案</h4>
                  {/* Test Mode Toggle */}
                  <label className="flex items-center gap-2 text-sm text-gray-600">
                    <input
                      type="checkbox"
                      checked={testMode}
                      onChange={(e) => {
                        setTestMode(e.target.checked);
                        if (e.target.checked) {
                          toast.success('⚡ 已启用测试模式 - 仅处理前100行数据');
                        } else {
                          toast.success('📊 已切换到完整模式 - 处理全部数据');
                        }
                      }}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                    <span className="font-medium">
                      🧪 测试模式 
                      <span className="text-gray-500 font-normal">
                        (仅处理前100行)
                      </span>
                    </span>
                  </label>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const costOptimized = {
                        "方案A (成本优先)": { cancel: 1.0, delay: 0.1, late_pax: 0.5, revenue: 1.0, change_time: 0.2, change_aircraft: 0.8, cancel_flight: 1.0, change_airport: 0.6, change_nature: 0.3, add_flight: 0.9 },
                        "方案B (运营优先)": { cancel: 0.5, delay: 1.0, late_pax: 1.0, revenue: 0.2, change_time: 0.1, change_aircraft: 0.4, cancel_flight: 0.8, change_airport: 0.3, change_nature: 0.2, add_flight: 0.5 }
                      };
                      setEditableWeights(costOptimized);
                      toast.success('💰 已应用成本优先策略');
                    }}
                  >
                    成本优先
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const serviceOptimized = {
                        "方案A (服务优先)": { cancel: 0.3, delay: 1.5, late_pax: 1.8, revenue: 0.5, change_time: 0.8, change_aircraft: 1.0, cancel_flight: 0.3, change_airport: 1.2, change_nature: 0.4, add_flight: 1.5 },
                        "方案B (灵活调整)": { cancel: 0.8, delay: 1.2, late_pax: 1.0, revenue: 0.8, change_time: 1.0, change_aircraft: 0.6, cancel_flight: 0.8, change_airport: 0.8, change_nature: 0.6, add_flight: 1.0 }
                      };
                      setEditableWeights(serviceOptimized);
                      toast.success('✈️ 已应用服务优先策略');
                    }}
                  >
                    服务优先
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const balanced = {
                        "方案A (平衡策略)": { cancel: 0.8, delay: 0.8, late_pax: 0.8, revenue: 0.8, change_time: 0.6, change_aircraft: 0.6, cancel_flight: 0.8, change_airport: 0.5, change_nature: 0.4, add_flight: 0.7 },
                        "方案B (平衡策略)": { cancel: 0.6, delay: 1.0, late_pax: 1.0, revenue: 0.6, change_time: 0.5, change_aircraft: 0.5, cancel_flight: 0.6, change_airport: 0.4, change_nature: 0.3, add_flight: 0.6 }
                      };
                      setEditableWeights(balanced);
                      toast.success('⚖️ 已应用均衡策略');
                    }}
                  >
                    均衡策略
                  </Button>
                </div>
              </div>

              {editableWeights && (
                <div className="space-y-6">
                  {Object.entries(editableWeights).map(([planName, weights]: [string, any]) => (
                    <div key={planName} className="border rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-4">{planName}</h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {Object.entries(weights).map(([key, value]: [string, any]) => {
                          const getWeightLabel = (key: string) => {
                            const labels: Record<string, string> = {
                              'cancel': '取消权重',
                              'delay': '延误权重', 
                              'late_pax': '延误旅客权重',
                              'revenue': '收入权重',
                              'change_time': '变更时刻权重',
                              'change_aircraft': '更换飞机权重',
                              'cancel_flight': '航班取消权重',
                              'change_airport': '变更机场权重',
                              'change_nature': '变更性质权重',
                              'add_flight': '新增航班权重'
                            };
                            return labels[key] || key;
                          };

                          const getWeightDescription = (key: string) => {
                            const descriptions: Record<string, string> = {
                              'cancel': '航班取消的成本权重',
                              'delay': '航班延误的成本权重',
                              'late_pax': '旅客延误的影响权重',
                              'revenue': '收入损失的权重',
                              'change_time': '变更起飞时间的成本',
                              'change_aircraft': '更换飞机的成本',
                              'cancel_flight': '取消航班的成本',
                              'change_airport': '变更机场的成本',
                              'change_nature': '变更航班性质的成本',
                              'add_flight': '新增航班的成本'
                            };
                            return descriptions[key] || '';
                          };

                          return (
                            <div key={key} className="space-y-2">
                              <label className="block text-sm font-medium text-gray-700">
                                {getWeightLabel(key)}
                              </label>
                              <input
                                type="number"
                                min="0"
                                max="2"
                                step="0.1"
                                value={value}
                                onChange={(e) => {
                                  const newValue = parseFloat(e.target.value) || 0;
                                  setEditableWeights((prev: any) => ({
                                    ...prev,
                                    [planName]: {
                                      ...prev[planName],
                                      [key]: newValue
                                    }
                                  }));
                                }}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                              <div className="text-xs text-gray-500">
                                {getWeightDescription(key)}<br/>
                                范围: 0.0 - 2.0 (数值越大优先级越高)
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}

                  <div className="flex justify-center gap-4 pt-6">
                    <Button
                      variant="outline"
                      size="lg"
                      onClick={() => {
                        // 重置为原始权重
                        setEditableWeights(JSON.parse(JSON.stringify(weightConfirmation.weights)));
                        toast.success('🤖 已重置为AI推荐权重');
                      }}
                    >
                      重置为AI推荐
                    </Button>
                    <Button
                      size="lg"
                      onClick={() => {
                        toast.success('✅ 权重已确认，开始优化计算');
                        continueWithWeights(editableWeights);
                      }}
                      className="bg-blue-500 hover:bg-blue-600"
                    >
                      确认权重并继续
                    </Button>
                  </div>
                </div>
              )}
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
                  <div className="text-2xl font-bold text-blue-600">{finalResult.summary.processed_flights || finalResult.summary.total_flights}</div>
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
                      {(expandedPlans[planName] ? flights : flights.slice(0, 5)).map((flight, index) => (
                        <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                          <div className="flex items-center gap-3">
                            <span className="font-mono text-sm font-medium">{flight.flight_number}</span>
                            <Badge variant="outline" className="text-xs">
                              {flight.adjustment_action}
                            </Badge>
                          </div>
                          <div className="text-sm text-gray-500">
                            {flight.additional_delay_minutes > 0 && `+${flight.additional_delay_minutes}min `}
                            {flight.reason}
                          </div>
                        </div>
                      ))}
                      {flights.length > 5 && (
                        <div className="text-center py-2">
                          {!expandedPlans[planName] ? (
                            <button
                              onClick={() => setExpandedPlans(prev => ({ ...prev, [planName]: true }))}
                              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                            >
                              显示更多 ({flights.length - 5} 个航班) ↓
                            </button>
                          ) : (
                            <button
                              onClick={() => setExpandedPlans(prev => ({ ...prev, [planName]: false }))}
                              className="text-sm text-gray-600 hover:text-gray-800 font-medium"
                            >
                              收起 ↑
                            </button>
                          )}
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