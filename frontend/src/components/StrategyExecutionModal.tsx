import React, { useState, useEffect } from 'react';
import { XMarkIcon, PlayIcon, StopIcon, EyeIcon } from '@heroicons/react/24/outline';

interface StrategyExecutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  strategy: any;
  onExecuted: () => void;
}

// 股票范围选项
const STOCK_SCOPES = [
  { value: 'all', label: '全部股票', description: '所有A股市场股票' },
  { value: 'industry', label: '按行业筛选', description: '选择特定行业的股票' },
  { value: 'concept', label: '按概念筛选', description: '选择特定概念的股票' },
  { value: 'index', label: '指数成分股', description: '选择指数成分股' },
  { value: 'custom', label: '自定义股票', description: '手动输入股票代码' }
];

// 市场类型选项
const MARKET_TYPES = [
  { value: 'all', label: '全部市场' },
  { value: 'main', label: '主板' },
  { value: 'sme', label: '中小板' },
  { value: 'gem', label: '创业板' },
  { value: 'star', label: '科创板' },
  { value: 'bj', label: '北交所' }
];

// 执行状态映射
const STATUS_MAP = {
  'pending': { label: '等待执行', color: 'text-warning' },
  'running': { label: '执行中', color: 'text-info' },
  'data_fetching': { label: '数据获取中', color: 'text-info' },
  'factor_calculating': { label: '因子计算中', color: 'text-info' },
  'ranking': { label: '排序计算中', color: 'text-info' },
  'filtering': { label: '筛选中', color: 'text-info' },
  'completed': { label: '执行完成', color: 'text-success' },
  'failed': { label: '执行失败', color: 'text-error' },
  'cancelled': { label: '已取消', color: 'text-warning' }
};

const StrategyExecutionModal: React.FC<StrategyExecutionModalProps> = ({
  isOpen,
  onClose,
  strategy,
  onExecuted
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [executionProgress, setExecutionProgress] = useState<any>(null);
  const [executionLogs, setExecutionLogs] = useState<any[]>([]);
  const [showLogs, setShowLogs] = useState(false);

  // 执行配置状态
  const [executionConfig, setExecutionConfig] = useState({
    scope: 'all',
    markets: ['all'],
    industries: [],
    concepts: [],
    index_codes: [],
    custom_stocks: '',
    
    // 基础筛选
    min_market_cap: '',
    max_market_cap: '',
    min_price: '',
    max_price: '',
    min_turnover: '',
    max_turnover: '',
    
    // 特殊筛选
    exclude_st: true,
    exclude_new_stock: true,
    exclude_suspend: true,
    
    // 执行选项
    dry_run: false,
    enable_cache: true,
    max_execution_time: 300
  });

  // 可用选项状态
  const [availableOptions, setAvailableOptions] = useState({
    industries: [],
    concepts: [],
    indices: [],
    markets: MARKET_TYPES
  });

  // 加载可用选项
  useEffect(() => {
    if (isOpen) {
      loadAvailableOptions();
    }
  }, [isOpen]);

  // 轮询执行进度
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (executionId && isExecuting) {
      interval = setInterval(async () => {
        try {
          const response = await fetch(`/api/v1/strategy-execution/executions/${executionId}/progress`);
          if (response.ok) {
            const progress = await response.json();
            setExecutionProgress(progress);
            
            if (progress.status === 'completed' || progress.status === 'failed' || progress.status === 'cancelled') {
              setIsExecuting(false);
              if (progress.status === 'completed') {
                onExecuted();
              }
            }
          }
        } catch (error) {
          console.error('获取执行进度失败:', error);
        }
      }, 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [executionId, isExecuting, onExecuted]);

  const loadAvailableOptions = async () => {
    try {
      const response = await fetch('/api/v1/strategy-execution/scopes');
      if (response.ok) {
        const options = await response.json();
        setAvailableOptions(options);
      }
    } catch (error) {
      console.error('加载选项失败:', error);
    }
  };

  const handleExecuteStrategy = async () => {
    try {
      setIsExecuting(true);
      
      // 构建股票筛选条件
      const stockFilter = {
        scope: executionConfig.scope,
        markets: executionConfig.markets.includes('all') ? null : executionConfig.markets,
        industries: executionConfig.industries.length > 0 ? executionConfig.industries : null,
        concepts: executionConfig.concepts.length > 0 ? executionConfig.concepts : null,
        index_codes: executionConfig.index_codes.length > 0 ? executionConfig.index_codes : null,
        custom_stocks: executionConfig.custom_stocks ? 
          executionConfig.custom_stocks.split(/[,\s]+/).filter(s => s.trim()) : null,
        
        // 基础筛选
        min_market_cap: executionConfig.min_market_cap ? parseFloat(executionConfig.min_market_cap) : null,
        max_market_cap: executionConfig.max_market_cap ? parseFloat(executionConfig.max_market_cap) : null,
        min_price: executionConfig.min_price ? parseFloat(executionConfig.min_price) : null,
        max_price: executionConfig.max_price ? parseFloat(executionConfig.max_price) : null,
        min_turnover: executionConfig.min_turnover ? parseFloat(executionConfig.min_turnover) : null,
        max_turnover: executionConfig.max_turnover ? parseFloat(executionConfig.max_turnover) : null,
        
        // 特殊筛选
        exclude_st: executionConfig.exclude_st,
        exclude_new_stock: executionConfig.exclude_new_stock,
        exclude_suspend: executionConfig.exclude_suspend
      };

      // 执行策略
      const response = await fetch(`/api/v1/strategy-execution/${strategy.strategy_id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stock_filter: stockFilter,
          dry_run: executionConfig.dry_run,
          save_result: true,
          enable_cache: executionConfig.enable_cache,
          max_execution_time: executionConfig.max_execution_time
        })
      });

      if (response.ok) {
        const result = await response.json();
        setExecutionId(result.execution_id);
        setCurrentStep(3); // 跳转到执行监控页面
      } else {
        throw new Error('执行请求失败');
      }
      
    } catch (error) {
      console.error('执行策略失败:', error);
      setIsExecuting(false);
      alert('执行策略失败，请重试');
    }
  };

  const handleCancelExecution = async () => {
    if (!executionId) return;
    
    try {
      const response = await fetch(`/api/v1/strategy-execution/executions/${executionId}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: '用户手动取消' })
      });
      
      if (response.ok) {
        setIsExecuting(false);
        setExecutionProgress(prev => prev ? { ...prev, status: 'cancelled' } : null);
      }
    } catch (error) {
      console.error('取消执行失败:', error);
    }
  };

  const loadExecutionLogs = async () => {
    if (!executionId) return;
    
    try {
      const response = await fetch(`/api/v1/strategy-execution/executions/${executionId}/logs?limit=50`);
      if (response.ok) {
        const result = await response.json();
        setExecutionLogs(result.logs || []);
      }
    } catch (error) {
      console.error('加载执行日志失败:', error);
    }
  };

  const handleReset = () => {
    setCurrentStep(1);
    setIsExecuting(false);
    setExecutionId(null);
    setExecutionProgress(null);
    setExecutionLogs([]);
    setShowLogs(false);
  };

  const formatTime = (timeStr: string) => {
    return new Date(timeStr).toLocaleTimeString('zh-CN');
  };

  if (!isOpen) return null;

  return (
    <dialog className="modal modal-open">
      <div className="modal-box max-w-5xl max-h-[90vh] bg-base-100 border border-base-300 shadow-2xl">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-base-300">
          <h3 className="text-xl font-bold text-base-content">
            执行策略: {strategy?.name}
          </h3>
          <button
            onClick={() => {
              handleReset();
              onClose();
            }}
            className="btn btn-ghost btn-sm btn-circle"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* 步骤指示器 */}
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

        {/* 第一步：选择股票范围 */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h4 className="text-lg font-semibold text-base-content mb-2">选择股票范围</h4>
              <p className="text-base-content/70">选择策略执行的股票池范围</p>
            </div>

            {/* 股票范围选择 */}
            <div className="form-control">
              <label className="label">
                <span className="label-text font-medium">股票范围</span>
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {STOCK_SCOPES.map((scope) => (
                  <div
                    key={scope.value}
                    className={`
                      card border cursor-pointer transition-all duration-200
                      ${executionConfig.scope === scope.value 
                        ? 'border-primary bg-primary/10' 
                        : 'border-base-300 hover:border-primary/50'
                      }
                    `}
                    onClick={() => setExecutionConfig({
                      ...executionConfig,
                      scope: scope.value
                    })}
                  >
                    <div className="card-body p-4">
                      <h5 className="font-medium">{scope.label}</h5>
                      <p className="text-sm text-base-content/70">{scope.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 具体选项 */}
            {executionConfig.scope === 'industry' && (
              <div className="form-control">
                <label className="label">
                  <span className="label-text font-medium">选择行业</span>
                </label>
                <select 
                  multiple 
                  className="select select-bordered h-32"
                  value={executionConfig.industries}
                  onChange={(e) => {
                    const selected = Array.from(e.target.selectedOptions, option => option.value);
                    setExecutionConfig({ ...executionConfig, industries: selected });
                  }}
                >
                  {availableOptions.industries.map((industry: any) => (
                    <option key={industry.code} value={industry.code}>
                      {industry.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {executionConfig.scope === 'concept' && (
              <div className="form-control">
                <label className="label">
                  <span className="label-text font-medium">选择概念</span>
                </label>
                <select 
                  multiple 
                  className="select select-bordered h-32"
                  value={executionConfig.concepts}
                  onChange={(e) => {
                    const selected = Array.from(e.target.selectedOptions, option => option.value);
                    setExecutionConfig({ ...executionConfig, concepts: selected });
                  }}
                >
                  {availableOptions.concepts.map((concept: any) => (
                    <option key={concept.code} value={concept.code}>
                      {concept.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {executionConfig.scope === 'custom' && (
              <div className="form-control">
                <label className="label">
                  <span className="label-text font-medium">自定义股票代码</span>
                </label>
                <textarea
                  className="textarea textarea-bordered h-24"
                  placeholder="输入股票代码，用逗号或空格分隔，如：000001.SZ, 600036.SH"
                  value={executionConfig.custom_stocks}
                  onChange={(e) => setExecutionConfig({
                    ...executionConfig,
                    custom_stocks: e.target.value
                  })}
                />
              </div>
            )}

            <div className="flex justify-end">
              <button
                className="btn btn-primary"
                onClick={() => setCurrentStep(2)}
              >
                下一步：筛选条件
              </button>
            </div>
          </div>
        )}

        {/* 第二步：设置筛选条件 */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h4 className="text-lg font-semibold text-base-content mb-2">设置筛选条件</h4>
              <p className="text-base-content/70">配置股票筛选和执行参数</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 基础筛选 */}
              <div className="space-y-4">
                <h5 className="font-medium text-base-content">基础筛选</h5>
                
                <div className="grid grid-cols-2 gap-3">
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text text-sm">最小市值（万元）</span>
                    </label>
                    <input
                      type="number"
                      className="input input-bordered input-sm"
                      placeholder="0"
                      value={executionConfig.min_market_cap}
                      onChange={(e) => setExecutionConfig({
                        ...executionConfig,
                        min_market_cap: e.target.value
                      })}
                    />
                  </div>
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text text-sm">最大市值（万元）</span>
                    </label>
                    <input
                      type="number"
                      className="input input-bordered input-sm"
                      placeholder="无限制"
                      value={executionConfig.max_market_cap}
                      onChange={(e) => setExecutionConfig({
                        ...executionConfig,
                        max_market_cap: e.target.value
                      })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text text-sm">最小股价（元）</span>
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      className="input input-bordered input-sm"
                      placeholder="0"
                      value={executionConfig.min_price}
                      onChange={(e) => setExecutionConfig({
                        ...executionConfig,
                        min_price: e.target.value
                      })}
                    />
                  </div>
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text text-sm">最大股价（元）</span>
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      className="input input-bordered input-sm"
                      placeholder="无限制"
                      value={executionConfig.max_price}
                      onChange={(e) => setExecutionConfig({
                        ...executionConfig,
                        max_price: e.target.value
                      })}
                    />
                  </div>
                </div>
              </div>

              {/* 特殊筛选 */}
              <div className="space-y-4">
                <h5 className="font-medium text-base-content">特殊筛选</h5>
                
                <div className="form-control">
                  <label className="cursor-pointer label">
                    <span className="label-text">排除ST股票</span>
                    <input
                      type="checkbox"
                      className="checkbox checkbox-primary"
                      checked={executionConfig.exclude_st}
                      onChange={(e) => setExecutionConfig({
                        ...executionConfig,
                        exclude_st: e.target.checked
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
                      checked={executionConfig.exclude_new_stock}
                      onChange={(e) => setExecutionConfig({
                        ...executionConfig,
                        exclude_new_stock: e.target.checked
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
                      checked={executionConfig.exclude_suspend}
                      onChange={(e) => setExecutionConfig({
                        ...executionConfig,
                        exclude_suspend: e.target.checked
                      })}
                    />
                  </label>
                </div>

                <div className="form-control">
                  <label className="cursor-pointer label">
                    <span className="label-text">模拟执行</span>
                    <input
                      type="checkbox"
                      className="checkbox checkbox-secondary"
                      checked={executionConfig.dry_run}
                      onChange={(e) => setExecutionConfig({
                        ...executionConfig,
                        dry_run: e.target.checked
                      })}
                    />
                  </label>
                </div>
              </div>
            </div>

            <div className="flex justify-between">
              <button
                className="btn btn-outline"
                onClick={() => setCurrentStep(1)}
              >
                上一步
              </button>
              <button
                className="btn btn-primary"
                onClick={handleExecuteStrategy}
                disabled={isExecuting}
              >
                {isExecuting ? '启动中...' : '开始执行'}
              </button>
            </div>
          </div>
        )}

        {/* 第三步：执行监控 */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h4 className="text-lg font-semibold text-base-content mb-2">执行监控</h4>
              <p className="text-base-content/70">策略执行进度和日志监控</p>
            </div>

            {/* 执行状态 */}
            {executionProgress && (
              <div className="card bg-base-200">
                <div className="card-body">
                  <div className="flex items-center justify-between mb-4">
                    <h5 className="font-medium">执行状态</h5>
                    <div className="flex gap-2">
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => {
                          setShowLogs(!showLogs);
                          if (!showLogs) loadExecutionLogs();
                        }}
                      >
                        <EyeIcon className="w-4 h-4 mr-1" />
                        {showLogs ? '隐藏' : '查看'}日志
                      </button>
                      {isExecuting && (
                        <button
                          className="btn btn-error btn-sm"
                          onClick={handleCancelExecution}
                        >
                          <StopIcon className="w-4 h-4 mr-1" />
                          取消执行
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">当前状态:</span>
                      <span className={`font-medium ${STATUS_MAP[executionProgress.status]?.color || 'text-base-content'}`}>
                        {STATUS_MAP[executionProgress.status]?.label || executionProgress.status}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm">当前阶段:</span>
                      <span className="font-medium">{executionProgress.current_stage}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm">总体进度:</span>
                      <span className="font-medium">{executionProgress.overall_progress?.toFixed(1) || 0}%</span>
                    </div>

                    <div className="w-full bg-base-300 rounded-full h-2">
                      <div 
                        className="bg-primary h-2 rounded-full transition-all duration-300"
                        style={{ width: `${executionProgress.overall_progress || 0}%` }}
                      ></div>
                    </div>

                    {executionProgress.latest_log && (
                      <div className="bg-base-100 rounded p-3 mt-4">
                        <div className="text-sm text-base-content/70">最新日志:</div>
                        <div className="text-sm mt-1">[{formatTime(executionProgress.latest_log.timestamp)}] {executionProgress.latest_log.message}</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* 执行日志 */}
            {showLogs && (
              <div className="card bg-base-200">
                <div className="card-body">
                  <h5 className="font-medium mb-3">执行日志</h5>
                  <div className="bg-base-100 rounded p-4 max-h-64 overflow-y-auto">
                    {executionLogs.length > 0 ? (
                      <div className="space-y-2">
                        {executionLogs.map((log, index) => (
                          <div key={index} className="text-sm">
                            <span className="text-base-content/60">[{formatTime(log.timestamp)}]</span>
                            <span className={`ml-2 font-medium ${
                              log.level === 'error' ? 'text-error' :
                              log.level === 'warning' ? 'text-warning' :
                              log.level === 'info' ? 'text-info' : ''
                            }`}>
                              [{log.stage}]
                            </span>
                            <span className="ml-2">{log.message}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center text-base-content/60 py-4">
                        暂无日志数据
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-between">
              <button
                className="btn btn-outline"
                onClick={handleReset}
                disabled={isExecuting}
              >
                重新配置
              </button>
              {executionProgress?.status === 'completed' && (
                <button
                  className="btn btn-success"
                  onClick={() => {
                    onExecuted();
                    onClose();
                  }}
                >
                  查看结果
                </button>
              )}
            </div>
          </div>
        )}
      </div>
      <form method="dialog" className="modal-backdrop">
        <button>close</button>
      </form>
    </dialog>
  );
};

export default StrategyExecutionModal;