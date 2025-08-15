import { 
  Plane, 
  Brain, 
  Settings, 
  BarChart3, 
  FileText, 
  Upload, 
  TrendingUp 
} from 'lucide-react';

export interface NavigationItem {
  id: string;
  label: string;
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
}

export interface NavigationGroup {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  items: NavigationItem[];
}

export const navigationConfig: NavigationGroup[] = [
  {
    id: 'event-system',
    label: '事件处理系统',
    icon: Plane,
    items: [
      {
        id: 'event-analysis',
        label: '事件分析',
        description: 'AI智能分析事件类型和严重程度',
        icon: Brain
      },
      {
        id: 'weight-strategy',
        label: '权重策略',
        description: '生成优化权重配置方案',
        icon: Settings
      },
      {
        id: 'data-processing',
        label: '数据处理',
        description: '加载航班数据和约束条件',
        icon: Upload
      },
      {
        id: 'optimization-calc',
        label: '优化计算',
        description: '生成多种调整方案',
        icon: BarChart3
      },
      {
        id: 'plan-decision',
        label: '方案决策',
        description: '智能选择最优方案',
        icon: TrendingUp
      },
      {
        id: 'execution-issue',
        label: '执行下发',
        description: '生成执行指令和报告',
        icon: FileText
      }
    ]
  }
];
