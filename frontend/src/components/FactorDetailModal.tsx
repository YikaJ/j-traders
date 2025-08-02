import React from 'react';
import Editor from '@monaco-editor/react';
import { Factor } from '../services/api';

interface FactorDetailModalProps {
  factor: Factor;
  isOpen: boolean;
  onClose: () => void;
  onAction: (action: string, factor: Factor) => void;
  mode: 'selection' | 'browse';
  isSelected: boolean;
}

const FactorDetailModal: React.FC<FactorDetailModalProps> = ({
  factor,
  isOpen,
  onClose,
  onAction,
  mode,
  isSelected
}) => {
  if (!isOpen) return null;

  // 获取分类显示名称
  const getCategoryDisplayName = (category: string): string => {
    const categoryMap: { [key: string]: string } = {
      'trend': '趋势类',
      'momentum': '动量类', 
      'volatility': '波动率类',
      'value': '价值类',
      'volume': '成交量类',
      'alpha101': 'Alpha101基础因子',
      'alpha101_extended': 'Alpha101扩展因子',
      'alpha101_more_factors': 'Alpha101增强因子',
      'alpha101_phase2': 'Alpha101进阶因子',
      'alpha101_phase3': 'Alpha101高级因子',
      'alpha101_phase4': 'Alpha101专家因子',
      'parametric': '参数化因子',
      'custom': '自定义因子',
      'test': '测试分类'
    };
    return categoryMap[category] || category;
  };

  // 获取因子代码（优先使用formula字段，如果没有则使用code字段）
  const getFactorCode = () => {
    return factor.formula || factor.code || '暂无代码';
  };

  return (
    <div className="modal modal-open">
      <div className="modal-box w-11/12 max-w-4xl">
        <h3 className="font-bold text-lg mb-4">
          因子详情 - {factor.display_name}
        </h3>

        <div className="space-y-4">
          {/* 基本信息 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">
                <span className="label-text font-semibold">因子ID</span>
              </label>
              <div className="text-sm">{factor.factor_id}</div>
            </div>
            <div>
              <label className="label">
                <span className="label-text font-semibold">分类</span>
              </label>
              <div className="badge badge-info">
                {getCategoryDisplayName(factor.category)}
              </div>
            </div>
          </div>

          {/* 描述 */}
          <div>
            <label className="label">
              <span className="label-text font-semibold">描述</span>
            </label>
            <div className="text-sm bg-base-200 p-3 rounded">
              {factor.description}
            </div>
          </div>

          {/* 因子代码 - 使用Monaco Editor */}
          <div>
            <label className="label">
              <span className="label-text font-semibold">因子代码</span>
            </label>
            <div className="border border-base-300 rounded-lg overflow-hidden">
              <Editor
                height="300px"
                defaultLanguage="python"
                value={getFactorCode()}
                options={{
                  readOnly: true,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  fontSize: 14,
                  lineNumbers: 'on',
                  roundedSelection: false,
                  scrollbar: {
                    vertical: 'visible',
                    horizontal: 'visible'
                  },
                  theme: 'vs-dark'
                }}
                theme="vs-dark"
              />
            </div>
          </div>

          {/* 默认参数 */}
          {factor.default_parameters && Object.keys(factor.default_parameters).length > 0 && (
            <div>
              <label className="label">
                <span className="label-text font-semibold">默认参数</span>
              </label>
              <div className="overflow-x-auto">
                <table className="table table-sm">
                  <thead>
                    <tr>
                      <th>参数名</th>
                      <th>默认值</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(factor.default_parameters).map(([key, value]) => (
                      <tr key={key}>
                        <td className="font-mono text-xs">{key}</td>
                        <td>{String(value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Alpha101特殊说明 */}
          {(factor.category === 'alpha101' || factor.category === 'alpha101_extended' || factor.category === 'alpha101_more_factors' || factor.category === 'alpha101_phase2' || factor.category === 'alpha101_phase3' || factor.category === 'alpha101_phase4') && (
            <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg border border-amber-200 dark:border-amber-800">
              <h4 className="font-semibold mb-2 text-amber-800 dark:text-amber-200">
                🏆 Alpha101因子说明
              </h4>
              <p className="text-sm text-amber-700 dark:text-amber-300">
                这是基于WorldQuant 101 Formulaic Alphas论文的成熟量化因子，
                在实际交易中具有良好的历史表现。该因子主要捕捉市场特征。
              </p>
            </div>
          )}
        </div>

        <div className="modal-action">
          <button
            className="btn"
            onClick={onClose}
          >
            关闭
          </button>
          {mode === 'selection' && !isSelected && (
            <button
              className="btn btn-primary"
              onClick={() => {
                onClose();
                onAction('select', factor);
              }}
            >
              添加到策略
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default FactorDetailModal; 