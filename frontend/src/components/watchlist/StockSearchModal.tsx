import React, { useState } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { SearchStock } from '../../services/api';

interface StockSearchModalProps {
  visible: boolean;
  searchResults: SearchStock[];
  searchLoading: boolean;
  searchKeyword: string;
  notes: string;
  onClose: () => void;
  onSearch: (keyword: string) => void;
  onAddStock: (stock: SearchStock) => void;
  onSetSearchKeyword: (keyword: string) => void;
  onSetNotes: (notes: string) => void;
}

const StockSearchModal: React.FC<StockSearchModalProps> = ({
  visible,
  searchResults,
  searchLoading,
  searchKeyword,
  notes,
  onClose,
  onSearch,
  onAddStock,
  onSetSearchKeyword,
  onSetNotes
}) => {
  if (!visible) return null;

  const getMarketColor = (market: string) => {
    return market === 'SH' ? 'badge-error' : 'badge-success';
  };

  const handleClose = () => {
    onClose();
    onSetSearchKeyword('');
    onSetNotes('');
  };

  return (
    <dialog className="modal modal-open">
      <div className="modal-box w-11/12 max-w-4xl">
        <h3 className="font-bold text-lg mb-4">添加股票到自选股</h3>
        
        <div className="space-y-4">
          {/* 搜索框 */}
          <div className="form-control">
            <label className="label">
              <span className="label-text">搜索股票</span>
            </label>
            <div className="join">
              <input 
                type="text"
                className="input input-bordered join-item flex-1"
                placeholder="请输入股票代码或名称"
                value={searchKeyword}
                onChange={(e) => onSetSearchKeyword(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    onSearch(searchKeyword);
                  }
                }}
              />
              <button 
                className={`btn btn-primary join-item ${searchLoading ? 'loading' : ''}`}
                onClick={() => onSearch(searchKeyword)}
                disabled={searchLoading}
              >
                <MagnifyingGlassIcon className="w-4 h-4" />
                搜索
              </button>
            </div>
          </div>

          {/* 搜索结果 */}
          {searchResults.length > 0 && (
            <div className="form-control">
              <label className="label">
                <span className="label-text">搜索结果</span>
              </label>
              <div className="overflow-x-auto max-h-80">
                <table className="table table-compact">
                  <thead>
                    <tr>
                      <th>代码</th>
                      <th>名称</th>
                      <th>行业</th>
                      <th>地区</th>
                      <th>市场</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {searchResults.map((stock) => (
                      <tr key={stock.symbol}>
                        <td className="font-mono text-sm">{stock.symbol}</td>
                        <td className="font-medium">{stock.name}</td>
                        <td className="text-sm">{stock.industry || '-'}</td>
                        <td className="text-sm">{stock.area || '-'}</td>
                        <td>
                          <div className={`badge badge-sm ${getMarketColor(stock.market || '')}`}>
                            {stock.market || '-'}
                          </div>
                        </td>
                        <td>
                          <button 
                            className="btn btn-ghost btn-xs"
                            onClick={() => onAddStock(stock)}
                          >
                            添加
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 备注 */}
          <div className="form-control">
            <label className="label">
              <span className="label-text">备注</span>
            </label>
            <textarea 
              className="textarea textarea-bordered h-20"
              placeholder="可选：为这只股票添加备注信息"
              value={notes}
              onChange={(e) => onSetNotes(e.target.value)}
            />
          </div>
        </div>
        
        <div className="modal-action">
          <button 
            className="btn" 
            onClick={handleClose}
          >
            取消
          </button>
        </div>
      </div>
      <form method="dialog" className="modal-backdrop">
        <button>close</button>
      </form>
    </dialog>
  );
};

export default StockSearchModal; 