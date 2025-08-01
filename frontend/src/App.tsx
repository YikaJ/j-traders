import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  HeartIcon
} from '@heroicons/react/24/outline';

// 页面组件
import Dashboard from './pages/Dashboard';
import QuantitativeSelection from './pages/QuantitativeSelection';
import Watchlist from './pages/Watchlist';

const menuItems = [
  {
    key: '/',
    icon: ChartBarIcon,
    label: '大盘监控',
    path: '/'
  },
  {
    key: '/quantitative',
    icon: CurrencyDollarIcon,
    label: '量化选股',
    path: '/quantitative'
  },
  {
    key: '/watchlist',
    icon: HeartIcon,
    label: '自选股',
    path: '/watchlist'
  },
];

const AppContent: React.FC = () => {
  const location = useLocation();

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/': return '大盘监控';
      case '/quantitative': return '量化选股';
      case '/watchlist': return '自选股管理';
      default: return '量化选股系统';
    }
  };

  return (
    <div className="min-h-screen bg-base-200">
      <div className="drawer lg:drawer-open">
        <input id="drawer-toggle" type="checkbox" className="drawer-toggle" />
        
        {/* Page content */}
        <div className="drawer-content flex flex-col">
          {/* Navbar */}
          <div className="navbar bg-base-100 shadow-lg">
            <div className="flex-none lg:hidden">
              <label htmlFor="drawer-toggle" className="btn btn-square btn-ghost">
                <svg className="inline-block w-6 h-6 stroke-current" fill="none" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path>
                </svg>
              </label>
            </div>
            <div className="flex-1">
              <h1 className="text-xl font-bold">{getPageTitle()}</h1>
            </div>
            <div className="flex-none">
              <div className="text-sm">
                <span className="badge badge-success badge-sm mr-2">正常</span>
                <span className="text-base-content/60">
                  最后更新: {new Date().toLocaleTimeString()}
                </span>
              </div>
            </div>
          </div>

          {/* Page content */}
          <main className="flex-1 p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/quantitative" element={<QuantitativeSelection />} />
              <Route path="/watchlist" element={<Watchlist />} />
            </Routes>
          </main>
        </div>

        {/* Sidebar */}
        <div className="drawer-side">
          <label htmlFor="drawer-toggle" className="drawer-overlay"></label>
          <aside className="w-64 min-h-full bg-base-100">
            {/* Logo */}
            <div className="flex items-center justify-center h-16 border-b border-base-200">
              <h2 className="text-lg font-bold text-primary">量化选股系统</h2>
            </div>
            
            {/* Menu */}
            <ul className="menu p-4 w-full">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                
                return (
                  <li key={item.key}>
                    <Link 
                      to={item.path}
                      className={`flex items-center gap-3 ${isActive ? 'active' : ''}`}
                    >
                      <Icon className="w-5 h-5" />
                      <span>{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </aside>
        </div>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <AppContent />
    </Router>
  );
};

export default App;
