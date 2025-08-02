import React from 'react';
import Editor from '@monaco-editor/react';
import { Factor } from '../services/api';

interface FactorFormulaModalProps {
  factor: Factor;
  isOpen: boolean;
  onClose: () => void;
  onAction: (action: string, factor: Factor) => void;
  mode: 'selection' | 'browse';
  isSelected: boolean;
}

const FactorFormulaModal: React.FC<FactorFormulaModalProps> = ({
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
      <div className="modal-box w-11/12 max-w-5xl">
        <h3 className="font-bold text-lg mb-4">
          {factor.display_name} - 因子代码
        </h3>

        <div className="space-y-4">
          {/* 基本信息 */}
          <div className="bg-base-200 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">基本信息</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">因子ID：</span>
                <code className="bg-base-300 px-2 py-1 rounded">{factor.factor_id}</code>
              </div>
              <div>
                <span className="font-medium">分类：</span>
                <span className={`badge badge-sm ml-2 ${
                  factor.category === 'trend' ? 'badge-info' :
                  factor.category === 'momentum' ? 'badge-warning' :
                  factor.category === 'volume' ? 'badge-success' :
                  factor.category === 'alpha101' ? 'badge-secondary' :
                  'badge-neutral'
                }`}>
                  {getCategoryDisplayName(factor.category)}
                </span>
              </div>
              <div className="md:col-span-2">
                <span className="font-medium">描述：</span>
                <p className="mt-1 text-base-content/80">{factor.description}</p>
              </div>
            </div>
          </div>

          {/* 因子代码 - 使用Monaco Editor */}
          <div className="bg-base-200 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">因子代码</h4>
            <div className="border border-base-300 rounded-lg overflow-hidden">
              <Editor
                height="400px"
                defaultLanguage="python"
                value={getFactorCode()}
                options={{
                  readOnly: true,
                  minimap: { enabled: true },
                  scrollBeyondLastLine: false,
                  fontSize: 14,
                  lineNumbers: 'on',
                  roundedSelection: false,
                  scrollbar: {
                    vertical: 'visible',
                    horizontal: 'visible'
                  },
                  theme: 'vs-dark',
                  wordWrap: 'on',
                  folding: true,
                  foldingStrategy: 'indentation'
                }}
                theme="vs-dark"
              />
            </div>
          </div>

          {/* 输入字段 */}
          <div className="bg-base-200 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">输入字段</h4>
            <div className="flex flex-wrap gap-2">
              {factor.input_fields?.map((field: string, index: number) => (
                <span key={index} className="badge badge-outline">
                  {field}
                </span>
              )) || <span className="text-base-content/60">无特定要求</span>}
            </div>
          </div>

          {/* 参数配置 */}
          {factor.default_parameters && Object.keys(factor.default_parameters).length > 0 && (
            <div className="bg-base-200 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">可配置参数</h4>
              <div className="space-y-2">
                {Object.entries(factor.default_parameters).map(([key, param]: [string, any]) => (
                  <div key={key} className="flex justify-between items-center text-sm">
                    <div>
                      <span className="font-medium">{key}：</span>
                      <span className="text-base-content/70 ml-1">
                        {param?.description || '无描述'}
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <span className="badge badge-ghost badge-sm">
                        类型: {param?.type || 'unknown'}
                      </span>
                      <span className="badge badge-ghost badge-sm">
                        默认: {param?.default || 'N/A'}
                      </span>
                      {param?.minimum !== undefined && param?.maximum !== undefined && (
                        <span className="badge badge-ghost badge-sm">
                          范围: {param?.minimum}-{param?.maximum}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
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

export default FactorFormulaModal; 