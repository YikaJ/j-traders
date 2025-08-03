import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import {
  XMarkIcon,
  SparklesIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import { factorApi, Factor } from '../services/api';

interface FactorNormalizationModalProps {
  isOpen: boolean;
  onClose: () => void;
  factor: Factor | null;
  onNormalizationUpdated: (factor: Factor) => void;
}

interface NormalizationMethod {
  value: string;
  label: string;
  description: string;
  codeTemplate: string;
}

const NORMALIZATION_METHODS: NormalizationMethod[] = [
  {
    value: 'z_score',
    label: 'Z-Score标准化',
    description: '将因子值转换为标准正态分布，均值为0，标准差为1',
    codeTemplate: `def normalize(data):
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
  },
];

const FactorNormalizationModal: React.FC<FactorNormalizationModalProps> = ({
  isOpen,
  onClose,
  factor,
  onNormalizationUpdated,
}) => {

  const [customCode, setCustomCode] = useState<string>('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [showSuccessAnimation, setShowSuccessAnimation] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  // 初始化：每次打开都预填充Z-Score模板
  useEffect(() => {
    if (factor && isOpen) {
      // 每次都预填充Z-Score模板
      const method = NORMALIZATION_METHODS.find(m => m.value === 'z_score');
      if (method) {
        setCustomCode(method.codeTemplate);
      }
    }
  }, [factor, isOpen]);

  const validateForm = (): string[] => {
    const errors: string[] = [];

    if (!customCode.trim()) {
      errors.push('标准化代码不能为空');
    }

    return errors;
  };



  const handleUpdateNormalization = async () => {
    const errors = validateForm();
    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }

    if (!factor) return;

    try {
      setIsUpdating(true);
      
      const updateData = {
        normalization_code: customCode,
      };

      const updatedFactor = await factorApi.updateFactor(factor.id, updateData);
      
      setShowSuccessAnimation(true);
      setTimeout(() => {
        setShowSuccessAnimation(false);
        onNormalizationUpdated(updatedFactor);
        onClose();
      }, 1500);
    } catch (error) {
      console.error('更新标准化配置失败:', error);
      setValidationErrors(['更新失败，请重试']);
    } finally {
      setIsUpdating(false);
    }
  };

  const handlePreview = async () => {
    if (!factor) return;

    try {
      setIsPreviewLoading(true);
      
      // 调用后端API来预览标准化效果
      const previewResult = await factorApi.previewNormalization(factor.id, {
        normalization_code: customCode,
      });
      
      setPreviewData(previewResult);
    } catch (error) {
      console.error('预览失败:', error);
      setValidationErrors(['预览失败，请检查标准化代码']);
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleReset = () => {
    // 重置为Z-Score模板
    const method = NORMALIZATION_METHODS.find(m => m.value === 'z_score');
    if (method) {
      setCustomCode(method.codeTemplate);
    }
    setValidationErrors([]);
  };

  if (!isOpen || !factor) return null;

  return (
    <dialog className="modal modal-open">
      <div className="modal-box max-w-6xl max-h-[90vh] bg-base-100 border border-base-300 shadow-2xl">
        {/* 成功动画覆盖层 */}
        {showSuccessAnimation && (
          <div className="absolute inset-0 bg-base-100/95 flex items-center justify-center z-50 rounded-lg">
            <div className="text-center">
              <CheckCircleIcon className="w-16 h-16 text-success mx-auto mb-4 animate-pulse" />
              <h3 className="text-xl font-bold text-success mb-2">
                更新成功！
              </h3>
              <p className="text-base-content/70">标准化配置已更新</p>
            </div>
          </div>
        )}

        {/* 头部 */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-base-300">
          <div className="flex items-center gap-3">
            <SparklesIcon className="w-6 h-6 text-primary" />
            <h3 className="text-xl font-bold text-base-content">因子标准化配置</h3>
            <div className="badge badge-primary">{factor.display_name}</div>
          </div>
          <button
            onClick={onClose}
            className="btn btn-ghost btn-sm btn-circle"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* 错误提示 */}
        {validationErrors.length > 0 && (
          <div className="alert alert-error mb-4">
            <ExclamationTriangleIcon className="w-5 h-5" />
            <div>
              <h4 className="font-bold">配置错误</h4>
              <ul className="text-sm">
                {validationErrors.map((error, index) => (
                  <li key={index}>• {error}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <div className="space-y-6">
          {/* 标准化方法说明 */}
          <div className="bg-base-200 rounded-lg p-4">
            <div className="flex items-center gap-3 mb-3">
              <span className="badge badge-primary">Z-Score标准化</span>
              <h4 className="text-lg font-semibold">标准化方法</h4>
            </div>
            <p className="text-base-content/70">
              将因子值转换为标准正态分布，均值为0，标准差为1。这是最常用的标准化方法，适用于大多数数值型因子。
            </p>
          </div>

          {/* 代码编辑器 */}
          <div>
            <h4 className="text-lg font-semibold mb-4">标准化代码</h4>
            <div className="border border-base-300 rounded-lg overflow-hidden">
              <Editor
                height="400px"
                language="python"
                value={customCode}
                onChange={(value) => setCustomCode(value || '')}
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  lineNumbers: 'on',
                  roundedSelection: false,
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                }}
                theme="vs-dark"
              />
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-3">
            <button
              onClick={handlePreview}
              disabled={isPreviewLoading}
              className="btn btn-outline btn-primary"
            >
              {isPreviewLoading ? (
                <span className="loading loading-spinner loading-sm"></span>
              ) : (
                '预览效果'
              )}
            </button>
            <button
              onClick={handleReset}
              className="btn btn-outline"
            >
              重置
            </button>
          </div>

          {/* 预览结果 */}
          {previewData && (
            <div>
              <h4 className="text-lg font-semibold mb-4">预览结果</h4>
              <div className="bg-base-200 rounded-lg p-4">
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <h6 className="font-medium text-sm text-base-content/70">原始值</h6>
                    <div className="text-sm font-mono">
                      {previewData.original_values.map((val: number, index: number) => (
                        <span key={index} className="mr-2">{val.toFixed(2)}</span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h6 className="font-medium text-sm text-base-content/70">标准化值</h6>
                    <div className="text-sm font-mono">
                      {previewData.normalized_values.map((val: number, index: number) => (
                        <span key={index} className="mr-2">{val.toFixed(2)}</span>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="border-t border-base-300 pt-4">
                  <h6 className="font-medium text-sm text-base-content/70 mb-2">统计信息</h6>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>均值: {previewData.statistics.mean.toFixed(2)}</div>
                    <div>标准差: {previewData.statistics.std.toFixed(2)}</div>
                    <div>最小值: {previewData.statistics.min.toFixed(2)}</div>
                    <div>最大值: {previewData.statistics.max.toFixed(2)}</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 底部操作按钮 */}
        <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-base-300">
          <button
            onClick={onClose}
            className="btn btn-ghost"
          >
            取消
          </button>
          <button
            onClick={handleUpdateNormalization}
            disabled={isUpdating}
            className="btn btn-primary"
          >
            {isUpdating ? (
              <span className="loading loading-spinner loading-sm"></span>
            ) : (
              '保存配置'
            )}
          </button>
        </div>
      </div>
    </dialog>
  );
};

export default FactorNormalizationModal; 