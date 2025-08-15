"use client";

import React from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { navigationConfig } from '@/config/navigation';

interface SidebarProps {
  activeTab: string;
  navigationState: Record<string, boolean>;
  onToggleNavGroup: (groupId: string) => void;
  onTabChange: (tabId: string) => void;
  getActiveGroup: () => string;
}

export function Sidebar({
  activeTab,
  navigationState,
  onToggleNavGroup,
  onTabChange,
  getActiveGroup
}: SidebarProps) {
  return (
    <div className="w-80 bg-white/90 backdrop-blur-sm border-r border-gray-200 shadow-lg flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
          AI+航班调整系统
        </h1>
        <p className="text-gray-600 text-sm mt-1">多智能体驱动的航班调整解决方案</p>
      </div>
      
      <nav className="flex-1 p-4 space-y-2">
        {navigationConfig.map((group) => (
          <div key={group.id} className="space-y-1">
            {/* 分组标题 */}
            <button
              onClick={() => onToggleNavGroup(group.id)}
              className={`w-full flex items-center justify-between p-3 rounded-lg transition-all duration-200 ${
                getActiveGroup() === group.id
                  ? 'bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 text-indigo-700'
                  : 'hover:bg-gray-50 text-gray-700'
              }`}
            >
              <div className="flex items-center space-x-3">
                <group.icon className="h-5 w-5" />
                <span className="font-medium">{group.label}</span>
              </div>
              {navigationState[group.id] ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
            
            {/* 子项目 */}
            {navigationState[group.id] && (
              <div className="ml-6 space-y-1">
                {group.items.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => onTabChange(item.id)}
                    className={`w-full flex items-center space-x-3 p-3 rounded-lg transition-all duration-200 text-left ${
                      activeTab === item.id
                        ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg'
                        : 'hover:bg-gray-50 text-gray-600'
                    }`}
                  >
                    <item.icon className="h-4 w-4" />
                    <div className="flex-1">
                      <div className="font-medium">{item.label}</div>
                      {item.description && (
                        <div className={`text-xs mt-1 ${
                          activeTab === item.id ? 'text-blue-100' : 'text-gray-500'
                        }`}>
                          {item.description}
                        </div>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>
    </div>
  );
}
