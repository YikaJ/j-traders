import React, { useState, useEffect, useRef } from 'react';
import { ChevronDownIcon, ChevronUpIcon, XMarkIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { dataFieldApi, DataField, DataFieldConfig, DataFieldCategory } from '../services/api';

interface FieldSelectorProps {
  selectedFields: string[];
  onChange: (fields: string[]) => void;
  placeholder?: string;
  showValidation?: boolean;
  disabled?: boolean;
  className?: string;
}

const FieldSelector: React.FC<FieldSelectorProps> = ({
  selectedFields,
  onChange,
  placeholder = "选择数据字段...",
  showValidation = true,
  disabled = false,
  className = ""
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [fieldConfigs, setFieldConfigs] = useState<DataFieldConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [validationStatus, setValidationStatus] = useState<string>('');
  const [validationMessage, setValidationMessage] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<DataFieldCategory | 'all'>('all');
  
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  // 分类名称映射
  const categoryNames = {
    price: '价格类',
    volume: '成交量类',
    technical: '技术指标类',
    fundamental: '基本面类',
    derived: '衍生指标类'
  };

  // 加载字段配置
  useEffect(() => {
    loadFieldConfigs();
  }, []);

  // 验证字段组合
  useEffect(() => {
    if (showValidation && selectedFields.length > 0) {
      validateFields();
    } else {
      setValidationStatus('');
      setValidationMessage('');
    }
  }, [selectedFields, showValidation]);

  // 点击外部关闭下拉框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 下拉框打开时聚焦搜索框
  useEffect(() => {
    if (isOpen && searchRef.current) {
      setTimeout(() => searchRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const loadFieldConfigs = async () => {
    try {
      setLoading(true);
      const response = await dataFieldApi.getFactorInputFields();
      setFieldConfigs(response.categories);
    } catch (error) {
      console.error('加载字段配置失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const validateFields = async () => {
    try {
      const result = await dataFieldApi.validateFieldCombination(selectedFields);
      setValidationStatus(result.status);
      setValidationMessage(result.message);
    } catch (error) {
      console.error('验证字段组合失败:', error);
    }
  };

  const getAllFields = (): DataField[] => {
    return fieldConfigs.flatMap(config => config.fields);
  };

  const getFilteredFields = (): DataField[] => {
    let fields = getAllFields();
    
    // 按分类筛选
    if (selectedCategory !== 'all') {
      fields = fields.filter(field => field.category === selectedCategory);
    }
    
    // 按搜索词筛选
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      fields = fields.filter(field => 
        field.display_name.toLowerCase().includes(term) ||
        field.field_name.toLowerCase().includes(term) ||
        field.description.toLowerCase().includes(term)
      );
    }
    
    return fields;
  };

  const getSelectedFieldsData = (): DataField[] => {
    const allFields = getAllFields();
    return selectedFields.map(fieldId => 
      allFields.find(field => field.field_id === fieldId)
    ).filter(Boolean) as DataField[];
  };

  const handleFieldToggle = (fieldId: string) => {
    const newFields = selectedFields.includes(fieldId)
      ? selectedFields.filter(id => id !== fieldId)
      : [...selectedFields, fieldId];
    
    onChange(newFields);
  };

  const handleRemoveField = (fieldId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    const newFields = selectedFields.filter(id => id !== fieldId);
    onChange(newFields);
  };

  const handleClearAll = () => {
    onChange([]);
  };

  const renderSelectedFields = () => {
    const selectedFieldsData = getSelectedFieldsData();
    
    if (selectedFieldsData.length === 0) {
      return <span className="text-base-content/60">{placeholder}</span>;
    }

    return (
      <div className="flex flex-wrap gap-1">
        {selectedFieldsData.map(field => (
          <span 
            key={field.field_id}
            className="inline-flex items-center gap-1 px-2 py-1 bg-primary/20 text-primary rounded text-sm"
          >
            {field.display_name}
            {field.is_required && <span className="text-error">*</span>}
            <button
              type="button"
              onClick={(e) => handleRemoveField(field.field_id, e)}
              className="hover:text-error"
              disabled={disabled}
            >
              <XMarkIcon className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>
    );
  };

  const renderFieldOption = (field: DataField) => {
    const isSelected = selectedFields.includes(field.field_id);
    
    return (
      <div
        key={field.field_id}
        onClick={() => !disabled && handleFieldToggle(field.field_id)}
        className={`
          flex items-start gap-3 p-3 cursor-pointer hover:bg-base-200/50 border-b border-base-300/30
          ${isSelected ? 'bg-primary/5 border-l-4 border-l-primary' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => {}}
          className="checkbox checkbox-primary checkbox-sm mt-1"
          disabled={disabled}
        />
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-base-content">
              {field.display_name}
            </span>
            {field.is_required && (
              <span className="text-error text-xs">必需</span>
            )}
            {field.unit && (
              <span className="text-base-content/60 text-xs">({field.unit})</span>
            )}
          </div>
          
          <div className="text-sm text-base-content/70 mt-1">
            {field.description}
          </div>
          
          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs text-base-content/50">
              字段名: {field.field_name}
            </span>
            {field.example_value && (
              <span className="text-xs text-base-content/50">
                示例: {field.example_value}
              </span>
            )}
          </div>
        </div>
      </div>
    );
  };

  const filteredFields = getFilteredFields();
  const groupedFields = selectedCategory === 'all' 
    ? fieldConfigs.reduce((acc, config) => {
        const categoryFields = config.fields.filter(field => 
          filteredFields.includes(field)
        );
        if (categoryFields.length > 0) {
          acc[config.category] = {
            config,
            fields: categoryFields
          };
        }
        return acc;
      }, {} as Record<string, { config: DataFieldConfig; fields: DataField[] }>)
    : null;

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* 选择框 */}
      <div
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={`
          min-h-[48px] px-3 py-2 border border-base-300 rounded-lg cursor-pointer
          transition-all duration-200 bg-base-100
          ${isOpen ? 'border-primary ring-2 ring-primary/20' : 'hover:border-base-content/30'}
          ${disabled ? 'opacity-50 cursor-not-allowed bg-base-200' : ''}
          ${validationStatus === 'error' ? 'border-error' : ''}
          ${validationStatus === 'warning' ? 'border-warning' : ''}
        `}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="flex-1 min-w-0">
            {renderSelectedFields()}
          </div>
          
          <div className="flex items-center gap-2 flex-shrink-0">
            {selectedFields.length > 0 && !disabled && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleClearAll();
                }}
                className="text-base-content/60 hover:text-error"
                title="清空所有"
              >
                <XMarkIcon className="w-4 h-4" />
              </button>
            )}
            
            {isOpen ? (
              <ChevronUpIcon className="w-5 h-5 text-base-content/60" />
            ) : (
              <ChevronDownIcon className="w-5 h-5 text-base-content/60" />
            )}
          </div>
        </div>
      </div>

      {/* 验证信息 */}
      {showValidation && validationMessage && (
        <div className={`
          mt-1 text-xs px-2
          ${validationStatus === 'error' ? 'text-error' : ''}
          ${validationStatus === 'warning' ? 'text-warning' : ''}
        `}>
          {validationMessage}
        </div>
      )}

      {/* 下拉列表 */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-base-100 border border-base-300 rounded-lg shadow-lg max-h-96 overflow-hidden">
          {/* 搜索和筛选 */}
          <div className="p-3 border-b border-base-300/30 bg-base-50">
            <div className="relative mb-3">
              <input
                ref={searchRef}
                type="text"
                placeholder="搜索字段..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm border border-base-300 rounded focus:border-primary focus:outline-none"
              />
              <MagnifyingGlassIcon className="absolute left-2.5 top-2.5 w-4 h-4 text-base-content/60" />
            </div>
            
            <div className="flex gap-2">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value as DataFieldCategory | 'all')}
                className="select select-sm select-bordered flex-1"
              >
                <option value="all">所有分类</option>
                {Object.entries(categoryNames).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 字段列表 */}
          <div className="max-h-64 overflow-y-auto">
            {loading ? (
              <div className="p-4 text-center text-base-content/60">
                <span className="loading loading-spinner loading-sm mr-2"></span>
                加载中...
              </div>
            ) : filteredFields.length === 0 ? (
              <div className="p-4 text-center text-base-content/60">
                {searchTerm ? '未找到匹配的字段' : '暂无可用字段'}
              </div>
            ) : selectedCategory === 'all' && groupedFields ? (
              // 按分类分组显示
              Object.entries(groupedFields).map(([category, { config, fields }]) => (
                <div key={category}>
                  <div className="sticky top-0 px-3 py-2 bg-base-200 text-sm font-medium text-base-content/80 border-b border-base-300/30">
                    {categoryNames[category as keyof typeof categoryNames]} ({fields.length})
                  </div>
                  {fields.map(field => renderFieldOption(field))}
                </div>
              ))
            ) : (
              // 平铺显示
              filteredFields.map(field => renderFieldOption(field))
            )}
          </div>

          {/* 底部统计 */}
          <div className="p-2 border-t border-base-300/30 bg-base-50 text-xs text-base-content/60">
            已选择 {selectedFields.length} 个字段
            {filteredFields.length > 0 && ` / 共 ${filteredFields.length} 个可选字段`}
          </div>
        </div>
      )}
    </div>
  );
};

export default FieldSelector;