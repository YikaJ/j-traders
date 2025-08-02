import React from 'react';
import {
  PlayIcon,
  AdjustmentsHorizontalIcon,
  BeakerIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { SelectedFactor } from '../../services/api';

interface SelectionWizardProps {
  selectedFactors: SelectedFactor[];
  executeForm: {
    max_results: number;
    filters: {
      exclude_st: boolean;
      exclude_new_stock: boolean;
      min_market_cap: number;
      max_pe: number;
      min_roe: number;
    };
  };
  executing: boolean;
  isWeightValid: () => boolean;
  getTotalWeight: () => number;
  onExecuteStrategy: () => void;
  onNormalizeWeights: () => void;
  onSetExecuteForm: (form: any) => void;
  onSetActiveTab: (tab: 'factor-library' | 'strategy-config' | 'selection-wizard' | 'weight-config' | 'factor-analysis') => void;
}

const SelectionWizard: React.FC<SelectionWizardProps> = ({
  selectedFactors,
  executeForm,
  executing,
  isWeightValid,
  getTotalWeight,
  onExecuteStrategy,
  onNormalizeWeights,
  onSetExecuteForm,
  onSetActiveTab
}) => {
  return (
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
                onClick={() => onSetActiveTab('factor-library')}
              >
                浏览因子库
              </button>
              <button
                className="btn btn-outline"
                onClick={() => onSetActiveTab('strategy-config')}
              >
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
                  onChange={(e) => onSetExecuteForm({
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
                  onChange={(e) => onSetExecuteForm({
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
                      onChange={(e) => onSetExecuteForm({
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
                      onChange={(e) => onSetExecuteForm({
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
                    onChange={(e) => onSetExecuteForm({
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
                    onClick={onNormalizeWeights}
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
                onClick={() => onSetActiveTab('weight-config')}
              >
                <AdjustmentsHorizontalIcon className="w-5 h-5" />
                高级权重配置
              </button>
              <button
                className="btn btn-outline"
                onClick={() => onSetActiveTab('factor-analysis')}
              >
                <BeakerIcon className="w-5 h-5" />
                因子分析
              </button>
              <button
                className={`btn btn-primary btn-lg ${executing ? 'loading' : ''}`}
                onClick={onExecuteStrategy}
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
  );
};

export default SelectionWizard; 