import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import {
  XMarkIcon,
  SparklesIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { factorApi, CustomFactorCreateRequest, FactorTag } from '../services/api';
import TagInput, { Tag } from './common/TagInput';

interface FactorCreateModalImprovedProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

const FactorCreateModalImproved: React.FC<FactorCreateModalImprovedProps> = ({
  isOpen,
  onClose,
  onCreated,
}) => {
  const [createFactorForm, setCreateFactorForm] = useState({
    name: '',
    display_name: '',
    description: '',
    formula: '',
    normalization_code: '',
    input_fields: ['close'],
    default_parameters: {},
    calculation_method: 'formula',
  });
  const [selectedTags, setSelectedTags] = useState<FactorTag[]>([]);
  const [availableTags, setAvailableTags] = useState<FactorTag[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [showSuccessAnimation, setShowSuccessAnimation] = useState(false);
  const [isLoadingTags, setIsLoadingTags] = useState(false);

  // 类型转换函数：FactorTag -> Tag
  const convertFactorTagToTag = (factorTag: FactorTag): Tag => ({
    id: factorTag.id.toString(),
    name: factorTag.name,
    display_name: factorTag.display_name,
    color: factorTag.color,
  });

  // 类型转换函数：Tag -> FactorTag
  const convertTagToFactorTag = (tag: Tag): FactorTag => ({
    id: parseInt(tag.id),
    name: tag.name,
    display_name: tag.display_name,
    color: tag.color,
    is_active: true,
    usage_count: 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  });

  // 加载可用标签
  useEffect(() => {
    if (isOpen) {
      loadAvailableTags();
    }
  }, [isOpen]);

  const loadAvailableTags = async () => {
    try {
      setIsLoadingTags(true);
      const tags = await factorApi.getAllFactorTags(true); // 只获取启用的标签
      setAvailableTags(tags);
    } catch (error) {
      console.error('加载标签失败:', error);
    } finally {
      setIsLoadingTags(false);
    }
  };

  // 创建新标签
  const handleCreateTag = async (tagName: string): Promise<FactorTag | null> => {
    try {
      const newTag = await factorApi.createFactorTag({
        name: tagName.toLowerCase().replace(/\s+/g, '_'),
        display_name: tagName,
        description: `用户创建的标签: ${tagName}`,
        color: '#3B82F6', // 默认蓝色
      });
      
      // 更新可用标签列表
      setAvailableTags(prev => [...prev, newTag]);
      
      return newTag;
    } catch (error) {
      console.error('创建标签失败:', error);
      return null;
    }
  };



  // 验证表单
  const validateForm = (): string[] => {
    const errors: string[] = [];

    if (!createFactorForm.name.trim()) {
      errors.push('请填写因子名称');
    }

    if (!createFactorForm.display_name.trim()) {
      errors.push('请填写显示名称');
    }

    if (!createFactorForm.formula.trim()) {
      errors.push('请编写因子代码');
    }

    if (createFactorForm.input_fields.length === 0) {
      errors.push('请至少选择一个输入字段');
    }

    return errors;
  };

  // 保存新因子
  const handleSaveNewFactor = async () => {
    try {
      setIsCreating(true);
      setValidationErrors([]);

      // 验证表单
      const errors = validateForm();
      if (errors.length > 0) {
        setValidationErrors(errors);
        return;
      }

      // 准备创建请求数据
      const createRequest: CustomFactorCreateRequest = {
        name: createFactorForm.name,
        display_name: createFactorForm.display_name,
        description: createFactorForm.description,
        formula: createFactorForm.formula,

        normalization_code: createFactorForm.normalization_code,
        default_parameters: createFactorForm.default_parameters,
        calculation_method: createFactorForm.calculation_method,
        input_fields: createFactorForm.input_fields,
        tag_ids: selectedTags.map(tag => tag.id),
      };

      // 调用API创建因子
      await factorApi.createCustomFactor(createRequest);

      // 显示成功动画
      setShowSuccessAnimation(true);
      setTimeout(() => {
        setShowSuccessAnimation(false);
        handleResetForm();
        onCreated();
        onClose();
      }, 2000);

    } catch (error: any) {
      console.error('创建因子失败:', error);
      setValidationErrors([
        error.response?.data?.detail || error.message || '创建因子失败，请重试'
      ]);
    } finally {
      setIsCreating(false);
    }
  };

  // 重置表单
  const handleResetForm = () => {
    setCreateFactorForm({
      name: '',
      display_name: '',
      description: '',
      formula: '',

      normalization_code: '',
      input_fields: ['close'],
      default_parameters: {},
      calculation_method: 'formula',
    });
    setSelectedTags([]);
    setCurrentStep(1);
    setValidationErrors([]);
  };

  // 生成默认代码模板
  const generateDefaultCode = () => {
    const inputFields =
      createFactorForm.input_fields.length > 0
        ? createFactorForm.input_fields
        : ['close'];

    const dataAccess = inputFields
      .map((field) => `    ${field} = data['${field}']`)
      .join('\n');

    return `def calculate(data):
    """
    ${createFactorForm.description || '自定义因子计算函数'}
    
    参数:
        data: pandas.DataFrame - 包含股票历史数据的DataFrame
        
    可用字段:
${inputFields
  .map((field) => `        - ${field}: ${getFieldDescription(field)}`)
  .join('\n')}
    
    返回:
        float - 因子原始值，标准化在策略层面处理
    """
    import pandas as pd
    import numpy as np
    
    # 获取输入数据
${dataAccess}
    
    # 在这里编写你的因子计算逻辑
    # 示例：计算价格动量因子
    returns = data['close'].pct_change()
    
    # 计算过去10天的累积收益
    momentum = returns.rolling(window=10).sum()
    
    # 获取最新值
    latest_momentum = momentum.iloc[-1]
    
    # 检查数据有效性
    if pd.isna(latest_momentum):
        return 0.0
    
    # 返回原始值，标准化在策略层面处理
    return float(latest_momentum)`;
  };

  // 生成默认标准化代码模板
  const generateDefaultNormalizationCode = () => {
    return `def normalize(data):
    """
    自定义标准化逻辑
    
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
    
    # 在这里编写你的标准化逻辑
    # 示例：将因子值缩放到[0,1]区间
    normalized_result = (factor_value - factor_value.min()) / (factor_value.max() - factor_value.min())
    
    # 检查数据有效性
    if pd.isna(normalized_result).any():
        return pd.Series(np.nan, index=factor_value.index)
    
    return normalized_result`;
  };

  // 获取字段描述
  const getFieldDescription = (fieldName: string): string => {
    const descriptions: Record<string, string> = {
      open: '开盘价',
      high: '最高价',
      low: '最低价',
      close: '收盘价',
      volume: '成交量',
      amount: '成交额',
      pre_close: '前收盘价',
      change: '涨跌额',
      pct_change: '涨跌幅',
    };
    return descriptions[fieldName] || fieldName;
  };

  // 步骤指示器
  const StepIndicator = () => (
    <div className="flex items-center justify-center mb-6">
      <div className="flex items-center space-x-2">
        {[1, 2, 3, 4].map((step) => (
          <React.Fragment key={step}>
            <div
              className={`
              w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
              transition-all duration-300
              ${
                currentStep >= step
                  ? 'bg-primary text-primary-content'
                  : 'bg-base-300 text-base-content/60'
              }
            `}
            >
              {step}
            </div>
            {step < 4 && (
              <div
                className={`
                w-12 h-0.5 transition-all duration-300
                ${currentStep > step ? 'bg-primary' : 'bg-base-300'}
              `}
              />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );

  if (!isOpen) return null;

  return (
    <dialog className="modal modal-open">
      <div className="modal-box max-w-6xl max-h-[90vh] bg-base-100 border border-base-300 shadow-2xl">
        {/* 成功动画覆盖层 */}
        {showSuccessAnimation && (
          <div className="absolute inset-0 bg-base-100/95 flex items-center justify-center z-50 rounded-lg">
            <div className="text-center">
              <CheckCircleIcon className="w-16 h-16 text-success mx-auto mb-4 animate-pulse" />
              <h3 className="text-xl font-bold text-success mb-2">
                创建成功！
              </h3>
              <p className="text-base-content/70">因子已成功添加到因子库</p>
            </div>
          </div>
        )}

        {/* 头部 */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-base-300">
          <div className="flex items-center gap-3">
            <SparklesIcon className="w-6 h-6 text-primary" />
            <h3 className="text-xl font-bold text-base-content">创建新因子</h3>
          </div>
          <button
            onClick={() => {
              handleResetForm();
              onClose();
            }}
            className="btn btn-ghost btn-sm btn-circle"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* 步骤指示器 */}
        <StepIndicator />

        {/* 错误提示 */}
        {validationErrors.length > 0 && (
          <div className="alert alert-error mb-6">
            <ExclamationTriangleIcon className="w-5 h-5" />
            <div>
              <h4 className="font-medium">请修正以下问题:</h4>
              <ul className="list-disc list-inside mt-1">
                {validationErrors.map((error, index) => (
                  <li key={index} className="text-sm">
                    {error}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <div className="space-y-6">
          {/* 第一步：基本信息 */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <div className="text-center mb-6">
                <h4 className="text-lg font-semibold text-base-content mb-2">
                  基本信息
                </h4>
                <p className="text-base-content/70">
                  设置因子的基本标识和描述信息
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="form-control">
                  <label className="label">
                    <span className="label-text font-medium">因子名称 *</span>
                    <span className="label-text-alt text-xs">英文名称</span>
                  </label>
                  <input
                    type="text"
                    className="input input-bordered bg-base-100 focus:border-primary"
                    placeholder="例如: Custom Momentum Factor"
                    value={createFactorForm.name}
                    onChange={(e) =>
                      setCreateFactorForm({
                        ...createFactorForm,
                        name: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="form-control">
                  <label className="label">
                    <span className="label-text font-medium">显示名称 *</span>
                    <span className="label-text-alt text-xs">
                      界面显示的中文名称
                    </span>
                  </label>
                  <input
                    type="text"
                    className="input input-bordered bg-base-100 focus:border-primary"
                    placeholder="例如: 自定义动量因子"
                    value={createFactorForm.display_name}
                    onChange={(e) =>
                      setCreateFactorForm({
                        ...createFactorForm,
                        display_name: e.target.value,
                      })
                    }
                  />
                </div>


              </div>

              {/* 因子标签选择 */}
              <div className="form-control">
                <label className="label">
                  <span className="label-text font-medium">因子标签</span>
                  <span className="label-text-alt text-xs">
                    选择或创建标签来分类因子
                  </span>
                </label>
                {isLoadingTags ? (
                  <div className="flex items-center justify-center py-4">
                    <span className="loading loading-spinner loading-md"></span>
                    <span className="ml-2 text-base-content/70">加载标签中...</span>
                  </div>
                ) : (
                  <TagInput
                    tags={selectedTags.map(convertFactorTagToTag)}
                    availableTags={availableTags.map(convertFactorTagToTag)}
                    onTagsChange={(tags: Tag[]) => setSelectedTags(tags.map(convertTagToFactorTag))}
                    onCreateTag={async (tagName: string) => {
                      const result = await handleCreateTag(tagName);
                      return result ? convertFactorTagToTag(result) : null;
                    }}
                    placeholder="选择或创建标签..."
                    maxTags={5}
                  />
                )}
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text font-medium">因子描述</span>
                  <span className="label-text-alt text-xs">
                    详细说明因子的用途和计算逻辑
                  </span>
                </label>
                <textarea
                  className="textarea textarea-bordered bg-base-100 focus:border-primary h-24 resize-none"
                  placeholder="请描述因子的计算原理、应用场景和预期效果..."
                  value={createFactorForm.description}
                  onChange={(e) =>
                    setCreateFactorForm({
                      ...createFactorForm,
                      description: e.target.value,
                    })
                  }
                />
              </div>

              <div className="flex justify-end pt-4">
                <button
                  className="btn btn-primary"
                  onClick={() => setCurrentStep(2)}
                  disabled={
                    !createFactorForm.name ||
                    !createFactorForm.display_name
                  }
                >
                  下一步：编写代码
                </button>
              </div>
            </div>
          )}

          {/* 第二步：编写代码 */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <div className="text-center mb-6">
                <h4 className="text-lg font-semibold text-base-content mb-2">
                  编写因子代码
                </h4>
                <p className="text-base-content/70">实现因子的计算逻辑</p>
              </div>

              <div className="form-control">
                <div className="flex items-center justify-between mb-3">
                  <label className="label">
                    <span className="label-text font-medium">因子代码 *</span>
                  </label>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline btn-primary"
                    onClick={() =>
                      setCreateFactorForm({
                        ...createFactorForm,
                        formula: generateDefaultCode(),
                      })
                    }
                  >
                    <SparklesIcon className="w-4 h-4 mr-1" />
                    生成模板
                  </button>
                </div>

                <div className="border border-base-300 rounded-lg overflow-hidden">
                  <Editor
                    height="400px"
                    defaultLanguage="python"
                    value={createFactorForm.formula}
                    onChange={(value) =>
                      setCreateFactorForm({
                        ...createFactorForm,
                        formula: value || '',
                      })
                    }
                    options={{
                      readOnly: false,
                      minimap: { enabled: false },
                      scrollBeyondLastLine: false,
                      fontSize: 14,
                      lineNumbers: 'on',
                      wordWrap: 'on',
                      folding: true,
                      quickSuggestions: true,
                      autoIndent: 'full',
                      formatOnPaste: true,
                      formatOnType: true,
                    }}
                    theme="vs-dark"
                  />
                </div>
              </div>

              {/* 代码编写帮助 */}
              <div className="bg-info/10 border border-info/20 rounded-lg p-4">
                <h5 className="font-semibold text-info mb-3">💡 因子设计提示</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <h6 className="font-medium mb-2">设计原则:</h6>
                    <ul className="space-y-1 text-base-content/70">
                      <li>
                        <code>返回原始值</code> - 因子返回原始计算结果
                      </li>
                      <li>
                        <code>策略层面标准化</code> - 标准化在策略层面统一处理
                      </li>
                      <li>
                        <code>保持简洁</code> - 专注于因子逻辑，避免复杂处理
                      </li>
                      <li>
                        <code>易于复用</code> - 同一因子可用于不同标准化策略
                      </li>
                    </ul>
                  </div>
                  <div>
                    <h6 className="font-medium mb-2">多因子模型优势:</h6>
                    <ul className="space-y-1 text-base-content/70">
                      <li>• 策略层面统一管理标准化</li>
                      <li>• 支持动态调整标准化方法</li>
                      <li>• 便于因子组合和权重优化</li>
                      <li>• 提高因子复用性和灵活性</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="flex justify-between pt-4">
                <button
                  className="btn btn-outline"
                  onClick={() => setCurrentStep(1)}
                >
                  上一步
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => setCurrentStep(3)}
                  disabled={!createFactorForm.formula.trim()}
                >
                  下一步：标准化方案
                </button>
              </div>
            </div>
          )}

          {/* 第三步：标准化方案 */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <div className="text-center mb-6">
                <h4 className="text-lg font-semibold text-base-content mb-2">
                  标准化方案
                </h4>
                <p className="text-base-content/70">选择因子的标准化处理方法</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 标准化方法选择 */}
                <div className="space-y-4">
                  <div className="card bg-base-200 shadow-lg">
                    <div className="card-body">
                      <h5 className="card-title text-base mb-4">选择标准化方法</h5>
                      
                      <div className="space-y-3">
                        <button
                          type="button"
                          className="btn btn-outline btn-primary w-full justify-start"
                          onClick={() => {
                            const zscoreCode = `def normalize_factor(factor_values):
    """Z-Score 标准化"""
    import numpy as np
    
    if len(factor_values) == 0:
        return factor_values
    
    mean_val = np.mean(factor_values)
    std_val = np.std(factor_values)
    
    if std_val == 0:
        return factor_values - mean_val
    
    return (factor_values - mean_val) / std_val`;
                            setCreateFactorForm({
                              ...createFactorForm,
                              normalization_code: zscoreCode,
                            });
                          }}
                        >
                          <div className="w-3 h-3 bg-primary rounded-full mr-3"></div>
                          Z-Score 标准化
                          <span className="badge badge-primary badge-sm ml-auto">推荐</span>
                        </button>
                        
                        <button
                          type="button"
                          className="btn btn-outline w-full justify-start"
                          onClick={() => {
                            const minmaxCode = `def normalize_factor(factor_values):
    """Min-Max 标准化"""
    import numpy as np
    
    if len(factor_values) == 0:
        return factor_values
    
    min_val = np.min(factor_values)
    max_val = np.max(factor_values)
    
    if max_val == min_val:
        return factor_values - min_val
    
    return (factor_values - min_val) / (max_val - min_val)`;
                            setCreateFactorForm({
                              ...createFactorForm,
                              normalization_code: minmaxCode,
                            });
                          }}
                        >
                          <div className="w-3 h-3 bg-secondary rounded-full mr-3"></div>
                          Min-Max 标准化
                        </button>
                        
                        <button
                          type="button"
                          className="btn btn-outline w-full justify-start"
                          onClick={() => {
                            const rankCode = `def normalize_factor(factor_values):
    """Rank 标准化"""
    import numpy as np
    
    if len(factor_values) == 0:
        return factor_values
    
    # 计算排名并标准化到[0,1]区间
    ranks = np.argsort(np.argsort(factor_values))
    return ranks / (len(factor_values) - 1) if len(factor_values) > 1 else ranks`;
                            setCreateFactorForm({
                              ...createFactorForm,
                              normalization_code: rankCode,
                            });
                          }}
                        >
                          <div className="w-3 h-3 bg-accent rounded-full mr-3"></div>
                          Rank 标准化
                        </button>
                        
                        <button
                          type="button"
                          className="btn btn-outline w-full justify-start"
                          onClick={() => {
                            setCreateFactorForm({
                              ...createFactorForm,
                              normalization_code: generateDefaultNormalizationCode(),
                            });
                          }}
                        >
                          <div className="w-3 h-3 bg-neutral rounded-full mr-3"></div>
                          自定义模板
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 标准化代码编辑器 */}
                <div className="form-control lg:col-span-2">
                  <div className="flex items-center justify-between mb-3">
                    <label className="label">
                      <span className="label-text font-medium">标准化代码</span>
                      <span className="label-text-alt text-xs">点击左侧按钮选择模板，或直接编辑代码</span>
                    </label>
                    <button
                      type="button"
                      className="btn btn-sm btn-outline btn-primary"
                      onClick={() =>
                        setCreateFactorForm({
                          ...createFactorForm,
                          normalization_code: generateDefaultNormalizationCode(),
                        })
                      }
                    >
                      <SparklesIcon className="w-4 h-4 mr-1" />
                      重置模板
                    </button>
                  </div>

                  <div className="border border-base-300 rounded-lg overflow-hidden">
                    <Editor
                      height="400px"
                      defaultLanguage="python"
                      value={createFactorForm.normalization_code}
                      onChange={(value) =>
                        setCreateFactorForm({
                          ...createFactorForm,
                          normalization_code: value || '',
                        })
                      }
                      options={{
                        readOnly: false,
                        minimap: { enabled: false },
                        scrollBeyondLastLine: false,
                        fontSize: 14,
                        lineNumbers: 'on',
                        wordWrap: 'on',
                        folding: true,
                        quickSuggestions: true,
                        autoIndent: 'full',
                        formatOnPaste: true,
                        formatOnType: true,
                      }}
                      theme="vs-dark"
                    />
                  </div>
                </div>
              </div>

              {/* 标准化说明 */}
              <div className="bg-success/10 border border-success/20 rounded-lg p-4">
                <h5 className="font-semibold text-success mb-3">📊 标准化说明</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <h6 className="font-medium mb-2">标准化方法:</h6>
                    <ul className="space-y-1 text-base-content/70">
                      <li><code>Z-Score</code> - 均值为0，标准差为1的标准化</li>
                      <li><code>Min-Max</code> - 缩放到[0,1]区间</li>
                      <li><code>Rank</code> - 基于排序的标准化</li>
                      <li><code>Custom</code> - 自定义标准化逻辑</li>
                    </ul>
                  </div>
                  <div>
                    <h6 className="font-medium mb-2">使用建议:</h6>
                    <ul className="space-y-1 text-base-content/70">
                      <li>• 大多数因子推荐使用Z-Score标准化</li>
                      <li>• 自定义代码需要返回标准化后的Series</li>
                      <li>• 变量名必须为normalized_result</li>
                      <li>• 支持pandas和numpy库</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="flex justify-between pt-4">
                <button
                  className="btn btn-outline"
                  onClick={() => setCurrentStep(2)}
                >
                  上一步
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => setCurrentStep(4)}
                >
                  下一步：确认创建
                </button>
              </div>
            </div>
          )}

          {/* 第四步：确认创建 */}
          {currentStep === 4 && (
            <div className="space-y-4">
              <div className="text-center mb-6">
                <h4 className="text-lg font-semibold text-base-content mb-2">
                  确认创建
                </h4>
                <p className="text-base-content/70">检查因子信息并创建</p>
              </div>

              {/* 因子信息预览 */}
              <div className="bg-base-200 rounded-lg p-6">
                <h5 className="font-semibold mb-4">因子信息预览</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p><strong>名称:</strong> {createFactorForm.name}</p>
                    <p><strong>显示名称:</strong> {createFactorForm.display_name}</p>
                    <p><strong>标准化:</strong> Z-Score</p>
                    <p><strong>标签:</strong> {selectedTags.map(tag => tag.display_name).join(', ') || '无'}</p>
                  </div>
                  <div>
                    <p><strong>描述:</strong> {createFactorForm.description || '无'}</p>
                    <p><strong>代码长度:</strong> {createFactorForm.formula.length} 字符</p>
                    <p><strong>标准化代码:</strong> {createFactorForm.normalization_code ? '已设置' : '使用默认'}</p>
                  </div>
                </div>
              </div>

              <div className="flex justify-between pt-4">
                <button
                  className="btn btn-outline"
                  onClick={() => setCurrentStep(3)}
                >
                  上一步
                </button>
                <button
                  className={`btn btn-success ${isCreating ? 'loading' : ''}`}
                  onClick={handleSaveNewFactor}
                  disabled={isCreating}
                >
                  {isCreating ? '创建中...' : '创建因子'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      <form method="dialog" className="modal-backdrop">
        <button>close</button>
      </form>
    </dialog>
  );
};

export default FactorCreateModalImproved;
