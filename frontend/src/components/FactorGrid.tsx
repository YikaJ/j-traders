import React from 'react';
import { 
  EyeIcon, 
  InformationCircleIcon, 
  PencilIcon, 
  ClockIcon, 
  PlusIcon 
} from '@heroicons/react/24/outline';
import { Factor, SelectedFactor } from '../services/api';

interface FactorGridProps {
  factors: Factor[];
  selectedFactors: SelectedFactor[];
  mode: 'selection' | 'browse';
  onFactorAction: (action: string, factor: Factor) => void;
  isFactorSelected: (factorId: string) => boolean;
}

const FactorGrid: React.FC<FactorGridProps> = ({
  factors,
  selectedFactors,
  mode,
  onFactorAction,
  isFactorSelected
}) => {
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

  // 获取分类徽章样式
  const getCategoryBadgeClass = (category: string): string => {
    const badgeMap: { [key: string]: string } = {
      'trend': 'badge-info',
      'momentum': 'badge-warning',
      'volume': 'badge-success',
      'alpha101': 'badge-secondary',
      'alpha101_extended': 'badge-secondary',
      'alpha101_more_factors': 'badge-secondary',
      'alpha101_phase2': 'badge-secondary',
      'alpha101_phase3': 'badge-secondary',
      'alpha101_phase4': 'badge-secondary',
      'volatility': 'badge-accent',
      'value': 'badge-primary',
      'custom': 'badge-neutral'
    };
    return badgeMap[category] || 'badge-neutral';
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
      {factors.map((factor) => (
        <div
          key={factor.id}
          className={`card bg-base-200 shadow-md hover:shadow-lg transition-all ${
            isFactorSelected(factor.id) ? 'ring-2 ring-success' : ''
          }`}
        >
          <div className="card-body p-4">
            {/* 因子标题 */}
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-semibold text-sm truncate flex-1">
                {factor.display_name}
              </h3>
              <div className="flex gap-1 ml-2">
                <div className={`badge badge-sm ${getCategoryBadgeClass(factor.category)}`}>
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
              <div className="flex gap-1">
                <button
                  className="btn btn-ghost btn-xs"
                  onClick={() => onFactorAction('detail', factor)}
                  title="查看详情"
                >
                  <EyeIcon className="w-3 h-3" />
                  查看
                </button>
                <button
                  className="btn btn-ghost btn-xs"
                  onClick={() => onFactorAction('formula', factor)}
                  title="查看公式"
                >
                  <InformationCircleIcon className="w-3 h-3" />
                  公式
                </button>
                <button
                  className="btn btn-ghost btn-xs"
                  onClick={() => onFactorAction('edit', factor)}
                  title="编辑因子"
                >
                  <PencilIcon className="w-3 h-3" />
                  编辑
                </button>
                <button
                  className="btn btn-ghost btn-xs"
                  onClick={() => onFactorAction('history', factor)}
                  title="查看历史"
                >
                  <ClockIcon className="w-3 h-3" />
                  历史
                </button>
              </div>

              {mode === 'selection' && (
                <button
                  className={`btn btn-xs ${
                    isFactorSelected(factor.id)
                      ? 'btn-success'
                      : 'btn-primary'
                  }`}
                  onClick={() => onFactorAction('select', factor)}
                  disabled={isFactorSelected(factor.id)}
                  title={isFactorSelected(factor.id) ? '已选择' : '添加到策略'}
                >
                  {isFactorSelected(factor.id) ? (
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
  );
};

export default FactorGrid; 