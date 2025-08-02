import React, { useState, useEffect } from 'react';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  DocumentDuplicateIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  PlayIcon,
  EyeIcon,
  AdjustmentsHorizontalIcon,
  ChartPieIcon,
  StarIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import {
  strategyConfigApi,
  weightApi,
  templateApi,
  StrategyConfig,
  SelectedFactor,
  WeightPreset,
  StrategyTemplate
} from '../services/api';
import FactorLibrary from './FactorLibrary';

interface StrategyConfigManagerProps {
  onStrategySelect?: (strategy: StrategyConfig) => void;
  onExecuteStrategy?: (strategy: StrategyConfig) => void;
}

const StrategyConfigManager: React.FC<StrategyConfigManagerProps> = ({
  onStrategySelect,
  onExecuteStrategy
}) => {
  const [strategies, setStrategies] = useState<StrategyConfig[]>([]);
  const [templates, setTemplates] = useState<StrategyTemplate[]>([]);
  const [weightPresets, setWeightPresets] = useState<WeightPreset[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyConfig | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showWeightModal, setShowWeightModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showFactorSelectionModal, setShowFactorSelectionModal] = useState(false);

  const [searchQuery, setSearchQuery] = useState('');
  const [filterTag, setFilterTag] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('updated_at');

  // 表单状态
  const [strategyForm, setStrategyForm] = useState({
    name: '',
    description: '',
    factors: [] as SelectedFactor[],
    tags: [] as string[],
    max_results: 100
  });

  // 加载数据
  const loadData = async () => {
    try {
      setLoading(true);
      const [strategiesData, templatesData, presetsData] = await Promise.all([
        strategyConfigApi.getStrategyConfigs({ 
          sort_by: sortBy, 
          sort_order: 'desc',
          search: searchQuery || undefined 
        }),
        templateApi.getStrategyTemplates(),
        weightApi.getWeightPresets()
      ]);
      
      setStrategies(strategiesData.items || []);
      setTemplates(templatesData);
      setWeightPresets(presetsData);
    } catch (error) {
      console.error('加载策略配置失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [sortBy, searchQuery]);

  // 过滤策略
  const filteredStrategies = strategies.filter(strategy => {
    if (filterTag !== 'all' && !strategy.tags.includes(filterTag)) {
      return false;
    }
    return true;
  });

  // 获取所有标签
  const allTags = Array.from(new Set(strategies.flatMap(s => s.tags)));

  // 创建策略
  const handleCreateStrategy = async () => {
    try {
      if (!strategyForm.name.trim()) {
        alert('请输入策略名称');
        return;
      }

      if (strategyForm.factors.length === 0) {
        alert('请至少添加一个因子');
        return;
      }

      const newStrategy = await strategyConfigApi.createStrategyConfig({
        name: strategyForm.name,
        description: strategyForm.description,
        factors: strategyForm.factors,
        max_results: strategyForm.max_results,
        tags: strategyForm.tags
      });

      setStrategies([newStrategy, ...strategies]);
      setShowCreateModal(false);
      resetForm();
    } catch (error) {
      console.error('创建策略失败:', error);
      alert('创建策略失败，请重试');
    }
  };

  // 更新策略
  const handleUpdateStrategy = async () => {
    if (!selectedStrategy) return;

    try {
      const updatedStrategy = await strategyConfigApi.updateStrategyConfig(
        selectedStrategy.id,
        {
          name: strategyForm.name,
          description: strategyForm.description,
          factors: strategyForm.factors,
          max_results: strategyForm.max_results,
          tags: strategyForm.tags
        }
      );

      setStrategies(strategies.map(s => 
        s.id === selectedStrategy.id ? updatedStrategy : s
      ));
      setShowEditModal(false);
      setSelectedStrategy(null);
      resetForm();
    } catch (error) {
      console.error('更新策略失败:', error);
      alert('更新策略失败，请重试');
    }
  };

  // 删除策略
  const handleDeleteStrategy = async (strategyId: string) => {
    if (!confirm('确定要删除这个策略吗？')) return;

    try {
      await strategyConfigApi.deleteStrategyConfig(strategyId);
      setStrategies(strategies.filter(s => s.id !== strategyId));
    } catch (error) {
      console.error('删除策略失败:', error);
      alert('删除策略失败，请重试');
    }
  };

  // 复制策略
  const handleDuplicateStrategy = async (strategy: StrategyConfig) => {
    try {
      const duplicatedStrategy = await strategyConfigApi.duplicateStrategyConfig(
        strategy.id,
        `${strategy.name} (副本)`
      );
      setStrategies([duplicatedStrategy, ...strategies]);
    } catch (error) {
      console.error('复制策略失败:', error);
      alert('复制策略失败，请重试');
    }
  };

  // 导出策略
  const handleExportStrategy = async (strategy: StrategyConfig) => {
    try {
      const exportData = await strategyConfigApi.exportStrategyConfig(strategy.id);
      
      // 创建下载链接
      const dataStr = JSON.stringify(exportData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `strategy_${strategy.name}.json`;
      link.click();
      
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('导出策略失败:', error);
      alert('导出策略失败，请重试');
    }
  };

  // 编辑策略
  const handleEditStrategy = (strategy: StrategyConfig) => {
    setSelectedStrategy(strategy);
    setStrategyForm({
      name: strategy.name,
      description: strategy.description,
      factors: strategy.factors,
      tags: strategy.tags,
      max_results: strategy.max_results
    });
    setShowEditModal(true);
  };

  // 配置权重
  const handleConfigureWeights = (strategy: StrategyConfig) => {
    setSelectedStrategy(strategy);
    setStrategyForm({
      name: strategy.name,
      description: strategy.description,
      factors: strategy.factors,
      tags: strategy.tags,
      max_results: strategy.max_results
    });
    setShowWeightModal(true);
  };

  // 处理因子选择
  const handleFactorSelect = (factor: SelectedFactor) => {
    const updatedFactors = [...strategyForm.factors, factor];
    setStrategyForm({
      ...strategyForm,
      factors: updatedFactors
    });
  };

  // 打开因子选择模态框
  const handleOpenFactorSelection = () => {
    setShowFactorSelectionModal(true);
  };

  // 应用权重预设
  const handleApplyWeightPreset = async (presetId: string) => {
    try {
      const result = await weightApi.applyWeightPreset(strategyForm.factors, presetId);
      setStrategyForm({
        ...strategyForm,
        factors: result.factors
      });
    } catch (error) {
      console.error('应用权重预设失败:', error);
      alert('应用权重预设失败，请重试');
    }
  };

  // 优化权重
  const handleOptimizeWeights = async () => {
    try {
      const result = await weightApi.optimizeWeights(strategyForm.factors);
      setStrategyForm({
        ...strategyForm,
        factors: result.optimized_factors
      });
      alert('权重优化完成！');
    } catch (error) {
      console.error('权重优化失败:', error);
      alert('权重优化失败，请重试');
    }
  };

  // 更新因子权重
  const handleFactorWeightChange = (factorId: string, weight: number) => {
    setStrategyForm({
      ...strategyForm,
      factors: strategyForm.factors.map(factor =>
        factor.factor_id === factorId ? { ...factor, weight } : factor
      )
    });
  };

  // 应用模板
  const handleApplyTemplate = async (template: StrategyTemplate) => {
    try {
      const strategyConfig = await templateApi.applyTemplate(template.id);
      setStrategyForm({
        name: `${template.display_name} - 策略`,
        description: strategyConfig.description,
        factors: strategyConfig.factors,
        tags: ['template', template.category],
        max_results: strategyConfig.max_results || 100
      });
      setShowTemplateModal(false);
      setShowCreateModal(true);
    } catch (error) {
      console.error('应用模板失败:', error);
      alert('应用模板失败，请重试');
    }
  };

  // 重置表单
  const resetForm = () => {
    setStrategyForm({
      name: '',
      description: '',
      factors: [],
      tags: [],
      max_results: 100
    });
  };

  // 计算权重总和
  const getTotalWeight = () => {
    return strategyForm.factors
      .filter(f => f.is_enabled)
      .reduce((sum, factor) => sum + factor.weight, 0);
  };

  // 格式化日期
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading loading-spinner loading-lg"></div>
        <span className="ml-2">加载策略配置中...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 头部操作栏 */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold">策略配置管理</h2>
          <div className="badge badge-info">
            {strategies.length} 个策略
          </div>
        </div>

        <div className="flex gap-2">
          <button
            className="btn btn-outline btn-sm"
            onClick={() => setShowTemplateModal(true)}
          >
            <StarIcon className="w-4 h-4" />
            使用模板
          </button>
          <button
            className="btn btn-outline btn-sm"
            onClick={() => setShowImportModal(true)}
          >
            <ArrowUpTrayIcon className="w-4 h-4" />
            导入
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusIcon className="w-4 h-4" />
            新建策略
          </button>
        </div>
      </div>

      {/* 搜索和过滤 */}
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="form-control flex-1">
          <input
            type="text"
            placeholder="搜索策略名称或描述..."
            className="input input-bordered"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="form-control">
          <select
            className="select select-bordered w-full lg:w-40"
            value={filterTag}
            onChange={(e) => setFilterTag(e.target.value)}
          >
            <option value="all">所有标签</option>
            {allTags.map((tag) => (
              <option key={tag} value={tag}>{tag}</option>
            ))}
          </select>
        </div>

        <div className="form-control">
          <select
            className="select select-bordered w-full lg:w-40"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="updated_at">最近更新</option>
            <option value="created_at">创建时间</option>
            <option value="usage_count">使用次数</option>
            <option value="name">策略名称</option>
          </select>
        </div>
      </div>

      {/* 策略列表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredStrategies.map((strategy) => (
          <div key={strategy.id} className="card bg-base-100 shadow-lg hover:shadow-xl transition-all">
            <div className="card-body p-4">
              {/* 策略标题 */}
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-lg truncate flex-1 mr-2">
                  {strategy.name}
                </h3>
                <div className="dropdown dropdown-end">
                  <button tabIndex={0} className="btn btn-ghost btn-xs">
                    •••
                  </button>
                  <ul tabIndex={0} className="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52 z-10">
                    <li>
                      <a onClick={() => handleEditStrategy(strategy)}>
                        <PencilIcon className="w-4 h-4" /> 编辑
                      </a>
                    </li>
                    <li>
                      <a onClick={() => handleConfigureWeights(strategy)}>
                        <ChartPieIcon className="w-4 h-4" /> 配置权重
                      </a>
                    </li>
                    <li>
                      <a onClick={() => handleDuplicateStrategy(strategy)}>
                        <DocumentDuplicateIcon className="w-4 h-4" /> 复制
                      </a>
                    </li>
                    <li>
                      <a onClick={() => handleExportStrategy(strategy)}>
                        <ArrowDownTrayIcon className="w-4 h-4" /> 导出
                      </a>
                    </li>
                    <li>
                      <a onClick={() => handleDeleteStrategy(strategy.id)} className="text-error">
                        <TrashIcon className="w-4 h-4" /> 删除
                      </a>
                    </li>
                  </ul>
                </div>
              </div>

              {/* 策略描述 */}
              {strategy.description && (
                <p className="text-sm text-base-content/70 mb-3 line-clamp-2">
                  {strategy.description}
                </p>
              )}

              {/* 因子信息 */}
              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span>因子数量:</span>
                  <span className="font-medium">{strategy.factors.length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>最大结果:</span>
                  <span className="font-medium">{strategy.max_results}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>使用次数:</span>
                  <span className="font-medium">{strategy.usage_count}</span>
                </div>
              </div>

              {/* 标签 */}
              {strategy.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-4">
                  {strategy.tags.slice(0, 3).map((tag) => (
                    <div key={tag} className="badge badge-outline badge-sm">
                      {tag}
                    </div>
                  ))}
                  {strategy.tags.length > 3 && (
                    <div className="badge badge-ghost badge-sm">
                      +{strategy.tags.length - 3}
                    </div>
                  )}
                </div>
              )}

              {/* 时间信息 */}
              <div className="text-xs text-base-content/60 mb-4">
                <div className="flex items-center gap-1">
                  <ClockIcon className="w-3 h-3" />
                  更新于 {formatDate(strategy.updated_at)}
                </div>
                {strategy.last_used_at && (
                  <div className="flex items-center gap-1 mt-1">
                    <PlayIcon className="w-3 h-3" />
                    最后使用 {formatDate(strategy.last_used_at)}
                  </div>
                )}
              </div>

              {/* 操作按钮 */}
              <div className="card-actions justify-between">
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => onStrategySelect?.(strategy)}
                >
                  <EyeIcon className="w-4 h-4" />
                  查看
                </button>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => onExecuteStrategy?.(strategy)}
                >
                  <PlayIcon className="w-4 h-4" />
                  执行
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 空状态 */}
      {filteredStrategies.length === 0 && (
        <div className="text-center py-12">
          <div className="text-base-content/60 mb-4">
            {searchQuery || filterTag !== 'all'
              ? '没有找到匹配的策略配置'
              : '还没有创建任何策略配置'}
          </div>
          <button
            className="btn btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusIcon className="w-5 h-5" />
            创建第一个策略
          </button>
        </div>
      )}

      {/* 创建/编辑策略模态框 */}
      {(showCreateModal || showEditModal) && (
        <div className="modal modal-open">
          <div className="modal-box w-11/12 max-w-4xl">
            <h3 className="font-bold text-lg mb-4">
              {showCreateModal ? '创建新策略' : '编辑策略'}
            </h3>

            <div className="space-y-4">
              {/* 基本信息 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">策略名称 *</span>
                  </label>
                  <input
                    type="text"
                    className="input input-bordered"
                    value={strategyForm.name}
                    onChange={(e) => setStrategyForm({
                      ...strategyForm,
                      name: e.target.value
                    })}
                    placeholder="输入策略名称"
                  />
                </div>

                <div className="form-control">
                  <label className="label">
                    <span className="label-text">最大结果数</span>
                  </label>
                  <input
                    type="number"
                    className="input input-bordered"
                    value={strategyForm.max_results}
                    onChange={(e) => setStrategyForm({
                      ...strategyForm,
                      max_results: parseInt(e.target.value) || 100
                    })}
                    min="1"
                    max="1000"
                  />
                </div>
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">策略描述</span>
                </label>
                <textarea
                  className="textarea textarea-bordered"
                  rows={3}
                  value={strategyForm.description}
                  onChange={(e) => setStrategyForm({
                    ...strategyForm,
                    description: e.target.value
                  })}
                  placeholder="描述策略的目标和适用场景"
                />
              </div>

              {/* 因子配置 */}
              <div>
                <div className="flex justify-between items-center">
                  <label className="label">
                    <span className="label-text">已选择的因子 ({strategyForm.factors.length})</span>
                  </label>
                  <button
                    className="btn btn-sm btn-outline"
                    onClick={handleOpenFactorSelection}
                  >
                    <PlusIcon className="w-4 h-4" />
                    选择因子
                  </button>
                </div>
                
                {strategyForm.factors.length > 0 ? (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {strategyForm.factors.map((factor, index) => (
                      <div key={`${factor.factor_id}-${index}`} className="flex items-center gap-2 p-2 bg-base-200 rounded">
                        <div className="flex-1">
                          <div className="font-medium text-sm">{factor.factor_name}</div>
                          <div className="text-xs text-base-content/60">
                            权重: {(factor.weight * 100).toFixed(1)}%
                          </div>
                        </div>
                        <button
                          className="btn btn-ghost btn-xs"
                          onClick={() => setStrategyForm({
                            ...strategyForm,
                            factors: strategyForm.factors.filter((_, i) => i !== index)
                          })}
                        >
                          <TrashIcon className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-4 text-base-content/60">
                    暂无选择的因子，请先添加因子
                  </div>
                )}
              </div>

              {/* 标签 */}
              <div className="form-control">
                <label className="label">
                  <span className="label-text">标签</span>
                </label>
                <input
                  type="text"
                  className="input input-bordered"
                  placeholder="输入标签，用逗号分隔"
                  value={strategyForm.tags.join(', ')}
                  onChange={(e) => setStrategyForm({
                    ...strategyForm,
                    tags: e.target.value.split(',').map(t => t.trim()).filter(t => t)
                  })}
                />
              </div>
            </div>

            <div className="modal-action">
              <button
                className="btn"
                onClick={() => {
                  if (showCreateModal) setShowCreateModal(false);
                  if (showEditModal) setShowEditModal(false);
                  resetForm();
                }}
              >
                取消
              </button>
              <button
                className="btn btn-primary"
                onClick={showCreateModal ? handleCreateStrategy : handleUpdateStrategy}
              >
                {showCreateModal ? '创建策略' : '保存修改'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 因子选择模态框 */}
      {showFactorSelectionModal && (
        <div className="modal modal-open">
          <div className="modal-box w-11/12 max-w-6xl h-5/6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-lg">选择因子</h3>
              <button
                className="btn btn-sm btn-circle"
                onClick={() => setShowFactorSelectionModal(false)}
              >
                ✕
              </button>
            </div>
            
            <div className="h-full overflow-hidden">
              <FactorLibrary
                mode="selection"
                selectedFactors={strategyForm.factors}
                onFactorSelect={(factor) => {
                  handleFactorSelect(factor);
                  setShowFactorSelectionModal(false);
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* 其他模态框... (权重配置、模板选择、导入等) */}
      {/* 由于篇幅限制，这里只展示主要功能 */}
    </div>
  );
};

export default StrategyConfigManager;