import React from 'react';
import { Factor } from '../services/api';

interface FactorCategoryFilterProps {
  categories: string[];
  selectedCategory: string;
  onCategoryChange: (category: string) => void;
  factors: Factor[];
}

const FactorCategoryFilter: React.FC<FactorCategoryFilterProps> = ({
  categories,
  selectedCategory,
  onCategoryChange,
  factors
}) => {
  // 获取分类统计
  const getCategoryStats = () => {
    const stats: { [key: string]: number } = {};
    factors.forEach(factor => {
      stats[factor.category] = (stats[factor.category] || 0) + 1;
    });
    return stats;
  };

  const categoryStats = getCategoryStats();

  return (
    <div className="form-control">
      <select
        className="select select-bordered w-full lg:w-48"
        value={selectedCategory}
        onChange={(e) => onCategoryChange(e.target.value)}
      >
        <option value="all">全部分类</option>
        {categories.map((category) => (
          <option key={category} value={category}>
            {getCategoryDisplayName(category)} ({categoryStats[category] || 0})
          </option>
        ))}
      </select>
    </div>
  );
};

// 获取分类显示名称
const getCategoryDisplayName = (category: string): string => {
  const categoryMap: { [key: string]: string } = {
    'trend': '趋势类',
    'momentum': '动量类', 
    'volatility': '波动率类',
    'value': '价值类',
    'volume': '成交量类',
    'alpha101': 'Alpha101基础因子',
    'alpha101_extended': 'Alpha101扩展因子',
    'alpha101_more_factors': 'Alpha101增强因子',
    'alpha101_phase2': 'Alpha101进阶因子',
    'alpha101_phase3': 'Alpha101高级因子',
    'alpha101_phase4': 'Alpha101专家因子',
    'parametric': '参数化因子',
    'custom': '自定义因子'
  };
  return categoryMap[category] || category;
};

export default FactorCategoryFilter; 