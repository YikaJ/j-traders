import React, { useState, useEffect } from 'react';
import {
  Cog6ToothIcon,
  SparklesIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { factorApi, Factor } from '../services/api';
import FactorNormalizationModal from './FactorNormalizationModal';

interface FactorNormalizationServiceProps {
  factor: Factor;
  onFactorUpdated: (factor: Factor) => void;
}

interface NormalizationStatus {
  hasNormalization: boolean;
  method: string;
  isCustom: boolean;
  lastUpdated?: string;
}

const FactorNormalizationService: React.FC<FactorNormalizationServiceProps> = ({
  factor,
  onFactorUpdated,
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [normalizationStatus, setNormalizationStatus] = useState<NormalizationStatus>({
    hasNormalization: false,
    method: '',
    isCustom: false,
  });

  // 分析因子的标准化状态
  useEffect(() => {
    const status: NormalizationStatus = {
      hasNormalization: !!(factor.normalization_code),
      method: 'z_score', // 统一显示为Z-Score
      isCustom: false, // 不再区分自定义
      lastUpdated: factor.updated_at,
    };
    setNormalizationStatus(status);
  }, [factor]);

  const handleNormalizationUpdated = (updatedFactor: Factor) => {
    onFactorUpdated(updatedFactor);
  };

  const getMethodDisplayName = (method: string): string => {
    const methodMap: Record<string, string> = {
      'z_score': 'Z-Score标准化',
    };
    return methodMap[method] || method;
  };

  const getMethodDescription = (method: string): string => {
    const descriptions: Record<string, string> = {
      'z_score': '将因子值转换为标准正态分布，均值为0，标准差为1',
    };
    return descriptions[method] || '';
  };

  const getMethodColor = (method: string): string => {
    const colorMap: Record<string, string> = {
      'z_score': 'badge-primary',
    };
    return colorMap[method] || 'badge-base-300';
  };

  return (
    <div className="space-y-4">
      {/* 标准化状态卡片 */}
      <div className="card bg-base-100 border border-base-300 shadow-sm">
        <div className="card-body p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Cog6ToothIcon className="w-5 h-5 text-primary" />
              <div>
                <h4 className="font-semibold text-base-content">标准化配置</h4>
                <p className="text-sm text-base-content/70">
                  {normalizationStatus.hasNormalization 
                    ? '已配置标准化方案'
                    : '未配置标准化方案'
                  }
                </p>
              </div>
            </div>
            
            <button
              onClick={() => setIsModalOpen(true)}
              className="btn btn-primary btn-sm"
            >
              <SparklesIcon className="w-4 h-4" />
              {normalizationStatus.hasNormalization ? '编辑配置' : '配置标准化'}
            </button>
          </div>

          {/* 标准化详情 */}
          {normalizationStatus.hasNormalization && (
            <div className="mt-4 p-3 bg-base-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className={`badge ${getMethodColor(normalizationStatus.method)}`}>
                  {getMethodDisplayName(normalizationStatus.method)}
                </span>
                {normalizationStatus.isCustom && (
                  <span className="badge badge-outline badge-sm">自定义</span>
                )}
              </div>
              
              <p className="text-sm text-base-content/70 mb-2">
                {getMethodDescription(normalizationStatus.method)}
              </p>
              
              {normalizationStatus.lastUpdated && (
                <p className="text-xs text-base-content/50">
                  最后更新: {new Date(normalizationStatus.lastUpdated).toLocaleString()}
                </p>
              )}
            </div>
          )}

          {/* 未配置时的提示 */}
          {!normalizationStatus.hasNormalization && (
            <div className="mt-4 p-3 bg-warning/10 border border-warning/20 rounded-lg">
              <div className="flex items-center gap-2">
                <ExclamationTriangleIcon className="w-4 h-4 text-warning" />
                <span className="text-sm text-warning">
                  建议配置标准化方案以确保因子值的一致性和可比性
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

              {/* 标准化方法说明 */}
        <div className="card bg-base-100 border border-base-300 shadow-sm">
          <div className="card-body p-4">
            <h5 className="font-semibold mb-3">标准化方法说明</h5>
            <div className="p-3 bg-base-200 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <span className="badge badge-primary badge-xs">Z-Score</span>
                <span className="font-medium">Z-Score标准化</span>
              </div>
              <p className="text-base-content/70">
                将因子值转换为标准正态分布，均值为0，标准差为1。这是最常用的标准化方法，适用于大多数数值型因子。
              </p>
            </div>
          </div>
        </div>

      {/* 标准化模态框 */}
      <FactorNormalizationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        factor={factor}
        onNormalizationUpdated={handleNormalizationUpdated}
      />
    </div>
  );
};

export default FactorNormalizationService; 