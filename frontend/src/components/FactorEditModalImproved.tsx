import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { 
  XMarkIcon, 
  CheckIcon, 
  ExclamationTriangleIcon,
  ArrowPathIcon,
  PencilIcon
} from '@heroicons/react/24/outline';
import { factorApi, Factor, FactorFormulaUpdate, FormulaValidationResult } from '../services/api';

interface FactorEditModalImprovedProps {
  factor: Factor;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: () => void;
}

const FactorEditModalImproved: React.FC<FactorEditModalImprovedProps> = ({
  factor,
  isOpen,
  onClose,
  onUpdate
}) => {
  const [editingFormula, setEditingFormula] = useState('');
  const [editingDescription, setEditingDescription] = useState('');
  const [editingInputFields, setEditingInputFields] = useState<string[]>([]);
  const [editingNormalizationMethod, setEditingNormalizationMethod] = useState('');
  const [editingNormalizationCode, setEditingNormalizationCode] = useState('');
  const [formulaValidation, setFormulaValidation] = useState<FormulaValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [currentTab, setCurrentTab] = useState<'basic' | 'code' | 'normalization'>('basic');
  const [hasChanges, setHasChanges] = useState(false);

  // 初始化表单数据
  useEffect(() => {
    if (factor && isOpen) {
      setEditingFormula(factor.code || '');
      setEditingDescription(factor.description || '');
      setEditingInputFields(['close']); // 默认使用close字段
      setFormulaValidation(null);
      setHasChanges(false);
    }
  }, [factor, isOpen]);

  // 检测变更
  useEffect(() => {
    const originalFormula = factor.code || '';
    const originalDescription = factor.description || '';
    const originalInputFields = ['close']; // 默认字段
    
    const hasFormChanged = 
      editingFormula !== originalFormula ||
      editingDescription !== originalDescription ||
      JSON.stringify(editingInputFields) !== JSON.stringify(originalInputFields);
    
    setHasChanges(hasFormChanged);
  }, [editingFormula, editingDescription, editingInputFields, factor]);

  // 验证公式
  const handleValidateFormula = async () => {
    if (!editingFormula.trim()) {
      setFormulaValidation({
        id: factor.id,
        is_valid: false,
        errors: ['公式不能为空'],
        warnings: []
      });
      return;
    }
    
    try {
      setIsValidating(true);
      const result = await factorApi.validateFactorFormula(factor.id.toString(), editingFormula);
      setFormulaValidation(result);
    } catch (error) {
      console.error('验证公式失败:', error);
      setFormulaValidation({
        id: factor.id,
        is_valid: false,
        errors: ['验证失败，请检查网络连接'],
        warnings: []
      });
    } finally {
      setIsValidating(false);
    }
  };

  // 保存修改
  const handleSave = async () => {
    if (!editingFormula.trim()) {
      alert('公式不能为空');
      return;
    }
    
    if (editingInputFields.length === 0) {
      alert('至少需要选择一个输入字段');
      return;
    }
    
    try {
      setIsSaving(true);
      
      // 构建更新数据
      const update: FactorFormulaUpdate & { input_fields?: string[] } = {
        code: editingFormula,
        description: editingDescription || undefined
      };
      
      // 允许修改输入字段
      update.input_fields = editingInputFields;
      
      await factorApi.updateFactorFormula(factor.id.toString(), update);
      
      onClose();
      alert('保存成功！');
      onUpdate();
      
    } catch (error) {
      console.error('保存失败:', error);
      alert('保存失败，请重试');
    } finally {
      setIsSaving(false);
    }
  };

  // 重置公式
  const handleReset = async () => {
    if (!confirm('确定要重置此因子到原始状态吗？这将撤销所有修改。')) return;
    
    try {
      await factorApi.resetFactorFormula(factor.id.toString());
      onClose();
      alert('已重置到原始状态');
      onUpdate();
    } catch (error) {
      console.error('重置失败:', error);
      alert('重置失败，请重试');
    }
  };

  // 取消编辑
  const handleCancel = () => {
    if (hasChanges) {
      if (!confirm('您有未保存的修改，确定要取消吗？')) {
        return;
      }
    }
    onClose();
  };

  // 生成代码模板
  const generateCodeTemplate = () => {
    const factorId = factor.id;
    const inputFields = editingInputFields;
    
    return `def calculate_${factorId}(data):
    """
    ${editingDescription || factor.name}
    
    参数:
        data: pandas.DataFrame - 包含股票历史数据
        
    可用字段:
${inputFields.map(field => `        - $$${field}: ${getFieldDescription(field)}`).join('\n')}
    
    返回:
        pandas.Series - 计算得到的因子值
    """
    import pandas as pd
    import numpy as np
    
    # 获取输入数据
${inputFields.map(field => `    $$${field} = data['$$${field}']`).join('\n')}
    
    # 在这里编写因子计算逻辑
    # 示例：计算收益率
    returns = data['close'].pct_change()
    
    # 返回因子值
    factor_value = returns
    
    return factor_value.fillna(0)`;
  };

  const getFieldDescription = (fieldName: string): string => {
    const descriptions: Record<string, string> = {
      'open': '开盘价',
      'high': '最高价', 
      'low': '最低价',
      'close': '收盘价',
      'volume': '成交量',
      'amount': '成交额',
      'pre_close': '前收盘价',
      'change': '涨跌额',
      'pct_change': '涨跌幅'
    };
    return descriptions[fieldName] || fieldName;
  };

  if (!isOpen || !factor) return null;

  return (
    <dialog className="modal modal-open">
      <div className="modal-box max-w-6xl max-h-[90vh] bg-base-100 border border-base-300 shadow-2xl">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-base-300">
          <div className="flex items-center gap-3">
            <PencilIcon className="w-6 h-6 text-primary" />
            <div>
              <h3 className="text-xl font-bold text-base-content">编辑因子</h3>
              <p className="text-base-content/70 text-sm">{factor.name}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {hasChanges && (
              <span className="badge badge-warning badge-sm">未保存</span>
            )}
            <button onClick={handleCancel} className="btn btn-ghost btn-sm btn-circle">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 标签页 */}
        <div className="tabs tabs-bordered mb-6">
          <button 
            className={`tab ${currentTab === 'basic' ? 'tab-active' : ''}`}
            onClick={() => setCurrentTab('basic')}
          >
            基本设置
          </button>
          <button 
            className={`tab ${currentTab === 'code' ? 'tab-active' : ''}`}
            onClick={() => setCurrentTab('code')}
          >
            代码编辑
          </button>
        </div>

        {/* 基本设置标签页 */}
        {currentTab === 'basic' && (
          <div className="space-y-6">
            {/* 因子基本信息 */}
            <div className="bg-base-200/30 rounded-lg p-4">
              <h4 className="font-semibold mb-3 text-base-content">因子信息</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-base-content/70">因子ID:</span>
                  <span className="ml-2 font-mono text-primary">{factor.id}</span>
                </div>
                <div>
                  <span className="text-base-content/70">标签:</span>
                  <span className="ml-2">
                    {factor.tags && factor.tags.length > 0 ? (
                      factor.tags.map(tag => (
                        <span key={tag.id} className="badge badge-sm mr-1" style={{ backgroundColor: tag.color }}>
                          {tag.display_name}
                        </span>
                      ))
                    ) : (
                      <span className="text-base-content/60">无标签</span>
                    )}
                  </span>
                </div>
                <div>
                  <span className="text-base-content/70">名称:</span>
                  <span className="ml-2">{factor.name}</span>
                </div>
                <div>
                  <span className="text-base-content/70">代码:</span>
                  <span className="ml-2">{factor.code.substring(0, 50)}...</span>
                </div>
              </div>
            </div>

            {/* 描述编辑 */}
            <div className="form-control">
              <label className="label">
                <span className="label-text font-medium">因子描述</span>
              </label>
              <textarea
                className="textarea textarea-bordered bg-base-100 focus:border-primary h-24 resize-none"
                placeholder="描述因子的用途和计算逻辑..."
                value={editingDescription}
                onChange={(e) => setEditingDescription(e.target.value)}
              />
            </div>
          </div>
        )}

        {/* 代码编辑标签页 */}
        {currentTab === 'code' && (
          <div className="space-y-4">
            {/* 工具栏 */}
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-base-content">因子代码</h4>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="btn btn-sm btn-outline btn-primary"
                  onClick={() => setEditingFormula(generateCodeTemplate())}
                >
                  生成模板
                </button>
                <button
                  type="button"
                  className={`btn btn-sm btn-outline ${isValidating ? 'loading' : ''}`}
                  onClick={handleValidateFormula}
                  disabled={isValidating}
                >
                  验证代码
                </button>
              </div>
            </div>

            {/* 代码编辑器 */}
            <div className="border border-base-300 rounded-lg overflow-hidden">
              <Editor
                height="400px"
                defaultLanguage="python"
                value={editingFormula}
                onChange={(value) => setEditingFormula(value || '')}
                options={{
                  readOnly: false,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  fontSize: 14,
                  lineNumbers: 'on',
                  wordWrap: 'on',
                  folding: true,
                  quickSuggestions: true,
                  autoIndent: 'full',
                  formatOnPaste: true,
                  formatOnType: true,
                }}
                theme="vs-dark"
              />
            </div>

            {/* 验证结果 */}
            {formulaValidation && (
              <div className={`
                alert
                ${formulaValidation.is_valid ? 'alert-success' : 'alert-error'}
              `}>
                <div className="flex items-start gap-3">
                  {formulaValidation.is_valid ? (
                    <CheckIcon className="w-5 h-5 flex-shrink-0" />
                  ) : (
                    <ExclamationTriangleIcon className="w-5 h-5 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <div className="font-medium">
                      {formulaValidation.is_valid ? '代码验证通过' : '代码验证失败'}
                    </div>
                    {formulaValidation.errors && formulaValidation.errors.length > 0 && (
                      <div className="text-sm mt-1">
                        <strong>错误：</strong>{formulaValidation.errors.join('；')}
                      </div>
                    )}
                    {formulaValidation.warnings && formulaValidation.warnings.length > 0 && (
                      <div className="text-sm mt-1">
                        <strong>警告：</strong>{formulaValidation.warnings.join('；')}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* 编程提示 */}
            <div className="bg-base-200/50 rounded-lg p-4">
              <h5 className="font-semibold mb-3">💡 编程提示</h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <h6 className="font-medium mb-2">常用函数:</h6>
                  <ul className="space-y-1 text-base-content/70">
                    <li><code>.pct_change()</code> - 计算收益率</li>
                    <li><code>.rolling(n).mean()</code> - n日移动平均</li>
                    <li><code>.rolling(n).std()</code> - n日标准差</li>
                    <li><code>.shift(n)</code> - 向前/后移动n期</li>
                  </ul>
                </div>
                <div>
                  <h6 className="font-medium mb-2">注意事项:</h6>
                  <ul className="space-y-1 text-base-content/70">
                    <li>• 函数必须返回pandas.Series</li>
                    <li>• 处理空值和异常情况</li>
                    <li>• 避免未来数据泄露</li>
                    <li>• 保持代码简洁易懂</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 底部操作栏 */}
        <div className="flex items-center justify-between pt-6 mt-6 border-t border-base-300">
          <button
            type="button"
            className="btn btn-outline btn-error"
            onClick={handleReset}
          >
            <ArrowPathIcon className="w-4 h-4 mr-1" />
            重置
          </button>
          
          <div className="flex gap-3">
            <button
              type="button"
              className="btn btn-outline"
              onClick={handleCancel}
            >
              取消
            </button>
            <button
              type="button"
              className={`btn btn-primary ${isSaving ? 'loading' : ''}`}
              onClick={handleSave}
              disabled={isSaving || !hasChanges}
            >
              {isSaving ? '保存中...' : '保存修改'}
            </button>
          </div>
        </div>
      </div>
      <form method="dialog" className="modal-backdrop">
        <button>close</button>
      </form>
    </dialog>
  );
};

export default FactorEditModalImproved;