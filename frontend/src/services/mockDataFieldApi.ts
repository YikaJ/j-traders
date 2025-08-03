// 模拟数据字段API服务
import { 
  DataField, 
  DataFieldConfig, 
  DataFieldCategory, 
  DataFieldType,
  FactorInputFieldsResponse,
  FieldValidationResult 
} from './api';

// 模拟数据
const MOCK_DATA_FIELDS: Record<DataFieldCategory, DataField[]> = {
  [DataFieldCategory.PRICE]: [
    {
      field_id: "open",
      field_name: "open",
      display_name: "开盘价",
      description: "当日开盘价格",
      category: DataFieldCategory.PRICE,
      field_type: DataFieldType.NUMERIC,
      unit: "元",
      is_required: false,
      is_common: true,
      tushare_field: "open",
      example_value: "12.45",
      validation_rules: { min: 0, max: 10000 }
    },
    {
      field_id: "high",
      field_name: "high",
      display_name: "最高价",
      description: "当日最高价格",
      category: DataFieldCategory.PRICE,
      field_type: DataFieldType.NUMERIC,
      unit: "元",
      is_required: false,
      is_common: true,
      tushare_field: "high",
      example_value: "12.89",
      validation_rules: { min: 0, max: 10000 }
    },
    {
      field_id: "low",
      field_name: "low",
      display_name: "最低价",
      description: "当日最低价格",
      category: DataFieldCategory.PRICE,
      field_type: DataFieldType.NUMERIC,
      unit: "元",
      is_required: false,
      is_common: true,
      tushare_field: "low",
      example_value: "12.01",
      validation_rules: { min: 0, max: 10000 }
    },
    {
      field_id: "close",
      field_name: "close",
      display_name: "收盘价",
      description: "当日收盘价格",
      category: DataFieldCategory.PRICE,
      field_type: DataFieldType.NUMERIC,
      unit: "元",
      is_required: true,
      is_common: true,
      tushare_field: "close",
      example_value: "12.34",
      validation_rules: { min: 0, max: 10000 }
    },
    {
      field_id: "pre_close",
      field_name: "pre_close",
      display_name: "前收盘价",
      description: "前一交易日收盘价",
      category: DataFieldCategory.PRICE,
      field_type: DataFieldType.NUMERIC,
      unit: "元",
      is_required: false,
      is_common: true,
      tushare_field: "pre_close",
      example_value: "12.10",
      validation_rules: { min: 0, max: 10000 }
    },
    {
      field_id: "adj_close",
      field_name: "adj_close",
      display_name: "复权收盘价",
      description: "前复权收盘价",
      category: DataFieldCategory.PRICE,
      field_type: DataFieldType.NUMERIC,
      unit: "元",
      is_required: false,
      is_common: false,
      tushare_field: "adj_close",
      example_value: "12.50",
      validation_rules: { min: 0, max: 10000 }
    }
  ],
  [DataFieldCategory.VOLUME]: [
    {
      field_id: "vol",
      field_name: "vol",
      display_name: "成交量",
      description: "当日成交量",
      category: DataFieldCategory.VOLUME,
      field_type: DataFieldType.NUMERIC,
      unit: "手",
      is_required: false,
      is_common: true,
      tushare_field: "vol",
      example_value: "12345",
      validation_rules: { min: 0 }
    },
    {
      field_id: "amount",
      field_name: "amount",
      display_name: "成交额",
      description: "当日成交金额",
      category: DataFieldCategory.VOLUME,
      field_type: DataFieldType.NUMERIC,
      unit: "千元",
      is_required: false,
      is_common: true,
      tushare_field: "amount",
      example_value: "1234567",
      validation_rules: { min: 0 }
    },
    {
      field_id: "turnover_rate",
      field_name: "turnover_rate",
      display_name: "换手率",
      description: "当日换手率",
      category: DataFieldCategory.VOLUME,
      field_type: DataFieldType.NUMERIC,
      unit: "%",
      is_required: false,
      is_common: true,
      tushare_field: "turnover_rate",
      example_value: "2.5",
      validation_rules: { min: 0, max: 100 }
    }
  ],
  [DataFieldCategory.TECHNICAL]: [
    {
      field_id: "ma5",
      field_name: "ma5",
      display_name: "5日均线",
      description: "5日移动平均线",
      category: DataFieldCategory.TECHNICAL,
      field_type: DataFieldType.NUMERIC,
      unit: "元",
      is_required: false,
      is_common: true,
      tushare_field: null,
      example_value: "12.50",
      validation_rules: { min: 0 }
    },
    {
      field_id: "ma20",
      field_name: "ma20",
      display_name: "20日均线",
      description: "20日移动平均线",
      category: DataFieldCategory.TECHNICAL,
      field_type: DataFieldType.NUMERIC,
      unit: "元",
      is_required: false,
      is_common: true,
      tushare_field: null,
      example_value: "12.80",
      validation_rules: { min: 0 }
    },
    {
      field_id: "rsi",
      field_name: "rsi",
      display_name: "RSI指标",
      description: "相对强弱指标",
      category: DataFieldCategory.TECHNICAL,
      field_type: DataFieldType.NUMERIC,
      unit: "",
      is_required: false,
      is_common: false,
      tushare_field: null,
      example_value: "65.5",
      validation_rules: { min: 0, max: 100 }
    },
    {
      field_id: "macd",
      field_name: "macd",
      display_name: "MACD指标",
      description: "指数移动平均线聚合/分离",
      category: DataFieldCategory.TECHNICAL,
      field_type: DataFieldType.NUMERIC,
      unit: "",
      is_required: false,
      is_common: false,
      tushare_field: null,
      example_value: "0.15",
      validation_rules: {}
    }
  ],
  [DataFieldCategory.FUNDAMENTAL]: [
    {
      field_id: "pe",
      field_name: "pe",
      display_name: "市盈率",
      description: "市盈率TTM",
      category: DataFieldCategory.FUNDAMENTAL,
      field_type: DataFieldType.NUMERIC,
      unit: "倍",
      is_required: false,
      is_common: true,
      tushare_field: "pe_ttm",
      example_value: "15.5",
      validation_rules: { min: 0 }
    },
    {
      field_id: "pb",
      field_name: "pb",
      display_name: "市净率",
      description: "市净率",
      category: DataFieldCategory.FUNDAMENTAL,
      field_type: DataFieldType.NUMERIC,
      unit: "倍",
      is_required: false,
      is_common: true,
      tushare_field: "pb",
      example_value: "1.8",
      validation_rules: { min: 0 }
    },
    {
      field_id: "ps",
      field_name: "ps",
      display_name: "市销率",
      description: "市销率TTM",
      category: DataFieldCategory.FUNDAMENTAL,
      field_type: DataFieldType.NUMERIC,
      unit: "倍",
      is_required: false,
      is_common: false,
      tushare_field: "ps_ttm",
      example_value: "2.5",
      validation_rules: { min: 0 }
    },
    {
      field_id: "total_share",
      field_name: "total_share",
      display_name: "总股本",
      description: "总股本数量",
      category: DataFieldCategory.FUNDAMENTAL,
      field_type: DataFieldType.NUMERIC,
      unit: "万股",
      is_required: false,
      is_common: true,
      tushare_field: "total_share",
      example_value: "100000",
      validation_rules: { min: 0 }
    },
    {
      field_id: "float_share",
      field_name: "float_share",
      display_name: "流通股本",
      description: "流通股本数量",
      category: DataFieldCategory.FUNDAMENTAL,
      field_type: DataFieldType.NUMERIC,
      unit: "万股",
      is_required: false,
      is_common: true,
      tushare_field: "float_share",
      example_value: "80000",
      validation_rules: { min: 0 }
    }
  ],
  [DataFieldCategory.DERIVED]: [
    {
      field_id: "price_change",
      field_name: "price_change",
      display_name: "涨跌额",
      description: "相对前一交易日的涨跌额",
      category: DataFieldCategory.DERIVED,
      field_type: DataFieldType.NUMERIC,
      unit: "元",
      is_required: false,
      is_common: true,
      tushare_field: "change",
      example_value: "0.24",
      validation_rules: {}
    },
    {
      field_id: "price_change_pct",
      field_name: "price_change_pct",
      display_name: "涨跌幅",
      description: "相对前一交易日的涨跌幅",
      category: DataFieldCategory.DERIVED,
      field_type: DataFieldType.NUMERIC,
      unit: "%",
      is_required: false,
      is_common: true,
      tushare_field: "pct_chg",
      example_value: "2.0",
      validation_rules: {}
    },
    {
      field_id: "market_cap",
      field_name: "market_cap",
      display_name: "总市值",
      description: "总市值",
      category: DataFieldCategory.DERIVED,
      field_type: DataFieldType.NUMERIC,
      unit: "万元",
      is_required: false,
      is_common: true,
      tushare_field: null,
      example_value: "1000000",
      validation_rules: { min: 0 }
    }
  ]
};

const getCategoryDescription = (category: DataFieldCategory): string => {
  const descriptions = {
    [DataFieldCategory.PRICE]: "价格相关的基础数据字段，包括开盘价、收盘价、最高价、最低价等",
    [DataFieldCategory.VOLUME]: "成交量相关的数据字段，包括成交量、成交额、换手率等",
    [DataFieldCategory.TECHNICAL]: "技术指标相关的数据字段，包括移动平均线、技术指标等",
    [DataFieldCategory.FUNDAMENTAL]: "基本面数据字段，包括财务指标、估值指标等",
    [DataFieldCategory.DERIVED]: "衍生计算字段，基于基础数据计算得出的字段"
  };
  return descriptions[category] || "";
};

// 模拟API服务
export const mockDataFieldApi = {
  // 获取因子输入字段配置
  getFactorInputFields: async (
    categories?: DataFieldCategory[],
    includeCommonOnly: boolean = true
  ): Promise<FactorInputFieldsResponse> => {
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 筛选分类
    const selectedCategories = categories || Object.values(DataFieldCategory);
    
    // 构建响应数据
    const categoryConfigs: DataFieldConfig[] = [];
    let totalFields = 0;
    
    for (const category of selectedCategories) {
      if (category in MOCK_DATA_FIELDS) {
        let fields = MOCK_DATA_FIELDS[category];
        
        // 根据是否只显示常用字段进行筛选
        if (includeCommonOnly) {
          fields = fields.filter(f => f.is_common);
        }
        
        if (fields.length > 0) {
          const categoryConfig: DataFieldConfig = {
            category,
            fields,
            description: getCategoryDescription(category)
          };
          categoryConfigs.push(categoryConfig);
          totalFields += fields.length;
        }
      }
    }
    
    return {
      categories: categoryConfigs,
      total_fields: totalFields
    };
  },

  // 获取常用字段
  getCommonFields: async (): Promise<DataField[]> => {
    await new Promise(resolve => setTimeout(resolve, 200));
    
    const commonFields: DataField[] = [];
    for (const fields of Object.values(MOCK_DATA_FIELDS)) {
      commonFields.push(...fields.filter(f => f.is_common));
    }
    return commonFields;
  },

  // 根据字段ID获取字段信息
  getFieldById: async (fieldId: string): Promise<DataField> => {
    await new Promise(resolve => setTimeout(resolve, 200));
    
    for (const fields of Object.values(MOCK_DATA_FIELDS)) {
      const field = fields.find(f => f.field_id === fieldId);
      if (field) {
        return field;
      }
    }
    
    throw new Error(`字段 ${fieldId} 未找到`);
  },

  // 验证字段组合
  validateFieldCombination: async (fieldIds: string[]): Promise<FieldValidationResult> => {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    const result: FieldValidationResult = { status: "valid", message: "" };
    
    // 检查字段是否存在
    const allFields: DataField[] = [];
    for (const fields of Object.values(MOCK_DATA_FIELDS)) {
      allFields.push(...fields);
    }
    
    const allFieldIds = allFields.map(f => f.field_id);
    const invalidFields = fieldIds.filter(fid => !allFieldIds.includes(fid));
    
    if (invalidFields.length > 0) {
      result.status = "error";
      result.message = `无效字段: ${invalidFields.join(', ')}`;
      return result;
    }
    
    // 检查是否包含必需字段
    const requiredFields = allFields.filter(f => f.is_required).map(f => f.field_id);
    const missingRequired = requiredFields.filter(f => !fieldIds.includes(f));
    
    if (missingRequired.length > 0) {
      result.status = "warning";
      result.message = `缺少必需字段: ${missingRequired.join(', ')}`;
    }
    
    return result;
  }
};