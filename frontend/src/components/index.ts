// 统一导出所有组件
export { default as FactorLibrary } from './FactorLibrary';
export { default as StrategyConfigManager } from './StrategyConfigManager';
export { default as WeightConfigPanel } from './WeightConfigPanel';
export { default as FactorAnalysisPanel } from './FactorAnalysisPanel';

// Dashboard 相关组件
export { default as MarketIndicesCard } from './dashboard/MarketIndicesCard';
export { default as StockDataManagement } from './dashboard/StockDataManagement';
export { default as ShanghaiIndexChart } from './dashboard/ShanghaiIndexChart';
export { default as WatchlistMonitor } from './dashboard/WatchlistMonitor';
export { default as StockSyncModal } from './dashboard/StockSyncModal';
export { default as MessageAlert } from './dashboard/MessageAlert';

// Quantitative Selection 相关组件
export { default as SelectionWizard } from './quantitative/SelectionWizard';
export { default as SelectedFactorsOverview } from './quantitative/SelectedFactorsOverview';
export { default as StrategyResultModal } from './quantitative/StrategyResultModal';

// Watchlist 相关组件
export { default as StockSearchModal } from './watchlist/StockSearchModal';
export { default as DeleteConfirmModal } from './watchlist/DeleteConfirmModal';

// 通用组件
export { default as ThemeToggle } from './common/ThemeToggle';

// 导出组件相关的类型
export type {
  BuiltinFactor,
  SelectedFactor,
  StrategyConfig,
  WeightPreset,
  WeightOptimizationResult,
  CorrelationMatrix
} from '../services/api';