import React, { useState, useEffect } from 'react';
import {
  PlayIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  StarIcon,
  AdjustmentsHorizontalIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';

// 组件导入
import FactorLibrary from '../components/FactorLibrary';
import StrategyConfigManager from '../components/StrategyConfigManager';
import WeightConfigPanel from '../components/WeightConfigPanel';
import FactorAnalysisPanel from '../components/FactorAnalysisPanel';
import SelectionWizard from '../components/quantitative/SelectionWizard';
import SelectedFactorsOverview from '../components/quantitative/SelectedFactorsOverview';
import StrategyResultModal from '../components/quantitative/StrategyResultModal';
import MessageAlert from '../components/dashboard/MessageAlert';

// API导入
import {
  factorApi,
  strategyConfigApi,
  strategyApi,
  weightApi,
  StrategyConfig,
  SelectedFactor,
  StrategyResult,
  WeightPreset
} from '../services/api';

const QuantitativeSelection: React.FC = () => {
  // 主要状态
  const [activeTab, setActiveTab] = useState<'factor-library' | 'strategy-config' | 'selection-wizard' | 'weight-config' | 'factor-analysis'>('factor-library');
  const [selectedFactors, setSelectedFactors] = useState<SelectedFactor[]>([]);
  const [currentStrategy, setCurrentStrategy] = useState<StrategyConfig | null>(null);
  const [strategyResults, setStrategyResults] = useState<StrategyResult[]>([]);
  const [weightPresets, setWeightPresets] = useState<WeightPreset[]>([]);

  // UI状态
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [showResultModal, setShowResultModal] = useState(false);

  // 表单状态
  const [executeForm, setExecuteForm] = useState({
    max_results: 50,
    filters: {
      exclude_st: true,
      exclude_new_stock: true,
      min_market_cap: 1000000,
      max_pe: 100,
      min_roe: 0
    }
  });

  // 消息状态
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info' | 'warning', text: string } | null>(null);

  // 加载初始数据
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const presets = await weightApi.getWeightPresets();
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
    const exists = selectedFactors.some(f => f.factor_id === factor.factor_id);
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
    const updatedFactors = selectedFactors.filter(f => f.factor_id !== factorId);
    
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
      factor.factor_id === factorId ? { ...factor, weight } : factor
    ));
  };

  // 切换因子启用状态
  const handleFactorToggle = (factorId: string) => {
    setSelectedFactors(selectedFactors.map(factor =>
      factor.factor_id === factorId ? { ...factor, is_enabled: !factor.is_enabled } : factor
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

  // 执行策略
  const handleExecuteStrategy = async (strategy?: StrategyConfig) => {
    try {
      setExecuting(true);

      const factors = strategy ? strategy.factors : selectedFactors;
      const maxResults = strategy ? strategy.max_results : executeForm.max_results;

      if (factors.length === 0) {
        showMessage('warning', '请先选择至少一个因子');
        return;
      }

      const results = await strategyApi.executeStrategy({
        factors: factors,
        filters: executeForm.filters,
        max_results: maxResults
      });

      setStrategyResults(results);
      setShowResultModal(true);
      
      // 如果使用的是策略，记录使用次数
      if (strategy) {
        await strategyConfigApi.recordStrategyUsage(strategy.id);
      }

      showMessage('success', `策略执行完成，找到 ${results.length} 只股票`);
    } catch (error) {
      console.error('执行策略失败:', error);
      showMessage('error', '策略执行失败，请检查网络连接或重试');
    } finally {
      setExecuting(false);
    }
  };

  // 选择策略
  const handleStrategySelect = (strategy: StrategyConfig) => {
    setCurrentStrategy(strategy);
    setSelectedFactors(strategy.factors);
    setActiveTab('selection-wizard');
    showMessage('info', `已加载策略: ${strategy.name}`);
  };

  // 快速执行策略
  const handleQuickExecuteStrategy = (strategy: StrategyConfig) => {
    setCurrentStrategy(strategy);
    setExecuteForm({
      ...executeForm,
      max_results: strategy.max_results
    });
    handleExecuteStrategy(strategy);
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
          <a
            className={`tab ${activeTab === 'strategy-config' ? 'tab-active' : ''}`}
            onClick={() => setActiveTab('strategy-config')}
          >
            <Cog6ToothIcon className="w-4 h-4 mr-2" />
            策略管理
          </a>
          <a
            className={`tab ${activeTab === 'selection-wizard' ? 'tab-active' : ''}`}
            onClick={() => setActiveTab('selection-wizard')}
          >
            <StarIcon className="w-4 h-4 mr-2" />
            选股向导
          </a>
          {selectedFactors.length > 0 && (
            <>
              <a
                className={`tab ${activeTab === 'weight-config' ? 'tab-active' : ''}`}
                onClick={() => setActiveTab('weight-config')}
              >
                <AdjustmentsHorizontalIcon className="w-4 h-4 mr-2" />
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

        {/* 快速操作 */}
        <div className="flex gap-2">
          {selectedFactors.length > 0 && (
            <button
              className={`btn btn-primary btn-sm ${executing ? 'loading' : ''}`}
              onClick={() => handleExecuteStrategy()}
              disabled={executing || selectedFactors.length === 0}
            >
              {executing ? (
                '执行中...'
              ) : (
                <>
                  <PlayIcon className="w-4 h-4" />
                  快速执行
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* 已选因子概览 */}
      <SelectedFactorsOverview
        selectedFactors={selectedFactors}
        currentStrategy={currentStrategy}
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

        {activeTab === 'strategy-config' && (
          <StrategyConfigManager
            onStrategySelect={handleStrategySelect}
            onExecuteStrategy={handleQuickExecuteStrategy}
          />
        )}

        {activeTab === 'selection-wizard' && (
          <SelectionWizard
            selectedFactors={selectedFactors}
            executeForm={executeForm}
            executing={executing}
            isWeightValid={isWeightValid}
            getTotalWeight={getTotalWeight}
            onExecuteStrategy={() => handleExecuteStrategy()}
            onNormalizeWeights={handleNormalizeWeights}
            onSetExecuteForm={setExecuteForm}
            onSetActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'weight-config' && (
          <WeightConfigPanel
            factors={selectedFactors}
            onFactorsChange={setSelectedFactors}
            onClose={() => setActiveTab('selection-wizard')}
          />
        )}

        {activeTab === 'factor-analysis' && (
          <FactorAnalysisPanel
            factors={selectedFactors}
          />
        )}
      </div>

      {/* 策略执行结果模态框 */}
      <StrategyResultModal
        visible={showResultModal}
        results={strategyResults}
        onClose={() => setShowResultModal(false)}
      />
    </div>
  );
};

export default QuantitativeSelection;