import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  TrashIcon, 
  ArrowPathIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { watchlistApi, stockApi, WatchlistStock, SearchStock } from '../services/api';

// 导入组件
import StockSearchModal from '../components/watchlist/StockSearchModal';
import DeleteConfirmModal from '../components/watchlist/DeleteConfirmModal';
import MessageAlert from '../components/dashboard/MessageAlert';

const Watchlist: React.FC = () => {
  const [watchlist, setWatchlist] = useState<WatchlistStock[]>([]);
  const [isAddModalVisible, setIsAddModalVisible] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchStock[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(true);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info' | 'warning', text: string } | null>(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [notes, setNotes] = useState('');
  const [confirmDelete, setConfirmDelete] = useState<{ visible: boolean, stock: WatchlistStock | null }>({ visible: false, stock: null });

  // 消息提示函数
  const showMessage = (type: 'success' | 'error' | 'info' | 'warning', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
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
          changePercent: 3.04,
          addedAt: '2024-01-15'
        },
        {
          symbol: '000002.SZ',
          name: '万科A',
          price: 18.67,
          change: -0.23,
          changePercent: -1.22,
          addedAt: '2024-01-14'
        },
        {
          symbol: '600036.SH',
          name: '招商银行',
          price: 42.15,
          change: 1.23,
          changePercent: 3.01,
          addedAt: '2024-01-13'
        }
      ]);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setDataLoading(true);
      await loadWatchlist();
      setDataLoading(false);
    };
    loadData();
  }, []);

  const handleSearch = async (keyword: string) => {
    if (!keyword) {
      setSearchResults([]);
      return;
    }
    
    setSearchLoading(true);
    try {
      const results = await stockApi.searchStocks(keyword, 20);
      setSearchResults(results);
    } catch (error) {
      console.error('搜索股票失败:', error);
      showMessage('error', '搜索股票失败，请检查网络连接');
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleAddStock = async (stock: SearchStock) => {
    try {
      // 检查是否已存在
      if (watchlist.some(item => item.symbol === stock.symbol)) {
        showMessage('warning', '该股票已在自选股中');
        return;
      }

      const newStock = await watchlistApi.addToWatchlist(stock.symbol, stock.name);
      setWatchlist([...watchlist, newStock]);
      showMessage('success', `${stock.name} 已添加到自选股`);
      setIsAddModalVisible(false);
      setSearchKeyword('');
      setNotes('');
      setSearchResults([]); // 清空搜索结果
    } catch (error) {
      console.error('添加自选股失败:', error);
      showMessage('error', '添加自选股失败，请检查网络连接');
    }
  };

  const handleRemoveStock = async (stock: WatchlistStock) => {
    try {
      await watchlistApi.removeFromWatchlist(stock.id || 0);
      setWatchlist(watchlist.filter(s => s.id !== stock.id));
      showMessage('success', `${stock.name} 已从自选股中移除`);
      setConfirmDelete({ visible: false, stock: null });
    } catch (error) {
      console.error('删除自选股失败:', error);
      showMessage('error', '删除自选股失败，请检查网络连接');
    }
  };

  const handleRefresh = async () => {
    setDataLoading(true);
    await loadWatchlist();
    setDataLoading(false);
    showMessage('success', '数据刷新成功');
  };

  return (
    <div className="space-y-6">
      {/* 消息提示 */}
      <MessageAlert message={message} />

      {/* 自选股列表 */}
      <div className="card bg-base-100 shadow-xl">
        <div className="card-body">
          <div className="flex justify-between items-center mb-6">
            <h2 className="card-title text-xl">自选股 ({watchlist.length})</h2>
            <div className="flex gap-2">
              <button 
                className={`btn btn-outline ${dataLoading ? 'loading' : ''}`}
                onClick={handleRefresh}
                disabled={dataLoading}
              >
                <ArrowPathIcon className="w-4 h-4" />
                刷新
              </button>
              <button 
                className="btn btn-primary"
                onClick={() => setIsAddModalVisible(true)}
              >
                <PlusIcon className="w-4 h-4" />
                添加股票
              </button>
            </div>
          </div>
          
          {dataLoading ? (
            <div className="flex justify-center py-8">
              <div className="loading loading-spinner loading-lg"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>代码</th>
                    <th>名称</th>
                    <th>现价</th>
                    <th>涨跌</th>
                    <th>涨跌幅</th>
                    <th>添加日期</th>
                    <th>备注</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {watchlist.map((stock) => (
                    <tr key={stock.symbol}>
                      <td className="font-mono text-sm">{stock.symbol}</td>
                      <td className="font-medium">{stock.name}</td>
                      <td>¥{(stock.price || 0).toFixed(2)}</td>
                      <td className={`${
                        (stock.change || 0) >= 0 ? 'text-success' : 'text-error'
                      }`}>
                        {(stock.change || 0) >= 0 ? '+' : ''}{(stock.change || 0).toFixed(2)}
                      </td>
                      <td>
                        <div className={`badge badge-sm ${
                          (stock.changePercent || 0) >= 0 ? 'badge-success' : 'badge-error'
                        }`}>
                          {(stock.changePercent || 0) >= 0 ? '+' : ''}{(stock.changePercent || 0).toFixed(2)}%
                        </div>
                      </td>
                      <td className="text-sm">{stock.addedAt}</td>
                      <td className="text-sm">{stock.notes || '-'}</td>
                      <td>
                        <div className="flex gap-1">
                          <button 
                            className="btn btn-ghost btn-xs"
                            onClick={() => showMessage('info', '股票详情功能待实现')}
                          >
                            <EyeIcon className="w-3 h-3" />
                            详情
                          </button>
                          <button 
                            className="btn btn-ghost btn-xs text-error"
                            onClick={() => setConfirmDelete({ visible: true, stock })}
                          >
                            <TrashIcon className="w-3 h-3" />
                            移除
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {watchlist.length === 0 && (
                <div className="text-center py-8 text-base-content/60">
                  暂无自选股，点击"添加股票"开始添加
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 添加股票弹窗 */}
      <StockSearchModal
        visible={isAddModalVisible}
        searchResults={searchResults}
        searchLoading={searchLoading}
        searchKeyword={searchKeyword}
        notes={notes}
        onClose={() => setIsAddModalVisible(false)}
        onSearch={handleSearch}
        onAddStock={handleAddStock}
        onSetSearchKeyword={setSearchKeyword}
        onSetNotes={setNotes}
      />

      {/* 删除确认对话框 */}
      <DeleteConfirmModal
        visible={confirmDelete.visible}
        stock={confirmDelete.stock}
        onClose={() => setConfirmDelete({ visible: false, stock: null })}
        onConfirm={() => confirmDelete.stock && handleRemoveStock(confirmDelete.stock)}
      />
    </div>
  );
};

export default Watchlist;