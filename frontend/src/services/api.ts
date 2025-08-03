// API服务层 - 统一管理后端接口调用
import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API调用失败:', error);
    return Promise.reject(error);
  }
);

// ====== 接口类型定义 ======

// 因子标签相关接口
export interface FactorTag {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  color?: string;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface FactorTagCreate {
  name: string;
  display_name: string;
  description?: string;
  color?: string;
}

export interface FactorTagUpdate {
  display_name?: string;
  description?: string;
  color?: string;
  is_active?: boolean;
}

export interface FactorTagRelation {
  factor_id: string;
  tag_ids: number[];
  tags: FactorTag[];
}

// 市场指数相关接口
export interface MarketIndex {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
}

// 因子相关接口（统一）
export interface Factor {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  code: string;
  input_fields?: string[];
  default_parameters?: Record<string, any>;
  parameter_schema?: Record<string, any>;
  calculation_method?: string;
  is_active?: boolean;
  is_builtin?: boolean;
  usage_count?: number;
  last_used_at?: string;
  created_at?: string;
  updated_at?: string;
  version?: string;
  tags?: FactorTag[];
}

export interface FactorCreate {
  id?: string;
  name: string;
  display_name: string;
  description?: string;
  code: string;
  input_fields?: string[];
  default_parameters?: Record<string, any>;
  parameter_schema?: Record<string, any>;
  calculation_method?: string;
  is_active?: boolean;
  is_builtin?: boolean;
  version?: string;
}

export interface FactorUpdate {
  name?: string;
  display_name?: string;
  description?: string;
  code?: string;
  input_fields?: string[];
  default_parameters?: Record<string, any>;
  parameter_schema?: Record<string, any>;
  calculation_method?: string;
  is_active?: boolean;
  is_builtin?: boolean;
  version?: string;
}

export interface FactorTestRequest {
  id: string;
  code: string;
  input_fields?: string[];
  parameters?: Record<string, any>;
  data?: Record<string, any>;
}

export interface FactorTestResult {
  is_valid: boolean;
  errors?: string[];
  warnings?: string[];
  result?: any;
}

export interface FactorTestResponse {
  id: string;
  is_valid: boolean;
  errors?: string[];
  warnings?: string[];
  result?: any;
}

export interface FactorValidationResult {
  id: string;
  is_valid: boolean;
  errors?: string[];
  warnings?: string[];
}

export interface FactorFormulaUpdate {
  code: string;
  description?: string;
}

export interface FactorFormulaResponse {
  id: string;
  code: string;
}

export interface FormulaValidationResult {
  id: string;
  is_valid: boolean;
  errors?: string[];
  warnings?: string[];
}

export interface CustomFactorCreateRequest {
  factor_id: string;
  name: string;
  display_name: string;
  description: string;
  tags?: FactorTag[];
  formula: string;
  input_fields: string[];
  default_parameters: Record<string, any>;
  calculation_method: string;
}

export interface FormulaHistoryEntry {
  id: string;
  old_code: string;
  new_code: string;
  old_formula?: string; // 兼容旧版本
  new_formula?: string; // 兼容旧版本
  changed_by?: string;
  change_reason?: string;
  created_at: string;
  timestamp?: string; // 兼容旧版本
  description_change?: {
    old: string;
    new: string;
  };
}

export interface FactorHistoryResponse {
  id: string;
  history: FormulaHistoryEntry[];
}

export interface FactorParameters {
  [key: string]: any;
}

export interface SelectedFactor {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  tags?: FactorTag[];
  code: string;
  weight: number;
  is_enabled: boolean;
  parameters?: Record<string, any>;
}

// 策略配置相关接口
export interface StrategyConfig {
  id: string;
  name: string;
  description: string;
  factors: SelectedFactor[];
  filters: Record<string, any>;
  max_results: number;
  created_by?: string;
  tags: string[];
  last_used_at?: string;
  usage_count: number;
  is_template: boolean;
  created_at: string;
  updated_at: string;
}

export interface StrategyTemplate {
  id: string;
  name: string;
  display_name: string;
  description: string;
  category: 'value' | 'growth' | 'momentum' | 'technical' | 'quality';
  factor_configs: SelectedFactor[];
  default_weights: Record<string, number>;
  applicable_markets: string[];
  risk_level: 'low' | 'medium' | 'high';
  expected_return_range: string;
  usage_scenarios: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// 因子分析相关接口


// 策略执行结果
export interface StrategyResult {
  symbol: string;
  name: string;
  score: number;
  rank: number;
  price: number;
  changePercent: number;
  factor_scores?: Record<string, number>;
  industry?: string;
  market_cap?: number;
}

// 自选股相关接口
export interface WatchlistStock {
  id?: number;
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  addedAt?: string;
  notes?: string;
}

export interface SearchStock {
  symbol: string;
  name: string;
  industry?: string;
  area?: string;
  market?: string;
}

export interface SyncResult {
  success: boolean;
  message: string;
  new_stocks: number;
  updated_stocks: number;
  total_fetched: number;
  errors: number;
  duration: number;
}

// 权重预设相关




// ====== API 接口 ======

// 市场数据API
export const marketApi = {
  // 获取市场指数
  getMarketIndices: async (tradeDate?: string): Promise<any[]> => {
    const params = tradeDate ? { trade_date: tradeDate } : {};
    return api.get('/market/indices', { params });
  },

  // 获取股票行情
  getStockQuotes: async (symbols?: string[]): Promise<any[]> => {
    const params = symbols ? { symbols: symbols.join(',') } : {};
    return api.get('/market/quotes', { params });
  },

  // 获取股票历史数据
  getStockHistory: async (symbol: string, days?: number) => {
    const params = { days };
    return api.get(`/market/history/${symbol}`, { params });
  },
};

// 因子API（统一）
export const factorApi = {
  // 获取所有因子
  getFactors: async (search?: string): Promise<Factor[]> => {
    const params: any = {};
    if (search) params.search = search;
    return api.get('/factors/', { params });
  },

  // 获取指定因子详情
  getFactorInfo: async (factorId: string): Promise<Factor> => {
    return api.get(`/factors/${factorId}`);
  },

  // 创建因子
  createFactor: async (factorData: Partial<Factor>): Promise<Factor> => {
    return api.post('/factors/', factorData);
  },

  // 更新因子
  updateFactor: async (factorId: string, factorData: Partial<Factor>): Promise<Factor> => {
    return api.put(`/factors/${factorId}`, factorData);
  },

  // 删除因子
  deleteFactor: async (factorId: string): Promise<{ success: boolean; message: string }> => {
    return api.delete(`/factors/${factorId}`);
  },

  // 计算因子（可选实现，需后端支持）
  calculateFactor: async (factorId: string, stockData: any, parameters?: FactorParameters) => {
    return api.post(`/factors/${factorId}/test`, {
      stock_data: stockData,
      parameters: parameters || {}
    });
  },

  // 获取因子公式历史
  getFormulaHistory: async (factorId: string) => {
    return api.get(`/factors/${factorId}/formula-history`);
  },
  
  // 获取因子历史
  getFactorHistory: async (factorId: string) => {
    return api.get(`/factors/${factorId}/history`);
  },

  // 验证因子公式
  validateFactorFormula: async (factorId: string, formula: string): Promise<FormulaValidationResult> => {
    return api.post(`/factors/${factorId}/validate-formula`, { formula });
  },

  // 更新因子公式
  updateFactorFormula: async (factorId: string, update: FactorFormulaUpdate): Promise<Factor> => {
    return api.put(`/factors/${factorId}/formula`, update);
  },

  // 重置因子公式
  resetFactorFormula: async (factorId: string) => {
    return api.post<{ success: boolean; message: string }>(`/factors/${factorId}/reset-formula`);
  },

  // 因子标签相关API
  // 获取因子标签列表
  getAllFactorTags: async (isActive?: boolean): Promise<FactorTag[]> => {
    const params: any = {};
    if (isActive !== undefined) params.is_active = isActive;
    return api.get('/factors/tags/', { params });
  },

  // 创建因子标签
  createFactorTag: async (tagData: FactorTagCreate): Promise<FactorTag> => {
    return api.post('/factors/tags/', tagData);
  },

  // 更新因子标签
  updateFactorTag: async (tagId: number, tagData: FactorTagUpdate): Promise<FactorTag> => {
    return api.put(`/factors/tags/${tagId}`, tagData);
  },

  // 删除因子标签
  deleteFactorTag: async (tagId: number): Promise<{ message: string }> => {
    return api.delete(`/factors/tags/${tagId}`);
  },

  // 创建因子标签关联
  createFactorTagRelations: async (relationData: FactorTagRelation): Promise<FactorTagRelation> => {
    return api.post('/factors/tags/relations/', relationData);
  },

  // 获取因子的标签
  getFactorTags: async (factorId: string): Promise<FactorTag[]> => {
    return api.get(`/factors/${factorId}/tags/`);
  },
};

// 策略配置管理API
export const strategyConfigApi = {
  // 获取策略配置列表
  getStrategyConfigs: async (params?: {
    page?: number;
    size?: number;
    created_by?: string;
    tags?: string[];
    search?: string;
    sort_by?: string;
    sort_order?: string;
  }) => {
    return api.get<{ items: StrategyConfig[]; total: number }>('/strategy-configs/', { params });
  },

  // 获取指定策略配置
  getStrategyConfig: async (configId: string) => {
    return api.get<StrategyConfig>(`/strategy-configs/${configId}`);
  },

  // 创建策略配置
  createStrategyConfig: async (strategyData: {
    name: string;
    description?: string;
    factors: SelectedFactor[];
    filters?: Record<string, any>;
    max_results?: number;
    tags?: string[];
  }, createdBy?: string) => {
    const params = createdBy ? { created_by: createdBy } : {};
    return api.post<StrategyConfig>('/strategy-configs/', strategyData, { params });
  },

  // 更新策略配置
  updateStrategyConfig: async (configId: string, strategyData: Partial<StrategyConfig>) => {
    return api.put<StrategyConfig>(`/strategy-configs/${configId}`, strategyData);
  },

  // 删除策略配置
  deleteStrategyConfig: async (configId: string) => {
    return api.delete(`/strategy-configs/${configId}`);
  },

  // 复制策略配置
  duplicateStrategyConfig: async (configId: string, newName?: string, createdBy?: string) => {
    return api.post<StrategyConfig>(`/strategy-configs/${configId}/duplicate`, {
      new_name: newName,
      created_by: createdBy
    });
  },

  // 批量删除策略
  batchDeleteStrategies: async (configIds: string[]) => {
    return api.post('/strategy-configs/batch-delete', { config_ids: configIds });
  },

  // 导出策略配置
  exportStrategyConfig: async (configId: string) => {
    return api.get(`/strategy-configs/${configId}/export`);
  },

  // 导入策略配置
  importStrategyConfig: async (importData: any, createdBy?: string) => {
    return api.post('/strategy-configs/import', {
      import_data: importData,
      created_by: createdBy
    });
  },

  // 策略预览
  previewStrategy: async (factors: SelectedFactor[]) => {
    return api.post('/strategy-configs/preview', { factors });
  },

  // 记录策略使用
  recordStrategyUsage: async (configId: string) => {
    return api.post(`/strategy-configs/${configId}/usage`);
  },

  // 获取热门策略
  getPopularStrategies: async (limit: number = 10) => {
    return api.get('/strategy-configs/popular', { params: { limit } });
  },

  // 获取策略统计
  getStrategyStatistics: async (createdBy?: string, days: number = 30) => {
    const params: any = { days };
    if (createdBy) params.created_by = createdBy;
    return api.get('/strategy-configs/statistics', { params });
  },
};



// 策略模板和向导API
export const templateApi = {
  // 获取策略模板列表
  getStrategyTemplates: async (category?: string) => {
    const params = category ? { category } : {};
    return api.get<StrategyTemplate[]>('/strategy-templates/', { params });
  },

  // 获取指定模板详情
  getStrategyTemplate: async (templateId: string) => {
    return api.get<StrategyTemplate>(`/strategy-templates/${templateId}`);
  },

  // 应用策略模板
  applyTemplate: async (templateId: string, customizations?: any, strategyName?: string, createdBy?: string) => {
    return api.post<StrategyConfig>(`/strategy-templates/${templateId}/apply`, {
      template_id: templateId,
      customizations,
      strategy_name: strategyName,
      created_by: createdBy
    });
  },

  // 应用模板并保存
  applyTemplateAndSave: async (templateId: string, customizations?: any, strategyName?: string, createdBy?: string) => {
    return api.post(`/strategy-templates/${templateId}/apply-and-save`, {
      template_id: templateId,
      customizations,
      strategy_name: strategyName,
      created_by: createdBy
    });
  },

  // 获取模板推荐
  getTemplateRecommendations: async (userProfile: {
    risk_preference: string;
    investment_horizon: string;
    experience_level: string;
    preferred_categories?: string[];
    investment_amount?: number;
  }) => {
    return api.post('/strategy-templates/recommendations', userProfile);
  },

  // 对比模板
  compareTemplates: async (templateIds: string[]) => {
    return api.post('/strategy-templates/compare', { template_ids: templateIds });
  },

  // 策略向导 - 开始
  startWizard: async (userProfile: {
    risk_preference: string;
    investment_horizon: string;
    experience_level: string;
    preferred_categories?: string[];
    investment_amount?: number;
  }) => {
    return api.post('/strategy-templates/wizard/start', userProfile);
  },

  // 策略向导 - 处理步骤
  processWizardStep: async (step: number, userSelections: any, userProfile?: any) => {
    return api.post(`/strategy-templates/wizard/step/${step}`, {
      step,
      user_selections: userSelections,
      user_profile: userProfile
    });
  },

  // 获取因子建议
  getFactorSuggestions: async (selectedFactorIds: string[], riskPreference: string = 'medium', strategyObjective: string = 'balanced') => {
    return api.post('/strategy-templates/wizard/factor-suggestions', {
      selected_factor_ids: selectedFactorIds,
      risk_preference: riskPreference,
      strategy_objective: strategyObjective
    });
  },
};



// 策略执行API（更新为支持新的因子系统）
export const strategyApi = {
  // 执行选股策略
  executeStrategy: async (params: {
    strategy_config_id?: string;
    factors?: SelectedFactor[];
    filters?: any;
    max_results?: number;
  }): Promise<StrategyResult[]> => {
    return api.post('/strategy-execution/execute', params);
  },

  // 获取策略历史
  getStrategyHistory: async () => {
    return api.get('/strategy-execution/history');
  },

  // 策略回测（如果需要的话）
  backtestStrategy: async (params: {
    strategy_config_id?: string;
    factors?: SelectedFactor[];
    start_date: string;
    end_date: string;
    initial_capital?: number;
  }) => {
    return api.post('/strategy-execution/backtest', params);
  },
};

// 自选股管理API（保持不变）
export const watchlistApi = {
  // 获取自选股列表
  getWatchlist: async (): Promise<WatchlistStock[]> => {
    return api.get('/watchlist');
  },

  // 添加自选股
  addToWatchlist: async (symbol: string, name: string): Promise<WatchlistStock> => {
    return api.post('/watchlist', { symbol, name });
  },

  // 删除自选股
  removeFromWatchlist: async (id: number): Promise<void> => {
    return api.delete(`/watchlist/${id}`);
  },

  // 批量更新自选股价格
  updateWatchlistPrices: async (): Promise<WatchlistStock[]> => {
    return api.post('/watchlist/update-prices');
  },
};

// 股票数据管理API（保持不变）
export const stockApi = {
  // 搜索股票
  searchStocks: async (keyword: string, limit: number = 20): Promise<SearchStock[]> => {
    const params = { q: keyword, limit };
    return api.get('/stocks/search', { params });
  },

  // 获取股票同步信息
  getSyncInfo: async () => {
    return api.get('/stocks/sync/info');
  },

  // 同步股票数据
  syncStockData: async (): Promise<SyncResult> => {
    return api.post('/stocks/sync');
  },

  // 获取股票统计
  getStockStats: async () => {
    const params = { _t: Date.now() };
    return api.get('/stocks/stats', { params });
  },
};

// 数据字段配置相关接口
export interface DataField {
  field_id: string;
  field_name: string;
  display_name: string;
  description: string;
  category: DataFieldCategory;
  field_type: DataFieldType;
  unit?: string;
  is_required: boolean;
  is_common: boolean;
  tushare_field?: string;
  example_value?: string;
  validation_rules?: Record<string, any>;
}

export interface DataFieldConfig {
  category: DataFieldCategory;
  fields: DataField[];
  description: string;
}

export enum DataFieldCategory {
  PRICE = "price",
  VOLUME = "volume", 
  TECHNICAL = "technical",
  FUNDAMENTAL = "fundamental",
  DERIVED = "derived"
}

export enum DataFieldType {
  NUMERIC = "numeric",
  STRING = "string",
  DATE = "date",
  BOOLEAN = "boolean"
}

export interface FactorInputFieldsResponse {
  categories: DataFieldConfig[];
  total_fields: number;
}

export interface FieldValidationResult {
  status: "valid" | "warning" | "error";
  message: string;
}

// 数据字段配置API
export const dataFieldApi = {
  // 获取因子输入字段配置
  getFactorInputFields: async (
    categories?: DataFieldCategory[],
    includeCommonOnly: boolean = true
  ): Promise<FactorInputFieldsResponse> => {
    const params: Record<string, any> = {
      include_common_only: includeCommonOnly
    };
    
    if (categories && categories.length > 0) {
      // FastAPI需要重复参数名来处理数组
      categories.forEach(category => {
        if (!params.categories) params.categories = [];
        params.categories.push(category);
      });
    }
    
    return api.get('/data/fields', { params });
  },

  // 获取常用字段
  getCommonFields: async (): Promise<DataField[]> => {
    return api.get('/data/fields/common');
  },

  // 根据字段ID获取字段信息
  getFieldById: async (fieldId: string): Promise<DataField> => {
    return api.get(`/data/fields/${fieldId}`);
  },

  // 验证字段组合
  validateFieldCombination: async (fieldIds: string[]): Promise<FieldValidationResult> => {
    return api.post('/data/fields/validate', fieldIds);
  }
};

// 策略管理相关接口
export interface StrategyFactor {
  factor_id: string;
  weight: number;
  is_enabled: boolean;
}

export interface StrategyFilter {
  min_market_cap?: number;
  max_market_cap?: number;
  min_price?: number;
  max_price?: number;
  min_turnover?: number;
  max_turnover?: number;
  exclude_st: boolean;
  exclude_new_stock: boolean;
  exclude_suspend: boolean;
  industries?: string[];
  exclude_industries?: string[];
}

export interface StrategyConfig {
  max_results: number;
  rebalance_frequency: string;
  ranking_method: string;
}

export interface Strategy {
  strategy_id: string;
  name: string;
  description?: string;
  factors: StrategyFactor[];
  filters?: StrategyFilter;
  config?: StrategyConfig;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
  execution_count: number;
  last_executed_at?: string;
  avg_execution_time?: number;
  last_result_count?: number;
}

export interface StrategyCreate {
  name: string;
  description?: string;
  factors: StrategyFactor[];
  filters?: StrategyFilter;
  config?: StrategyConfig;
}

export interface StrategyUpdate {
  name?: string;
  description?: string;
  factors?: StrategyFactor[];
  filters?: StrategyFilter;
  config?: StrategyConfig;
  is_active?: boolean;
}

export interface StrategyListResponse {
  strategies: Strategy[];
  total: number;
  skip: number;
  limit: number;
}

export interface StrategyExecutionRequest {
  execution_date?: string;
  dry_run?: boolean;
  save_result?: boolean;
}

export interface StrategyExecutionResult {
  execution_id: string;
  strategy_id: string;
  execution_date: string;
  execution_time: number;
  stock_count: number;
  is_dry_run: boolean;
  status: string;
  error_message?: string;
  created_at: string;
}

export interface SelectedStock {
  stock_code: string;
  stock_name: string;
  composite_score: number;
  factor_scores: Record<string, number>;
  rank: number;
  market_cap?: number;
  price?: number;
  industry?: string;
}

export interface StrategyExecutionDetail extends StrategyExecutionResult {
  selected_stocks: SelectedStock[];
  factor_performance: Record<string, any>;
  execution_log: string[];
}

export interface AvailableFactor {
  factor_id: string;
  factor_name: string;
  display_name: string;
  description?: string;
  tags?: FactorTag[];
  is_active: boolean;
}

// 策略管理API
export const strategyManagementApi = {
  // 创建策略
  createStrategy: async (strategyData: StrategyCreate, createdBy?: string): Promise<Strategy> => {
    const params = createdBy ? { created_by: createdBy } : {};
    return api.post('/strategy-management/', strategyData, { params });
  },

  // 获取策略列表
  getStrategies: async (params?: {
    is_active?: boolean;
    created_by?: string;
    keyword?: string;
    skip?: number;
    limit?: number;
  }): Promise<StrategyListResponse> => {
    return api.get('/strategy-management/', { params });
  },

  // 获取单个策略
  getStrategy: async (strategyId: string): Promise<Strategy> => {
    return api.get(`/strategy-management/${strategyId}`);
  },

  // 更新策略
  updateStrategy: async (strategyId: string, strategyData: StrategyUpdate): Promise<Strategy> => {
    return api.put(`/strategy-management/${strategyId}`, strategyData);
  },

  // 删除策略
  deleteStrategy: async (strategyId: string): Promise<{ message: string }> => {
    return api.delete(`/strategy-management/${strategyId}`);
  },

  // 执行策略
  executeStrategy: async (strategyId: string, request: StrategyExecutionRequest): Promise<StrategyExecutionResult> => {
    return api.post(`/strategy-management/${strategyId}/execute`, request);
  },

  // 获取执行历史
  getExecutionHistory: async (strategyId: string, limit?: number): Promise<StrategyExecutionResult[]> => {
    const params = limit ? { limit } : {};
    return api.get(`/strategy-management/${strategyId}/executions`, { params });
  },

  // 获取执行详情
  getExecutionDetail: async (executionId: string): Promise<StrategyExecutionDetail> => {
    return api.get(`/strategy-management/executions/${executionId}`);
  },

  // 获取可用因子
  getAvailableFactors: async (strategyId: string): Promise<{ factors: AvailableFactor[] }> => {
    return api.get(`/strategy-management/${strategyId}/available-factors`);
  },

  // 验证策略
  validateStrategy: async (strategyId: string): Promise<{
    is_valid: boolean;
    errors: string[];
    warnings: string[];
  }> => {
    return api.post(`/strategy-management/${strategyId}/validate`);
  }
};

// 健康检查
export const healthCheck = async () => {
  return api.get('/test');
};

export default api;