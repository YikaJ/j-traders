import React from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

interface FactorSearchProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

const FactorSearch: React.FC<FactorSearchProps> = ({
  searchQuery,
  onSearchChange
}) => {
  return (
    <div className="form-control flex-1">
      <div className="input-group">
        <input
          type="text"
          placeholder="搜索因子名称或描述..."
          className="input input-bordered flex-1"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
        />
        <button className="btn btn-square">
          <MagnifyingGlassIcon className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

export default FactorSearch; 