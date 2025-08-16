"use client";

import React from 'react';
import { Sidebar } from '@/components/Sidebar';
import { RealtimeDataBoard } from '@/components/RealtimeDataBoard/index';

export default function DataBoardPage() {
  return (
    <div className="min-h-screen bg-[#faf9f6]">
      <div className="h-screen flex">
        {/* 侧边栏 */}
        <Sidebar />
        
        {/* 主内容区域 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <main className="flex-1 overflow-y-auto">
            <RealtimeDataBoard />
          </main>
        </div>
      </div>
    </div>
  );
}
