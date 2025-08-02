import React from 'react';
import { 
  CircleStackIcon, 
  ArrowPathIcon 
} from '@heroicons/react/24/outline';

interface StockDataManagementProps {
  syncInfo: any;
  loading: boolean;
  onShowSyncModal: () => void;
  onRefresh: () => void;
}

const StockDataManagement: React.FC<StockDataManagementProps> = ({
  syncInfo,
  loading,
  onShowSyncModal,
  onRefresh
}) => {
  return (
    <div className="card bg-base-100 shadow-xl">
      <div className="card-body">
        <div className="flex justify-between items-center mb-6">
          <h2 className="card-title text-xl">股票数据管理</h2>
          <div className="flex gap-2">
            <button 
              className="btn btn-primary"
              onClick={onShowSyncModal}
            >
              <CircleStackIcon className="w-4 h-4" />
              数据同步
            </button>
            <button 
              className={`btn btn-outline ${loading ? 'loading' : ''}`}
              onClick={onRefresh}
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
  );
};

export default StockDataManagement; 