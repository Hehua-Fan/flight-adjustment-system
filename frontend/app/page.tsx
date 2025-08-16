"use client";

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Sidebar } from '@/components/Sidebar';

export default function HomePage() {
  const [activeTab, setActiveTab] = useState('realtime-dashboard');

  // 导航相关函数
  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
  };

  // 内容渲染
  const renderContent = () => {
    switch (activeTab) {
      case 'event-analysis':
      case 'weight-strategy':
      case 'data-processing':
      case 'optimization-calc':
      case 'plan-decision':
      case 'execution-issue':
        return (
          <Card>
            <CardContent className="p-12 text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-2">功能已移除</h3>
              <p className="text-gray-500">该功能已从系统中移除</p>
            </CardContent>
          </Card>
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
          onTabChange={handleTabChange}
        />

        {/* 主内容区域 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <main className="flex-1 overflow-y-auto p-6">
            {renderContent()}
          </main>
        </div>
      </div>
    </div>
  );
}