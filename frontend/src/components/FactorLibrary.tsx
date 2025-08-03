import React, { useState, useEffect } from 'react';
import { ChartBarIcon, PlusIcon } from '@heroicons/react/24/outline';
import { factorApi, Factor, SelectedFactor, FactorTag } from '../services/api';
import FactorSearch from './FactorSearch';
import FactorGrid from './FactorGrid';
import FactorDetailModal from './FactorDetailModal';
import FactorFormulaModal from './FactorFormulaModal';
import FactorEditModal from './FactorEditModal';
import FactorEditModalImproved from './FactorEditModalImproved';
import FactorCreateModal from './FactorCreateModal';
import FactorCreateModalImproved from './FactorCreateModalImproved';
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
  const [tags, setTags] = useState<FactorTag[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
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
      const [factorsData, tagsData] = await Promise.all([
        factorApi.getFactors(),
        factorApi.getAllFactorTags()
      ]);
      
      setFactors(factorsData);
      setFilteredFactors(factorsData);
      setTags(tagsData);
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

    // 按标签过滤
    if (selectedTags.length > 0) {
      filtered = filtered.filter(f => {
        const factorTags = f.tags?.map(tag => tag.name) || [];
        return selectedTags.some(selectedTag => factorTags.includes(selectedTag));
      });
    }

    // 按搜索关键词过滤
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(f =>
        f.display_name.toLowerCase().includes(query) ||
        (f.description?.toLowerCase().includes(query) || false) ||
        f.name.toLowerCase().includes(query)
      );
    }

    setFilteredFactors(filtered);
  }, [factors, selectedTags, searchQuery]);

  // 检查因子是否已选择
  const isFactorSelected = (factorId: string) => {
    return selectedFactors.some(f => f.id === factorId);
  };

  // 处理因子选择
  const handleFactorSelect = (factor: Factor) => {
    if (onFactorSelect) {
      if (isFactorSelected(factor.id)) {
        // 取消选择：找到已选择的因子并移除
        const selectedFactor = selectedFactors.find(f => f.id === factor.id);
        if (selectedFactor) {
          onFactorSelect(selectedFactor);
        }
      } else {
        // 选择：创建新的 SelectedFactor 对象
        const newSelectedFactor: SelectedFactor = {
          id: factor.id,
          name: factor.name,
          display_name: factor.display_name,
          description: factor.description,
          tags: factor.tags || [],
          code: factor.code,
          weight: 1.0,
          is_enabled: true
        };
        onFactorSelect(newSelectedFactor);
      }
    }
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
      case 'remove':
        // 移除因子：通过调用 onFactorSelect 来取消选择
        if (onFactorSelect) {
          const selectedFactor = selectedFactors.find(f => f.id === factor.id);
          if (selectedFactor) {
            onFactorSelect(selectedFactor);
          }
        }
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
          {/* 标签过滤器 */}
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">标签过滤</span>
            </label>
            <select
              className="select select-bordered"
              value={selectedTags.length > 0 ? selectedTags[0] : 'all'}
              onChange={(e) => {
                const value = e.target.value;
                if (value === 'all') {
                  setSelectedTags([]);
                } else {
                  setSelectedTags([value]);
                }
              }}
            >
              <option value="all">所有标签</option>
              {tags.map(tag => (
                <option key={tag.id} value={tag.name}>
                  {tag.display_name}
                </option>
              ))}
            </select>
          </div>
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
              {searchQuery || selectedTags.length > 0
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
            isSelected={isFactorSelected(selectedFactor.id)}
          />

          <FactorFormulaModal
            factor={selectedFactor}
            isOpen={showFormulaModal}
            onClose={() => setShowFormulaModal(false)}
            onAction={handleFactorAction}
            mode={mode}
            isSelected={isFactorSelected(selectedFactor.id)}
          />

          <FactorEditModalImproved
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

      <FactorCreateModalImproved
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreated={handleFactorUpdate}
      />
    </div>
  );
};

export default FactorLibrary; 