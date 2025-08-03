import React, { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';

// 组件导入
import FactorLibrary from '../components/FactorLibrary';
import WeightConfigPanel from '../components/WeightConfigPanel';
import FactorAnalysisPanel from '../components/FactorAnalysisPanel';
import SelectedFactorsOverview from '../components/quantitative/SelectedFactorsOverview';
import MessageAlert from '../components/dashboard/MessageAlert';

// API导入
import {
  weightApi,
  SelectedFactor,
  WeightPreset
} from '../services/api';

const QuantitativeSelection: React.FC = () => {
  // 主要状态
  const [activeTab, setActiveTab] = useState<'factor-library' | 'weight-config' | 'factor-analysis'>('factor-library');
  const [selectedFactors, setSelectedFactors] = useState<SelectedFactor[]>([]);
  const [, setWeightPresets] = useState<WeightPreset[]>([]);

  // 消息状态
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info' | 'warning', text: string } | null>(null);

  // 加载初始数据
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const {data: presets} = await weightApi.getWeightPresets();
      setWeightPresets(presets);
    } catch (error) {
      console.error('加载初始数据失败:', error);
    }
  };

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

    // 添加因子，默认权重为等权重
    const updatedFactors = [...selectedFactors, { ...factor, weight: 0 }];
    
    // 重新分配权重
    const enabledCount = updatedFactors.filter(f => f.is_enabled).length;
    if (enabledCount > 0) {
      const equalWeight = 1.0 / enabledCount;
      updatedFactors.forEach(f => {
        if (f.is_enabled) {
          f.weight = equalWeight;
        }
      });
    }

    setSelectedFactors(updatedFactors);
    showMessage('success', `已添加因子: ${factor.name}`);
  };

  // 移除因子
  const handleRemoveFactor = (factorId: string) => {
    const updatedFactors = selectedFactors.filter(f => f.id !== factorId);
    
    // 重新分配权重
    const enabledCount = updatedFactors.filter(f => f.is_enabled).length;
    if (enabledCount > 0) {
      const equalWeight = 1.0 / enabledCount;
      updatedFactors.forEach(f => {
        if (f.is_enabled) {
          f.weight = equalWeight;
        }
      });
    }

    setSelectedFactors(updatedFactors);
    showMessage('info', '因子已移除');
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

  // 标准化权重
  const handleNormalizeWeights = async () => {
    try {
      const result = await weightApi.normalizeWeights(selectedFactors);
      setSelectedFactors(Array.isArray(result) ? result : []);
      showMessage('success', '权重已标准化');
    } catch (error) {
      console.error('标准化权重失败:', error);
      showMessage('error', '标准化权重失败');
    }
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
            className={`tab ${activeTab === 'factor-library' ? 'tab-active' : ''}`}
            onClick={() => setActiveTab('factor-library')}
          >
            <ChartBarIcon className="w-4 h-4 mr-2" />
            因子库
          </a>
          {selectedFactors.length > 0 && (
            <>
              <a
                className={`tab ${activeTab === 'weight-config' ? 'tab-active' : ''}`}
                onClick={() => setActiveTab('weight-config')}
              >
                <BeakerIcon className="w-4 h-4 mr-2" />
                权重配置
              </a>
              <a
                className={`tab ${activeTab === 'factor-analysis' ? 'tab-active' : ''}`}
                onClick={() => setActiveTab('factor-analysis')}
              >
                <BeakerIcon className="w-4 h-4 mr-2" />
                因子分析
              </a>
            </>
          )}
        </div>
      </div>

      {/* 已选因子概览 */}
      <SelectedFactorsOverview
        selectedFactors={selectedFactors}
        currentStrategy={null}
        isWeightValid={isWeightValid}
        getTotalWeight={getTotalWeight}
        onRemoveFactor={handleRemoveFactor}
        onFactorWeightChange={handleFactorWeightChange}
        onFactorToggle={handleFactorToggle}
        onNormalizeWeights={handleNormalizeWeights}
      />

      {/* 主要内容区域 */}
      <div className="min-h-[600px]">
        {activeTab === 'factor-library' && (
          <FactorLibrary
            mode="selection"
            onFactorSelect={handleFactorSelect}
            selectedFactors={selectedFactors}
          />
        )}

        {activeTab === 'weight-config' && (
          <WeightConfigPanel
            factors={selectedFactors}
            onFactorsChange={setSelectedFactors}
            onClose={() => setActiveTab('factor-library')}
          />
        )}

        {activeTab === 'factor-analysis' && (
          <FactorAnalysisPanel
            factors={selectedFactors}
          />
        )}
      </div>
    </div>
  );
};

export default QuantitativeSelection;