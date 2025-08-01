// API服务层 - 统一管理后端接口调用
import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000,
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

export interface Factor {
  id: string;
  name: string;
  description: string;
  category: string;
  code: string;
}

export interface StrategyResult {
  symbol: string;
  name: string;
  score: number;
  rank: number;
  price: number;
  changePercent: number;
}

export interface WatchlistStock {
  id?: number;
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  addedAt?: string;
}

export interface SearchStock {
  symbol: string;
  name: string;
  industry?: string;
  area?: string;
  market?: string;
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
  getStockHistory: async (symbol: string, startDate?: string, endDate?: string) => {
    const params = { symbol, start_date: startDate, end_date: endDate };
    return api.get('/market/history', { params });
  },
};

// 因子管理API
export const factorApi = {
  // 获取所有因子
  getFactors: async (): Promise<Factor[]> => {
    return api.get('/factors');
  },

  // 创建因子
  createFactor: async (factor: Omit<Factor, 'id'>): Promise<Factor> => {
    return api.post('/factors', factor);
  },

  // 更新因子
  updateFactor: async (id: string, factor: Partial<Factor>): Promise<Factor> => {
    return api.put(`/factors/${id}`, factor);
  },

  // 删除因子
  deleteFactor: async (id: string): Promise<void> => {
    return api.delete(`/factors/${id}`);
  },

  // 测试因子
  testFactor: async (factorCode: string, symbols?: string[]) => {
    return api.post('/factors/test', { code: factorCode, symbols });
  },
};

// 策略执行API
export const strategyApi = {
  // 执行选股策略
  executeStrategy: async (params: {
    factors: string[];
    maxResults?: number;
    filters?: any;
  }): Promise<StrategyResult[]> => {
    return api.post('/strategies/execute', params);
  },

  // 获取策略历史
  getStrategyHistory: async () => {
    return api.get('/strategies/history');
  },

  // 回测策略
  backtestStrategy: async (params: {
    factors: string[];
    startDate: string;
    endDate: string;
    initialCapital?: number;
  }) => {
    return api.post('/strategies/backtest', params);
  },
};

// 自选股管理API
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

// 股票数据管理API
export const stockApi = {
  // 搜索股票
  searchStocks: async (keyword: string, limit: number = 20): Promise<SearchStock[]> => {
    const params = { q: keyword, limit };
    return api.get('/stocks/search', { params });
  },

  // 获取股票同步信息
  getSyncInfo: async () => {
    // 添加时间戳防止缓存
    return api.get('/stocks/sync/info');
  },

  // 同步股票数据
  syncStockData: async (): Promise<SyncResult> => {
    return api.post('/stocks/sync');
  },

  // 获取股票统计
  getStockStats: async () => {
    // 添加时间戳防止缓存
    const params = { _t: Date.now() };
    return api.get('/stocks/stats', { params });
  },
};

// 健康检查
export const healthCheck = async () => {
  return api.get('/test');
};

export default api;