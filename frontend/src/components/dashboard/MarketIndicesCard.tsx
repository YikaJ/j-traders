import React from 'react';
import { 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon 
} from '@heroicons/react/24/outline';
import { MarketIndex } from '../../services/api';

interface MarketIndicesCardProps {
  indices: MarketIndex[];
}

const MarketIndicesCard: React.FC<MarketIndicesCardProps> = ({ indices }) => {
  return (
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
  );
};

export default MarketIndicesCard; 