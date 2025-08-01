import React, { useState, useEffect } from 'react';
import { 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon, 
  ArrowPathIcon, 
  ArrowsRightLeftIcon, 
  CircleStackIcon 
} from '@heroicons/react/24/outline';
import Plot from 'react-plotly.js';
import { marketApi, watchlistApi, stockApi, MarketIndex, WatchlistStock } from '../services/api';
import dayjs from 'dayjs';

const Dashboard: React.FC = () => {
  const [indices, setIndices] = useState<MarketIndex[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistStock[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncModalVisible, setSyncModalVisible] = useState(false);
  const [syncInfo, setSyncInfo] = useState<any>(null);
  const [syncing, setSyncing] = useState(false);
  const [chartData, setChartData] = useState<{ dates: string[], prices: number[] }>({ dates: [], prices: [] });
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null);

  // 消息提示函数
  const showMessage = (type: 'success' | 'error' | 'info', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  // 加载市场指数数据
  const loadMarketIndices = async () => {
    try {
      const data = await marketApi.getMarketIndices();
      setIndices(data);
    } catch (error) {
      console.error('获取市场指数失败:', error);
      showMessage('error', '获取市场指数失败，请检查网络连接');
      // 如果API调用失败，使用模拟数据作为备用
      setIndices([
        {
          symbol: '000001.SH',
          name: '上证指数',
          price: 3245.12,
          change: 15.43,
          changePercent: 0.48,
          volume: 245600000
        },
        {
          symbol: '399001.SZ',
          name: '深证成指',
          price: 10234.56,
          change: -23.45,
          changePercent: -0.23,
          volume: 189400000
        },
        {
          symbol: '399006.SZ',
          name: '创业板指',
          price: 2156.78,
          change: 8.92,
          changePercent: 0.42,
          volume: 156700000
        }
      ]);
    }
  };

  // 加载上证指数历史数据
  const loadShanghaiIndexHistory = async () => {
    try {
      const historyData = await marketApi.getStockHistory('000001.SH', 30);
      if (historyData && historyData.data && historyData.data.length > 0) {
        const dates = historyData.data.map((item: any) => dayjs(item.date).format('YYYY-MM-DD HH:mm:ss'));
        const prices = historyData.data.map((item: any) => item.close);
        setChartData({ dates, prices });
      } else {
        setChartData({ dates: [], prices: [] });
      }
    } catch (error) {
      console.error('获取上证指数历史数据失败:', error);
      setChartData({ dates: [], prices: [] });
    }
  };

  // 加载自选股数据
  const loadWatchlist = async () => {
    try {
      const data = await watchlistApi.getWatchlist();
      setWatchlist(data);
    } catch (error) {
      console.error('获取自选股失败:', error);
      showMessage('error', '获取自选股失败，请检查网络连接');
      // 如果API调用失败，使用模拟数据作为备用
      setWatchlist([
        {
          symbol: '000001.SZ',
          name: '平安银行',
          price: 15.23,
          change: 0.45,
          changePercent: 3.04
        },
        {
          symbol: '000002.SZ',
          name: '万科A',
          price: 18.67,
          change: -0.23,
          changePercent: -1.22
        },
        {
          symbol: '600036.SH',
          name: '招商银行',
          price: 42.15,
          change: 1.23,
          changePercent: 3.01
        }
      ]);
    }
  };

  // 初始化数据加载
  useEffect(() => {
    const loadData = async () => {
      await Promise.all([loadMarketIndices(), loadWatchlist(), loadSyncInfo(), loadShanghaiIndexHistory()]);
    };
    loadData();
  }, []);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await Promise.all([loadMarketIndices(), loadWatchlist(), loadShanghaiIndexHistory()]);
      showMessage('success', '数据刷新成功');
    } catch (error) {
      showMessage('error', '数据刷新失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载股票同步信息
  const loadSyncInfo = async () => {
    try {
      const info = await stockApi.getSyncInfo();
      setSyncInfo(info);
    } catch (error) {
      console.error('获取同步信息失败:', error);
      showMessage('error', '获取同步信息失败');
    }
  };

  // 执行股票数据同步
  const handleStockSync = async () => {
    setSyncing(true);
    try {
      const result = await stockApi.syncStockData();
      
      showMessage('success', 
        `同步完成！共获取 ${result.total_fetched || 0} 只股票，` +
        `新增 ${result.new_stocks || 0} 只，更新 ${result.updated_stocks || 0} 只`
      );
      
      await loadSyncInfo();
      
      setTimeout(async () => {
        await loadSyncInfo();
        console.log('延迟刷新同步信息完成');
      }, 2000);
      
    } catch (error) {
      console.error('股票数据同步失败:', error);
      showMessage('error', '股票数据同步失败');
    } finally {
      setSyncing(false);
    }
  };

  // 打开同步对话框
  const showSyncModal = async () => {
    setSyncModalVisible(true);
    await loadSyncInfo();
  };

  return (
    <div className="space-y-6">
      {/* 消息提示 */}
      {message && (
        <div className={`alert ${
          message.type === 'success' ? 'alert-success' : 
          message.type === 'error' ? 'alert-error' : 'alert-info'
        }`}>
          <span>{message.text}</span>
        </div>
      )}

      {/* 市场指数卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {indices.map((index) => (
          <div key={index.symbol} className="card bg-base-100 shadow-xl">
            <div className="card-body p-6">
              <h3 className="card-title text-lg">{index.name}</h3>
              <div className="flex items-center gap-2">
                {(index.change || 0) >= 0 ? (
                  <ArrowTrendingUpIcon className="w-6 h-6 text-success" />
                ) : (
                  <ArrowTrendingDownIcon className="w-6 h-6 text-error" />
                )}
                <span className={`text-2xl font-bold ${
                  (index.change || 0) >= 0 ? 'text-success' : 'text-error'
                }`}>
                  {(index.price || 0).toFixed(2)}
                </span>
              </div>
              <div className="text-sm space-y-1">
                <div className={`${(index.change || 0) >= 0 ? 'text-success' : 'text-error'}`}>
                  {(index.change || 0) >= 0 ? '+' : ''}{(index.change || 0).toFixed(2)} 
                  ({(index.changePercent || 0) >= 0 ? '+' : ''}{(index.changePercent || 0).toFixed(2)}%)
                </div>
                <div className="text-base-content/60 text-xs">
                  成交量: {((index.volume || 0) / 100000000).toFixed(2)}亿
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 股票数据管理 */}
      <div className="card bg-base-100 shadow-xl">
        <div className="card-body">
          <div className="flex justify-between items-center mb-6">
            <h2 className="card-title text-xl">股票数据管理</h2>
            <div className="flex gap-2">
              <button 
                className="btn btn-primary"
                onClick={showSyncModal}
              >
                <CircleStackIcon className="w-4 h-4" />
                数据同步
              </button>
              <button 
                className={`btn btn-outline ${loading ? 'loading' : ''}`}
                onClick={async () => {
                  setLoading(true);
                  try {
                    await Promise.all([loadMarketIndices(), loadWatchlist(), loadSyncInfo()]);
                    showMessage('success', '数据刷新成功');
                  } catch (error) {
                    showMessage('error', '数据刷新失败');
                  } finally {
                    setLoading(false);
                  }
                }}
                disabled={loading}
              >
                <ArrowPathIcon className="w-4 h-4" />
                刷新数据
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="stat bg-base-200 rounded-lg">
              <div className="stat-figure text-primary">
                <CircleStackIcon className="w-8 h-8" />
              </div>
              <div className="stat-title">股票总数</div>
              <div className="stat-value text-primary">
                {syncInfo?.stock_count?.total || 0}
              </div>
            </div>
            
            <div className="stat bg-base-200 rounded-lg">
              <div className="stat-title">活跃股票</div>
              <div className="stat-value text-success">
                {syncInfo?.stock_count?.active || 0}
              </div>
            </div>
            
            <div className="stat bg-base-200 rounded-lg">
              <div className="stat-title">上交所</div>
              <div className="stat-value text-error">
                {syncInfo?.stock_count?.sh_market || 0}
              </div>
            </div>
            
            <div className="stat bg-base-200 rounded-lg">
              <div className="stat-title">深交所</div>
              <div className="stat-value text-success">
                {syncInfo?.stock_count?.sz_market || 0}
              </div>
            </div>
          </div>
          
          {syncInfo?.last_sync_time && (
            <div className="text-sm text-base-content/60 mt-4">
              最后同步时间: {new Date(syncInfo.last_sync_time).toLocaleString()}
            </div>
          )}
          <div className="text-xs text-base-content/40 mt-2">
            数据获取时间: {new Date().toLocaleString()}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 上证指数走势图 */}
        <div className="lg:col-span-2 card bg-base-100 shadow-xl">
          <div className="card-body">
            <div className="flex justify-between items-center mb-4">
              <h2 className="card-title">上证指数走势</h2>
              <button 
                className={`btn btn-outline btn-sm ${loading ? 'loading' : ''}`}
                onClick={handleRefresh}
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
                  bgcolor: '#000',
                  color: 'white',
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
        

        {/* 自选股监控 */}
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
      </div>

      {/* 股票数据同步对话框 */}
      {syncModalVisible && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg mb-4">股票数据同步</h3>
            
            <div className="space-y-4">
              <div>
                <p className="font-semibold mb-2">数据同步说明：</p>
                <ul className="list-disc list-inside text-sm space-y-1 text-base-content/80">
                  <li>同步操作将从数据源获取最新的股票列表信息</li>
                  <li>包括股票代码、名称、行业、地区等基础信息</li>
                  <li>同步过程可能需要几分钟时间，请耐心等待</li>
                  <li>同步完成后，股票搜索功能将使用最新数据</li>
                </ul>
              </div>
              
              {syncInfo && (
                <div className="bg-base-200 p-4 rounded-lg">
                  <p className="font-semibold mb-2">当前数据状态：</p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <p>股票总数: {syncInfo.stock_count?.total || 0}</p>
                    <p>活跃股票: {syncInfo.stock_count?.active || 0}</p>
                    <p>上交所: {syncInfo.stock_count?.sh_market || 0}</p>
                    <p>深交所: {syncInfo.stock_count?.sz_market || 0}</p>
                  </div>
                  {syncInfo.last_sync_time && (
                    <p className="text-sm mt-2">最后同步: {new Date(syncInfo.last_sync_time).toLocaleString()}</p>
                  )}
                </div>
              )}
              
              {syncing && (
                <div className="text-center py-8">
                  <div className="loading loading-spinner loading-lg"></div>
                  <p className="mt-4">正在同步股票数据，请稍候...</p>
                </div>
              )}
            </div>
            
            <div className="modal-action">
              <button 
                className="btn" 
                onClick={() => setSyncModalVisible(false)}
                disabled={syncing}
              >
                取消
              </button>
              <button 
                className={`btn btn-primary ${syncing ? 'loading' : ''}`}
                onClick={handleStockSync}
                disabled={syncing}
              >
                <ArrowsRightLeftIcon className="w-4 h-4" />
                开始同步
              </button>
            </div>
          </div>
          <div className="modal-backdrop" onClick={() => !syncing && setSyncModalVisible(false)}></div>
        </div>
      )}
    </div>  
  );
};

export default Dashboard;