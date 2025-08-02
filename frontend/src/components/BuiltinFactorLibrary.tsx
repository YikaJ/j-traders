import React, { useState, useEffect } from 'react';
import {
  FunnelIcon,
  MagnifyingGlassIcon,
  InformationCircleIcon,
  ChartBarIcon,
  EyeIcon,
  PlusIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import { builtinFactorApi, BuiltinFactor, FactorParameters, SelectedFactor } from '../services/api';

interface BuiltinFactorLibraryProps {
  onFactorSelect?: (factor: SelectedFactor) => void;
  selectedFactors?: SelectedFactor[];
  mode?: 'selection' | 'browse';
}

const BuiltinFactorLibrary: React.FC<BuiltinFactorLibraryProps> = ({
  onFactorSelect,
  selectedFactors = [],
  mode = 'browse'
}) => {
  const [factors, setFactors] = useState<BuiltinFactor[]>([]);
  const [filteredFactors, setFilteredFactors] = useState<BuiltinFactor[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFactor, setSelectedFactor] = useState<BuiltinFactor | null>(null);
  const [showFactorModal, setShowFactorModal] = useState(false);
  const [showParameterModal, setShowParameterModal] = useState(false);
  const [parameterForm, setParameterForm] = useState<FactorParameters>({});

  // 加载因子数据
  const loadFactors = async () => {
    try {
      setLoading(true);
      const [factorsData, categoriesData] = await Promise.all([
        builtinFactorApi.getBuiltinFactors(),
        builtinFactorApi.getFactorCategories()
      ]);
      
      setFactors(factorsData);
      setFilteredFactors(factorsData);
      setCategories(categoriesData);
    } catch (error) {
      console.error('加载因子库失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFactors();
  }, []);

  // 过滤因子
  useEffect(() => {
    let filtered = factors;

    // 按分类过滤
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(f => f.category === selectedCategory);
    }

    // 按搜索关键词过滤
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(f =>
        f.display_name.toLowerCase().includes(query) ||
        f.description.toLowerCase().includes(query) ||
        f.name.toLowerCase().includes(query)
      );
    }

    setFilteredFactors(filtered);
  }, [factors, selectedCategory, searchQuery]);

  // 获取分类显示名称
  const getCategoryDisplayName = (category: string) => {
    const categoryMap: Record<string, string> = {
      'trend': '趋势类',
      'momentum': '动量类',
      'volume': '价量类'
    };
    return categoryMap[category] || category;
  };

  // 获取分类图标
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'trend':
        return '📈';
      case 'momentum':
        return '⚡';
      case 'volume':
        return '📊';
      default:
        return '📋';
    }
  };

  // 查看因子详情
  const handleViewFactor = (factor: BuiltinFactor) => {
    setSelectedFactor(factor);
    setShowFactorModal(true);
  };

  // 添加因子到策略
  const handleAddFactor = (factor: BuiltinFactor) => {
    setSelectedFactor(factor);
    setParameterForm(factor.default_parameters || {});
    setShowParameterModal(true);
  };

  // 确认添加因子
  const handleConfirmAddFactor = () => {
    if (!selectedFactor || !onFactorSelect) return;

    const selectedFactorConfig: SelectedFactor = {
      factor_id: selectedFactor.factor_id,
      factor_type: 'builtin',
      factor_name: selectedFactor.display_name,
      parameters: parameterForm,
      weight: 0, // 权重稍后设置
      is_enabled: true
    };

    onFactorSelect(selectedFactorConfig);
    setShowParameterModal(false);
    setParameterForm({});
  };

  // 检查因子是否已选择
  const isFactorSelected = (factorId: string) => {
    return selectedFactors.some(f => f.factor_id === factorId);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading loading-spinner loading-lg"></div>
        <span className="ml-2">加载因子库中...</span>
      </div>
    );
  }

  return (
    <div className="card bg-base-100 shadow-lg">
      <div className="card-body">
        <div className="flex justify-between items-center mb-4">
          <h2 className="card-title text-xl">
            <ChartBarIcon className="w-6 h-6" />
            内置因子库
          </h2>
          <div className="badge badge-info">
            共 {factors.length} 个因子
          </div>
        </div>

        {/* 搜索和过滤 */}
        <div className="flex flex-col lg:flex-row gap-4 mb-6">
          {/* 搜索框 */}
          <div className="form-control flex-1">
            <div className="input-group">
              <input
                type="text"
                placeholder="搜索因子名称或描述..."
                className="input input-bordered flex-1"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button className="btn btn-square">
                <MagnifyingGlassIcon className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* 分类筛选 */}
          <div className="form-control">
            <select
              className="select select-bordered w-full lg:w-48"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <option value="all">全部分类</option>
              {categories.map((cat) => (
                <option key={cat.name} value={cat.name}>
                  {getCategoryDisplayName(cat.name)} ({cat.count})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 因子分类统计 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {categories.map((category) => (
            <div
              key={category.name}
              className={`stat bg-base-200 rounded-lg cursor-pointer transition-all hover:bg-base-300 ${
                selectedCategory === category.name ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => setSelectedCategory(selectedCategory === category.name ? 'all' : category.name)}
            >
              <div className="stat-figure text-2xl">
                {getCategoryIcon(category.name)}
              </div>
              <div className="stat-title">{getCategoryDisplayName(category.name)}</div>
              <div className="stat-value text-2xl">{category.count}</div>
              <div className="stat-desc">
                {category.factor_ids?.length || 0} 个可用因子
              </div>
            </div>
          ))}
        </div>

        {/* 因子列表 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredFactors.map((factor) => (
            <div
              key={factor.factor_id}
              className={`card bg-base-200 shadow-md hover:shadow-lg transition-all ${
                isFactorSelected(factor.factor_id) ? 'ring-2 ring-success' : ''
              }`}
            >
              <div className="card-body p-4">
                {/* 因子标题 */}
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-sm truncate flex-1">
                    {factor.display_name}
                  </h3>
                  <div className="flex gap-1 ml-2">
                    <div className={`badge badge-sm ${
                      factor.category === 'trend' ? 'badge-info' :
                      factor.category === 'momentum' ? 'badge-warning' :
                      factor.category === 'volume' ? 'badge-success' :
                      'badge-neutral'
                    }`}>
                      {getCategoryDisplayName(factor.category)}
                    </div>
                  </div>
                </div>

                {/* 因子描述 */}
                <p className="text-xs text-base-content/70 mb-3 line-clamp-2">
                  {factor.description}
                </p>

                {/* 因子信息 */}
                <div className="text-xs space-y-1 mb-3">
                  <div className="flex justify-between">
                    <span className="text-base-content/60">计算方法:</span>
                    <span className="badge badge-outline badge-xs">
                      {factor.calculation_method}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-base-content/60">输入字段:</span>
                    <span className="text-xs">
                      {factor.input_fields?.join(', ') || 'N/A'}
                    </span>
                  </div>
                </div>

                {/* 操作按钮 */}
                <div className="card-actions justify-between">
                  <button
                    className="btn btn-ghost btn-xs"
                    onClick={() => handleViewFactor(factor)}
                  >
                    <EyeIcon className="w-3 h-3" />
                    查看
                  </button>

                  {mode === 'selection' && (
                    <button
                      className={`btn btn-xs ${
                        isFactorSelected(factor.factor_id)
                          ? 'btn-success'
                          : 'btn-primary'
                      }`}
                      onClick={() => handleAddFactor(factor)}
                      disabled={isFactorSelected(factor.factor_id)}
                    >
                      {isFactorSelected(factor.factor_id) ? (
                        <>已选择</>
                      ) : (
                        <>
                          <PlusIcon className="w-3 h-3" />
                          添加
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 无结果提示 */}
        {filteredFactors.length === 0 && (
          <div className="text-center py-8">
            <div className="text-base-content/60">
              {searchQuery || selectedCategory !== 'all'
                ? '没有找到匹配的因子'
                : '暂无可用因子'}
            </div>
          </div>
        )}
      </div>

      {/* 因子详情模态框 */}
      {showFactorModal && selectedFactor && (
        <div className="modal modal-open">
          <div className="modal-box w-11/12 max-w-3xl">
            <h3 className="font-bold text-lg mb-4">
              因子详情 - {selectedFactor.display_name}
            </h3>

            <div className="space-y-4">
              {/* 基本信息 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">因子ID</span>
                  </label>
                  <div className="text-sm">{selectedFactor.factor_id}</div>
                </div>
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">分类</span>
                  </label>
                  <div className="badge badge-info">
                    {getCategoryDisplayName(selectedFactor.category)}
                  </div>
                </div>
              </div>

              {/* 描述 */}
              <div>
                <label className="label">
                  <span className="label-text font-semibold">描述</span>
                </label>
                <div className="text-sm bg-base-200 p-3 rounded">
                  {selectedFactor.description}
                </div>
              </div>

              {/* 计算公式 */}
              <div>
                <label className="label">
                  <span className="label-text font-semibold">计算公式</span>
                </label>
                <div className="mockup-code text-xs">
                  <pre><code>{selectedFactor.formula}</code></pre>
                </div>
              </div>

              {/* 默认参数 */}
              {selectedFactor.default_parameters && Object.keys(selectedFactor.default_parameters).length > 0 && (
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">默认参数</span>
                  </label>
                  <div className="overflow-x-auto">
                    <table className="table table-sm">
                      <thead>
                        <tr>
                          <th>参数名</th>
                          <th>默认值</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(selectedFactor.default_parameters).map(([key, value]) => (
                          <tr key={key}>
                            <td className="font-mono text-xs">{key}</td>
                            <td>{String(value)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            <div className="modal-action">
              <button
                className="btn"
                onClick={() => setShowFactorModal(false)}
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 参数配置模态框 */}
      {showParameterModal && selectedFactor && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg mb-4">
              配置因子参数 - {selectedFactor.display_name}
            </h3>

            <div className="space-y-4">
              {/* 通用参数 */}
              <div className="form-control">
                <label className="label">
                  <span className="label-text">周期 (period)</span>
                </label>
                <input
                  type="number"
                  className="input input-bordered"
                  placeholder="输入周期天数"
                  value={parameterForm.period || ''}
                  onChange={(e) => setParameterForm({
                    ...parameterForm,
                    period: e.target.value ? parseInt(e.target.value) : undefined
                  })}
                />
              </div>

              {/* 特殊参数 - MACD */}
              {selectedFactor.factor_id.includes('macd') && (
                <>
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">快速周期 (fast_period)</span>
                    </label>
                    <input
                      type="number"
                      className="input input-bordered"
                      placeholder="默认: 12"
                      value={parameterForm.fast_period || ''}
                      onChange={(e) => setParameterForm({
                        ...parameterForm,
                        fast_period: e.target.value ? parseInt(e.target.value) : undefined
                      })}
                    />
                  </div>

                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">慢速周期 (slow_period)</span>
                    </label>
                    <input
                      type="number"
                      className="input input-bordered"
                      placeholder="默认: 26"
                      value={parameterForm.slow_period || ''}
                      onChange={(e) => setParameterForm({
                        ...parameterForm,
                        slow_period: e.target.value ? parseInt(e.target.value) : undefined
                      })}
                    />
                  </div>

                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">信号周期 (signal_period)</span>
                    </label>
                    <input
                      type="number"
                      className="input input-bordered"
                      placeholder="默认: 9"
                      value={parameterForm.signal_period || ''}
                      onChange={(e) => setParameterForm({
                        ...parameterForm,
                        signal_period: e.target.value ? parseInt(e.target.value) : undefined
                      })}
                    />
                  </div>
                </>
              )}

              {/* 布林带参数 */}
              {selectedFactor.factor_id.includes('boll') && (
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">标准差倍数 (multiplier)</span>
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    className="input input-bordered"
                    placeholder="默认: 2.0"
                    value={parameterForm.multiplier || ''}
                    onChange={(e) => setParameterForm({
                      ...parameterForm,
                      multiplier: e.target.value ? parseFloat(e.target.value) : undefined
                    })}
                  />
                </div>
              )}

              {/* 参数说明 */}
              <div className="alert alert-info">
                <InformationCircleIcon className="w-5 h-5" />
                <span className="text-sm">
                  留空将使用默认参数。参数配置影响因子计算结果，请根据需要调整。
                </span>
              </div>
            </div>

            <div className="modal-action">
              <button
                className="btn"
                onClick={() => {
                  setShowParameterModal(false);
                  setParameterForm({});
                }}
              >
                取消
              </button>
              <button
                className="btn btn-primary"
                onClick={handleConfirmAddFactor}
              >
                添加因子
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BuiltinFactorLibrary;