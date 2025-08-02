import React from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import Plot from 'react-plotly.js';

interface ShanghaiIndexChartProps {
  chartData: { dates: string[], prices: number[] };
  loading: boolean;
  onRefresh: () => void;
}

const ShanghaiIndexChart: React.FC<ShanghaiIndexChartProps> = ({
  chartData,
  loading,
  onRefresh
}) => {
  return (
    <div className="lg:col-span-2 card bg-base-100 shadow-xl">
      <div className="card-body">
        <div className="flex justify-between items-center mb-4">
          <h2 className="card-title">上证指数走势</h2>
          <button 
            className={`btn btn-outline btn-sm ${loading ? 'loading' : ''}`}
            onClick={onRefresh}
            disabled={loading}
          >
            <ArrowPathIcon className="w-4 h-4" />
            刷新
          </button>
        </div>
        <Plot
          data={[
            {
              x: chartData.dates,
              y: chartData.prices,
              type: 'scatter',
              mode: 'lines',
              name: '上证指数',
              line: { color: '#1890ff', width: 2 }
            }
          ]}
          layout={{
            width: undefined,
            height: 300,
            margin: { l: 50, r: 50, t: 20, b: 50 },
            xaxis: { title: { text: '日期' } },
            yaxis: { title: { text: '点数' } },
            showlegend: false,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            modebar: {
              bgcolor: 'rgba(0,0,0,0.1)',
              color: '#ffffff',
              activecolor: '#1890ff'
            },
            font: {
              color: '#ffffff'
            }
          }}
          config={{ responsive: true }}
          style={{ width: '100%' }}
        />
      </div>
    </div>
  );
};

export default ShanghaiIndexChart; 