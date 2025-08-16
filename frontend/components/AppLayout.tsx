"use client";

import React from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';

interface ClientLayoutWrapperProps {
  children: React.ReactNode;
}

export function ClientLayoutWrapper({ children }: ClientLayoutWrapperProps) {
  const pathname = usePathname();
  
  // 定义需要显示Sidebar的路由
  const routesWithSidebar = ['/', '/data-board', '/constraint', '/plan/create', '/plan/library'];
  const shouldShowSidebar = routesWithSidebar.includes(pathname);

  if (!shouldShowSidebar) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="h-screen flex">
        {/* 侧边栏 */}
        <Sidebar />
        
        {/* 主内容区域 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <main className="flex-1 overflow-y-auto">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}

// 通用的 AppLayout 组件，总是显示侧边栏
interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        {children}
      </div>
    </div>
  );
}
