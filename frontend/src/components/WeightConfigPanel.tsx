import React, { useState, useEffect } from 'react';
import {
  AdjustmentsHorizontalIcon,
  ChartPieIcon,
  ArrowPathIcon,
  SparklesIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import {
  weightApi,
  SelectedFactor,
  WeightPreset,
  WeightOptimizationResult
} from '../services/api';

interface WeightConfigPanelProps {
  factors: SelectedFactor[];
  onFactorsChange: (factors: SelectedFactor[]) => void;
  onClose?: () => void;
}

const WeightConfigPanel: React.FC<WeightConfigPanelProps> = ({
  factors,
  onFactorsChange,
  onClose
}) => {
  const [weightPresets, setWeightPresets] = useState<WeightPreset[]>([]);
  const [loading, setLoading] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState<WeightOptimizationResult | null>(null);
  const [showOptimizationModal, setShowOptimizationModal] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);

  // 加载权重预设
  useEffect(() => {
    loadWeightPresets();
    validateWeights();
  }, []);

  useEffect(() => {
    validateWeights();
  }, [factors]);

  const loadWeightPresets = async () => {
    try {
      const presets = await weightApi.getWeightPresets();
      setWeightPresets(presets);
    } catch (error) {
      console.error('加载权重预设失败:', error);
    }
  };

  // 验证权重配置
  const validateWeights = async () => {
    try {
      const result = await weightApi.validateWeights(factors);
      setValidationResult(result);
    } catch (error) {
      console.error('验证权重失败:', error);
    }
  };

  // 应用权重预设
  const handleApplyPreset = async (presetId: string) => {
    try {
      setLoading(true);
      const result = await weightApi.applyWeightPreset(factors, presetId);
      onFactorsChange(result.factors);
    } catch (error) {
      console.error('应用权重预设失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 标准化权重
  const handleNormalizeWeights = async () => {
    try {
      setLoading(true);
      const result = await weightApi.normalizeWeights(factors);
      onFactorsChange(result.factors);
    } catch (error) {
      console.error('标准化权重失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 优化权重
  const handleOptimizeWeights = async (method: string = 'correlation_adjusted') => {
    try {
      setLoading(true);
      const result = await weightApi.optimizeWeights(factors, method);
      setOptimizationResult(result);
      setShowOptimizationModal(true);
    } catch (error) {
      console.error('优化权重失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 应用优化结果
  const handleApplyOptimization = () => {
    if (optimizationResult) {
      onFactorsChange(optimizationResult.optimized_factors);
      setShowOptimizationModal(false);
    }
  };

  // 更新因子权重
  const handleFactorWeightChange = (factorId: string, weight: number) => {
    const updatedFactors = factors.map(factor =>
      factor.factor_id === factorId ? { ...factor, weight: Math.max(0, Math.min(1, weight)) } : factor
    );
    onFactorsChange(updatedFactors);
  };

  // 切换因子启用状态
  const handleFactorToggle = (factorId: string) => {
    const updatedFactors = factors.map(factor =>
      factor.factor_id === factorId ? { ...factor, is_enabled: !factor.is_enabled } : factor
    );
    onFactorsChange(updatedFactors);
  };

  // 等权重分配
  const handleEqualWeight = () => {
    const enabledFactors = factors.filter(f => f.is_enabled);
    const equalWeight = enabledFactors.length > 0 ? 1.0 / enabledFactors.length : 0;
    
    const updatedFactors = factors.map(factor => ({
      ...factor,
      weight: factor.is_enabled ? equalWeight : 0
    }));
    
    onFactorsChange(updatedFactors);
  };

  // 计算总权重
  const getTotalWeight = () => {
    return factors
      .filter(f => f.is_enabled)
      .reduce((sum, factor) => sum + factor.weight, 0);
  };

  // 检查权重是否有效
  const isWeightValid = () => {
    const total = getTotalWeight();
    return Math.abs(total - 1.0) < 0.01;
  };

  // 获取权重状态
  const getWeightStatus = () => {
    const total = getTotalWeight();
    if (Math.abs(total - 1.0) < 0.01) return 'success';
    if (total > 1.1) return 'error';
    if (total < 0.9) return 'warning';
    return 'info';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-success';
      case 'error': return 'text-error';
      case 'warning': return 'text-warning';
      default: return 'text-info';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircleIcon className="w-5 h-5" />;
      case 'error': case 'warning': return <ExclamationTriangleIcon className="w-5 h-5" />;
      default: return <InformationCircleIcon className="w-5 h-5" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* 权重状态概览 */}
      <div className="card bg-base-100 shadow-lg">
        <div className="card-body p-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2">
              <ChartPieIcon className="w-5 h-5" />
              权重配置状态
            </h3>
            <div className={`flex items-center gap-2 ${getStatusColor(getWeightStatus())}`}>
              {getStatusIcon(getWeightStatus())}
              <span className="font-medium">
                总权重: {(getTotalWeight() * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          {/* 权重分布可视化 */}
          <div className="mt-4">
            <div className="flex h-4 bg-base-200 rounded-full overflow-hidden">
              {factors
                .filter(f => f.is_enabled && f.weight > 0)
                .map((factor, index) => (
                  <div
                    key={factor.factor_id}
                    className={`h-full ${
                      index % 4 === 0 ? 'bg-primary' :
                      index % 4 === 1 ? 'bg-secondary' :
                      index % 4 === 2 ? 'bg-accent' : 'bg-info'
                    }`}
                    style={{ width: `${factor.weight * 100}%` }}
                    title={`${factor.factor_name}: ${(factor.weight * 100).toFixed(1)}%`}
                  />
                ))}
            </div>
          </div>

          {/* 验证结果 */}
          {validationResult && (
            <div className="mt-4">
              {validationResult.errors && validationResult.errors.length > 0 && (
                <div className="alert alert-error alert-sm">
                  <ExclamationTriangleIcon className="w-4 h-4" />
                  <div>
                    <div className="font-semibold">权重配置错误</div>
                    <div className="text-sm">
                      {validationResult.errors.join('; ')}
                    </div>
                  </div>
                </div>
              )}

              {validationResult.warnings && validationResult.warnings.length > 0 && (
                <div className="alert alert-warning alert-sm mt-2">
                  <InformationCircleIcon className="w-4 h-4" />
                  <div>
                    <div className="font-semibold">权重配置警告</div>
                    <div className="text-sm">
                      {validationResult.warnings.join('; ')}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 快速权重预设 */}
      <div className="card bg-base-100 shadow-lg">
        <div className="card-body p-4">
          <h3 className="font-semibold mb-3">快速权重预设</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
            {weightPresets.map((preset) => (
              <button
                key={preset.id}
                className="btn btn-outline btn-sm"
                onClick={() => handleApplyPreset(preset.id)}
                disabled={loading}
              >
                {preset.name}
              </button>
            ))}
            <button
              className="btn btn-outline btn-sm"
              onClick={handleEqualWeight}
              disabled={loading}
            >
              等权重分配
            </button>
          </div>
        </div>
      </div>

      {/* 详细权重配置 */}
      <div className="card bg-base-100 shadow-lg">
        <div className="card-body p-4">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold">详细权重配置</h3>
            <div className="flex gap-2">
              <button
                className="btn btn-outline btn-sm"
                onClick={handleNormalizeWeights}
                disabled={loading}
              >
                <ArrowPathIcon className="w-4 h-4" />
                标准化
              </button>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => handleOptimizeWeights()}
                disabled={loading}
              >
                <SparklesIcon className="w-4 h-4" />
                智能优化
              </button>
            </div>
          </div>

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {factors.map((factor, index) => (
              <div
                key={`${factor.factor_id}-${index}`}
                className={`p-4 border rounded-lg transition-all ${
                  factor.is_enabled ? 'border-primary bg-primary/5' : 'border-base-300 bg-base-200'
                }`}
              >
                {/* 因子标题和开关 */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      className="checkbox checkbox-primary"
                      checked={factor.is_enabled}
                      onChange={() => handleFactorToggle(factor.factor_id)}
                    />
                    <div>
                      <div className="font-medium">{factor.factor_name}</div>
                      <div className="text-sm text-base-content/60">
                        {factor.factor_id}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">
                      {(factor.weight * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-base-content/60">
                      权重
                    </div>
                  </div>
                </div>

                {/* 权重滑块 */}
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.005"
                    value={factor.weight}
                    onChange={(e) => handleFactorWeightChange(factor.factor_id, parseFloat(e.target.value))}
                    className="range range-primary flex-1"
                    disabled={!factor.is_enabled}
                  />
                  <input
                    type="number"
                    className="input input-bordered input-sm w-20"
                    value={(factor.weight * 100).toFixed(1)}
                    onChange={(e) => handleFactorWeightChange(
                      factor.factor_id,
                      parseFloat(e.target.value) / 100 || 0
                    )}
                    step="0.1"
                    min="0"
                    max="100"
                    disabled={!factor.is_enabled}
                  />
                  <span className="text-sm">%</span>
                </div>

                {/* 因子参数信息 */}
                {factor.parameters && Object.keys(factor.parameters).length > 0 && (
                  <div className="mt-2 text-xs text-base-content/60">
                    参数: {Object.entries(factor.parameters)
                      .filter(([, value]) => value !== undefined && value !== null)
                      .map(([key, value]) => `${key}=${value}`)
                      .join(', ')
                    }
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* 权重操作建议 */}
          {!isWeightValid() && (
            <div className="mt-4 p-3 bg-warning/10 border border-warning/20 rounded-lg">
              <div className="flex items-center gap-2 text-warning">
                <ExclamationTriangleIcon className="w-4 h-4" />
                <span className="font-medium">权重配置建议</span>
              </div>
              <div className="mt-2 text-sm">
                当前总权重为 {(getTotalWeight() * 100).toFixed(1)}%，建议调整为100%以获得最佳选股效果。
              </div>
              <div className="mt-2 flex gap-2">
                <button
                  className="btn btn-warning btn-xs"
                  onClick={handleNormalizeWeights}
                  disabled={loading}
                >
                  自动标准化
                </button>
                <button
                  className="btn btn-outline btn-xs"
                  onClick={() => handleOptimizeWeights()}
                  disabled={loading}
                >
                  智能优化
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 关闭按钮 */}
      {onClose && (
        <div className="flex justify-center">
          <button className="btn btn-primary" onClick={onClose}>
            完成配置
          </button>
        </div>
      )}

      {/* 优化结果模态框 */}
      {showOptimizationModal && optimizationResult && (
        <div className="modal modal-open">
          <div className="modal-box w-11/12 max-w-4xl">
            <h3 className="font-bold text-lg mb-4">权重优化结果</h3>

            <div className="space-y-4">
              {/* 优化方法和性能指标 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">优化方法</span>
                  </label>
                  <div className="badge badge-primary">
                    {optimizationResult.optimization_method}
                  </div>
                </div>
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">性能提升</span>
                  </label>
                  <div className="text-sm">
                    {Object.entries(optimizationResult.performance_metrics).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span>{key}:</span>
                        <span className="font-medium">{typeof value === 'number' ? value.toFixed(3) : value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* 权重对比 */}
              <div>
                <label className="label">
                  <span className="label-text font-semibold">权重对比</span>
                </label>
                <div className="overflow-x-auto">
                  <table className="table table-sm">
                    <thead>
                      <tr>
                        <th>因子</th>
                        <th>原权重</th>
                        <th>优化权重</th>
                        <th>变化</th>
                      </tr>
                    </thead>
                    <tbody>
                      {optimizationResult.optimized_factors.map((optimizedFactor, index) => {
                        const originalFactor = factors.find(f => f.factor_id === optimizedFactor.factor_id);
                        const change = optimizedFactor.weight - (originalFactor?.weight || 0);
                        return (
                          <tr key={optimizedFactor.factor_id}>
                            <td>{optimizedFactor.factor_name}</td>
                            <td>{((originalFactor?.weight || 0) * 100).toFixed(1)}%</td>
                            <td>{(optimizedFactor.weight * 100).toFixed(1)}%</td>
                            <td>
                              <span className={`font-medium ${
                                change > 0 ? 'text-success' : change < 0 ? 'text-error' : 'text-base-content'
                              }`}>
                                {change > 0 ? '+' : ''}{(change * 100).toFixed(1)}%
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 优化建议 */}
              {optimizationResult.recommendations && optimizationResult.recommendations.length > 0 && (
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">优化建议</span>
                  </label>
                  <div className="space-y-2">
                    {optimizationResult.recommendations.map((recommendation, index) => (
                      <div key={index} className="alert alert-info alert-sm">
                        <InformationCircleIcon className="w-4 h-4" />
                        <span className="text-sm">{recommendation}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="modal-action">
              <button
                className="btn"
                onClick={() => setShowOptimizationModal(false)}
              >
                取消
              </button>
              <button
                className="btn btn-primary"
                onClick={handleApplyOptimization}
              >
                应用优化结果
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WeightConfigPanel;