import React, { useState } from 'react';
import {
  ChartBarIcon,
  BeakerIcon,
  CircleStackIcon,
  AcademicCapIcon,
  InformationCircleIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import {
  factorAnalysisApi,
  SelectedFactor,
  CorrelationMatrix
} from '../services/api';

interface FactorAnalysisPanelProps {
  factors: SelectedFactor[];
}

const FactorAnalysisPanel: React.FC<FactorAnalysisPanelProps> = ({
  factors
}) => {
  const [analysisType, setAnalysisType] = useState<'statistics' | 'correlation' | 'effectiveness' | 'batch'>('statistics');
  const [loading, setLoading] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [correlationMatrix, setCorrelationMatrix] = useState<CorrelationMatrix | null>(null);
  const [selectedFactorId, setSelectedFactorId] = useState<string>('');

  // 模拟因子数据
  const generateMockFactorData = (factorId: string) => {
    return Array.from({ length: 100 }, (_, i) => ({
      date: `2024-01-${String(i + 1).padStart(2, '0')}`,
      value: Math.random() * 2 - 1,
      percentile: Math.random() * 100
    }));
  };

  const handleFactorAnalysis = async (selectedFactorId: string) => {
    if (!selectedFactorId) return;

    const selectedFactor = factors.find(f => f.id === selectedFactorId);
    if (!selectedFactor) return;

    // 生成模拟数据
    const factorData: Record<string, any[]> = {};
    factorData[selectedFactor.name] = generateMockFactorData(selectedFactor.id);

    setAnalysisResults(null); // Clear previous results
    setCorrelationMatrix(null);
    setSelectedFactorId(selectedFactorId);
  };

  const handleCorrelationAnalysis = async () => {
    if (factors.length < 2) {
      alert('请至少选择两个因子进行相关性分析');
      return;
    }

    try {
      const factorData = generateFactorDataDict();
      const result = await factorAnalysisApi.calculateCorrelationMatrix(factorData);
      setCorrelationMatrix(result.data);
    } catch (error) {
      console.error('相关性分析失败:', error);
    }
  };

  // 生成因子数据字典
  const generateFactorDataDict = () => {
    const factorData: Record<string, number[]> = {};
    factors.forEach(factor => {
      if (factor.is_enabled) {
        factorData[factor.name] = generateMockFactorData(factor.id).map(d => d.value);
      }
    });
    return factorData;
  };

  // 执行统计分析
  const handleStatisticsAnalysis = async () => {
    if (!selectedFactorId) return;

    try {
      setLoading(true);
      const selectedFactor = factors.find(f => f.id === selectedFactorId);
      if (!selectedFactor) return;

      const factorValues = generateMockFactorData(selectedFactor.id).map(d => d.value);
      const result = await factorAnalysisApi.analyzeFactorStatistics(
        factorValues,
        selectedFactor.id,
        selectedFactor.name
      );
      setAnalysisResults(result);
    } catch (error) {
      console.error('统计分析失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 执行有效性分析
  const handleEffectivenessAnalysis = async () => {
    if (!selectedFactorId) return;

    try {
      setLoading(true);
      const selectedFactor = factors.find(f => f.id === selectedFactorId);
      if (!selectedFactor) return;

      const factorValues = generateMockFactorData(selectedFactor.id).map(d => d.value);
      const result = await factorAnalysisApi.analyzeFactorEffectiveness(
        factorValues,
        selectedFactor.id
      );
      setAnalysisResults(result);
    } catch (error) {
      console.error('有效性分析失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 执行批量分析
  const handleBatchAnalysis = async () => {
    try {
      setLoading(true);
      const factorData = generateFactorDataDict();
      
      if (Object.keys(factorData).length === 0) {
        alert('批量分析需要至少1个启用的因子');
        return;
      }

      const result = await factorAnalysisApi.performBatchAnalysis(factorData);
      setAnalysisResults(result);
    } catch (error) {
      console.error('批量分析失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 执行分析
  const handleRunAnalysis = () => {
    switch (analysisType) {
      case 'statistics':
        handleStatisticsAnalysis();
        break;
      case 'correlation':
        handleCorrelationAnalysis();
        break;
      case 'effectiveness':
        handleEffectivenessAnalysis();
        break;
      case 'batch':
        handleBatchAnalysis();
        break;
    }
  };

  // 导出分析结果
  const handleExportResults = () => {
    if (!analysisResults) return;

    const dataStr = JSON.stringify(analysisResults, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `factor_analysis_${analysisType}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
  };

  // 获取相关性颜色
  const getCorrelationColor = (value: number) => {
    const abs = Math.abs(value);
    if (abs >= 0.8) return 'bg-error text-error-content';
    if (abs >= 0.6) return 'bg-warning text-warning-content';
    if (abs >= 0.4) return 'bg-info text-info-content';
    return 'bg-base-200';
  };

  const enabledFactors = factors.filter(f => f.is_enabled);

  return (
    <div className="space-y-6">
      {/* 分析选项 */}
      <div className="card bg-base-100 shadow-lg">
        <div className="card-body p-4">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <BeakerIcon className="w-5 h-5" />
            因子分析配置
          </h3>

          {/* 分析类型选择 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <button
              className={`btn ${analysisType === 'statistics' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setAnalysisType('statistics')}
            >
              <ChartBarIcon className="w-4 h-4" />
              统计分析
            </button>
            <button
              className={`btn ${analysisType === 'correlation' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setAnalysisType('correlation')}
            >
              <CircleStackIcon className="w-4 h-4" />
              相关性分析
            </button>
            <button
              className={`btn ${analysisType === 'effectiveness' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setAnalysisType('effectiveness')}
            >
              <AcademicCapIcon className="w-4 h-4" />
              有效性分析
            </button>
            <button
              className={`btn ${analysisType === 'batch' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setAnalysisType('batch')}
            >
              <BeakerIcon className="w-4 h-4" />
              批量分析
            </button>
          </div>

          {/* 因子选择（单因子分析时） */}
          {(analysisType === 'statistics' || analysisType === 'effectiveness') && (
            <div className="form-control">
              <label className="label">
                <span className="label-text">选择分析因子</span>
              </label>
              <select
                className="select select-bordered"
                value={selectedFactorId}
                onChange={(e) => handleFactorAnalysis(e.target.value)}
              >
                <option value="">请选择要分析的因子</option>
                {enabledFactors.map((factor) => (
                  <option key={factor.id} value={factor.id}>
                    {factor.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* 分析说明 */}
          <div className="mt-4">
            <div className="alert alert-info">
              <InformationCircleIcon className="w-5 h-5" />
              <div className="text-sm">
                {analysisType === 'statistics' && '统计分析将计算单个因子的基础统计特征，包括均值、标准差、分布等指标。'}
                {analysisType === 'correlation' && '相关性分析将计算多个因子之间的相关性矩阵，帮助识别冗余因子。'}
                {analysisType === 'effectiveness' && '有效性分析将评估因子的选股能力和稳定性。'}
                {analysisType === 'batch' && '批量分析将对所有启用的因子进行综合分析，包括统计、相关性和有效性。'}
              </div>
            </div>
          </div>

          {/* 执行按钮 */}
          <div className="flex justify-between items-center mt-4">
            <div className="text-sm text-base-content/60">
              已选择 {enabledFactors.length} 个因子进行分析
            </div>
            <div className="flex gap-2">
              {analysisResults && (
                <button
                  className="btn btn-outline btn-sm"
                  onClick={handleExportResults}
                >
                  <ArrowDownTrayIcon className="w-4 h-4" />
                  导出结果
                </button>
              )}
              <button
                className={`btn btn-primary btn-sm ${loading ? 'loading' : ''}`}
                onClick={handleRunAnalysis}
                disabled={loading || enabledFactors.length === 0 || 
                  ((analysisType === 'statistics' || analysisType === 'effectiveness') && !selectedFactorId) ||
                  (analysisType === 'correlation' && enabledFactors.length < 2)
                }
              >
                {loading ? '分析中...' : '开始分析'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 分析结果 */}
      {analysisResults && (
        <div className="card bg-base-100 shadow-lg">
          <div className="card-body p-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold flex items-center gap-2">
                <EyeIcon className="w-5 h-5" />
                分析结果
              </h3>
              <div className="flex items-center gap-2 text-sm text-base-content/60">
                <ClockIcon className="w-4 h-4" />
                {new Date().toLocaleString()}
              </div>
            </div>

            {/* 统计分析结果 */}
            {analysisType === 'statistics' && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="stat bg-base-200 rounded-lg">
                    <div className="stat-title">均值</div>
                    <div className="stat-value text-lg">{analysisResults.mean?.toFixed(3) || 'N/A'}</div>
                  </div>
                  <div className="stat bg-base-200 rounded-lg">
                    <div className="stat-title">标准差</div>
                    <div className="stat-value text-lg">{analysisResults.std?.toFixed(3) || 'N/A'}</div>
                  </div>
                  <div className="stat bg-base-200 rounded-lg">
                    <div className="stat-title">偏度</div>
                    <div className="stat-value text-lg">{analysisResults.skewness?.toFixed(3) || 'N/A'}</div>
                  </div>
                  <div className="stat bg-base-200 rounded-lg">
                    <div className="stat-title">峰度</div>
                    <div className="stat-value text-lg">{analysisResults.kurtosis?.toFixed(3) || 'N/A'}</div>
                  </div>
                </div>

                {/* 分布信息 */}
                {analysisResults.distribution && (
                  <div>
                    <h4 className="font-medium mb-2">分布特征</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="p-3 bg-base-200 rounded">
                        <div className="text-sm text-base-content/60">正态性检验</div>
                        <div className="font-medium">
                          {analysisResults.distribution.normality_test?.is_normal ? '通过' : '未通过'}
                        </div>
                      </div>
                      <div className="p-3 bg-base-200 rounded">
                        <div className="text-sm text-base-content/60">缺失值比例</div>
                        <div className="font-medium">
                          {(analysisResults.null_ratio * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div className="p-3 bg-base-200 rounded">
                        <div className="text-sm text-base-content/60">异常值比例</div>
                        <div className="font-medium">
                          {analysisResults.outlier_ratio ? (analysisResults.outlier_ratio * 100).toFixed(1) + '%' : 'N/A'}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 相关性分析结果 */}
            {analysisType === 'correlation' && correlationMatrix && (
              <div className="space-y-4">
                <div className="overflow-x-auto">
                  <table className="table table-sm">
                    <thead>
                      <tr>
                        <th></th>
                        {correlationMatrix.factor_names.map((name) => (
                          <th key={name} className="text-center min-w-20">
                            {name.length > 8 ? name.substring(0, 8) + '...' : name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {correlationMatrix.factor_names.map((rowName) => (
                        <tr key={rowName}>
                          <td className="font-medium">
                            {rowName.length > 10 ? rowName.substring(0, 10) + '...' : rowName}
                          </td>
                          {correlationMatrix.factor_names.map((colName) => {
                            const value = correlationMatrix.correlation_matrix[rowName]?.[colName] || 0;
                            return (
                              <td key={colName} className="text-center">
                                <div
                                  className={`px-2 py-1 rounded text-xs font-medium ${getCorrelationColor(value)}`}
                                  title={`${rowName} vs ${colName}: ${value.toFixed(3)}`}
                                >
                                  {value.toFixed(2)}
                                </div>
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* 相关性统计 */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-3 bg-base-200 rounded">
                    <div className="text-sm text-base-content/60">高相关性对数</div>
                    <div className="font-medium">
                      {analysisResults.high_correlation_pairs?.length || 0}
                    </div>
                  </div>
                  <div className="p-3 bg-base-200 rounded">
                    <div className="text-sm text-base-content/60">分析方法</div>
                    <div className="font-medium">{correlationMatrix.method}</div>
                  </div>
                  <div className="p-3 bg-base-200 rounded">
                    <div className="text-sm text-base-content/60">样本数量</div>
                    <div className="font-medium">{correlationMatrix.sample_size}</div>
                  </div>
                </div>
              </div>
            )}

            {/* 有效性分析结果 */}
            {analysisType === 'effectiveness' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="stat bg-base-200 rounded-lg">
                    <div className="stat-title">整体有效性得分</div>
                    <div className="stat-value text-lg">
                      {analysisResults.overall_score?.toFixed(2) || 'N/A'}
                    </div>
                  </div>
                  <div className="stat bg-base-200 rounded-lg">
                    <div className="stat-title">区分度</div>
                    <div className="stat-value text-lg">
                      {analysisResults.discrimination_score?.toFixed(2) || 'N/A'}
                    </div>
                  </div>
                  <div className="stat bg-base-200 rounded-lg">
                    <div className="stat-title">稳定性</div>
                    <div className="stat-value text-lg">
                      {analysisResults.stability_score?.toFixed(2) || 'N/A'}
                    </div>
                  </div>
                </div>

                {/* 有效性建议 */}
                {analysisResults.recommendations && analysisResults.recommendations.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">优化建议</h4>
                    <div className="space-y-2">
                      {analysisResults.recommendations.map((recommendation: string, index: number) => (
                        <div key={index} className="alert alert-info alert-sm">
                          <InformationCircleIcon className="w-4 h-4" />
                          <span className="text-sm">{recommendation}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 批量分析结果 */}
            {analysisType === 'batch' && (
              <div className="space-y-4">
                {/* 因子概览 */}
                <div className="overflow-x-auto">
                  <table className="table table-sm">
                    <thead>
                      <tr>
                        <th>因子名称</th>
                        <th>有效性得分</th>
                        <th>稳定性</th>
                        <th>区分度</th>
                        <th>建议</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysisResults.factor_summary?.map((summary: any, index: number) => (
                        <tr key={index}>
                          <td className="font-medium">{summary.factor_name}</td>
                          <td>
                            <div className="badge badge-primary">
                              {summary.effectiveness_score?.toFixed(2) || 'N/A'}
                            </div>
                          </td>
                          <td>{summary.stability_score?.toFixed(2) || 'N/A'}</td>
                          <td>{summary.discrimination_score?.toFixed(2) || 'N/A'}</td>
                          <td>
                            <div className={`badge badge-sm ${
                              summary.recommendation === 'keep' ? 'badge-success' :
                              summary.recommendation === 'optimize' ? 'badge-warning' :
                              'badge-error'
                            }`}>
                              {summary.recommendation === 'keep' ? '保留' :
                               summary.recommendation === 'optimize' ? '优化' : '移除'}
                            </div>
                          </td>
                        </tr>
                      )) || []}
                    </tbody>
                  </table>
                </div>

                {/* 整体统计 */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="stat bg-base-200 rounded-lg">
                    <div className="stat-title">总因子数</div>
                    <div className="stat-value text-lg">{enabledFactors.length}</div>
                  </div>
                  <div className="stat bg-base-200 rounded-lg">
                    <div className="stat-title">高质量因子</div>
                    <div className="stat-value text-lg">
                      {analysisResults.factor_summary?.filter((f: any) => f.recommendation === 'keep').length || 0}
                    </div>
                  </div>
                  <div className="stat bg-base-200 rounded-lg">
                    <div className="stat-title">需要优化</div>
                    <div className="stat-value text-lg">
                      {analysisResults.factor_summary?.filter((f: any) => f.recommendation === 'optimize').length || 0}
                    </div>
                  </div>
                  <div className="stat bg-base-200 rounded-lg">
                    <div className="stat-title">建议移除</div>
                    <div className="stat-value text-lg">
                      {analysisResults.factor_summary?.filter((f: any) => f.recommendation === 'remove').length || 0}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 空状态 */}
      {enabledFactors.length === 0 && (
        <div className="card bg-base-100 shadow-lg">
          <div className="card-body text-center py-12">
            <BeakerIcon className="w-16 h-16 mx-auto text-base-content/40 mb-4" />
            <div className="text-lg font-medium mb-2">暂无可分析的因子</div>
            <div className="text-base-content/60">
              请先启用一些因子后再进行分析
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FactorAnalysisPanel;