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

// 市场数据相关接口
export interface MarketIndex {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  amount?: number;
  tradeDate?: string;
}

export interface StockQuote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume?: number;
  amount?: number;
}

// 内置因子相关接口
export interface BuiltinFactor {
  factor_id: string;
  name: string;
  display_name: string;
  description: string;
  category: 'trend' | 'momentum' | 'volume';
  calculation_method: 'pandas' | 'talib' | 'custom';
  formula: string;
  default_parameters: Record<string, any>;
  parameter_schema: Record<string, any>;
  input_fields: string[];
  output_type: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FactorParameters {
  period?: number;
  fast_period?: number;
  slow_period?: number;
  signal_period?: number;
  multiplier?: number;
  custom_params?: Record<string, any>;
}

export interface SelectedFactor {
  factor_id: string;
  factor_type: 'builtin' | 'custom';
  factor_name: string;
  parameters: FactorParameters;
  weight: number;
  is_enabled: boolean;
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
export interface FactorStatistics {
  id: number;
  factor_id: string;
  factor_type: string;
  analysis_date: string;
  mean: number;
  std: number;
  min: number;
  max: number;
  median: number;
  q25: number;
  q75: number;
  skewness: number;
  kurtosis: number;
  null_ratio: number;
  effectiveness_score: number;
}

export interface CorrelationMatrix {
  correlation_matrix: Record<string, Record<string, number>>;
  factor_names: string[];
  method: string;
  sample_size: number;
  calculation_date: string;
}

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
export interface WeightPreset {
  id: string;
  name: string;
  description: string;
  applicable_categories: string[];
}

export interface WeightOptimizationResult {
  optimized_factors: SelectedFactor[];
  optimization_method: string;
  performance_metrics: Record<string, number>;
  recommendations: string[];
  analysis_details: Record<string, any>;
}

export interface FactorFormulaUpdate {
  formula: string;
  description?: string;
}

export interface FactorFormulaResponse {
  factor_id: string;
  formula: string;
  description: string;
  updated_at: string;
  success: boolean;
}

export interface FormulaValidationResult {
  factor_id: string;
  formula: string;
  is_valid: boolean;
  error_message?: string;
  warnings?: string[];
}

export interface FormulaHistoryEntry {
  timestamp: string;
  old_formula: string;
  new_formula: string;
  description_change: {
    old: string;
    new: string;
  };
}

// ====== API 接口 ======

// 市场数据API
export const marketApi = {
  // 获取市场指数
  getMarketIndices: async (tradeDate?: string): Promise<MarketIndex[]> => {
    const params = tradeDate ? { trade_date: tradeDate } : {};
    return api.get('/market/indices', { params });
  },

  // 获取股票行情
  getStockQuotes: async (symbols?: string[]): Promise<StockQuote[]> => {
    const params = symbols ? { symbols: symbols.join(',') } : {};
    return api.get('/market/quotes', { params });
  },

  // 获取股票历史数据
  getStockHistory: async (symbol: string, days?: number) => {
    const params = { days };
    return api.get(`/market/history/${symbol}`, { params });
  },
};

// 内置因子库API
export const builtinFactorApi = {
  // 获取所有内置因子
  getBuiltinFactors: async (category?: string, search?: string): Promise<BuiltinFactor[]> => {
    const params: any = {};
    if (category) params.category = category;
    if (search) params.search = search;
    return api.get('/builtin-factors/', { params });
  },

  // 获取因子分类
  getFactorCategories: async () => {
    return api.get('/builtin-factors/categories');
  },

  // 获取指定因子详情
  getFactorInfo: async (factorId: string): Promise<BuiltinFactor> => {
    return api.get(`/builtin-factors/${factorId}`);
  },

  // 预览因子计算结果
  previewFactor: async (factorId: string, sampleData: any, parameters?: FactorParameters) => {
    return api.post(`/builtin-factors/${factorId}/preview`, {
      sample_data: sampleData,
      parameters: parameters || {}
    });
  },

  // 验证因子参数
  validateFactorParameters: async (factorId: string, parameters: FactorParameters) => {
    return api.post(`/builtin-factors/${factorId}/validate`, { parameters });
  },

  // 计算单个因子
  calculateFactor: async (factorId: string, stockData: any, parameters?: FactorParameters) => {
    return api.post('/builtin-factors/calculate', {
      factor_id: factorId,
      stock_data: stockData,
      parameters: parameters || {}
    });
  },

  // 批量计算因子
  batchCalculateFactors: async (factorConfigs: Array<{
    factor_id: string;
    parameters?: FactorParameters;
  }>, stockData: any) => {
    return api.post('/builtin-factors/batch-calculate', {
      factor_configs: factorConfigs,
      stock_data: stockData
    });
  },

  // 获取引擎状态
  getEngineStatus: async () => {
    return api.get('/builtin-factors/engine/status');
  },

  // 清除缓存
  clearCache: async () => {
    return api.post('/builtin-factors/engine/clear-cache');
  },

  // 更新因子公式
  updateFactorFormula: async (factorId: string, update: FactorFormulaUpdate): Promise<FactorFormulaResponse> => {
    const response = await api.put(`/api/v1/builtin-factors/${factorId}/formula`, update);
    return response.data;
  },

  // 验证因子公式
  validateFactorFormula: async (factorId: string, formula: string): Promise<FormulaValidationResult> => {
    const response = await api.post(`/api/v1/builtin-factors/${factorId}/validate-formula`, {
      formula,
    });
    return response.data;
  },

  // 获取因子公式历史记录
  getFactorFormulaHistory: async (factorId: string): Promise<{ factor_id: string; history: FormulaHistoryEntry[] }> => {
    const response = await api.get(`/api/v1/builtin-factors/${factorId}/formula-history`);
    return response.data;
  },

  // 重置因子公式
  resetFactorFormula: async (factorId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post(`/api/v1/builtin-factors/${factorId}/reset-formula`);
    return response.data;
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
    return api.get('/strategy-configs/', { params });
  },

  // 获取指定策略配置
  getStrategyConfig: async (configId: string): Promise<StrategyConfig> => {
    return api.get(`/strategy-configs/${configId}`);
  },

  // 创建策略配置
  createStrategyConfig: async (strategyData: {
    name: string;
    description?: string;
    factors: SelectedFactor[];
    filters?: Record<string, any>;
    max_results?: number;
    tags?: string[];
  }, createdBy?: string): Promise<StrategyConfig> => {
    const params = createdBy ? { created_by: createdBy } : {};
    return api.post('/strategy-configs/', strategyData, { params });
  },

  // 更新策略配置
  updateStrategyConfig: async (configId: string, strategyData: Partial<StrategyConfig>): Promise<StrategyConfig> => {
    return api.put(`/strategy-configs/${configId}`, strategyData);
  },

  // 删除策略配置
  deleteStrategyConfig: async (configId: string) => {
    return api.delete(`/strategy-configs/${configId}`);
  },

  // 复制策略配置
  duplicateStrategyConfig: async (configId: string, newName?: string, createdBy?: string) => {
    return api.post(`/strategy-configs/${configId}/duplicate`, {
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

// 权重管理API
export const weightApi = {
  // 验证权重配置
  validateWeights: async (factors: SelectedFactor[]) => {
    return api.post('/strategy-configs/weights/validate', { factors });
  },

  // 标准化权重
  normalizeWeights: async (factors: SelectedFactor[], targetSum: number = 1.0) => {
    return api.post('/strategy-configs/weights/normalize', {
      factors,
      target_sum: targetSum
    });
  },

  // 获取权重预设
  getWeightPresets: async (): Promise<WeightPreset[]> => {
    return api.get('/strategy-configs/weights/presets');
  },

  // 应用权重预设
  applyWeightPreset: async (factors: SelectedFactor[], presetId: string) => {
    return api.post('/strategy-configs/weights/apply-preset', {
      factors,
      preset_id: presetId
    });
  },

  // 优化权重
  optimizeWeights: async (factors: SelectedFactor[], optimizationMethod: string = 'correlation_adjusted'): Promise<WeightOptimizationResult> => {
    return api.post('/strategy-configs/weights/optimize', {
      factors,
      optimization_method: optimizationMethod
    });
  },

  // 获取权重建议
  getWeightSuggestions: async (factors: SelectedFactor[]) => {
    return api.post('/strategy-configs/weights/suggestions', { factors });
  },
};

// 策略模板和向导API
export const templateApi = {
  // 获取策略模板列表
  getStrategyTemplates: async (category?: string): Promise<StrategyTemplate[]> => {
    const params = category ? { category } : {};
    return api.get('/strategy-templates/', { params });
  },

  // 获取指定模板详情
  getStrategyTemplate: async (templateId: string): Promise<StrategyTemplate> => {
    return api.get(`/strategy-templates/${templateId}`);
  },

  // 应用策略模板
  applyTemplate: async (templateId: string, customizations?: any, strategyName?: string, createdBy?: string) => {
    return api.post(`/strategy-templates/${templateId}/apply`, {
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

// 因子分析API
export const factorAnalysisApi = {
  // 分析单个因子统计特征
  analyzeFactorStatistics: async (factorValues: number[], factorId?: string, factorName?: string) => {
    return api.post('/factor-analysis/statistics', {
      factor_values: factorValues,
      factor_id: factorId,
      factor_name: factorName
    });
  },

  // 计算相关性矩阵
  calculateCorrelationMatrix: async (factorData: Record<string, number[]>, method: string = 'pearson', threshold: number = 0.7) => {
    return api.post('/factor-analysis/correlation-matrix', {
      factor_data: factorData,
      method,
      threshold
    });
  },

  // 因子聚类分析
  performFactorClustering: async (factorData: Record<string, number[]>) => {
    return api.post('/factor-analysis/clustering', {
      factor_data: factorData
    });
  },

  // 多重共线性检测
  detectMulticollinearity: async (factorData: Record<string, number[]>) => {
    return api.post('/factor-analysis/multicollinearity', {
      factor_data: factorData
    });
  },

  // 主成分分析
  performPCA: async (factorData: Record<string, number[]>, nComponents?: number) => {
    const params = nComponents ? { n_components: nComponents } : {};
    return api.post('/factor-analysis/pca', { factor_data: factorData }, { params });
  },

  // 因子有效性分析
  analyzeFactorEffectiveness: async (factorValues: number[], factorId?: string, stockMetadata?: any) => {
    return api.post('/factor-analysis/effectiveness', {
      factor_values: factorValues,
      factor_id: factorId,
      stock_metadata: stockMetadata
    });
  },

  // 比较多个因子
  compareFactors: async (factorData: Record<string, number[]>, analysisTypes: string[] = ['statistics', 'correlation', 'effectiveness']) => {
    return api.post('/factor-analysis/compare-factors', {
      factor_data: factorData,
      analysis_types: analysisTypes
    });
  },

  // 分位数分析
  performQuantileAnalysis: async (factorValues: number[], stockReturns?: number[]) => {
    return api.post('/factor-analysis/quantile-analysis', {
      factor_values: factorValues,
      stock_returns: stockReturns
    });
  },

  // 因子组合有效性分析
  analyzeCombinationEffectiveness: async (factorData: Record<string, number[]>, weights?: number[]) => {
    return api.post('/factor-analysis/combination-effectiveness', factorData, {
      params: weights ? { weights: weights.join(',') } : {}
    });
  },

  // 批量因子分析
  performBatchAnalysis: async (factorData: Record<string, number[]>, analysisTypes: string[] = ['statistics', 'correlation', 'effectiveness']) => {
    return api.post('/factor-analysis/batch-analysis', factorData, {
      params: { analysis_types: analysisTypes.join(',') }
    });
  },

  // 获取因子统计历史
  getFactorStatisticsHistory: async (factorId: string, days: number = 30) => {
    return api.get(`/factor-analysis/statistics/history/${factorId}`, {
      params: { days }
    });
  },

  // 获取因子相关性历史
  getFactorCorrelationHistory: async (factorId: string, days: number = 30) => {
    return api.get(`/factor-analysis/correlation/history/${factorId}`, {
      params: { days }
    });
  },

  // 获取分析汇总
  getAnalysisSummary: async (factorIds: string[], days: number = 7) => {
    return api.get('/factor-analysis/analysis-summary', {
      params: {
        factor_ids: factorIds.join(','),
        days
      }
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
    return api.post('/strategies/execute', params);
  },

  // 获取策略历史
  getStrategyHistory: async () => {
    return api.get('/strategies/history');
  },

  // 策略回测（如果需要的话）
  backtestStrategy: async (params: {
    strategy_config_id?: string;
    factors?: SelectedFactor[];
    start_date: string;
    end_date: string;
    initial_capital?: number;
  }) => {
    return api.post('/strategies/backtest', params);
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

// 健康检查
export const healthCheck = async () => {
  return api.get('/test');
};

export default api;