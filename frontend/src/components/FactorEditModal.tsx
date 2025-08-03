import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { 
  ArrowPathIcon, 
  CheckIcon, 
  XMarkIcon 
} from '@heroicons/react/24/outline';
import { factorApi, Factor, FactorFormulaUpdate, FormulaValidationResult } from '../services/api';

interface FactorEditModalProps {
  factor: Factor;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: () => void;
}

const FactorEditModal: React.FC<FactorEditModalProps> = ({
  factor,
  isOpen,
  onClose,
  onUpdate
}) => {
  const [editingFormula, setEditingFormula] = useState(factor.code || '');
  const [editingDescription, setEditingDescription] = useState(factor.description || '');
  const [editingInputFields, setEditingInputFields] = useState<string[]>(factor.input_fields || []);
  const [formulaValidation, setFormulaValidation] = useState<FormulaValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  const hasChanges = () => {
    const originalFormula = factor.code || '';
    return editingFormula !== originalFormula ||
           editingDescription !== (factor.description || '') ||
           JSON.stringify(editingInputFields) !== JSON.stringify(factor.input_fields || []);
  };

  // 验证公式
  const handleValidateFormula = async () => {
    if (!editingFormula.trim()) {
      setFormulaValidation({
        id: factor.id,
        is_valid: false,
        errors: ['公式不能为空']
      });
      return;
    }

    try {
      const result = await factorApi.validateFactorFormula(factor.id, editingFormula);
      setFormulaValidation(result);
    } catch (error) {
      setFormulaValidation({
        id: factor.id,
        is_valid: false,
        errors: ['验证失败']
      });
    }
  };

  // 保存公式
  const handleSaveFormula = async () => {
    if (!editingFormula.trim()) {
      alert('公式不能为空');
      return;
    }
    
    try {
      setIsSaving(true);
      const update: FactorFormulaUpdate = {
        code: editingFormula
      };
      
      await factorApi.updateFactorFormula(factor.id, update);
      
      // 关闭编辑模态框
      onClose();
      
      // 显示成功消息
      alert('公式保存成功！');
      
      // 通知父组件更新
      onUpdate();
      
    } catch (error) {
      console.error('保存公式失败:', error);
      alert('保存公式失败，请重试');
    } finally {
      setIsSaving(false);
    }
  };

  // 重置公式
  const handleResetFormula = async () => {
    if (!confirm('确定要重置此因子的公式到原始状态吗？')) return;
    
    try {
      setIsResetting(true);
      await factorApi.resetFactorFormula(factor.id);
      onClose();
      alert('公式已重置到原始状态');
      onUpdate();
    } catch (error) {
      console.error('重置公式失败:', error);
      alert('重置公式失败，请重试');
    } finally {
      setIsResetting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal modal-open">
      <div className="modal-box max-w-5xl">
        <h3 className="font-bold text-lg mb-4">
          编辑因子代码 - {factor.display_name}
        </h3>

        <div className="space-y-4">
          {/* 基本信息 */}
          <div className="bg-base-200 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">因子信息</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">因子ID：</span>
                <code className="bg-base-300 px-2 py-1 rounded">{factor.id}</code>
              </div>
              <div>
                <span className="font-medium">标签：</span>
                <div className="flex flex-wrap gap-1 ml-2">
                  {factor.tags && factor.tags.length > 0 ? (
                    factor.tags.map(tag => (
                      <span key={tag.id} className="badge badge-sm" style={{ backgroundColor: tag.color }}>
                        {tag.display_name}
                      </span>
                    ))
                  ) : (
                    <span className="badge badge-sm badge-neutral">无标签</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* 代码编辑区 */}
          <div className="space-y-3">
            <div>
              <label className="label">
                <span className="label-text font-medium">因子代码</span>
                <div className="flex gap-2">
                  <button
                    className={`btn btn-xs ${isValidating ? 'loading' : ''}`}
                    onClick={handleValidateFormula}
                    disabled={isValidating || !editingFormula.trim()}
                  >
                    {isValidating ? '验证中...' : '验证代码'}
                  </button>
                  <button
                    className="btn btn-xs btn-ghost"
                    onClick={handleResetFormula}
                  >
                    <ArrowPathIcon className="w-3 h-3" />
                    重置
                  </button>
                </div>
              </label>
              <div className="border border-base-300 rounded-lg overflow-hidden">
                <Editor
                  height="400px"
                  defaultLanguage="python"
                  value={editingFormula}
                  onChange={(value) => setEditingFormula(value || '')}
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
            </div>

            <div>
              <label className="label">
                <span className="label-text font-medium">描述（可选）</span>
              </label>
              <textarea
                className="textarea textarea-bordered w-full h-20"
                placeholder="因子描述..."
                value={editingDescription}
                onChange={(e) => setEditingDescription(e.target.value)}
              />
            </div>
          </div>

          {/* 验证结果 */}
          {formulaValidation && (
            <div className={`alert ${formulaValidation.is_valid ? 'alert-success' : 'alert-error'}`}>
              <div className="flex items-center gap-2">
                {formulaValidation.is_valid ? (
                  <CheckIcon className="w-5 h-5" />
                ) : (
                  <XMarkIcon className="w-5 h-5" />
                )}
                <div>
                  <div className="font-medium">
                    {formulaValidation.is_valid ? '代码验证通过' : '代码验证失败'}
                  </div>
                  {formulaValidation.errors && formulaValidation.errors.length > 0 && (
                    <div className="text-sm opacity-80">
                      错误：{formulaValidation.errors.join('；')}
                    </div>
                  )}
                  {formulaValidation.warnings && formulaValidation.warnings.length > 0 && (
                    <div className="text-sm opacity-80">
                      警告：{formulaValidation.warnings.join('；')}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* 帮助提示 */}
          <div className="bg-base-200 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">代码编写帮助</h4>
            <div className="text-xs space-y-1">
              <div><code>def calculate_{factor.id}(data):</code> - 函数定义</div>
              <div><code>import pandas as pd</code> - 导入pandas</div>
              <div><code>import numpy as np</code> - 导入numpy</div>
              <div><code>data['close']</code> - 收盘价数据</div>
              <div><code>data['high']</code> - 最高价数据</div>
              <div><code>data['low']</code> - 最低价数据</div>
              <div><code>data['volume']</code> - 成交量数据</div>
              <div><code>.pct_change()</code> - 计算收益率</div>
              <div><code>.rolling(window=20).mean()</code> - 20日移动平均</div>
              <div><code>.rolling(window=20).std()</code> - 20日标准差</div>
            </div>
          </div>
        </div>

        <div className="modal-action">
          <button
            className="btn"
            onClick={onClose}
          >
            取消
          </button>
          <button
            className={`btn btn-primary ${isSaving ? 'loading' : ''}`}
            onClick={handleSaveFormula}
            disabled={isSaving || !editingFormula.trim() || (formulaValidation ? !formulaValidation.is_valid : false)}
          >
            {isSaving ? '保存中...' : '保存代码'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FactorEditModal; 