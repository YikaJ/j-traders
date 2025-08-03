import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import {
  XMarkIcon,
  SparklesIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { factorApi, CustomFactorCreateRequest, FactorTag } from '../services/api';
import FieldSelector from './FieldSelector';
import TagInput from './common/TagInput';

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
    const errors = validateForm();
    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }

    try {
      setIsCreating(true);
      setValidationErrors([]);

      // 转换为后端期望的格式
      const factorData = {
        name: createFactorForm.name,
        display_name: createFactorForm.display_name,
        description: createFactorForm.description,
        code: createFactorForm.formula,  // 将formula映射为code
        input_fields: createFactorForm.input_fields,
        default_parameters: createFactorForm.default_parameters,
        calculation_method: createFactorForm.calculation_method,
      };

      const createdFactor = await factorApi.createFactor(factorData);

      // 如果有选择的标签，创建标签关联
      if (selectedTags.length > 0) {
        try {
          await factorApi.createFactorTagRelations({
            factor_id: createdFactor.id,
            tag_ids: selectedTags.map(tag => tag.id),
            tags: selectedTags,
          });
        } catch (error) {
          console.error('创建标签关联失败:', error);
          // 不阻止因子创建成功
        }
      }

      // 显示成功动画
      setShowSuccessAnimation(true);
      setTimeout(() => {
        setShowSuccessAnimation(false);
        onClose();
        onCreated();
        handleResetForm();
      }, 1500);
    } catch (error) {
      console.error('创建因子失败:', error);
      setValidationErrors(['创建因子失败，请检查网络连接或稍后重试']);
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
        pandas.Series - 计算得到的因子值
    """
    # 获取输入数据
${dataAccess}
    
    # 在这里编写你的因子计算逻辑
    # 示例：计算价格变化率
    returns = data['close'].pct_change()
    
    # 计算过去10天的累积收益（可根据需要调整）
    factor_value = returns.rolling(window=10).sum()
    
    # 处理无效值
    factor_value = factor_value.fillna(0)
    
    return factor_value`;
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
        {[1, 2, 3].map((step) => (
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
            {step < 3 && (
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
                    tags={selectedTags}
                    availableTags={availableTags}
                    onTagsChange={setSelectedTags}
                    onCreateTag={handleCreateTag}
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
                  下一步：选择数据字段
                </button>
              </div>
            </div>
          )}

          {/* 第二步：选择输入字段 */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <div className="text-center mb-6">
                <h4 className="text-lg font-semibold text-base-content mb-2">
                  数据字段配置
                </h4>
                <p className="text-base-content/70">
                  选择因子计算所需的数据字段
                </p>
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text font-medium">输入字段 *</span>
                  <span className="label-text-alt text-xs">
                    因子计算时可以使用的数据字段
                  </span>
                </label>
                <FieldSelector
                  selectedFields={createFactorForm.input_fields}
                  onChange={(fields) =>
                    setCreateFactorForm({
                      ...createFactorForm,
                      input_fields: fields,
                    })
                  }
                  placeholder="请选择因子计算需要的数据字段..."
                  showValidation={true}
                />
              </div>

              {/* 字段预览 */}
              {createFactorForm.input_fields.length > 0 && (
                <div className="bg-base-200/50 rounded-lg p-4">
                  <h5 className="font-medium text-base-content mb-3">
                    已选择的字段预览
                  </h5>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {createFactorForm.input_fields.map((field) => (
                      <div
                        key={field}
                        className="bg-base-100 rounded p-2 text-sm"
                      >
                        <span className="font-medium text-primary">
                          data['${field}']
                        </span>
                        <div className="text-base-content/70">
                          {getFieldDescription(field)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

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
                  disabled={createFactorForm.input_fields.length === 0}
                >
                  下一步：编写代码
                </button>
              </div>
            </div>
          )}

          {/* 第三步：编写代码 */}
          {currentStep === 3 && (
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
                <h5 className="font-semibold text-info mb-3">💡 编写提示</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <h6 className="font-medium mb-2">常用函数:</h6>
                    <ul className="space-y-1 text-base-content/70">
                      <li>
                        <code>.pct_change()</code> - 计算收益率
                      </li>
                      <li>
                        <code>.rolling(n).mean()</code> - n日移动平均
                      </li>
                      <li>
                        <code>.rolling(n).std()</code> - n日标准差
                      </li>
                      <li>
                        <code>.shift(n)</code> - 向前/后移动n期
                      </li>
                    </ul>
                  </div>
                  <div>
                    <h6 className="font-medium mb-2">注意事项:</h6>
                    <ul className="space-y-1 text-base-content/70">
                      <li>• 函数必须返回pandas.Series</li>
                      <li>• 处理空值和异常情况</li>
                      <li>• 避免未来数据泄露</li>
                      <li>• 保持代码简洁易懂</li>
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
                  className={`btn btn-success ${isCreating ? 'loading' : ''}`}
                  onClick={handleSaveNewFactor}
                  disabled={isCreating || !createFactorForm.formula.trim()}
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
