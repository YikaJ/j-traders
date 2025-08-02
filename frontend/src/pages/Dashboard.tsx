import React, { useState, useEffect } from 'react';
import dayjs from 'dayjs';
import { marketApi, watchlistApi, stockApi, MarketIndex, WatchlistStock } from '../services/api';

// 导入组件
import MarketIndicesCard from '../components/dashboard/MarketIndicesCard';
import StockDataManagement from '../components/dashboard/StockDataManagement';
import ShanghaiIndexChart from '../components/dashboard/ShanghaiIndexChart';
import WatchlistMonitor from '../components/dashboard/WatchlistMonitor';
import StockSyncModal from '../components/dashboard/StockSyncModal';
import MessageAlert from '../components/dashboard/MessageAlert';

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
      <MessageAlert message={message} />

      {/* 市场指数卡片 */}
      <MarketIndicesCard indices={indices} />

      {/* 股票数据管理 */}
      <StockDataManagement
        syncInfo={syncInfo}
        loading={loading}
        onShowSyncModal={showSyncModal}
        onRefresh={handleRefresh}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 上证指数走势图 */}
        <ShanghaiIndexChart
          chartData={chartData}
          loading={loading}
          onRefresh={handleRefresh}
        />

        {/* 自选股监控 */}
        <WatchlistMonitor watchlist={watchlist} />
      </div>

      {/* 股票数据同步对话框 */}
      <StockSyncModal
        visible={syncModalVisible}
        syncInfo={syncInfo}
        syncing={syncing}
        onClose={() => setSyncModalVisible(false)}
        onSync={handleStockSync}
      />
    </div>  
  );
};

export default Dashboard;