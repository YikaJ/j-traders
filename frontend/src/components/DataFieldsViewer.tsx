import React, { useState, useEffect } from 'react';
import {
  MagnifyingGlassIcon,
  InformationCircleIcon,
  TagIcon,
  CubeIcon,
  ChartBarIcon,
  CircleStackIcon,
  CalculatorIcon,
  BanknotesIcon
} from '@heroicons/react/24/outline';
import { 
  DataField, 
  DataFieldConfig, 
  DataFieldCategory, 
  DataFieldType,
  FactorInputFieldsResponse 
} from '../services/api';
import { mockDataFieldApi } from '../services/mockDataFieldApi';

interface DataFieldsViewerProps {
  onFieldSelect?: (field: DataField) => void;
  selectedFields?: string[];
  mode?: 'selection' | 'browse';
}

const DataFieldsViewer: React.FC<DataFieldsViewerProps> = ({
  onFieldSelect,
  selectedFields = [],
  mode = 'browse'
}) => {
  const [data, setData] = useState<FactorInputFieldsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<DataFieldCategory[]>([]);
  const [selectedField, setSelectedField] = useState<DataField | null>(null);
  const [showCommonOnly, setShowCommonOnly] = useState(true);

  // 分类图标映射
  const getCategoryIcon = (category: DataFieldCategory) => {
    switch (category) {
      case DataFieldCategory.PRICE:
        return BanknotesIcon;
      case DataFieldCategory.VOLUME:
        return ChartBarIcon;
      case DataFieldCategory.TECHNICAL:
        return CalculatorIcon;
      case DataFieldCategory.FUNDAMENTAL:
        return CircleStackIcon;
      case DataFieldCategory.DERIVED:
        return CubeIcon;
      default:
        return TagIcon;
    }
  };

  // 分类显示名称映射
  const getCategoryDisplayName = (category: DataFieldCategory) => {
    switch (category) {
      case DataFieldCategory.PRICE:
        return '价格数据';
      case DataFieldCategory.VOLUME:
        return '成交量数据';
      case DataFieldCategory.TECHNICAL:
        return '技术指标';
      case DataFieldCategory.FUNDAMENTAL:
        return '基本面数据';
      case DataFieldCategory.DERIVED:
        return '衍生数据';
      default:
        return category;
    }
  };

  // 获取字段类型颜色
  const getFieldTypeColor = (fieldType: DataFieldType) => {
    switch (fieldType) {
      case DataFieldType.NUMERIC:
        return 'badge-primary';
      case DataFieldType.STRING:
        return 'badge-secondary';
      case DataFieldType.DATE:
        return 'badge-accent';
      case DataFieldType.BOOLEAN:
        return 'badge-info';
      default:
        return 'badge-neutral';
    }
  };

  // 加载数据字段
  const loadDataFields = async () => {
    try {
      setLoading(true);
      const response = await mockDataFieldApi.getFactorInputFields(
        selectedCategories.length > 0 ? selectedCategories : undefined,
        showCommonOnly
      );
      setData(response);
    } catch (error) {
      console.error('加载数据字段失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDataFields();
  }, [selectedCategories, showCommonOnly]);

  // 过滤字段
  const getFilteredFields = () => {
    if (!data) return [];
    
    let allFields: DataField[] = [];
    data.categories.forEach(category => {
      allFields = [...allFields, ...category.fields];
    });

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      allFields = allFields.filter(field =>
        field.display_name.toLowerCase().includes(query) ||
        field.description.toLowerCase().includes(query) ||
        field.field_name.toLowerCase().includes(query) ||
        (field.tushare_field && field.tushare_field.toLowerCase().includes(query))
      );
    }

    return allFields;
  };

  // 处理分类筛选
  const handleCategoryToggle = (category: DataFieldCategory) => {
    setSelectedCategories(prev => 
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  // 检查字段是否已选择
  const isFieldSelected = (fieldId: string) => {
    return selectedFields.includes(fieldId);
  };

  const filteredFields = getFilteredFields();

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 搜索和过滤区域 */}
      <div className="card bg-base-100 shadow">
        <div className="card-body">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* 搜索框 */}
            <div className="form-control flex-1">
              <div className="input-group">
                <span>
                  <MagnifyingGlassIcon className="w-5 h-5" />
                </span>
                <input
                  type="text"
                  placeholder="搜索字段名称、描述或 Tushare 字段..."
                  className="input input-bordered flex-1"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            {/* 常用字段切换 */}
            <div className="form-control">
              <label className="label cursor-pointer">
                <span className="label-text mr-2">仅显示常用字段</span>
                <input
                  type="checkbox"
                  className="toggle toggle-primary"
                  checked={showCommonOnly}
                  onChange={(e) => setShowCommonOnly(e.target.checked)}
                />
              </label>
            </div>
          </div>

          {/* 分类筛选 */}
          <div className="flex flex-wrap gap-2 mt-4">
            {Object.values(DataFieldCategory).map(category => {
              const Icon = getCategoryIcon(category);
              const isSelected = selectedCategories.includes(category);
              
              return (
                <button
                  key={category}
                  className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => handleCategoryToggle(category)}
                >
                  <Icon className="w-4 h-4" />
                  {getCategoryDisplayName(category)}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 统计信息 */}
      <div className="stats shadow">
        <div className="stat">
          <div className="stat-title">总字段数</div>
          <div className="stat-value text-primary">{data?.total_fields || 0}</div>
        </div>
        <div className="stat">
          <div className="stat-title">当前显示</div>
          <div className="stat-value">{filteredFields.length}</div>
        </div>
        <div className="stat">
          <div className="stat-title">分类数量</div>
          <div className="stat-value">{data?.categories.length || 0}</div>
        </div>
      </div>

      {/* 字段列表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {filteredFields.map(field => (
          <div
            key={field.field_id}
            className={`card bg-base-100 shadow hover:shadow-md transition-shadow cursor-pointer border-2 ${
              isFieldSelected(field.field_id) ? 'border-primary' : 'border-transparent'
            }`}
            onClick={() => {
              setSelectedField(field);
              if (onFieldSelect) {
                onFieldSelect(field);
              }
            }}
          >
            <div className="card-body p-4">
              {/* 字段标题 */}
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-lg truncate">
                    {field.display_name}
                  </h3>
                  <p className="text-sm opacity-70 font-mono">
                    {field.field_name}
                  </p>
                </div>
                {field.is_required && (
                  <span className="badge badge-error badge-sm">必需</span>
                )}
              </div>

              {/* 字段描述 */}
              <p className="text-sm opacity-80 line-clamp-2 mt-2">
                {field.description}
              </p>

              {/* 字段信息 */}
              <div className="space-y-2 mt-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs opacity-60">类型</span>
                  <span className={`badge badge-sm ${getFieldTypeColor(field.field_type)}`}>
                    {field.field_type}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-xs opacity-60">分类</span>
                  <span className="badge badge-outline badge-sm">
                    {getCategoryDisplayName(field.category)}
                  </span>
                </div>

                {field.unit && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs opacity-60">单位</span>
                    <span className="text-xs">{field.unit}</span>
                  </div>
                )}

                {field.tushare_field && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs opacity-60">Tushare字段</span>
                    <span className="text-xs font-mono bg-base-200 px-1 rounded">
                      {field.tushare_field}
                    </span>
                  </div>
                )}
              </div>

              {/* 示例值 */}
              {field.example_value && (
                <div className="mt-3 p-2 bg-base-200 rounded">
                  <span className="text-xs opacity-60">示例值: </span>
                  <span className="text-xs font-mono">{field.example_value}</span>
                </div>
              )}

              {/* 操作按钮 */}
              <div className="card-actions justify-end mt-4">
                <button
                  className="btn btn-sm btn-ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedField(field);
                  }}
                >
                  <InformationCircleIcon className="w-4 h-4" />
                  详情
                </button>
                {mode === 'selection' && (
                  <button
                    className={`btn btn-sm ${
                      isFieldSelected(field.field_id) ? 'btn-error' : 'btn-primary'
                    }`}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onFieldSelect) {
                        onFieldSelect(field);
                      }
                    }}
                  >
                    {isFieldSelected(field.field_id) ? '移除' : '选择'}
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 无结果提示 */}
      {filteredFields.length === 0 && (
        <div className="text-center py-8">
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-lg font-semibold mb-2">未找到匹配的字段</h3>
          <p className="text-gray-500">请尝试调整搜索条件或筛选器</p>
        </div>
      )}

      {/* 字段详情模态框 */}
      {selectedField && (
        <DataFieldDetailModal
          field={selectedField}
          isOpen={!!selectedField}
          onClose={() => setSelectedField(null)}
        />
      )}
    </div>
  );
};

// 字段详情模态框组件
interface DataFieldDetailModalProps {
  field: DataField;
  isOpen: boolean;
  onClose: () => void;
}

const DataFieldDetailModal: React.FC<DataFieldDetailModalProps> = ({
  field,
  isOpen,
  onClose
}) => {
  const getCategoryDisplayName = (category: DataFieldCategory) => {
    switch (category) {
      case DataFieldCategory.PRICE:
        return '价格数据';
      case DataFieldCategory.VOLUME:
        return '成交量数据';
      case DataFieldCategory.TECHNICAL:
        return '技术指标';
      case DataFieldCategory.FUNDAMENTAL:
        return '基本面数据';
      case DataFieldCategory.DERIVED:
        return '衍生数据';
      default:
        return category;
    }
  };

  const getTushareApiUrl = (fieldName?: string) => {
    if (!fieldName) return null;
    // 根据字段名称推断可能的 Tushare API 接口
    // 这里可以根据实际情况建立更完整的映射关系
    if (['open', 'high', 'low', 'close', 'pre_close', 'vol', 'amount'].includes(fieldName)) {
      return 'https://tushare.pro/document/2?doc_id=27'; // 日线行情
    }
    if (['pe', 'pb', 'ps', 'dv_ratio', 'dv_ttm', 'total_share'].includes(fieldName)) {
      return 'https://tushare.pro/document/2?doc_id=79'; // 每日指标
    }
    return 'https://tushare.pro/document/2'; // 默认文档首页
  };

  if (!isOpen) return null;

  return (
    <div className="modal modal-open">
      <div className="modal-box max-w-4xl">
        <button
          className="btn btn-sm btn-circle absolute right-2 top-2"
          onClick={onClose}
        >
          ✕
        </button>

        <h3 className="font-bold text-lg mb-4">数据字段详情</h3>

        <div className="space-y-6">
          {/* 基本信息 */}
          <div className="card bg-base-200">
            <div className="card-body">
              <h4 className="card-title text-base">基本信息</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <span className="text-sm opacity-60">显示名称</span>
                  <p className="font-semibold">{field.display_name}</p>
                </div>
                <div>
                  <span className="text-sm opacity-60">字段名称</span>
                  <p className="font-mono text-sm">{field.field_name}</p>
                </div>
                <div>
                  <span className="text-sm opacity-60">数据类型</span>
                  <p>{field.field_type}</p>
                </div>
                <div>
                  <span className="text-sm opacity-60">分类</span>
                  <p>{getCategoryDisplayName(field.category)}</p>
                </div>
                {field.unit && (
                  <div>
                    <span className="text-sm opacity-60">单位</span>
                    <p>{field.unit}</p>
                  </div>
                )}
                <div>
                  <span className="text-sm opacity-60">状态</span>
                  <div className="flex gap-2">
                    {field.is_required && (
                      <span className="badge badge-error badge-sm">必需</span>
                    )}
                    {field.is_common && (
                      <span className="badge badge-success badge-sm">常用</span>
                    )}
                  </div>
                </div>
              </div>
              <div className="mt-4">
                <span className="text-sm opacity-60">描述</span>
                <p>{field.description}</p>
              </div>
            </div>
          </div>

          {/* Tushare 接口信息 */}
          {field.tushare_field && (
            <div className="card bg-base-200">
              <div className="card-body">
                <h4 className="card-title text-base">Tushare 接口信息</h4>
                <div className="space-y-3">
                  <div>
                    <span className="text-sm opacity-60">对应字段</span>
                    <p className="font-mono text-sm bg-base-100 p-2 rounded">
                      {field.tushare_field}
                    </p>
                  </div>
                  <div>
                    <span className="text-sm opacity-60">相关接口文档</span>
                    <div className="mt-2">
                      <a
                        href={getTushareApiUrl(field.tushare_field) || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-sm btn-outline btn-primary"
                      >
                        查看 Tushare 文档
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 示例值和验证规则 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {field.example_value && (
              <div className="card bg-base-200">
                <div className="card-body">
                  <h4 className="card-title text-base">示例值</h4>
                  <p className="font-mono text-sm bg-base-100 p-2 rounded">
                    {field.example_value}
                  </p>
                </div>
              </div>
            )}

            {field.validation_rules && (
              <div className="card bg-base-200">
                <div className="card-body">
                  <h4 className="card-title text-base">验证规则</h4>
                  <pre className="text-xs bg-base-100 p-2 rounded overflow-auto">
                    {JSON.stringify(field.validation_rules, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="modal-action">
          <button className="btn" onClick={onClose}>关闭</button>
        </div>
      </div>
    </div>
  );
};

export default DataFieldsViewer;