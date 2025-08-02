import React, { useState, useEffect } from 'react';
import { XMarkIcon, CheckCircleIcon, ExclamationTriangleIcon, PlusIcon } from '@heroicons/react/24/outline';
import { 
  strategyManagementApi, 
  StrategyCreate, 
  StrategyFactor, 
  AvailableFactor,
  factorApi,
  Factor
} from '../services/api';

interface StrategyCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

const StrategyCreateModal: React.FC<StrategyCreateModalProps> = ({
  isOpen,
  onClose,
  onCreated
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isCreating, setIsCreating] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [showSuccessAnimation, setShowSuccessAnimation] = useState(false);
  const [availableFactors, setAvailableFactors] = useState<Factor[]>([]);
  const [loadingFactors, setLoadingFactors] = useState(false);

  const [strategyForm, setStrategyForm] = useState<StrategyCreate>({
    name: '',
    description: '',
    factors: [],
    filters: {
      exclude_st: true,
      exclude_new_stock: true,
      exclude_suspend: true
    },
    config: {
      max_results: 50,
      rebalance_frequency: 'weekly',
      ranking_method: 'composite'
    }
  });

  // 加载可用因子
  useEffect(() => {
    if (isOpen) {
      loadAvailableFactors();
    }
  }, [isOpen]);

  const loadAvailableFactors = async () => {
    try {
      setLoadingFactors(true);
      const factors = await factorApi.getFactors();
      setAvailableFactors(factors.filter(f => f.is_active));
    } catch (error) {
      console.error('加载因子失败:', error);
    } finally {
      setLoadingFactors(false);
    }
  };

  // 验证表单
  const validateForm = (): string[] => {
    const errors: string[] = [];
    
    if (!strategyForm.name.trim()) {
      errors.push('请填写策略名称');
    }
    
    if (strategyForm.factors.length === 0) {
      errors.push('请至少选择一个因子');
    }
    
    // 验证权重
    const enabledFactors = strategyForm.factors.filter(f => f.is_enabled);
    if (enabledFactors.length === 0) {
      errors.push('请至少启用一个因子');
    } else {
      const totalWeight = enabledFactors.reduce((sum, f) => sum + f.weight, 0);
      if (Math.abs(totalWeight - 1.0) > 0.001) {
        errors.push(`启用因子的权重总和必须为1.0，当前为${totalWeight.toFixed(3)}`);
      }
    }
    
    return errors;
  };

  // 创建策略
  const handleCreateStrategy = async () => {
    const errors = validateForm();
    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }
    
    try {
      setIsCreating(true);
      setValidationErrors([]);
      
      await strategyManagementApi.createStrategy(strategyForm);
      
      // 显示成功动画
      setShowSuccessAnimation(true);
      setTimeout(() => {
        setShowSuccessAnimation(false);
        onClose();
        onCreated();
        handleResetForm();
      }, 1500);
      
    } catch (error) {
      console.error('创建策略失败:', error);
      setValidationErrors(['创建策略失败，请检查网络连接或稍后重试']);
    } finally {
      setIsCreating(false);
    }
  };

  // 重置表单
  const handleResetForm = () => {
    setStrategyForm({
      name: '',
      description: '',
      factors: [],
      filters: {
        exclude_st: true,
        exclude_new_stock: true,
        exclude_suspend: true
      },
      config: {
        max_results: 50,
        rebalance_frequency: 'weekly',
        ranking_method: 'composite'
      }
    });
    setCurrentStep(1);
    setValidationErrors([]);
  };

  // 添加因子
  const handleAddFactor = (factor: Factor) => {
    const newStrategyFactor: StrategyFactor = {
      factor_id: factor.factor_id,
      factor_name: factor.display_name || factor.name,
      weight: 0,
      is_enabled: true
    };

    const newFactors = [...strategyForm.factors, newStrategyFactor];
    
    // 自动分配等权重
    const enabledFactors = newFactors.filter(f => f.is_enabled);
    const equalWeight = 1.0 / enabledFactors.length;
    
    const updatedFactors = newFactors.map(f => 
      f.is_enabled ? { ...f, weight: equalWeight } : f
    );

    setStrategyForm({
      ...strategyForm,
      factors: updatedFactors
    });
  };

  // 移除因子
  const handleRemoveFactor = (factorId: string) => {
    const newFactors = strategyForm.factors.filter(f => f.factor_id !== factorId);
    
    // 重新分配权重
    const enabledFactors = newFactors.filter(f => f.is_enabled);
    if (enabledFactors.length > 0) {
      const equalWeight = 1.0 / enabledFactors.length;
      const updatedFactors = newFactors.map(f => 
        f.is_enabled ? { ...f, weight: equalWeight } : f
      );
      
      setStrategyForm({
        ...strategyForm,
        factors: updatedFactors
      });
    } else {
      setStrategyForm({
        ...strategyForm,
        factors: newFactors
      });
    }
  };

  // 更新因子权重
  const handleUpdateFactorWeight = (factorId: string, weight: number) => {
    const updatedFactors = strategyForm.factors.map(f => 
      f.factor_id === factorId ? { ...f, weight } : f
    );
    
    setStrategyForm({
      ...strategyForm,
      factors: updatedFactors
    });
  };

  // 切换因子启用状态
  const handleToggleFactor = (factorId: string) => {
    const updatedFactors = strategyForm.factors.map(f => 
      f.factor_id === factorId ? { ...f, is_enabled: !f.is_enabled } : f
    );
    
    // 重新分配权重
    const enabledFactors = updatedFactors.filter(f => f.is_enabled);
    if (enabledFactors.length > 0) {
      const equalWeight = 1.0 / enabledFactors.length;
      const finalFactors = updatedFactors.map(f => 
        f.is_enabled ? { ...f, weight: equalWeight } : { ...f, weight: 0 }
      );
      
      setStrategyForm({
        ...strategyForm,
        factors: finalFactors
      });
    } else {
      setStrategyForm({
        ...strategyForm,
        factors: updatedFactors
      });
    }
  };

  // 获取未选择的因子
  const getUnselectedFactors = () => {
    const selectedIds = new Set(strategyForm.factors.map(f => f.factor_id));
    return availableFactors.filter(f => !selectedIds.has(f.factor_id));
  };

  // 步骤指示器
  const StepIndicator = () => (
    <div className="flex items-center justify-center mb-6">
      <div className="flex items-center space-x-2">
        {[1, 2, 3].map((step) => (
          <React.Fragment key={step}>
            <div className={`
              w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
              transition-all duration-300
              ${currentStep >= step 
                ? 'bg-primary text-primary-content' 
                : 'bg-base-300 text-base-content/60'
              }
            `}>
              {step}
            </div>
            {step < 3 && (
              <div className={`
                w-12 h-0.5 transition-all duration-300
                ${currentStep > step ? 'bg-primary' : 'bg-base-300'}
              `} />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );

  if (!isOpen) return null;

  return (
    <div className="modal modal-open backdrop-blur-sm">
      <div className="modal-box max-w-4xl max-h-[90vh] bg-base-100 border border-base-300 shadow-2xl">
        {/* 成功动画覆盖层 */}
        {showSuccessAnimation && (
          <div className="absolute inset-0 bg-base-100/95 flex items-center justify-center z-50 rounded-lg">
            <div className="text-center">
              <CheckCircleIcon className="w-16 h-16 text-success mx-auto mb-4 animate-pulse" />
              <h3 className="text-xl font-bold text-success mb-2">策略创建成功！</h3>
              <p className="text-base-content/70">策略已添加到策略库</p>
            </div>
          </div>
        )}

        {/* 头部 */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-base-300">
          <h3 className="text-xl font-bold text-base-content">创建新策略</h3>
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
                  <li key={index} className="text-sm">{error}</li>
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
                <h4 className="text-lg font-semibold text-base-content mb-2">基本信息</h4>
                <p className="text-base-content/70">设置策略的名称和描述</p>
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text font-medium">策略名称 *</span>
                </label>
                <input
                  type="text"
                  className="input input-bordered bg-base-100 focus:border-primary"
                  placeholder="例如: 多因子选股策略"
                  value={strategyForm.name}
                  onChange={(e) => setStrategyForm({
                    ...strategyForm,
                    name: e.target.value
                  })}
                />
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text font-medium">策略描述</span>
                </label>
                <textarea
                  className="textarea textarea-bordered bg-base-100 focus:border-primary h-24 resize-none"
                  placeholder="描述策略的目标、适用市场环境等..."
                  value={strategyForm.description}
                  onChange={(e) => setStrategyForm({
                    ...strategyForm,
                    description: e.target.value
                  })}
                />
              </div>

              <div className="flex justify-end pt-4">
                <button
                  className="btn btn-primary"
                  onClick={() => setCurrentStep(2)}
                  disabled={!strategyForm.name.trim()}
                >
                  下一步：选择因子
                </button>
              </div>
            </div>
          )}

          {/* 第二步：因子选择 */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <div className="text-center mb-6">
                <h4 className="text-lg font-semibold text-base-content mb-2">因子选择</h4>
                <p className="text-base-content/70">选择要使用的因子并设置权重</p>
              </div>

              {/* 已选择的因子 */}
              <div className="bg-base-200/30 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h5 className="font-medium text-base-content">
                    已选择因子 ({strategyForm.factors.length})
                  </h5>
                  <div className="text-sm text-base-content/70">
                    权重总和: {strategyForm.factors.filter(f => f.is_enabled).reduce((sum, f) => sum + f.weight, 0).toFixed(3)}
                  </div>
                </div>

                {strategyForm.factors.length === 0 ? (
                  <div className="text-center py-8 text-base-content/60">
                    还未选择任何因子，请从下方添加
                  </div>
                ) : (
                  <div className="space-y-3">
                    {strategyForm.factors.map((factor) => (
                      <div key={factor.factor_id} className="flex items-center gap-4 p-3 bg-base-100 rounded border">
                        <input
                          type="checkbox"
                          className="checkbox checkbox-primary"
                          checked={factor.is_enabled}
                          onChange={() => handleToggleFactor(factor.factor_id)}
                        />
                        
                        <div className="flex-1">
                          <div className="font-medium text-base-content">{factor.factor_name}</div>
                          <div className="text-sm text-base-content/70">{factor.factor_id}</div>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-base-content/70">权重:</span>
                          <input
                            type="number"
                            className="input input-sm input-bordered w-20"
                            min="0"
                            max="1"
                            step="0.001"
                            value={factor.weight.toFixed(3)}
                            onChange={(e) => handleUpdateFactorWeight(factor.factor_id, parseFloat(e.target.value) || 0)}
                            disabled={!factor.is_enabled}
                          />
                        </div>
                        
                        <button
                          className="btn btn-sm btn-ghost btn-circle text-error"
                          onClick={() => handleRemoveFactor(factor.factor_id)}
                        >
                          <XMarkIcon className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 可选择的因子 */}
              <div className="bg-base-200/30 rounded-lg p-4">
                <h5 className="font-medium text-base-content mb-4">
                  可选择因子 ({getUnselectedFactors().length})
                </h5>
                
                {loadingFactors ? (
                  <div className="text-center py-4">
                    <span className="loading loading-spinner loading-sm mr-2"></span>
                    加载中...
                  </div>
                ) : getUnselectedFactors().length === 0 ? (
                  <div className="text-center py-4 text-base-content/60">
                    所有因子都已选择
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-64 overflow-y-auto">
                    {getUnselectedFactors().map((factor) => (
                      <div
                        key={factor.factor_id}
                        className="flex items-center gap-3 p-3 bg-base-100 rounded border hover:bg-base-200/50 cursor-pointer"
                        onClick={() => handleAddFactor(factor)}
                      >
                        <PlusIcon className="w-5 h-5 text-primary" />
                        <div className="flex-1">
                          <div className="font-medium text-base-content">{factor.display_name || factor.name}</div>
                          <div className="text-sm text-base-content/70">{factor.factor_id}</div>
                          <div className="text-xs text-base-content/60">{factor.description}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
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
                  disabled={strategyForm.factors.length === 0}
                >
                  下一步：配置参数
                </button>
              </div>
            </div>
          )}

          {/* 第三步：配置参数 */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <div className="text-center mb-6">
                <h4 className="text-lg font-semibold text-base-content mb-2">配置参数</h4>
                <p className="text-base-content/70">设置策略执行参数和筛选条件</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 策略配置 */}
                <div className="space-y-4">
                  <h5 className="font-medium text-base-content">策略配置</h5>
                  
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">最大选股数量</span>
                    </label>
                    <input
                      type="number"
                      className="input input-bordered"
                      min="1"
                      max="1000"
                      value={strategyForm.config?.max_results}
                      onChange={(e) => setStrategyForm({
                        ...strategyForm,
                        config: {
                          ...strategyForm.config!,
                          max_results: parseInt(e.target.value) || 50
                        }
                      })}
                    />
                  </div>

                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">调仓频率</span>
                    </label>
                    <select
                      className="select select-bordered"
                      value={strategyForm.config?.rebalance_frequency}
                      onChange={(e) => setStrategyForm({
                        ...strategyForm,
                        config: {
                          ...strategyForm.config!,
                          rebalance_frequency: e.target.value
                        }
                      })}
                    >
                      <option value="daily">每日</option>
                      <option value="weekly">每周</option>
                      <option value="monthly">每月</option>
                    </select>
                  </div>
                </div>

                {/* 筛选条件 */}
                <div className="space-y-4">
                  <h5 className="font-medium text-base-content">筛选条件</h5>
                  
                  <div className="form-control">
                    <label className="cursor-pointer label">
                      <span className="label-text">排除ST股票</span>
                      <input
                        type="checkbox"
                        className="checkbox checkbox-primary"
                        checked={strategyForm.filters?.exclude_st}
                        onChange={(e) => setStrategyForm({
                          ...strategyForm,
                          filters: {
                            ...strategyForm.filters!,
                            exclude_st: e.target.checked
                          }
                        })}
                      />
                    </label>
                  </div>

                  <div className="form-control">
                    <label className="cursor-pointer label">
                      <span className="label-text">排除新股</span>
                      <input
                        type="checkbox"
                        className="checkbox checkbox-primary"
                        checked={strategyForm.filters?.exclude_new_stock}
                        onChange={(e) => setStrategyForm({
                          ...strategyForm,
                          filters: {
                            ...strategyForm.filters!,
                            exclude_new_stock: e.target.checked
                          }
                        })}
                      />
                    </label>
                  </div>

                  <div className="form-control">
                    <label className="cursor-pointer label">
                      <span className="label-text">排除停牌股票</span>
                      <input
                        type="checkbox"
                        className="checkbox checkbox-primary"
                        checked={strategyForm.filters?.exclude_suspend}
                        onChange={(e) => setStrategyForm({
                          ...strategyForm,
                          filters: {
                            ...strategyForm.filters!,
                            exclude_suspend: e.target.checked
                          }
                        })}
                      />
                    </label>
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
                  onClick={handleCreateStrategy}
                  disabled={isCreating}
                >
                  {isCreating ? '创建中...' : '创建策略'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StrategyCreateModal;