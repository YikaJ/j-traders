// 组件统一导入入口
export { default as FactorAnalysisPanel } from './FactorAnalysisPanel';
export { default as StrategyConfigManager } from './StrategyConfigManager';
export { default as WeightConfigPanel } from './WeightConfigPanel';
export { default as FactorLibrary } from './FactorLibrary';
export { default as FactorSearch } from './FactorSearch';
export { default as FactorCategoryFilter } from './FactorCategoryFilter';
export { default as FactorGrid } from './FactorGrid';
export { default as FactorDetailModal } from './FactorDetailModal';
export { default as FactorFormulaModal } from './FactorFormulaModal';
export { default as FactorEditModal } from './FactorEditModal';
export { default as FactorCreateModal } from './FactorCreateModal';
export { default as FactorHistoryModal } from './FactorHistoryModal';

// 导出组件相关的类型
export type {
  BuiltinFactor,
  SelectedFactor,
  StrategyConfig,
  WeightPreset,
  WeightOptimizationResult,
  CorrelationMatrix
} from '../services/api';