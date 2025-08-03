import React, { useState } from 'react';
import {
  Cog6ToothIcon,
  SparklesIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import { factorApi, Factor } from '../services/api';

interface FactorNormalizationToolProps {
  factors: Factor[];
  onFactorsUpdated: (factors: Factor[]) => void;
}

interface NormalizationTemplate {
  id: string;
  name: string;
  description: string;
  method: string;
  code: string;
  color: string;
}

const NORMALIZATION_TEMPLATES: NormalizationTemplate[] = [
  {
    id: 'z_score',
    name: 'Z-Score标准化',
    description: '将因子值转换为标准正态分布，均值为0，标准差为1',
    method: 'z_score',
    code: `def normalize(data):
    """
    Z-Score标准化
    
    参数:
        data: pandas.DataFrame - 包含股票历史数据的DataFrame
        
    可用字段:
        - 因子原始值 (factor_value)
        
    返回:
        pandas.Series - 标准化后的因子值
    """
    import pandas as pd
    import numpy as np
    
    # 获取因子原始值
    factor_value = data['factor_value']
    
    # Z-Score标准化
    mean_val = factor_value.mean()
    std_val = factor_value.std()
    
    if std_val == 0:
        return pd.Series(0, index=factor_value.index)
    
    normalized_result = (factor_value - mean_val) / std_val
    
    # 检查数据有效性
    if pd.isna(normalized_result).any():
        return pd.Series(np.nan, index=factor_value.index)
    
    return normalized_result`,
    color: 'badge-primary',
  },
];

const FactorNormalizationTool: React.FC<FactorNormalizationToolProps> = ({
  factors,
  onFactorsUpdated,
}) => {

  const [selectedFactors, setSelectedFactors] = useState<string[]>([]);
  const [isApplying, setIsApplying] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>('');



  const handleFactorSelection = (factorId: string, checked: boolean) => {
    if (checked) {
      setSelectedFactors(prev => [...prev, factorId]);
    } else {
      setSelectedFactors(prev => prev.filter(id => id !== factorId));
    }
  };

  const handleSelectAll = () => {
    setSelectedFactors(factors.map(f => f.id));
  };

  const handleDeselectAll = () => {
    setSelectedFactors([]);
  };

  const handleApplyNormalization = async () => {
    if (selectedFactors.length === 0) {
      setErrorMessage('请选择至少一个因子');
      return;
    }

    const template = NORMALIZATION_TEMPLATES.find(t => t.id === 'z_score');
    if (!template) {
      setErrorMessage('标准化模板不可用');
      return;
    }

    try {
      setIsApplying(true);
      setErrorMessage('');

      const updatedFactors: Factor[] = [];
      
      for (const factorId of selectedFactors) {
        const factor = factors.find(f => f.id === factorId);
        if (factor) {
          const updatedFactor = await factorApi.updateFactor(factorId, {
            normalization_code: template.code,
          });
          updatedFactors.push(updatedFactor);
        }
      }

      onFactorsUpdated(updatedFactors);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 2000);
      setSelectedFactors([]);
    } catch (error) {
      console.error('应用标准化失败:', error);
      setErrorMessage('应用标准化失败，请重试');
    } finally {
      setIsApplying(false);
    }
  };

  const getFactorsWithoutNormalization = () => {
    return factors.filter(factor => !factor.normalization_code);
  };

  const factorsWithoutNormalization = getFactorsWithoutNormalization();

  return (
    <div className="card bg-base-100 border border-base-300 shadow-sm">
      <div className="card-body">
        <div className="flex items-center gap-3 mb-4">
          <Cog6ToothIcon className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-semibold">批量标准化配置</h3>
        </div>

        {/* 错误提示 */}
        {errorMessage && (
          <div className="alert alert-error mb-4">
            <ExclamationTriangleIcon className="w-5 h-5" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* 成功提示 */}
        {showSuccess && (
          <div className="alert alert-success mb-4">
            <CheckCircleIcon className="w-5 h-5" />
            <span>标准化配置已成功应用到 {selectedFactors.length} 个因子</span>
          </div>
        )}

        <div className="space-y-6">
          {/* 标准化方法说明 */}
          <div className="bg-base-200 rounded-lg p-4">
            <div className="flex items-center gap-3 mb-3">
              <span className="badge badge-primary">Z-Score标准化</span>
              <h4 className="font-semibold">标准化方法</h4>
            </div>
            <p className="text-base-content/70">
              将因子值转换为标准正态分布，均值为0，标准差为1。这是最常用的标准化方法，适用于大多数数值型因子。
            </p>
          </div>

          {/* 因子选择 */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold">选择因子</h4>
              <div className="flex gap-2">
                <button
                  onClick={handleSelectAll}
                  className="btn btn-xs btn-outline"
                >
                  全选
                </button>
                <button
                  onClick={handleDeselectAll}
                  className="btn btn-xs btn-outline"
                >
                  取消全选
                </button>
              </div>
            </div>

            {factorsWithoutNormalization.length === 0 ? (
              <div className="text-center py-8 text-base-content/60">
                <InformationCircleIcon className="w-12 h-12 mx-auto mb-2" />
                <p>所有因子都已配置标准化方案</p>
              </div>
            ) : (
              <div className="max-h-64 overflow-y-auto space-y-2">
                {factorsWithoutNormalization.map((factor) => (
                  <label key={factor.id} className="flex items-center gap-3 p-2 rounded hover:bg-base-200">
                    <input
                      type="checkbox"
                      className="checkbox checkbox-sm"
                      checked={selectedFactors.includes(factor.id)}
                      onChange={(e) => handleFactorSelection(factor.id, e.target.checked)}
                    />
                    <div className="flex-1">
                      <div className="font-medium text-sm">{factor.display_name}</div>
                      <div className="text-xs text-base-content/60">{factor.id}</div>
                    </div>
                  </label>
                ))}
              </div>
            )}

            <div className="mt-4 text-sm text-base-content/60">
              已选择 {selectedFactors.length} 个因子
            </div>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-base-300">
          <button
            onClick={handleApplyNormalization}
            disabled={isApplying || selectedFactors.length === 0}
            className="btn btn-primary"
          >
            {isApplying ? (
              <span className="loading loading-spinner loading-sm"></span>
            ) : (
              <>
                <SparklesIcon className="w-4 h-4" />
                应用标准化 ({selectedFactors.length})
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FactorNormalizationTool; 