"use client";

import React from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { navigationConfig, NavigationItem } from '@/config/navigation';
import Image from 'next/image';

interface SidebarProps {
  activeTab?: string;
  onTabChange?: (tabId: string) => void;
}

export function Sidebar({
  activeTab,
  onTabChange
}: SidebarProps) {
  const router = useRouter();
  const pathname = usePathname();

  const handleItemClick = (item: NavigationItem) => {
    if (item.route) {
      // 如果有路由配置，则跳转到对应路由
      router.push(item.route);
    } else if (onTabChange) {
      // 否则使用原有的tab切换逻辑
      onTabChange(item.id);
    }
  };

  const isItemActive = (item: NavigationItem) => {
    if (item.route) {
      // 如果有路由配置，基于当前路径判断是否激活
      return pathname === item.route;
    }
    // 否则基于activeTab判断
    return activeTab === item.id;
  };

  return (
    <div className="w-50 bg-[#faf9f6] backdrop-blur-sm shadow-lg flex flex-col">
      <div className="p-6 flex justify-center">
        <Image src="/logo.png" alt="logo" width={80} height={80} className="cursor-pointer" onClick={() => router.push('/')} />
      </div>
      
      <nav className="flex-1 p-4 space-y-4">
        {navigationConfig.map((group) => (
          <div key={group.id} className="space-y-2">
            {/* 分类标题 */}
            <div className="text-gray-500 font-medium text-sm px-3 py-1">
              {group.label}
            </div>
            
            {/* 菜单项目 */}
            <div className="space-y-1">
              {group.items.map((item) => {
                const isActive = isItemActive(item);
                return (
                  <button
                    key={item.id}
                    onClick={() => handleItemClick(item)}
                    className={`w-full flex items-center space-x-3 p-3 rounded-lg transition-all duration-200 text-left cursor-pointer ${
                      isActive
                        ? 'bg-[#f1eee6] text-black font-medium'
                        : 'hover:bg-[#f1eee6] text-gray-700'
                    }`}
                  >
                    <item.icon 
                      className="h-4 w-4" 
                      isActive={isActive}
                    />
                    <div className="flex-1">
                      <div className="font-medium">{item.label}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
    </div>
  );
}
