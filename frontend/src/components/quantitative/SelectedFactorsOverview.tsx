import React from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { SelectedFactor, StrategyConfig } from '../../services/api';

interface SelectedFactorsOverviewProps {
  selectedFactors: SelectedFactor[];
  currentStrategy: StrategyConfig | null;
  isWeightValid: () => boolean;
  getTotalWeight: () => number;
  onRemoveFactor: (factorId: string) => void;
  onFactorWeightChange: (factorId: string, weight: number) => void;
  onFactorToggle: (factorId: string) => void;
  onNormalizeWeights: () => void;
}

const SelectedFactorsOverview: React.FC<SelectedFactorsOverviewProps> = ({
  selectedFactors,
  currentStrategy,
  isWeightValid,
  getTotalWeight,
  onRemoveFactor,
  onFactorWeightChange,
  onFactorToggle,
  onNormalizeWeights
}) => {
  if (selectedFactors.length === 0) return null;

  return (
    <div className="card bg-base-100 shadow-lg">
      <div className="card-body p-4">
        <div className="flex justify-between items-center mb-3">
          <h3 className="font-semibold">
            已选择因子 ({selectedFactors.length})
            {currentStrategy && (
              <span className="text-sm text-base-content/60 ml-2">
                来自策略: {currentStrategy.name}
              </span>
            )}
          </h3>
          <div className="flex items-center gap-2">
            <span className={`text-sm ${isWeightValid() ? 'text-success' : 'text-warning'}`}>
              总权重: {(getTotalWeight() * 100).toFixed(1)}%
            </span>
            {!isWeightValid() && (
              <ExclamationTriangleIcon className="w-4 h-4 text-warning" />
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-3">
          {selectedFactors.map((factor, index) => (
            <div
              key={`${factor.id}-${index}`}
              className={`p-3 border rounded-lg ${
                factor.is_enabled ? 'border-primary bg-primary/5' : 'border-base-300 bg-base-200'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium text-sm truncate">{factor.name}</h4>
                <div className="flex gap-1">
                  <input
                    type="checkbox"
                    className="checkbox checkbox-sm"
                    checked={factor.is_enabled}
                    onChange={() => onFactorToggle(factor.id)}
                  />
                  <button
                    className="btn btn-ghost btn-xs"
                    onClick={() => onRemoveFactor(factor.id)}
                  >
                    ×
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs">权重:</span>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={factor.weight}
                  onChange={(e) => onFactorWeightChange(factor.id, parseFloat(e.target.value))}
                  className="range range-xs flex-1"
                  disabled={!factor.is_enabled}
                />
                <span className="text-xs w-12 text-right">
                  {((factor.weight ?? 0) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>

        {!isWeightValid() && (
          <div className="mt-3 flex gap-2">
            <button
              className="btn btn-warning btn-sm"
              onClick={onNormalizeWeights}
            >
              标准化权重
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SelectedFactorsOverview; 