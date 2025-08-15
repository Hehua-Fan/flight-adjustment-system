"use client";

import React from 'react';
import { Button } from '@/components/ui/button';

interface FileInfo {
  cdm_files?: Array<{
    name: string;
    size: number;
    modified: string;
  }>;
  constraint_files?: Array<{
    name: string;
    exists: boolean;
    size?: number;
    modified?: string;
  }>;
}

interface FilePreview {
  filename: string;
  content: string;
}

interface DataManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  fileInfo: FileInfo | null;
  filePreview: FilePreview | null;
  onFileUpload: (file: File, type: string) => Promise<void>;
  onFileDelete: (filename: string, type: string) => Promise<void>;
  onFilePreview: (filename: string, type: string) => Promise<void>;
  onClosePreview: () => void;
}

export function DataManagerModal({
  isOpen,
  onClose,
  fileInfo,
  filePreview,
  onFileUpload,
  onFileDelete,
  onFilePreview,
  onClosePreview
}: DataManagerModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[80vh] overflow-hidden">
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-800">数据管理</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              ×
            </Button>
          </div>
        </div>
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* CDM文件管理 */}
            <div>
              <h4 className="font-medium text-slate-800 mb-4">CDM航班数据</h4>
              <div className="space-y-3">
                {fileInfo?.cdm_files?.map((file, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-slate-800">{file.name}</div>
                      <div className="text-xs text-slate-500">
                        {(file.size / 1024 / 1024).toFixed(1)}MB • {new Date(file.modified).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => onFilePreview(file.name, 'cdm')}>
                        预览
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => onFileDelete(file.name, 'cdm')} className="text-red-600">
                        删除
                      </Button>
                    </div>
                  </div>
                )) || <div className="text-sm text-slate-500 p-4 border border-dashed rounded-lg text-center">暂无CDM文件</div>}
                
                <div className="border-2 border-dashed border-slate-300 rounded-lg p-4 text-center hover:border-blue-400 transition-colors">
                  <input
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) onFileUpload(file, 'cdm');
                    }}
                    className="hidden"
                    id="cdm-upload-modal"
                  />
                  <label htmlFor="cdm-upload-modal" className="cursor-pointer">
                    <div className="text-sm text-slate-600 font-medium">📁 上传CDM文件</div>
                    <div className="text-xs text-slate-500 mt-1">支持 .csv, .xlsx, .xls 格式</div>
                  </label>
                </div>
              </div>
            </div>

            {/* 约束文件管理 */}
            <div>
              <h4 className="font-medium text-slate-800 mb-4">约束条件文件</h4>
              <div className="space-y-3">
                {fileInfo?.constraint_files?.map((file, idx) => (
                  <div key={idx} className={`flex items-center justify-between p-3 rounded-lg ${
                    file.exists ? 'bg-emerald-50 border border-emerald-200' : 'bg-red-50 border border-red-200'
                  }`}>
                    <div className="flex items-center gap-3 flex-1">
                      <div className={`w-2 h-2 rounded-full ${file.exists ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                      <div>
                        <div className="text-sm font-medium text-slate-800">{file.name}</div>
                        <div className="text-xs text-slate-500">
                          {file.exists ? `${((file.size || 0) / 1024).toFixed(1)}KB • ${new Date(file.modified || '').toLocaleString()}` : '文件缺失'}
                        </div>
                      </div>
                    </div>
                    {file.exists && (
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => onFilePreview(file.name, 'constraint')}>
                          预览
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => onFileDelete(file.name, 'constraint')} className="text-red-600">
                          删除
                        </Button>
                      </div>
                    )}
                  </div>
                )) || <div className="text-sm text-slate-500 p-4 border border-dashed rounded-lg text-center">暂无约束文件</div>}
                
                <div className="border-2 border-dashed border-slate-300 rounded-lg p-4 text-center hover:border-emerald-400 transition-colors">
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) onFileUpload(file, 'constraint');
                    }}
                    className="hidden"
                    id="constraint-upload-modal"
                  />
                  <label htmlFor="constraint-upload-modal" className="cursor-pointer">
                    <div className="text-sm text-slate-600 font-medium">📋 上传约束文件</div>
                    <div className="text-xs text-slate-500 mt-1">文件名需为预定义的约束类型 (.csv)</div>
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* 文件预览 */}
          {filePreview && (
            <div className="mt-6 p-4 border rounded-lg bg-slate-50">
              <div className="flex items-center justify-between mb-3">
                <h5 className="font-medium text-slate-800">文件预览: {filePreview.filename}</h5>
                <Button variant="ghost" size="sm" onClick={onClosePreview}>
                  关闭
                </Button>
              </div>
              <div className="bg-white p-3 rounded border overflow-auto max-h-64">
                <pre className="text-xs font-mono whitespace-pre-wrap text-slate-600">
                  {filePreview.content}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
