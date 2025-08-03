import React, { useState, useEffect } from 'react';
import { PlusIcon, PlayIcon, PencilIcon, TrashIcon, EyeIcon } from '@heroicons/react/24/outline';
import { strategyManagementApi, Strategy, StrategyListResponse } from '../services/api';
import StrategyCreateModal from '../components/StrategyCreateModal';
import StrategyExecutionModal from '../components/StrategyExecutionModal';

const StrategyManagement: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [keyword, setKeyword] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showExecutionModal, setShowExecutionModal] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);

  // 加载策略列表
  useEffect(() => {
    loadStrategies();
  }, [currentPage, keyword]);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      const response: StrategyListResponse = await strategyManagementApi.getStrategies({
        keyword: keyword || undefined,
        skip: (currentPage - 1) * pageSize,
        limit: pageSize
      });
      
      setStrategies(response.strategies);
      setTotal(response.total);
    } catch (error) {
      console.error('加载策略列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 执行策略
  const handleExecuteStrategy = (strategy: Strategy) => {
    setSelectedStrategy(strategy);
    setShowExecutionModal(true);
  };

  // 查看策略详情
  const handleViewStrategy = (strategy: Strategy) => {
    setSelectedStrategy(strategy);
    setShowExecutionModal(true);
  };

  // 删除策略
  const handleDeleteStrategy = async (strategy: Strategy) => {
    if (!confirm(`确定要删除策略"${strategy.name}"吗？此操作不可撤销。`)) {
      return;
    }
    
    try {
      await strategyManagementApi.deleteStrategy(strategy.strategy_id);
      alert('策略删除成功');
      loadStrategies(); // 刷新列表
    } catch (error) {
      console.error('删除策略失败:', error);
      alert('删除策略失败，请重试');
    }
  };

  // 格式化时间
  const formatDateTime = (dateTime: string) => {
    return new Date(dateTime).toLocaleString('zh-CN');
  };

  // 渲染策略卡片
  const renderStrategyCard = (strategy: Strategy) => (
    <div key={strategy.strategy_id} className="card bg-base-100 shadow-md border border-base-300">
      <div className="card-body">
        {/* 策略头部信息 */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h3 className="card-title text-lg">{strategy.name}</h3>
            {strategy.description && (
              <p className="text-base-content/70 text-sm mt-1">{strategy.description}</p>
            )}
          </div>
          <div className={`badge ${strategy.is_active ? 'badge-success' : 'badge-error'}`}>
            {strategy.is_active ? '启用' : '禁用'}
          </div>
        </div>

        {/* 因子信息 */}
        <div className="mb-4">
          <h4 className="font-semibold text-sm mb-2">
            因子配置 ({strategy.factors.length})
          </h4>
          <div className="flex flex-wrap gap-2">
            {strategy.factors.slice(0, 3).map((factor) => (
              <div key={factor.factor_id} className="badge badge-outline badge-sm">
                {factor.factor_name}
                {factor.is_enabled && (
                  <span className="ml-1 text-xs">({(factor.weight * 100).toFixed(1)}%)</span>
                )}
              </div>
            ))}
            {strategy.factors.length > 3 && (
              <div className="badge badge-ghost badge-sm">
                +{strategy.factors.length - 3}
              </div>
            )}
          </div>
        </div>

        {/* 统计信息 */}
        <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
          <div>
            <span className="text-base-content/70">执行次数:</span>
            <span className="ml-2 font-medium">{strategy.execution_count}</span>
          </div>
          <div>
            <span className="text-base-content/70">最大选股:</span>
            <span className="ml-2 font-medium">{strategy.config?.max_results || 50}</span>
          </div>
          {strategy.last_executed_at && (
            <div className="col-span-2">
              <span className="text-base-content/70">最后执行:</span>
              <span className="ml-2 font-medium">{formatDateTime(strategy.last_executed_at)}</span>
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="card-actions justify-end">
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => handleViewStrategy(strategy)}
            title="查看详情"
          >
            <EyeIcon className="w-4 h-4" />
          </button>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => {/* TODO: 编辑策略 */}}
            title="编辑策略"
          >
            <PencilIcon className="w-4 h-4" />
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={() => handleExecuteStrategy(strategy)}
            disabled={!strategy.is_active}
            title="执行策略"
          >
            <PlayIcon className="w-4 h-4" />
          </button>
          <button
            className="btn btn-error btn-sm"
            onClick={() => handleDeleteStrategy(strategy)}
            title="删除策略"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto p-6">
      {/* 页面头部 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-base-content">策略管理</h1>
          <p className="text-base-content/70 mt-1">创建和管理量化选股策略</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          创建策略
        </button>
      </div>

      {/* 搜索和筛选 */}
      <div className="card bg-base-100 shadow-sm border border-base-300 mb-6">
        <div className="card-body">
          <div className="flex gap-4 items-center">
            <div className="form-control flex-1">
              <input
                type="text"
                placeholder="搜索策略名称或描述..."
                className="input input-bordered"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
              />
            </div>
            <button
              className="btn btn-outline"
              onClick={() => loadStrategies()}
            >
              搜索
            </button>
          </div>
        </div>
      </div>

      {/* 统计信息 */}
      <div className="stats shadow mb-6">
        <div className="stat">
          <div className="stat-title">总策略数</div>
          <div className="stat-value text-primary">{total}</div>
        </div>
        <div className="stat">
          <div className="stat-title">启用策略</div>
          <div className="stat-value text-success">
            {strategies.filter(s => s.is_active).length}
          </div>
        </div>
        <div className="stat">
          <div className="stat-title">总执行次数</div>
          <div className="stat-value">
            {strategies.reduce((sum, s) => sum + s.execution_count, 0)}
          </div>
        </div>
      </div>

      {/* 策略列表 */}
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <span className="loading loading-spinner loading-lg"></span>
        </div>
      ) : strategies.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-base-content/60 mb-4">
            {keyword ? '未找到匹配的策略' : '还没有创建任何策略'}
          </div>
          {!keyword && (
            <button
              className="btn btn-primary"
              onClick={() => setShowCreateModal(true)}
            >
              <PlusIcon className="w-5 h-5 mr-2" />
              创建第一个策略
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {strategies.map(renderStrategyCard)}
          </div>

          {/* 分页 */}
          {total > pageSize && (
            <div className="flex justify-center mt-8">
              <div className="btn-group">
                <button
                  className="btn"
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  上一页
                </button>
                <button className="btn btn-active">
                  {currentPage}
                </button>
                <button
                  className="btn"
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage * pageSize >= total}
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* 策略创建模态框 */}
      <StrategyCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreated={() => {
          loadStrategies();
        }}
      />

      {/* 策略执行模态框 */}
      <StrategyExecutionModal
        isOpen={showExecutionModal}
        onClose={() => {
          setShowExecutionModal(false);
          setSelectedStrategy(null);
        }}
        strategy={selectedStrategy}
        onExecuted={() => {
          loadStrategies();
        }}
      />
    </div>
  );
};

export default StrategyManagement;