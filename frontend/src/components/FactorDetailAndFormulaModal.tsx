import React, { useState } from 'react';
import { XMarkIcon, CodeBracketIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { Factor } from '../services/api';
import MonacoEditor from '@monaco-editor/react';

interface FactorDetailAndFormulaModalProps {
  factor: Factor | null;
  isOpen: boolean;
  onClose: () => void;
}

const FactorDetailAndFormulaModal: React.FC<FactorDetailAndFormulaModalProps> = ({
  factor,
  isOpen,
  onClose
}) => {
  const [activeCodeTab, setActiveCodeTab] = useState<'calculation' | 'normalization'>('calculation');

  if (!isOpen || !factor) return null;

  const calculationCode = factor.code || '# 因子计算代码\n# 请在此处编写因子计算逻辑\n\ndef calculate_factor(data):\n    """计算因子值"""\n    # 示例代码\n    return data.get("close", 0)';
  
  const normalizationCode = factor.normalization_code || '# 因子标准化代码\n# 请在此处编写因子标准化逻辑\n\ndef normalize_factor(factor_values):\n    """标准化因子值"""\n    # Z-Score 标准化示例\n    import numpy as np\n    \n    if len(factor_values) == 0:\n        return factor_values\n    \n    mean_val = np.mean(factor_values)\n    std_val = np.std(factor_values)\n    \n    if std_val == 0:\n        return factor_values - mean_val\n    \n    return (factor_values - mean_val) / std_val';

  return (
    <div className="modal modal-open">
      <div className="modal-box w-11/12 max-w-7xl h-5/6 bg-base-100 shadow-2xl">
        {/* 模态框头部 */}
        <div className="flex justify-between items-center mb-6 border-b border-base-300 pb-4">
          <div className="flex items-center gap-3">
            <div className="avatar placeholder">
              <div className="bg-primary text-primary-content rounded-full w-10">
                <ChartBarIcon className="w-5 h-5" />
              </div>
            </div>
            <div>
              <h3 className="text-xl font-bold">{factor.display_name}</h3>
              <p className="text-sm text-base-content/60 font-mono">{factor.name}</p>
            </div>
          </div>
          <button
            className="btn btn-ghost btn-sm btn-circle hover:bg-base-200"
            onClick={onClose}
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* 主要内容区域 - 两列布局 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
          {/* 左侧：基本信息 */}
          <div className="space-y-4">
            <div className="card bg-base-200 shadow-lg">
              <div className="card-body">
                <h4 className="card-title text-lg mb-4">
                  <div className="w-2 h-2 bg-primary rounded-full mr-2"></div>
                  基本信息
                </h4>
                
                <div className="space-y-4">
                  {/* 描述 */}
                  <div className="alert alert-info">
                    <div>
                      <h4 className="font-bold">描述</h4>
                      <p className="text-sm">{factor.description || '暂无描述'}</p>
                    </div>
                  </div>

                  {/* 计算方法 */}
                  <div className="stats stats-vertical shadow">
                    <div className="stat">
                      <div className="stat-title">计算方法</div>
                      <div className="stat-value text-lg">
                        <span className="badge badge-primary badge-lg">{factor.calculation_method}</span>
                      </div>
                    </div>
                  </div>

                  {/* 输入字段 */}
                  <div className="stats stats-vertical shadow">
                    <div className="stat">
                      <div className="stat-title">输入字段</div>
                      <div className="stat-value text-lg">
                        {factor.input_fields && factor.input_fields.length > 0 
                          ? factor.input_fields.join(', ')
                          : 'N/A'
                        }
                      </div>
                    </div>
                  </div>

                  {/* 标签 */}
                  <div className="stats stats-vertical shadow">
                    <div className="stat">
                      <div className="stat-title">标签</div>
                      <div className="stat-value">
                        <div className="flex flex-wrap gap-2">
                          {factor.tags && factor.tags.length > 0 ? (
                            factor.tags.map(tag => (
                              <span 
                                key={tag.id} 
                                className="badge badge-outline"
                                style={{ borderColor: tag.color, color: tag.color }}
                              >
                                {tag.display_name}
                              </span>
                            ))
                          ) : (
                            <span className="badge badge-neutral">无标签</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 标准化状态 */}
                  <div className="stats stats-vertical shadow">
                    <div className="stat">
                      <div className="stat-title">标准化状态</div>
                      <div className="stat-value">
                        {factor.normalization_code ? (
                          <div className="badge badge-success badge-lg gap-2">
                            <div className="w-2 h-2 bg-success-content rounded-full"></div>
                            已配置
                          </div>
                        ) : (
                          <div className="badge badge-warning badge-lg gap-2">
                            <div className="w-2 h-2 bg-warning-content rounded-full"></div>
                            未配置
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* 时间信息 */}
                  <div className="stats stats-vertical shadow">
                    <div className="stat">
                      <div className="stat-title">创建时间</div>
                      <div className="stat-value text-sm">
                        {factor.created_at ? new Date(factor.created_at).toLocaleString() : 'N/A'}
                      </div>
                    </div>
                    <div className="stat">
                      <div className="stat-title">更新时间</div>
                      <div className="stat-value text-sm">
                        {factor.updated_at ? new Date(factor.updated_at).toLocaleString() : 'N/A'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 右侧：代码区域 */}
          <div className="space-y-4">
            <div className="card bg-base-200 shadow-lg h-full">
              <div className="card-body">
                <h4 className="card-title text-lg mb-4">
                  <CodeBracketIcon className="w-5 h-5 text-primary" />
                  代码
                </h4>

                {/* 代码Tab切换 */}
                <div className="tabs tabs-boxed bg-base-100 mb-4">
                  <button
                    className={`tab ${activeCodeTab === 'calculation' ? 'tab-active' : ''}`}
                    onClick={() => setActiveCodeTab('calculation')}
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-current rounded-full"></div>
                      因子计算代码
                    </div>
                  </button>
                  <button
                    className={`tab ${activeCodeTab === 'normalization' ? 'tab-active' : ''}`}
                    onClick={() => setActiveCodeTab('normalization')}
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-current rounded-full"></div>
                      因子标准化代码
                    </div>
                  </button>
                </div>

                {/* 代码编辑器 */}
                <div className="flex-1 min-h-[400px] bg-base-100 rounded-lg overflow-hidden">
                  <MonacoEditor
                    height="100%"
                    language="python"
                    theme="vs-dark"
                    value={activeCodeTab === 'calculation' ? calculationCode : normalizationCode}
                    options={{
                      readOnly: true,
                      minimap: { enabled: false },
                      scrollBeyondLastLine: false,
                      fontSize: 12,
                      lineNumbers: 'on',
                      wordWrap: 'on',
                      folding: true,
                      automaticLayout: true,
                    }}
                  />
                </div>

                {/* 代码说明 */}
                <div className="alert alert-info mt-4">
                  <div>
                    <h5 className="font-bold">
                      {activeCodeTab === 'calculation' ? '因子计算说明' : '因子标准化说明'}
                    </h5>
                    <p className="text-sm">
                      {activeCodeTab === 'calculation' 
                        ? '此代码定义了因子的计算逻辑，输入原始数据并返回因子值。'
                        : '此代码定义了因子的标准化逻辑，将原始因子值转换为标准化后的值。'
                      }
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 模态框底部 */}
        <div className="modal-action pt-4 border-t border-base-300">
          <button className="btn btn-primary" onClick={onClose}>
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};

export default FactorDetailAndFormulaModal; 