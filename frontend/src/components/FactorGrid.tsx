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
  onFactorAction: (action: string, factor: Factor) => void;
}

const FactorGrid: React.FC<FactorGridProps> = ({
  factors,
  onFactorAction
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
      {factors.map((factor) => (
        <div
          key={factor.id}
          className={`card bg-base-200 shadow-md hover:shadow-lg transition-all
          }`}
        >
          <div className="card-body p-4">
            {/* 因子标题 */}
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-semibold text-sm truncate flex-1">
                {factor.display_name}
              </h3>
              <div className="flex gap-1 ml-2">
                {factor.tags && factor.tags.length > 0 ? (
                  factor.tags.map(tag => (
                    <div key={tag.id} className="badge badge-sm" style={{ backgroundColor: tag.color }}>
                      {tag.display_name}
                    </div>
                  ))
                ) : (
                  <div className="badge badge-sm badge-neutral">
                    无标签
                  </div>
                )}
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
                  title="查看详情和代码"
                >
                  <EyeIcon className="w-3 h-3" />
                  查看
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
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default FactorGrid; 