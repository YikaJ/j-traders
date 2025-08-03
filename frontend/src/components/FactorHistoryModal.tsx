import React, { useState, useEffect } from 'react';
import { factorApi, Factor, FormulaHistoryEntry } from '../services/api';

interface FactorHistoryModalProps {
  factor: Factor;
  isOpen: boolean;
  onClose: () => void;
}

const FactorHistoryModal: React.FC<FactorHistoryModalProps> = ({
  factor,
  isOpen,
  onClose
}) => {
  const [formulaHistory, setFormulaHistory] = useState<FormulaHistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);

  // 加载公式历史
  const loadFormulaHistory = async () => {
    if (!isOpen || !factor) return;
    
    try {
      setLoading(true);
      const response = await factorApi.getFactorHistory(factor.id);
      setFormulaHistory(response.data?.history || []);
    } catch (error) {
      console.error('加载公式历史失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadFormulaHistory();
    }
  }, [isOpen, factor]);

  if (!isOpen) return null;

  return (
    <div className="modal modal-open">
      <div className="modal-box max-w-3xl">
        <h3 className="font-bold text-lg mb-4">
          公式历史记录 - {factor.display_name}
        </h3>

        <div className="space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="loading loading-spinner loading-md"></div>
              <span className="ml-2">加载历史记录中...</span>
            </div>
          ) : formulaHistory.length === 0 ? (
            <div className="text-center py-8 text-base-content/60">
              暂无历史记录
            </div>
          ) : (
            <div className="space-y-3">
              {formulaHistory.map((entry, index) => (
                <div key={index} className="bg-base-200 p-4 rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <div className="text-sm text-base-content/70">
                      {new Date(entry.timestamp || entry.created_at).toLocaleString('zh-CN')}
                    </div>
                    <div className="badge badge-outline badge-sm">
                      第 {formulaHistory.length - index} 次修改
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div>
                      <div className="text-xs font-medium text-red-600 mb-1">修改前：</div>
                      <code className="block bg-red-50 dark:bg-red-900/20 p-2 rounded text-xs">
                        {entry.old_formula || entry.old_code || '(空)'}
                      </code>
                    </div>
                    
                    <div>
                      <div className="text-xs font-medium text-green-600 mb-1">修改后：</div>
                      <code className="block bg-green-50 dark:bg-green-900/20 p-2 rounded text-xs">
                        {entry.new_formula || entry.new_code}
                      </code>
                    </div>

                    {entry.description_change && entry.description_change.new !== entry.description_change.old && (
                      <div>
                        <div className="text-xs font-medium text-blue-600 mb-1">描述变更：</div>
                        <div className="text-xs">
                          <div className="text-red-600">
                            旧：{entry.description_change.old || '(空)'}
                          </div>
                          <div className="text-green-600">
                            新：{entry.description_change.new || '(空)'}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="modal-action">
          <button
            className="btn"
            onClick={onClose}
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};

export default FactorHistoryModal; 