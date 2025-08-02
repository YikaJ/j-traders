import React from 'react';
import { StrategyResult } from '../../services/api';

interface StrategyResultModalProps {
  visible: boolean;
  results: StrategyResult[];
  onClose: () => void;
}

const StrategyResultModal: React.FC<StrategyResultModalProps> = ({
  visible,
  results,
  onClose
}) => {
  if (!visible) return null;

  const handleExportResults = () => {
    const csv = results.map((result, index) => 
      `${index + 1},${result.symbol},${result.name},${result.score.toFixed(2)},${result.price.toFixed(2)},${result.changePercent.toFixed(2)}%`
    ).join('\n');
    
    const blob = new Blob([`排名,代码,名称,得分,价格,涨跌幅\n${csv}`], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `selection_result_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="modal modal-open">
      <div className="modal-box w-11/12 max-w-6xl">
        <h3 className="font-bold text-lg mb-4">
          选股结果 ({results.length} 只股票)
        </h3>

        {results.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table table-sm">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>股票代码</th>
                  <th>股票名称</th>
                  <th>综合得分</th>
                  <th>当前价格</th>
                  <th>涨跌幅</th>
                  <th>行业</th>
                </tr>
              </thead>
              <tbody>
                {results.map((result, index) => (
                  <tr key={result.symbol} className={index < 10 ? 'bg-success/10' : ''}>
                    <td className="font-medium">#{index + 1}</td>
                    <td className="font-mono">{result.symbol}</td>
                    <td>{result.name}</td>
                    <td>
                      <div className="badge badge-primary">
                        {result.score.toFixed(2)}
                      </div>
                    </td>
                    <td>¥{result.price.toFixed(2)}</td>
                    <td>
                      <span className={`font-medium ${
                        result.changePercent >= 0 ? 'text-success' : 'text-error'
                      }`}>
                        {result.changePercent >= 0 ? '+' : ''}{result.changePercent.toFixed(2)}%
                      </span>
                    </td>
                    <td>{result.industry || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-base-content/60">
              没有找到符合条件的股票
            </div>
          </div>
        )}

        <div className="modal-action">
          <button
            className="btn"
            onClick={onClose}
          >
            关闭
          </button>
          {results.length > 0 && (
            <button
              className="btn btn-primary"
              onClick={handleExportResults}
            >
              导出结果
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default StrategyResultModal; 