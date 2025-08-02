import React, { useState, useEffect } from 'react';
import {
  PlusIcon,
  PlayIcon,
  AdjustmentsHorizontalIcon,
  ChartBarIcon,
  ListBulletIcon,
  Cog6ToothIcon,
  StarIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';

// 组件导入
import BuiltinFactorLibrary from '../components/BuiltinFactorLibrary';
import StrategyConfigManager from '../components/StrategyConfigManager';
import WeightConfigPanel from '../components/WeightConfigPanel';
import FactorAnalysisPanel from '../components/FactorAnalysisPanel';

// API导入
import {
  builtinFactorApi,
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
    showMessage('success', `已添加因子: ${factor.factor_name}`);
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
      setSelectedFactors(result.factors);
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
      .reduce((sum, factor) => sum + factor.weight, 0);
  };

  // 检查权重是否有效
  const isWeightValid = () => {
    const total = getTotalWeight();
    return Math.abs(total - 1.0) < 0.01; // 1% 误差范围
  };

  return (
    <div className="space-y-6">
      {/* 消息提示 */}
      {message && (
        <div className={`alert ${
          message.type === 'success' ? 'alert-success' :
          message.type === 'error' ? 'alert-error' :
          message.type === 'warning' ? 'alert-warning' :
          'alert-info'
        } shadow-lg`}>
          <div>
            <span>{message.text}</span>
          </div>
        </div>
      )}

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
      {selectedFactors.length > 0 && (
        <div className="card bg-base-100 shadow-lg">
          <div className="card-body p-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-semibold">
                已选择因子 ({selectedFactors.length})
                {currentStrategy && (
                  <span className="text-sm text-base-content/60 ml-2">
                    来自策略: {currentStrategy.name}
                  </span>
                )}
              </h3>
              <div className="flex items-center gap-2">
                <span className={`text-sm ${isWeightValid() ? 'text-success' : 'text-warning'}`}>
                  总权重: {(getTotalWeight() * 100).toFixed(1)}%
                </span>
                {!isWeightValid() && (
                  <ExclamationTriangleIcon className="w-4 h-4 text-warning" />
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-3">
              {selectedFactors.map((factor, index) => (
                <div
                  key={`${factor.factor_id}-${index}`}
                  className={`p-3 border rounded-lg ${
                    factor.is_enabled ? 'border-primary bg-primary/5' : 'border-base-300 bg-base-200'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium text-sm truncate">{factor.factor_name}</h4>
                    <div className="flex gap-1">
                      <input
                        type="checkbox"
                        className="checkbox checkbox-sm"
                        checked={factor.is_enabled}
                        onChange={() => handleFactorToggle(factor.factor_id)}
                      />
                      <button
                        className="btn btn-ghost btn-xs"
                        onClick={() => handleRemoveFactor(factor.factor_id)}
                      >
                        ×
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs">权重:</span>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={factor.weight}
                      onChange={(e) => handleFactorWeightChange(factor.factor_id, parseFloat(e.target.value))}
                      className="range range-xs flex-1"
                      disabled={!factor.is_enabled}
                    />
                    <span className="text-xs w-12 text-right">
                      {(factor.weight * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {!isWeightValid() && (
              <div className="mt-3 flex gap-2">
                <button
                  className="btn btn-warning btn-sm"
                  onClick={handleNormalizeWeights}
                >
                  <ArrowPathIcon className="w-4 h-4" />
                  标准化权重
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 主要内容区域 */}
      <div className="min-h-[600px]">
        {activeTab === 'factor-library' && (
          <BuiltinFactorLibrary
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
          <div className="card bg-base-100 shadow-lg">
            <div className="card-body">
              <h2 className="card-title mb-4">选股向导</h2>
              
              {selectedFactors.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-base-content/60 mb-4">
                    请先从因子库中选择因子，或加载一个策略配置
                  </div>
                  <div className="flex gap-2 justify-center">
                    <button
                      className="btn btn-primary"
                      onClick={() => setActiveTab('factor-library')}
                    >
                      <ChartBarIcon className="w-5 h-5" />
                      浏览因子库
                    </button>
                    <button
                      className="btn btn-outline"
                      onClick={() => setActiveTab('strategy-config')}
                    >
                      <Cog6ToothIcon className="w-5 h-5" />
                      加载策略
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* 执行配置 */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div className="form-control">
                      <label className="label">
                        <span className="label-text">最大结果数</span>
                      </label>
                      <input
                        type="number"
                        className="input input-bordered"
                        value={executeForm.max_results}
                        onChange={(e) => setExecuteForm({
                          ...executeForm,
                          max_results: parseInt(e.target.value) || 50
                        })}
                        min="1"
                        max="500"
                      />
                    </div>

                    <div className="form-control">
                      <label className="label">
                        <span className="label-text">最小市值 (万元)</span>
                      </label>
                      <input
                        type="number"
                        className="input input-bordered"
                        value={executeForm.filters.min_market_cap / 10000}
                        onChange={(e) => setExecuteForm({
                          ...executeForm,
                          filters: {
                            ...executeForm.filters,
                            min_market_cap: (parseInt(e.target.value) || 100) * 10000
                          }
                        })}
                        placeholder="100"
                      />
                    </div>
                  </div>

                  {/* 过滤条件 */}
                  <div>
                    <label className="label">
                      <span className="label-text">过滤条件</span>
                    </label>
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                      <div className="form-control">
                        <label className="label cursor-pointer">
                          <span className="label-text">排除ST股</span>
                          <input
                            type="checkbox"
                            className="checkbox"
                            checked={executeForm.filters.exclude_st}
                            onChange={(e) => setExecuteForm({
                              ...executeForm,
                              filters: {
                                ...executeForm.filters,
                                exclude_st: e.target.checked
                              }
                            })}
                          />
                        </label>
                      </div>

                      <div className="form-control">
                        <label className="label cursor-pointer">
                          <span className="label-text">排除新股</span>
                          <input
                            type="checkbox"
                            className="checkbox"
                            checked={executeForm.filters.exclude_new_stock}
                            onChange={(e) => setExecuteForm({
                              ...executeForm,
                              filters: {
                                ...executeForm.filters,
                                exclude_new_stock: e.target.checked
                              }
                            })}
                          />
                        </label>
                      </div>

                      <div className="form-control">
                        <label className="label">
                          <span className="label-text">最大市盈率</span>
                        </label>
                        <input
                          type="number"
                          className="input input-bordered"
                          value={executeForm.filters.max_pe}
                          onChange={(e) => setExecuteForm({
                            ...executeForm,
                            filters: {
                              ...executeForm.filters,
                              max_pe: parseInt(e.target.value) || 100
                            }
                          })}
                          placeholder="100"
                        />
                      </div>
                    </div>
                  </div>

                  {/* 权重验证和建议 */}
                  {!isWeightValid() && (
                    <div className="alert alert-warning">
                      <ExclamationTriangleIcon className="w-5 h-5" />
                      <div>
                        <div className="font-semibold">权重配置需要调整</div>
                        <div className="text-sm">
                          当前总权重为 {(getTotalWeight() * 100).toFixed(1)}%，建议调整为100%以获得最佳结果。
                        </div>
                      </div>
                      <div>
                        <button
                          className="btn btn-warning btn-sm"
                          onClick={handleNormalizeWeights}
                        >
                          自动调整
                        </button>
                      </div>
                    </div>
                  )}

                  {/* 执行按钮 */}
                  <div className="flex gap-4 justify-center">
                    <button
                      className="btn btn-outline"
                      onClick={() => setActiveTab('weight-config')}
                    >
                      <AdjustmentsHorizontalIcon className="w-5 h-5" />
                      高级权重配置
                    </button>
                    <button
                      className="btn btn-outline"
                      onClick={() => setActiveTab('factor-analysis')}
                    >
                      <BeakerIcon className="w-5 h-5" />
                      因子分析
                    </button>
                    <button
                      className={`btn btn-primary btn-lg ${executing ? 'loading' : ''}`}
                      onClick={() => handleExecuteStrategy()}
                      disabled={executing || selectedFactors.length === 0}
                    >
                      {executing ? (
                        '执行中...'
                      ) : (
                        <>
                          <PlayIcon className="w-5 h-5" />
                          开始选股
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
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
      {showResultModal && (
        <div className="modal modal-open">
          <div className="modal-box w-11/12 max-w-6xl">
            <h3 className="font-bold text-lg mb-4">
              选股结果 ({strategyResults.length} 只股票)
            </h3>

            {strategyResults.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="table table-sm">
                  <thead>
                    <tr>
                      <th>排名</th>
                      <th>股票代码</th>
                      <th>股票名称</th>
                      <th>综合得分</th>
                      <th>当前价格</th>
                      <th>涨跌幅</th>
                      <th>行业</th>
                    </tr>
                  </thead>
                  <tbody>
                    {strategyResults.map((result, index) => (
                      <tr key={result.symbol} className={index < 10 ? 'bg-success/10' : ''}>
                        <td className="font-medium">#{index + 1}</td>
                        <td className="font-mono">{result.symbol}</td>
                        <td>{result.name}</td>
                        <td>
                          <div className="badge badge-primary">
                            {result.score.toFixed(2)}
                          </div>
                        </td>
                        <td>¥{result.price.toFixed(2)}</td>
                        <td>
                          <span className={`font-medium ${
                            result.changePercent >= 0 ? 'text-success' : 'text-error'
                          }`}>
                            {result.changePercent >= 0 ? '+' : ''}{result.changePercent.toFixed(2)}%
                          </span>
                        </td>
                        <td>{result.industry || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-base-content/60">
                  没有找到符合条件的股票
                </div>
              </div>
            )}

            <div className="modal-action">
              <button
                className="btn"
                onClick={() => setShowResultModal(false)}
              >
                关闭
              </button>
              {strategyResults.length > 0 && (
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    // 导出结果逻辑
                    const csv = strategyResults.map((result, index) => 
                      `${index + 1},${result.symbol},${result.name},${result.score.toFixed(2)},${result.price.toFixed(2)},${result.changePercent.toFixed(2)}%`
                    ).join('\n');
                    
                    const blob = new Blob([`排名,代码,名称,得分,价格,涨跌幅\n${csv}`], { type: 'text/csv' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `selection_result_${new Date().toISOString().split('T')[0]}.csv`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                >
                  导出结果
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuantitativeSelection;