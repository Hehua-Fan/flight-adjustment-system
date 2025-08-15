"use client";

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Info, Plus, Minus, Trash2 } from 'lucide-react';
import { ProcessStep } from '@/types';
import { toast } from 'sonner';

interface WeightStrategyPreviewProps {
  stepData: ProcessStep;
  analysisResult?: any;
  onWeightsConfirmed?: (weights: any) => void;
  testMode?: boolean;
  onTestModeChange?: (testMode: boolean) => void;
}

interface WeightScheme {
  id: string;
  name: string;
  cancel: number;
  delay: number;
  late_pax: number;
  revenue: number;
  change_time: number;
  change_aircraft: number;
  cancel_flight: number;
  change_airport: number;
  change_nature: number;
  add_flight: number;
}

// 权重字段配置
const WEIGHT_FIELDS = [
  { key: 'cancel', label: '取消成本', description: '航班取消的成本权重' },
  { key: 'delay', label: '延误成本', description: '航班延误的成本权重' },
  { key: 'late_pax', label: '旅客延误', description: '旅客延误的成本权重' },
  { key: 'revenue', label: '收入损失', description: '收入损失的权重' },
  { key: 'change_time', label: '改时间', description: '改变航班时间的操作成本' },
  { key: 'change_aircraft', label: '换机型', description: '更换飞机机型的操作成本' },
  { key: 'cancel_flight', label: '取消航班', description: '取消航班的操作成本' },
  { key: 'change_airport', label: '换机场', description: '更换机场的操作成本' },
  { key: 'change_nature', label: '改性质', description: '改变航班性质的操作成本' },
  { key: 'add_flight', label: '加班', description: '增加航班的操作成本' }
];

export function WeightStrategyPreview({ 
  stepData, 
  analysisResult, 
  onWeightsConfirmed, 
  testMode, 
  onTestModeChange 
}: WeightStrategyPreviewProps) {
  
  // 初始化权重方案
  const initializeWeightSchemes = (): WeightScheme[] => {
    if (analysisResult?.weights) {
      return Object.entries(analysisResult.weights).map(([name, weights]: [string, any], index) => ({
        id: `scheme-${index + 1}`,
        name,
        ...weights
      }));
    }
    
    // 默认方案
    return [
      {
        id: 'scheme-1',
        name: '方案1 (成本优先)',
        cancel: 0.8,
        delay: 0.3,
        late_pax: 1.0,
        revenue: 0.8,
        change_time: 0.3,
        change_aircraft: 0.5,
        cancel_flight: 0.8,
        change_airport: 0.4,
        change_nature: 0.2,
        add_flight: 0.7
      },
      {
        id: 'scheme-2',
        name: '方案2 (运营优先)',
        cancel: 0.3,
        delay: 1.5,
        late_pax: 1.2,
        revenue: 0.5,
        change_time: 0.2,
        change_aircraft: 0.3,
        cancel_flight: 0.5,
        change_airport: 0.7,
        change_nature: 0.1,
        add_flight: 0.4
      }
    ];
  };

  const [weightSchemes, setWeightSchemes] = useState<WeightScheme[]>(initializeWeightSchemes);


  // 添加新方案
  const addNewScheme = () => {
    const newScheme: WeightScheme = {
      id: `scheme-${Date.now()}`,
      name: `方案${weightSchemes.length + 1}`,
      cancel: 0.5,
      delay: 0.5,
      late_pax: 0.5,
      revenue: 0.5,
      change_time: 0.5,
      change_aircraft: 0.5,
      cancel_flight: 0.5,
      change_airport: 0.5,
      change_nature: 0.5,
      add_flight: 0.5
    };
    setWeightSchemes([...weightSchemes, newScheme]);
    toast.success('已添加新的权重方案');
  };

  // 删除方案
  const deleteScheme = (schemeId: string) => {
    if (weightSchemes.length <= 1) {
      toast.error('至少需要保留一个权重方案');
      return;
    }
    setWeightSchemes(weightSchemes.filter(scheme => scheme.id !== schemeId));
    toast.success('已删除权重方案');
  };

  // 更新权重值
  const updateWeight = (schemeId: string, field: string, value: number) => {
    setWeightSchemes(schemes => 
      schemes.map(scheme => 
        scheme.id === schemeId 
          ? { ...scheme, [field]: Math.max(0, Math.min(2, value)) }
          : scheme
      )
    );
  };

  // 更新方案名称
  const updateSchemeName = (schemeId: string, name: string) => {
    setWeightSchemes(schemes => 
      schemes.map(scheme => 
        scheme.id === schemeId 
          ? { ...scheme, name }
          : scheme
      )
    );
  };

  // 转换为后端期望的格式
  const convertToBackendFormat = () => {
    const result: Record<string, any> = {};
    weightSchemes.forEach(scheme => {
      const { name, ...weights } = scheme;
      result[name] = weights;
    });
    return result;
  };

  return (
    <div className="space-y-6">
      {/* 数学公式 */}
      <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
        <CardContent className="p-6">
          <div className="text-center mb-4">
            <h3 className="text-lg font-semibold text-blue-800 mb-2">优化目标函数</h3>
            <div className="bg-white p-4 rounded-lg border border-blue-200">
              <div className="text-sm text-slate-700 mb-2">总成本 = 延误成本 + 取消成本 + 操作调整成本</div>
              <div className="text-xs text-slate-500 font-mono">
                Minimize: Σ(w₁×取消 + w₂×延误 + w₃×旅客延误 + w₄×收入损失 + w₅×调整操作)
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 权重配置表格 */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-800">权重方案配置</h3>
            <Button onClick={addNewScheme} size="sm" className="gap-2">
              <Plus className="w-4 h-4" />
              添加方案
            </Button>
          </div>

          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-40">方案名称</TableHead>
                  {WEIGHT_FIELDS.map(field => (
                    <TableHead key={field.key} className="text-center min-w-20">
                      <div className="flex items-center justify-center gap-1">
                        <span className="text-xs">{field.label}</span>
                        <div className="relative group">
                          <Info className="w-3 h-3 text-slate-400 cursor-help" />
                          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-10">
                            {field.description}
                          </div>
                        </div>
                      </div>
                    </TableHead>
                  ))}
                  <TableHead className="w-20">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {weightSchemes.map((scheme) => (
                  <TableRow key={scheme.id}>
                    <TableCell>
                      <Input
                        value={scheme.name}
                        onChange={(e) => updateSchemeName(scheme.id, e.target.value)}
                        className="text-sm"
                      />
                    </TableCell>
                    {WEIGHT_FIELDS.map(field => (
                      <TableCell key={field.key} className="text-center">
                        <div className="flex items-center justify-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => updateWeight(scheme.id, field.key, scheme[field.key as keyof WeightScheme] as number - 0.1)}
                            className="w-6 h-6 p-0"
                          >
                            <Minus className="w-3 h-3" />
                          </Button>
                          <Input
                            type="number"
                            value={scheme[field.key as keyof WeightScheme]}
                            onChange={(e) => updateWeight(scheme.id, field.key, Number(e.target.value))}
                            min={0}
                            max={2}
                            step={0.1}
                            className="w-16 text-center text-xs"
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => updateWeight(scheme.id, field.key, scheme[field.key as keyof WeightScheme] as number + 0.1)}
                            className="w-6 h-6 p-0"
                          >
                            <Plus className="w-3 h-3" />
                          </Button>
                        </div>
                      </TableCell>
                    ))}
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteScheme(scheme.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        disabled={weightSchemes.length <= 1}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* 快速预设 */}
          <div className="mt-6 pt-4 border-t border-slate-200">
            <h4 className="text-sm font-medium text-slate-700 mb-3">快速预设</h4>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setWeightSchemes([
                    {
                      id: 'preset-cost',
                      name: '成本优先',
                      cancel: 0.8, delay: 0.3, late_pax: 1.0, revenue: 0.8,
                      change_time: 0.3, change_aircraft: 0.5, cancel_flight: 0.8,
                      change_airport: 0.4, change_nature: 0.2, add_flight: 0.7
                    }
                  ]);
                  toast.success('已应用成本优先预设');
                }}
              >
                成本优先
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setWeightSchemes([
                    {
                      id: 'preset-service',
                      name: '服务优先',
                      cancel: 0.3, delay: 1.5, late_pax: 1.2, revenue: 0.5,
                      change_time: 0.2, change_aircraft: 0.3, cancel_flight: 0.5,
                      change_airport: 0.7, change_nature: 0.1, add_flight: 0.4
                    }
                  ]);
                  toast.success('已应用服务优先预设');
                }}
              >
                服务优先
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setWeightSchemes([
                    {
                      id: 'preset-balanced',
                      name: '均衡方案',
                      cancel: 0.5, delay: 0.5, late_pax: 0.5, revenue: 0.5,
                      change_time: 0.5, change_aircraft: 0.5, cancel_flight: 0.5,
                      change_airport: 0.5, change_nature: 0.5, add_flight: 0.5
                    }
                  ]);
                  toast.success('已应用均衡方案预设');
                }}
              >
                均衡方案
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 确认权重按钮 */}
      <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
        <CardContent className="p-6">
          <div className="text-center space-y-4">
            <div className="text-blue-700 font-medium mb-2">权重策略配置</div>
            <p className="text-sm text-blue-600 mb-4">
              已配置 {weightSchemes.length} 个权重方案，确认无误后点击按钮继续
            </p>
            <div className="flex justify-center gap-4">
              <Button
                variant="outline"
                onClick={() => {
                  setWeightSchemes(initializeWeightSchemes());
                  toast.success('🤖 已重置为AI推荐权重');
                }}
              >
                🤖 重置为AI推荐
              </Button>
              <Button
                onClick={() => {
                  const weights = convertToBackendFormat();
                  toast.success('✅ 权重已确认，开始优化计算');
                  onWeightsConfirmed?.(weights);
                }}
                className="bg-blue-500 hover:bg-blue-600"
              >
                ✅ 确认权重并继续
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
