import React from 'react';
import { 
  Plane, 
  Settings, 
  PlaneTakeoff,
  Plus,
  BookOpen
} from 'lucide-react';
import { DashboardIcon } from '@/components/icons';

// Wrapper components for Lucide icons to handle isActive prop
const SettingsIcon: React.FC<{ className?: string; isActive?: boolean }> = ({ className }) => 
  <Settings className={className} />;

const PlusIcon: React.FC<{ className?: string; isActive?: boolean }> = ({ className }) => 
  <Plus className={className} />;

const BookOpenIcon: React.FC<{ className?: string; isActive?: boolean }> = ({ className }) => 
  <BookOpen className={className} />;

export interface NavigationItem {
  id: string;
  label: string;
  description?: string;
  icon: React.ComponentType<{ className?: string; isActive?: boolean }>;
  route?: string; // 添加路由字段
}

export interface NavigationGroup {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  items: NavigationItem[];
}

export const navigationConfig: NavigationGroup[] = [
  {
    id: 'realtime-monitoring',
    label: '实时监控系统',
    icon: Plane,
    items: [
      {
        id: 'realtime-dashboard',
        label: '实时数据看板',
        description: '航班实时状态监控和甘特图展示',
        icon: DashboardIcon,
        route: '/databoard'
      },
      {
        id: 'constraint-library',
        label: '约束条件库',
        description: '管理和查看各类航班运营约束条件',
        icon: SettingsIcon,
        route: '/constraint'
      }
    ]
  },
  {
    id: 'plan-management',
    label: '航班调整计划方案',
    icon: PlaneTakeoff,
    items: [
      {
        id: 'create-plan',
        label: '创建方案',
        description: '创建新的航班调整方案或编辑现有方案',
        icon: PlusIcon,
        route: '/plan/create'
      },
      {
        id: 'plan-library',
        label: '方案库',
        description: '管理和查看已保存的调整方案',
        icon: BookOpenIcon,
        route: '/plan/library'
      }
    ]
  }
];
