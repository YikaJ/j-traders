import React from 'react';
import { WatchlistStock } from '../../services/api';

interface WatchlistMonitorProps {
  watchlist: WatchlistStock[];
}

const WatchlistMonitor: React.FC<WatchlistMonitorProps> = ({ watchlist }) => {
  return (
    <div className="card bg-base-100 shadow-xl">
      <div className="card-body">
        <div className="flex justify-between items-center mb-4">
          <h2 className="card-title">自选股监控</h2>
          <a href="/watchlist" className="link link-primary">查看全部</a>
        </div>
        <div className="overflow-x-auto">
          <table className="table table-compact w-full">
            <thead>
              <tr>
                <th>代码</th>
                <th>名称</th>
                <th>现价</th>
                <th>涨跌幅</th>
              </tr>
            </thead>
            <tbody>
              {watchlist.map((stock) => (
                <tr key={stock.symbol}>
                  <td className="text-xs">{stock.symbol}</td>
                  <td className="text-sm font-medium">{stock.name}</td>
                  <td className="text-sm">¥{(stock.price || 0).toFixed(2)}</td>
                  <td>
                    <div className={`badge badge-sm ${
                      (stock.changePercent || 0) >= 0 ? 'badge-success' : 'badge-error'
                    }`}>
                      {(stock.changePercent || 0) >= 0 ? '+' : ''}{(stock.changePercent || 0).toFixed(2)}%
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default WatchlistMonitor; 