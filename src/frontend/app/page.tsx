"use client";

import React, { useState, useEffect } from 'react';

import { Card, CardContent } from '@/components/ui/card';

import { toast } from 'sonner';
import { 
  ProcessStep, 
  AnalysisResult, 
  OptimizationResult, 
  DataStatistics, 
  WeightConfirmation, 
  FileInfo, 
  FilePreview 
} from '@/types';
import { Sidebar } from '@/components/Sidebar';
import { DataManagerModal } from '@/components/Modal/DataManagerModal';
import { navigationConfig } from '@/config/navigation';

// 页面组件导入
import { EventAnalysis } from '@/components/pages/EventAnalysis';
import { WeightStrategy } from '@/components/pages/WeightStrategy';
import { DataProcessing } from '@/components/pages/DataProcessing';
import { OptimizationCalculation } from '@/components/pages/OptimizationCalculation';
import { PlanDecision } from '@/components/pages/PlanDecision';
import { ExecutionIssue } from '@/components/pages/ExecutionIssue';

export default function HomePage() {
  const [eventDescription, setEventDescription] = useState('');
  const [eventType, setEventType] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [testMode, setTestMode] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);
  const [activeTab, setActiveTab] = useState('event-analysis');
  
  const [processSteps, setProcessSteps] = useState<ProcessStep[]>([
    { id: 1, name: '事件分析', status: 'pending', description: 'AI智能分析事件类型和严重程度' },
    { id: 2, name: '权重策略', status: 'pending', description: '生成优化权重配置方案' },
    { id: 3, name: '数据处理', status: 'pending', description: '加载航班数据和约束条件' },
    { id: 4, name: '优化计算', status: 'pending', description: '生成多种调整方案' },
    { id: 5, name: '方案决策', status: 'pending', description: '智能选择最优方案' },
    { id: 6, name: '执行下发', status: 'pending', description: '生成执行指令和报告' }
  ]);
  
  const [finalResult, setFinalResult] = useState<OptimizationResult | null>(null);
  const [detailedProgress, setDetailedProgress] = useState<Array<Record<string, unknown>>>([]);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [dataStatistics, setDataStatistics] = useState<DataStatistics | null>(null);

  const [weightConfirmation, setWeightConfirmation] = useState<WeightConfirmation>({ 
    show: false, 
    weights: null, 
    confirmed: false 
  });

  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [showFileManager, setShowFileManager] = useState(false);
  const [filePreview, setFilePreview] = useState<FilePreview | null>(null);


  // 导航状态管理
  const [navigationState, setNavigationState] = useState<Record<string, boolean>>({
    'event-system': true,
    'schedule-system': false
  });

  // 加载文件信息
  useEffect(() => {
    const loadFileInfo = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/files/info');
        const data = await response.json() as FileInfo;
        setFileInfo(data);
        

      } catch (error) {
        console.error('加载文件信息失败:', error);
      }
    };
    
    loadFileInfo();
  }, []);

  const canStartAnalysis = (): boolean => {
    const hasCdmFile = Boolean(fileInfo?.cdm_files && fileInfo.cdm_files.length > 0);
    const hasConstraintFiles = Boolean(fileInfo?.constraint_files && fileInfo.constraint_files.some((f) => f.exists));
    const hasEventDescription = eventDescription.trim().length > 0;
    
    return hasCdmFile && hasConstraintFiles && hasEventDescription;
  };

  const handleAnalysis = async () => {
    if (!canStartAnalysis() || !eventDescription.trim()) return;
    
    setIsProcessing(true);
    setCurrentStep(1);
    
    // 更新步骤1为运行中
    setProcessSteps(prev => prev.map(step => 
      step.id === 1 ? { ...step, status: 'running' } : step
    ));

    try {
      const response = await fetch('http://localhost:8000/api/events/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: eventDescription,
          event_type: eventType,
          test_mode: testMode
        }),
      });

      if (!response.ok) throw new Error('分析失败');

      const result = await response.json();
      setAnalysisResult(result);
      
      // 更新步骤1为完成，步骤2为运行中
      setProcessSteps(prev => prev.map(step => 
        step.id === 1 ? { ...step, status: 'completed', result } : 
        step.id === 2 ? { ...step, status: 'running' } : step
      ));

      // 显示权重确认
      setWeightConfirmation({ show: true, weights: result.weights, confirmed: false, data: result });
      
      // 自动切换到权重策略页面
      setActiveTab('weight-strategy');
      
    } catch (error) {
      console.error('分析错误:', error);
      toast.error('分析失败，请重试');
      setProcessSteps(prev => prev.map(step => 
        step.id === 1 ? { ...step, status: 'error' } : step
      ));
    } finally {
      setIsProcessing(false);
    }
  };

  const continueWithWeights = async (confirmedWeights: Record<string, Record<string, number>>) => {
    try {
    setIsProcessing(true);
      
      // 更新步骤2为已完成，步骤3为运行中
      setProcessSteps(prev => prev.map(step => 
        step.id === 2 ? { ...step, status: 'completed', result: { user_confirmed: true, weights: confirmedWeights } } : 
        step.id === 3 ? { ...step, status: 'running' } : step
      ));
      
      setCurrentStep(3);
      setActiveTab('data-processing');
      
      // 调用后端优化API
      const response = await fetch('http://localhost:8000/api/optimization/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_description: eventDescription,
          weights: confirmedWeights,
          test_mode: testMode
        }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('优化结果:', result);
        
        // 设置数据统计信息（从 summary 字段获取）
        if (result.summary) {
          setDataStatistics({
            total_flights: result.summary.total_flights,
            normal_flights: result.summary.normal_flights,
            affected_flights: result.summary.cancelled_flights + result.summary.delayed_flights
          });
        }
        
        // 设置详细进度和最终结果
        setDetailedProgress([]);
        setFinalResult(result);
        
        // 更新后续步骤状态
        setProcessSteps(prev => prev.map(step => 
          step.id === 3 ? { ...step, status: 'completed', result } : 
          step.id === 4 ? { ...step, status: 'completed', result } :
          step.id === 5 ? { ...step, status: 'completed', result } :
          step.id === 6 ? { ...step, status: 'completed', result } : step
        ));
        
        setCurrentStep(6);
        
        toast.success('✅ 优化计算完成，所有方案已生成');
      } else {
        throw new Error('优化请求失败');
      }
    } catch (error) {
      console.error('权重确认错误:', error);
      toast.error('权重确认失败，请重试');
      
      // 回滚步骤状态
      setProcessSteps(prev => prev.map(step => 
        step.id === 2 ? { ...step, status: 'error' } : step
      ));
    } finally {
      setIsProcessing(false);
    }
  };

  // 文件管理函数
  const handleFileUpload = async (file: File, type: string) => {
      const formData = new FormData();
      formData.append('file', file);
      
    try {
      const response = await fetch(`http://localhost:8000/api/files/upload/${type}`, {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        toast.success(`${type === 'cdm' ? 'CDM' : '约束'}文件上传成功`);
      // 重新加载文件信息
        const fileInfoResponse = await fetch('http://localhost:8000/api/files/info');
        const data = await fileInfoResponse.json();
        setFileInfo(data);
      } else {
        toast.error('文件上传失败');
      }
    } catch (error) {
      console.error('上传错误:', error);
      toast.error('文件上传失败');
    }
  };

  const handleFileDelete = async (filename: string, type: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/files/${type}/${filename}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        toast.success('文件删除成功');
      // 重新加载文件信息
        const fileInfoResponse = await fetch('http://localhost:8000/api/files/info');
        const data = await fileInfoResponse.json();
        setFileInfo(data);
      } else {
        toast.error('文件删除失败');
      }
    } catch (error) {
      console.error('删除错误:', error);
      toast.error('文件删除失败');
    }
  };

  const handleFilePreview = async (filename: string, type: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/files/preview/${type}/${filename}`);
      const data = await response.json();
      
      if (response.ok) {
        setFilePreview({
          filename,
          content: data.content
        });
      } else {
        toast.error('文件预览失败');
      }
    } catch (error) {
      console.error('预览错误:', error);
      toast.error('文件预览失败');
    }
  };

  // 导航相关函数
  const toggleNavGroup = (groupId: string) => {
    setNavigationState(prev => ({
      ...prev,
      [groupId]: !prev[groupId]
    }));
  };

  const getActiveGroup = (): string => {
    return navigationConfig.find(group => 
      group.items.some(item => item.id === activeTab)
    )?.id || '';
  };

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
  };



  // 内容渲染
  const renderContent = () => {
    switch (activeTab) {
      case 'event-analysis':
        return (
          <EventAnalysis
            eventType={eventType}
            setEventType={setEventType}
            eventDescription={eventDescription}
            setEventDescription={setEventDescription}
            fileInfo={fileInfo}
            canStartAnalysis={canStartAnalysis}
            handleAnalysis={handleAnalysis}
            isProcessing={isProcessing}
            currentStep={currentStep}
            weightConfirmation={weightConfirmation}
            onShowFileManager={() => setShowFileManager(true)}
            analysisResult={analysisResult}
          />
        );

      case 'weight-strategy':
        return (
          <WeightStrategy
            processSteps={processSteps}
            analysisResult={analysisResult}
            onWeightsConfirmed={continueWithWeights}
            testMode={testMode}
            onTestModeChange={setTestMode}
            weightConfirmation={weightConfirmation}
          />
        );

      case 'data-processing':
        return (
          <DataProcessing
            stepData={processSteps.find(step => step.id === 3) || processSteps[2]}
            analysisResult={analysisResult}
            dataStatistics={dataStatistics}
          />
        );

      case 'optimization-calc':
        return (
          <OptimizationCalculation
            stepData={processSteps.find(step => step.id === 4) || processSteps[3]}
            detailedProgress={detailedProgress}
            isProcessing={isProcessing}
          />
        );

      case 'plan-decision':
        return (
          <PlanDecision
            stepData={processSteps.find(step => step.id === 5) || processSteps[4]}
            finalResult={finalResult}
            onPlanSelected={(planId) => {
              console.log('选择方案:', planId);
              // 这里可以处理方案选择逻辑
            }}
          />
        );

      case 'execution-issue':
        return (
          <ExecutionIssue
            stepData={processSteps.find(step => step.id === 6) || processSteps[5]}
            finalResult={finalResult}
            selectedPlan={null}
          />
        );

      default:
        return (
          <Card>
            <CardContent className="p-12 text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-2">功能开发中</h3>
              <p className="text-gray-500">该功能正在开发中，敬请期待</p>
          </CardContent>
        </Card>
        );
    }
                          };

                          return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="h-screen flex">
        {/* 侧边栏 */}
        <Sidebar
          activeTab={activeTab}
          navigationState={navigationState}
          onToggleNavGroup={toggleNavGroup}
          onTabChange={handleTabChange}
          getActiveGroup={getActiveGroup}
        />

        {/* 主内容区域 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <main className="flex-1 overflow-y-auto p-6">
            {renderContent()}
          </main>
                  </div>

        {/* 数据管理弹窗 */}
        <DataManagerModal
          isOpen={showFileManager}
          onClose={() => setShowFileManager(false)}
          fileInfo={fileInfo}
          filePreview={filePreview}
          onFileUpload={handleFileUpload}
          onFileDelete={handleFileDelete}
          onFilePreview={handleFilePreview}
          onClosePreview={() => setFilePreview(null)}
        />
                </div>
    </div>
  );
}
