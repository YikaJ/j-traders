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
  { value: 'all', label: '全量搜索', description: '所有A股市场股票' },
  { value: 'industry', label: '按行业搜索', description: '选择特定行业的股票' },
  { value: 'custom', label: '自定义股票代码', description: '手动输入股票代码' }
];

// 执行状态映射
const STATUS_MAP: Record<string, { label: string; color: string }> = {
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
  const [logLevel, setLogLevel] = useState<string>('');
  const [autoRefreshLogs, setAutoRefreshLogs] = useState(true);

  // 执行配置状态
  const [executionConfig, setExecutionConfig] = useState({
    scope: 'all',
    industries: [] as string[],
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
    max_execution_time: 300,
    
    // 频率限制
    rate_limit_enabled: true,
    max_calls_per_minute: 10,
    max_calls_per_hour: 200,
    max_calls_per_day: 1000,
    concurrent_limit: 3
  });

  // 可用选项状态
  const [availableOptions, setAvailableOptions] = useState({
    industries: []
  });

  // 重置状态
  useEffect(() => {
    if (isOpen) {
      setCurrentStep(1);
      setIsExecuting(false);
      setExecutionId(null);
      setExecutionProgress(null);
      setExecutionLogs([]);
      setShowLogs(false);
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

  // 自动刷新日志
  useEffect(() => {
    let logInterval: NodeJS.Timeout;
    
    if (executionId && showLogs && autoRefreshLogs && isExecuting) {
      // 立即加载一次日志
      loadExecutionLogs();
      
      // 每2秒刷新一次日志
      logInterval = setInterval(() => {
        loadExecutionLogs();
      }, 2000);
    }
    
    return () => {
      if (logInterval) clearInterval(logInterval);
    };
  }, [executionId, showLogs, autoRefreshLogs, isExecuting]);

  const loadAvailableOptions = async () => {
    try {
      const response = await fetch('/api/v1/strategy-execution/scopes');
      if (response.ok) {
        const options = await response.json();
        setAvailableOptions(options);
      } else {
        console.error('加载选项失败:', response.status, response.statusText);
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
        industries: executionConfig.industries.length > 0 ? executionConfig.industries : null,
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

      // 构建API频率限制配置
      const rateLimitConfig = executionConfig.rate_limit_enabled ? {
        max_calls_per_minute: executionConfig.max_calls_per_minute,
        max_calls_per_hour: executionConfig.max_calls_per_hour,
        max_calls_per_day: executionConfig.max_calls_per_day,
        concurrent_limit: executionConfig.concurrent_limit
      } : null;

      // 执行策略
      const response = await fetch(`/api/v1/strategy-execution/${strategy.strategy_id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stock_filter: stockFilter,
          dry_run: executionConfig.dry_run,
          save_result: true,
          enable_cache: executionConfig.enable_cache,
          max_execution_time: executionConfig.max_execution_time,
          rate_limit: rateLimitConfig
        })
      });

      if (response.ok) {
        const result = await response.json();
        setExecutionId(result.execution_id);
        setCurrentStep(4); // 跳转到执行监控页面
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
        setExecutionProgress((prev: any) => prev ? { ...prev, status: 'cancelled' } : null);
      }
    } catch (error) {
      console.error('取消执行失败:', error);
    }
  };

  const loadExecutionLogs = async () => {
    if (!executionId) return;
    
    try {
      let url = `/api/v1/strategy-execution/executions/${executionId}/logs?limit=100`;
      if (logLevel) {
        url += `&level=${logLevel}`;
      }
      
      const response = await fetch(url);
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

  const formatDateTime = (dateTime: string) => {
    return new Date(dateTime).toLocaleString('zh-CN');
  };

  if (!isOpen || !strategy) return null;

  return (
    <dialog className="modal modal-open">
      <div className="modal-box max-w-5xl max-h-[90vh] bg-base-100 border border-base-300 shadow-2xl">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-base-300">
          <h3 className="text-xl font-bold text-base-content">
            {currentStep === 1 ? '策略详情' : 
             currentStep === 2 ? '选择股票范围' :
             currentStep === 3 ? '设置筛选条件' : '执行监控'}: {strategy?.name}
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
            {[1, 2, 3, 4].map((step) => (
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
                {step < 4 && (
                  <div className={`
                    w-12 h-0.5 transition-all duration-300
                    ${currentStep > step ? 'bg-primary' : 'bg-base-300'}
                  `} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* 第一步：策略详情 */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h4 className="text-lg font-semibold text-base-content mb-2">策略详情</h4>
              <p className="text-base-content/70">查看策略配置和基本信息</p>
            </div>

            {/* 基本信息 */}
            <div className="card bg-base-200">
              <div className="card-body">
                <h5 className="font-medium mb-3">基本信息</h5>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-base-content/70">策略ID:</span>
                    <span className="ml-2 font-mono">{strategy.strategy_id}</span>
                  </div>
                  <div>
                    <span className="text-base-content/70">状态:</span>
                    <span className={`ml-2 badge badge-sm ${strategy.is_active ? 'badge-success' : 'badge-error'}`}>
                      {strategy.is_active ? '启用' : '禁用'}
                    </span>
                  </div>
                  <div>
                    <span className="text-base-content/70">创建时间:</span>
                    <span className="ml-2">{formatDateTime(strategy.created_at)}</span>
                  </div>
                  <div>
                    <span className="text-base-content/70">更新时间:</span>
                    <span className="ml-2">{formatDateTime(strategy.updated_at)}</span>
                  </div>
                </div>
                {strategy.description && (
                  <div className="mt-3">
                    <span className="text-base-content/70">描述:</span>
                    <p className="mt-1 text-sm">{strategy.description}</p>
                  </div>
                )}
              </div>
            </div>

            {/* 因子配置 */}
            <div className="card bg-base-200">
              <div className="card-body">
                <h5 className="font-medium mb-3">因子配置 ({strategy.factors.length})</h5>
                <div className="overflow-x-auto">
                  <table className="table table-sm">
                    <thead>
                      <tr>
                        <th>因子名称</th>
                        <th>因子ID</th>
                        <th>权重</th>
                        <th>状态</th>
                      </tr>
                    </thead>
                    <tbody>
                      {strategy.factors.map((factor: any) => (
                        <tr key={factor.id}>
                          <td className="font-medium">{factor.name}</td>
                          <td className="font-mono text-xs">{factor.id}</td>
                          <td className="text-right">{factor.weight.toFixed(2)}</td>
                          <td>
                            <span className={`badge badge-sm ${factor.is_enabled ? 'badge-success' : 'badge-ghost'}`}>
                              {factor.is_enabled ? '启用' : '禁用'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* 策略配置 */}
            {strategy.config && (
              <div className="card bg-base-200">
                <div className="card-body">
                  <h5 className="font-medium mb-3">策略配置</h5>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-base-content/70">最大选股数:</span>
                      <span className="ml-2 font-medium">{strategy.config.max_results}</span>
                    </div>
                    <div>
                      <span className="text-base-content/70">调仓频率:</span>
                      <span className="ml-2 font-medium">
                        {strategy.config.rebalance_frequency === 'daily' ? '每日' :
                         strategy.config.rebalance_frequency === 'weekly' ? '每周' : '每月'}
                      </span>
                    </div>
                    <div>
                      <span className="text-base-content/70">排序方法:</span>
                      <span className="ml-2 font-medium">{strategy.config.ranking_method}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 统计信息 */}
            <div className="card bg-base-200">
              <div className="card-body">
                <h5 className="font-medium mb-3">执行统计</h5>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-base-content/70">执行次数:</span>
                    <span className="ml-2 font-medium">{strategy.execution_count}</span>
                  </div>
                  {strategy.avg_execution_time && (
                    <div>
                      <span className="text-base-content/70">平均耗时:</span>
                      <span className="ml-2 font-medium">{strategy.avg_execution_time.toFixed(2)}秒</span>
                    </div>
                  )}
                  {strategy.last_result_count && (
                    <div>
                      <span className="text-base-content/70">最后选股数:</span>
                      <span className="ml-2 font-medium">{strategy.last_result_count}只</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                className="btn btn-primary"
                onClick={() => setCurrentStep(2)}
                disabled={!strategy.is_active}
              >
                下一步：选择股票范围
              </button>
            </div>
          </div>
        )}

        {/* 第二步：选择股票范围 */}
        {currentStep === 2 && (
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
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
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
                
                {/* 多选下拉框 */}
                <div className="dropdown w-full">
                  <div tabIndex={0} role="button" className="btn btn-outline w-full justify-between">
                    <span>
                      {executionConfig.industries.length > 0 
                        ? `已选择 ${executionConfig.industries.length} 个行业`
                        : '请选择行业'
                      }
                    </span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                  <ul tabIndex={0} className="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-full max-h-64 overflow-y-auto">
                    {availableOptions.industries.map((industry: any) => (
                      <li key={industry.code}>
                        <label className="cursor-pointer flex items-center gap-2">
                          <input
                            type="checkbox"
                            className="checkbox checkbox-primary checkbox-sm"
                            checked={executionConfig.industries.includes(industry.code)}
                            onChange={(e) => {
                              const newIndustries = e.target.checked
                                ? [...executionConfig.industries, industry.code]
                                : executionConfig.industries.filter(code => code !== industry.code);
                              setExecutionConfig({ ...executionConfig, industries: newIndustries });
                            }}
                          />
                          <span>{industry.name}</span>
                        </label>
                      </li>
                    ))}
                  </ul>
                </div>
                
                {/* 已选择的行业标签 */}
                {executionConfig.industries.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm text-base-content/70 mb-2">已选择的行业：</div>
                    <div className="flex flex-wrap gap-2">
                      {executionConfig.industries.map((industryCode: string) => {
                        const industry = availableOptions.industries.find((i: any) => i.code === industryCode);
                        return (
                          <div key={industryCode} className="badge badge-primary badge-outline">
                            {(industry as any)?.name || industryCode}
                            <button
                              className="ml-1"
                              onClick={() => {
                                const newIndustries = executionConfig.industries.filter(code => code !== industryCode);
                                setExecutionConfig({ ...executionConfig, industries: newIndustries });
                              }}
                            >
                              ×
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
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

            <div className="flex justify-between">
              <button
                className="btn btn-outline"
                onClick={() => setCurrentStep(1)}
              >
                上一步
              </button>
              <button
                className="btn btn-primary"
                onClick={() => setCurrentStep(3)}
              >
                下一步：筛选条件
              </button>
            </div>
          </div>
        )}

        {/* 第三步：设置筛选条件 */}
        {currentStep === 3 && (
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

            {/* API频率限制配置 */}
            <div className="card bg-base-200 mt-6">
              <div className="card-body">
                <div className="flex items-center justify-between mb-4">
                  <h5 className="font-medium text-base-content">API频率限制</h5>
                  <input
                    type="checkbox"
                    className="checkbox checkbox-primary"
                    checked={executionConfig.rate_limit_enabled}
                    onChange={(e) => setExecutionConfig({
                      ...executionConfig,
                      rate_limit_enabled: e.target.checked
                    })}
                  />
                </div>
                
                {executionConfig.rate_limit_enabled && (
                  <div className="space-y-4">
                    <div className="alert alert-info">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                      <span className="text-sm">配置API调用频率限制，避免超出Tushare接口限制</span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="form-control">
                        <label className="label">
                          <span className="label-text text-sm">每分钟最大调用次数</span>
                        </label>
                        <input
                          type="number"
                          className="input input-bordered input-sm"
                          placeholder="10"
                          min="1"
                          max="100"
                          value={executionConfig.max_calls_per_minute}
                          onChange={(e) => setExecutionConfig({
                            ...executionConfig,
                            max_calls_per_minute: parseInt(e.target.value) || 10
                          })}
                        />
                      </div>
                      <div className="form-control">
                        <label className="label">
                          <span className="label-text text-sm">每小时最大调用次数</span>
                        </label>
                        <input
                          type="number"
                          className="input input-bordered input-sm"
                          placeholder="200"
                          min="10"
                          max="1000"
                          value={executionConfig.max_calls_per_hour}
                          onChange={(e) => setExecutionConfig({
                            ...executionConfig,
                            max_calls_per_hour: parseInt(e.target.value) || 200
                          })}
                        />
                      </div>
                      <div className="form-control">
                        <label className="label">
                          <span className="label-text text-sm">每天最大调用次数</span>
                        </label>
                        <input
                          type="number"
                          className="input input-bordered input-sm"
                          placeholder="1000"
                          min="100"
                          max="10000"
                          value={executionConfig.max_calls_per_day}
                          onChange={(e) => setExecutionConfig({
                            ...executionConfig,
                            max_calls_per_day: parseInt(e.target.value) || 1000
                          })}
                        />
                      </div>
                      <div className="form-control">
                        <label className="label">
                          <span className="label-text text-sm">并发调用限制</span>
                        </label>
                        <input
                          type="number"
                          className="input input-bordered input-sm"
                          placeholder="3"
                          min="1"
                          max="10"
                          value={executionConfig.concurrent_limit}
                          onChange={(e) => setExecutionConfig({
                            ...executionConfig,
                            concurrent_limit: parseInt(e.target.value) || 3
                          })}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-between">
              <button
                className="btn btn-outline"
                onClick={() => setCurrentStep(2)}
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

        {/* 第四步：执行监控 */}
        {currentStep === 4 && (
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
                  <div className="flex items-center justify-between mb-4">
                    <h5 className="font-medium">执行日志</h5>
                    <div className="flex items-center gap-3">
                      {/* 日志级别过滤 */}
                      <select 
                        className="select select-bordered select-sm"
                        value={logLevel}
                        onChange={(e) => setLogLevel(e.target.value)}
                      >
                        <option value="">全部级别</option>
                        <option value="info">信息</option>
                        <option value="warning">警告</option>
                        <option value="error">错误</option>
                        <option value="debug">调试</option>
                      </select>
                      
                      {/* 自动刷新控制 */}
                      <label className="cursor-pointer label">
                        <span className="label-text text-sm mr-2">自动刷新</span>
                        <input
                          type="checkbox"
                          className="checkbox checkbox-primary checkbox-sm"
                          checked={autoRefreshLogs}
                          onChange={(e) => setAutoRefreshLogs(e.target.checked)}
                        />
                      </label>
                      
                      {/* 手动刷新 */}
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={loadExecutionLogs}
                        disabled={isExecuting && autoRefreshLogs}
                      >
                        🔄 刷新
                      </button>
                    </div>
                  </div>
                  
                  <div className="bg-base-100 rounded p-4 max-h-80 overflow-y-auto">
                    {executionLogs.length > 0 ? (
                      <div className="space-y-1">
                        {executionLogs.map((log, index) => (
                          <div key={index} className="text-sm font-mono">
                            <span className="text-base-content/50 text-xs">[{formatTime(log.timestamp)}]</span>
                            <span className={`ml-2 font-medium text-xs px-2 py-1 rounded ${
                              log.level === 'error' ? 'bg-error/20 text-error' :
                              log.level === 'warning' ? 'bg-warning/20 text-warning' :
                              log.level === 'info' ? 'bg-info/20 text-info' : 
                              log.level === 'debug' ? 'bg-base-300 text-base-content' : 'bg-base-300'
                            }`}>
                              {log.level?.toUpperCase()}
                            </span>
                            <span className="ml-2 text-primary font-medium">[{log.stage}]</span>
                            <span className="ml-2">{log.message}</span>
                            {log.progress && (
                              <span className="ml-2 text-success">({log.progress.toFixed(1)}%)</span>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center text-base-content/60 py-8">
                        {isExecuting ? (
                          <div className="flex flex-col items-center">
                            <div className="loading loading-spinner loading-md mb-2"></div>
                            <span>正在加载日志...</span>
                          </div>
                        ) : (
                          <span>暂无日志数据</span>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {/* 日志统计 */}
                  {executionLogs.length > 0 && (
                    <div className="text-xs text-base-content/70 mt-2">
                      共 {executionLogs.length} 条日志
                      {logLevel && ` (${logLevel} 级别)`}
                      {autoRefreshLogs && isExecuting && (
                        <span className="ml-2 text-info">• 自动刷新中</span>
                      )}
                    </div>
                  )}
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