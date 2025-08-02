import React from 'react';
import { ArrowsRightLeftIcon } from '@heroicons/react/24/outline';

interface StockSyncModalProps {
  visible: boolean;
  syncInfo: any;
  syncing: boolean;
  onClose: () => void;
  onSync: () => void;
}

const StockSyncModal: React.FC<StockSyncModalProps> = ({
  visible,
  syncInfo,
  syncing,
  onClose,
  onSync
}) => {
  if (!visible) return null;

  return (
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
            onClick={onClose}
            disabled={syncing}
          >
            取消
          </button>
          <button 
            className={`btn btn-primary ${syncing ? 'loading' : ''}`}
            onClick={onSync}
            disabled={syncing}
          >
            <ArrowsRightLeftIcon className="w-4 h-4" />
            开始同步
          </button>
        </div>
      </div>
      <div className="modal-backdrop" onClick={() => !syncing && onClose()}></div>
    </div>
  );
};

export default StockSyncModal; 