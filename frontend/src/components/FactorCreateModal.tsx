import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { factorApi, Factor, FactorCreate } from '../services/api';

interface FactorCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

const FactorCreateModal: React.FC<FactorCreateModalProps> = ({
  isOpen,
  onClose,
  onCreated
}) => {
  const [createFactorForm, setCreateFactorForm] = useState({
    id: '',
    name: '',
    display_name: '',
    description: '',
    category: 'custom',
    code: '',
    input_fields: ['close', 'high', 'low', 'volume'],
    default_parameters: {},
    parameter_schema: {},
    calculation_method: 'custom',
    is_active: true,
    is_builtin: false,
    version: '1.0.0'
  });
  const [isCreating, setIsCreating] = useState(false);

  // 保存新因子
  const handleSaveNewFactor = async () => {
    if (!createFactorForm.id || !createFactorForm.name || !createFactorForm.code) {
      alert('请填写所有必填字段');
      return;
    }
    
    try {
      setIsCreating(true);
      const factorData: FactorCreate = {
        id: createFactorForm.id,
        name: createFactorForm.name,
        display_name: createFactorForm.display_name,
        description: createFactorForm.description,
        category: createFactorForm.category,
        code: createFactorForm.code,
        input_fields: createFactorForm.input_fields,
        default_parameters: createFactorForm.default_parameters,
        parameter_schema: createFactorForm.parameter_schema,
        calculation_method: createFactorForm.calculation_method,
        is_active: createFactorForm.is_active,
        is_builtin: createFactorForm.is_builtin,
        version: createFactorForm.version
      };
      
      await factorApi.createFactor(factorData);
      onClose();
      alert('因子创建成功！');
      onCreated();
    } catch (error) {
      console.error('创建因子失败:', error);
      alert('创建因子失败，请重试');
    } finally {
      setIsCreating(false);
    }
  };

  // 重置表单
  const handleResetForm = () => {
    setCreateFactorForm({
      id: '',
      name: '',
      display_name: '',
      description: '',
      category: 'custom',
      code: '',
      input_fields: ['close', 'high', 'low', 'volume'],
      default_parameters: {},
      parameter_schema: {},
      calculation_method: 'custom',
      is_active: true,
      is_builtin: false,
      version: '1.0.0'
    });
  };

  // 生成默认代码模板
  const generateDefaultCode = () => {
    const factorId = createFactorForm.id || 'custom_factor';
    return `import numpy as np
import pandas as pd

def calculate_${factorId}(data):
    """
    自定义因子计算函数
    """
    # 获取价格数据
    close = data['close']
    high = data['high']
    low = data['low']
    volume = data['volume']
    
    # 计算因子值（示例：价格动量）
    result = close.pct_change(periods=5)
    
    return result`;
  };

  if (!isOpen) return null;

  return (
    <div className="modal modal-open">
      <div className="modal-box max-w-5xl">
        <h3 className="font-bold text-lg mb-4">
          创建新因子
        </h3>

        <div className="space-y-4">
          {/* 基本信息 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="form-control">
              <label className="label">
                <span className="label-text font-medium">因子ID *</span>
              </label>
              <input
                type="text"
                className="input input-bordered"
                placeholder="例如: custom_001"
                value={createFactorForm.id}
                onChange={(e) => setCreateFactorForm({
                  ...createFactorForm,
                  id: e.target.value
                })}
              />
            </div>

            <div className="form-control">
              <label className="label">
                <span className="label-text font-medium">因子名称 *</span>
              </label>
              <input
                type="text"
                className="input input-bordered"
                placeholder="例如: 自定义动量因子"
                value={createFactorForm.name}
                onChange={(e) => setCreateFactorForm({
                  ...createFactorForm,
                  name: e.target.value
                })}
              />
            </div>

            <div className="form-control">
              <label className="label">
                <span className="label-text font-medium">显示名称 *</span>
              </label>
              <input
                type="text"
                className="input input-bordered"
                placeholder="例如: 自定义动量因子"
                value={createFactorForm.display_name}
                onChange={(e) => setCreateFactorForm({
                  ...createFactorForm,
                  display_name: e.target.value
                })}
              />
            </div>

            <div className="form-control">
              <label className="label">
                <span className="label-text font-medium">分类</span>
              </label>
              <select
                className="select select-bordered"
                value={createFactorForm.category}
                onChange={(e) => setCreateFactorForm({
                  ...createFactorForm,
                  category: e.target.value
                })}
              >
                <option value="custom">自定义</option>
                <option value="trend">趋势类</option>
                <option value="momentum">动量类</option>
                <option value="volume">成交量类</option>
                <option value="volatility">波动率类</option>
                <option value="value">估值类</option>
              </select>
            </div>
          </div>

          {/* 描述 */}
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">描述</span>
            </label>
            <textarea
              className="textarea textarea-bordered h-20"
              placeholder="因子描述..."
              value={createFactorForm.description}
              onChange={(e) => setCreateFactorForm({
                ...createFactorForm,
                description: e.target.value
              })}
            />
          </div>

          {/* 输入字段 */}
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">输入字段</span>
            </label>
            <input
              type="text"
              className="input input-bordered"
              placeholder="例如: close,high,low,volume"
              value={createFactorForm.input_fields.join(', ')}
              onChange={(e) => setCreateFactorForm({
                ...createFactorForm,
                input_fields: e.target.value.split(',').map(f => f.trim()).filter(f => f)
              })}
            />
            <label className="label">
              <span className="label-text-alt">用逗号分隔多个字段</span>
            </label>
          </div>

          {/* 因子代码 */}
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">因子代码 *</span>
              <button
                type="button"
                className="btn btn-xs btn-ghost"
                onClick={() => setCreateFactorForm({
                  ...createFactorForm,
                  code: generateDefaultCode()
                })}
              >
                生成模板
              </button>
            </label>
            <div className="border border-base-300 rounded-lg overflow-hidden">
              <Editor
                height="400px"
                defaultLanguage="python"
                value={createFactorForm.code}
                onChange={(value) => setCreateFactorForm({
                  ...createFactorForm,
                  code: value || ''
                })}
                options={{
                  readOnly: false,
                  minimap: { enabled: true },
                  scrollBeyondLastLine: false,
                  fontSize: 14,
                  lineNumbers: 'on',
                  roundedSelection: false,
                  scrollbar: {
                    vertical: 'visible',
                    horizontal: 'visible'
                  },
                  theme: 'vs-dark',
                  wordWrap: 'on',
                  folding: true,
                  foldingStrategy: 'indentation',
                  suggestOnTriggerCharacters: true,
                  quickSuggestions: true,
                  parameterHints: {
                    enabled: true
                  }
                }}
                theme="vs-dark"
              />
            </div>
            <label className="label">
              <span className="label-text-alt">支持pandas和numpy函数，data参数包含股票数据</span>
            </label>
          </div>

          {/* 帮助提示 */}
          <div className="bg-base-200 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">代码编写帮助</h4>
            <div className="text-xs space-y-1">
              <div><code>import numpy as np</code> - 导入numpy</div>
              <div><code>import pandas as pd</code> - 导入pandas</div>
              <div><code>data['close']</code> - 收盘价数据</div>
              <div><code>data['high']</code> - 最高价数据</div>
              <div><code>data['low']</code> - 最低价数据</div>
              <div><code>data['volume']</code> - 成交量数据</div>
              <div><code>.pct_change(periods=5)</code> - 计算5日收益率</div>
              <div><code>.rolling(window=20).mean()</code> - 20日移动平均</div>
              <div><code>.rolling(window=20).std()</code> - 20日标准差</div>
              <div><code>return result</code> - 返回计算结果</div>
            </div>
          </div>
        </div>

        <div className="modal-action">
          <button
            className="btn"
            onClick={() => {
              handleResetForm();
              onClose();
            }}
          >
            取消
          </button>
          <button
            className={`btn btn-primary ${isCreating ? 'loading' : ''}`}
            onClick={handleSaveNewFactor}
            disabled={isCreating}
          >
            {isCreating ? '创建中...' : '创建因子'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FactorCreateModal; 