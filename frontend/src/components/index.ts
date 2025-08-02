// 组件统一导入入口
export { default as BuiltinFactorLibrary } from './BuiltinFactorLibrary';
export { default as StrategyConfigManager } from './StrategyConfigManager';
export { default as WeightConfigPanel } from './WeightConfigPanel';
export { default as FactorAnalysisPanel } from './FactorAnalysisPanel';

// 导出组件相关的类型
export type {
  BuiltinFactor,
  SelectedFactor,
  StrategyConfig,
  WeightPreset,
  WeightOptimizationResult,
  CorrelationMatrix
} from '../services/api';