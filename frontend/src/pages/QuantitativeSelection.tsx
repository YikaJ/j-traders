import React, { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  CircleStackIcon,
  CubeIcon
} from '@heroicons/react/24/outline';

// 组件导入
import FactorLibrary from '../components/FactorLibrary';
import DataFieldsViewer from '../components/DataFieldsViewer';
import SelectedFactorsOverview from '../components/quantitative/SelectedFactorsOverview';
import MessageAlert from '../components/dashboard/MessageAlert';

// API导入
import {
  SelectedFactor,
  DataField
} from '../services/api';

const QuantitativeSelection: React.FC = () => {
  // 标签页状态
  const [activeTab, setActiveTab] = useState<'factors' | 'fields'>('factors');

  // 主要状态
  const [selectedFactors, setSelectedFactors] = useState<SelectedFactor[]>([]);
  const [selectedFields, setSelectedFields] = useState<string[]>([]);

  // 消息状态
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info' | 'warning', text: string } | null>(null);

  // 显示消息
  const showMessage = (type: 'success' | 'error' | 'info' | 'warning', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  // 处理因子选择
  const handleFactorSelect = (factor: SelectedFactor) => {
    // 检查是否已存在
    const exists = selectedFactors.some(f => f.id === factor.id);
    if (exists) {
      showMessage('warning', '该因子已经添加过了');
      return;
    }

    // 添加因子
    const updatedFactors = [...selectedFactors, { ...factor, weight: 1.0, is_enabled: true }];
    setSelectedFactors(updatedFactors);
    showMessage('success', `已添加因子: ${factor.display_name}`);
  };

  // 移除因子
  const handleRemoveFactor = (factorId: string) => {
    const updatedFactors = selectedFactors.filter(f => f.id !== factorId);
    setSelectedFactors(updatedFactors);
    showMessage('info', '因子已移除');
  };

  // 处理数据字段选择
  const handleFieldSelect = (field: DataField) => {
    const isSelected = selectedFields.includes(field.field_id);
    if (isSelected) {
      // 移除字段
      setSelectedFields(prev => prev.filter(id => id !== field.field_id));
      showMessage('info', `已移除字段: ${field.display_name}`);
    } else {
      // 添加字段
      setSelectedFields(prev => [...prev, field.field_id]);
      showMessage('success', `已添加字段: ${field.display_name}`);
    }
  };

  // 更新因子权重
  const handleFactorWeightChange = (factorId: string, weight: number) => {
    setSelectedFactors(selectedFactors.map(factor =>
      factor.id === factorId ? { ...factor, weight } : factor
    ));
  };

  // 切换因子启用状态
  const handleFactorToggle = (factorId: string) => {
    setSelectedFactors(selectedFactors.map(factor =>
      factor.id === factorId ? { ...factor, is_enabled: !factor.is_enabled } : factor
    ));
  };

  // 计算总权重
  const getTotalWeight = () => {
    return selectedFactors
      .filter(f => f.is_enabled)
      .reduce((sum, factor) => sum + (factor.weight ?? 0), 0);
  };

  // 检查权重是否有效
  const isWeightValid = () => {
    const total = getTotalWeight();
    return Math.abs(total - 1.0) < 0.01; // 1% 误差范围
  };

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
          <a 
            className={`tab ${activeTab === 'fields' ? 'tab-active' : ''}`}
            onClick={() => setActiveTab('fields')}
          >
            <CircleStackIcon className="w-4 h-4 mr-2" />
            数据字段
          </a>
        </div>
        
        {/* 统计信息 */}
        <div className="flex gap-4 text-sm">
          {activeTab === 'factors' && (
            <>
              <span className="badge badge-outline">
                已选因子: {selectedFactors.length}
              </span>
              <span className={`badge ${isWeightValid() ? 'badge-success' : 'badge-warning'}`}>
                权重: {getTotalWeight().toFixed(2)}
              </span>
            </>
          )}
          {activeTab === 'fields' && (
            <span className="badge badge-outline">
              已选字段: {selectedFields.length}
            </span>
          )}
        </div>
      </div>

      {/* 已选因子概览 - 只在因子库标签页显示 */}
      {activeTab === 'factors' && selectedFactors.length > 0 && (
        <SelectedFactorsOverview
          selectedFactors={selectedFactors}
          currentStrategy={null}
          isWeightValid={isWeightValid}
          getTotalWeight={getTotalWeight}
          onRemoveFactor={handleRemoveFactor}
          onFactorWeightChange={handleFactorWeightChange}
          onFactorToggle={handleFactorToggle}
          onNormalizeWeights={() => {}}
        />
      )}

      {/* 主要内容区域 */}
      <div className="min-h-[600px]">
        {activeTab === 'factors' && (
          <FactorLibrary
            mode="selection"
            onFactorSelect={handleFactorSelect}
            selectedFactors={selectedFactors}
          />
        )}
        
        {activeTab === 'fields' && (
          <DataFieldsViewer
            mode="browse"
            onFieldSelect={handleFieldSelect}
            selectedFields={selectedFields}
          />
        )}
      </div>
    </div>
  );
};

export default QuantitativeSelection;