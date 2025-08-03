import React, { useState } from 'react';
import { ChartBarIcon, CircleStackIcon } from '@heroicons/react/24/outline';
import FactorLibrary from '../components/FactorLibrary';
import MessageAlert from '../components/dashboard/MessageAlert';
import { SelectedFactor } from '../services/api';

interface QuantitativeSelectionProps {}

const QuantitativeSelection: React.FC<QuantitativeSelectionProps> = () => {
  const [activeTab, setActiveTab] = useState<'factors'>('factors');
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info' | 'warning'; text: string } | null>(null);

  return (
    <div className="space-y-6">
      {/* 消息提示 */}
      <MessageAlert message={message} />

      {/* 顶部导航 */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div className="tabs tabs-boxed">
          <a 
            className={`tab ${activeTab === 'factors' ? 'tab-active' : ''}`}
            onClick={() => setActiveTab('factors')}
          >
            <ChartBarIcon className="w-4 h-4 mr-2" />
            因子库
          </a>
        </div>
      </div>

      {/* 主要内容区域 */}
      <div className="min-h-[600px]">
        <FactorLibrary />
      </div>
    </div>
  );
};

export default QuantitativeSelection;