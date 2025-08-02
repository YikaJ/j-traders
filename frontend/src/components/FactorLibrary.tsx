import React, { useState, useEffect } from 'react';
import { ChartBarIcon, PlusIcon } from '@heroicons/react/24/outline';
import { factorApi, Factor, SelectedFactor } from '../services/api';
import FactorSearch from './FactorSearch';
import FactorCategoryFilter from './FactorCategoryFilter';
import FactorGrid from './FactorGrid';
import FactorDetailModal from './FactorDetailModal';
import FactorFormulaModal from './FactorFormulaModal';
import FactorEditModal from './FactorEditModal';
import FactorCreateModal from './FactorCreateModal';
import FactorHistoryModal from './FactorHistoryModal';

interface FactorLibraryProps {
  onFactorSelect?: (factor: SelectedFactor) => void;
  selectedFactors?: SelectedFactor[];
  mode?: 'selection' | 'browse';
}

const FactorLibrary: React.FC<FactorLibraryProps> = ({
  onFactorSelect,
  selectedFactors = [],
  mode = 'browse'
}) => {
  const [factors, setFactors] = useState<Factor[]>([]);
  const [filteredFactors, setFilteredFactors] = useState<Factor[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFactor, setSelectedFactor] = useState<Factor | null>(null);
  
  // 模态框状态
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showFormulaModal, setShowFormulaModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);

  // 加载因子数据
  const loadFactors = async () => {
    try {
      setLoading(true);
      const [factorsData, categoriesData] = await Promise.all([
        factorApi.getFactors(),
        factorApi.getFactorCategories()
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

  // 检查因子是否已选择
  const isFactorSelected = (factorId: string) => {
    return selectedFactors.some(f => f.factor_id === factorId);
  };

  // 处理因子选择
  const handleFactorSelect = (factor: Factor) => {
    if (!onFactorSelect) return;

    const selectedFactorConfig: SelectedFactor = {
      factor_id: factor.factor_id,
      name: factor.display_name,
      parameters: factor.default_parameters || {},
      weight: 0,
      is_enabled: true
    };

    onFactorSelect(selectedFactorConfig);
  };

  // 处理因子操作
  const handleFactorAction = (action: string, factor: Factor) => {
    setSelectedFactor(factor);
    
    switch (action) {
      case 'detail':
        setShowDetailModal(true);
        break;
      case 'formula':
        setShowFormulaModal(true);
        break;
      case 'edit':
        setShowEditModal(true);
        break;
      case 'history':
        setShowHistoryModal(true);
        break;
      case 'select':
        handleFactorSelect(factor);
        break;
    }
  };

  // 处理创建新因子
  const handleCreateFactor = () => {
    setShowCreateModal(true);
  };

  // 处理因子更新
  const handleFactorUpdate = async () => {
    await loadFactors();
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
        {/* 标题栏 */}
        <div className="flex justify-between items-center mb-4">
          <h2 className="card-title text-xl">
            <ChartBarIcon className="w-6 h-6" />
            统一因子库
          </h2>
          <div className="flex items-center gap-2">
            <div className="badge badge-info">
              共 {factors.length} 个因子
            </div>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleCreateFactor}
            >
              <PlusIcon className="w-4 h-4" />
              新增因子
            </button>
          </div>
        </div>

        {/* 搜索和过滤 */}
        <div className="flex flex-col lg:flex-row gap-4 mb-6">
          <FactorSearch
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
          />
          <FactorCategoryFilter
            categories={categories}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
            factors={factors}
          />
        </div>

        {/* 因子网格 */}
        <FactorGrid
          factors={filteredFactors}
          selectedFactors={selectedFactors}
          mode={mode}
          onFactorAction={handleFactorAction}
          isFactorSelected={isFactorSelected}
        />

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

      {/* 模态框组件 */}
      {selectedFactor && (
        <>
          <FactorDetailModal
            factor={selectedFactor}
            isOpen={showDetailModal}
            onClose={() => setShowDetailModal(false)}
            onAction={handleFactorAction}
            mode={mode}
            isSelected={isFactorSelected(selectedFactor.factor_id)}
          />

          <FactorFormulaModal
            factor={selectedFactor}
            isOpen={showFormulaModal}
            onClose={() => setShowFormulaModal(false)}
            onAction={handleFactorAction}
            mode={mode}
            isSelected={isFactorSelected(selectedFactor.factor_id)}
          />

          <FactorEditModal
            factor={selectedFactor}
            isOpen={showEditModal}
            onClose={() => setShowEditModal(false)}
            onUpdate={handleFactorUpdate}
          />

          <FactorHistoryModal
            factor={selectedFactor}
            isOpen={showHistoryModal}
            onClose={() => setShowHistoryModal(false)}
          />
        </>
      )}

      <FactorCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreated={handleFactorUpdate}
      />
    </div>
  );
};

export default FactorLibrary; 