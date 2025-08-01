import React from 'react';
import { ConfigProvider, Layout, Menu, theme } from 'antd';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  FundOutlined,
  HeartOutlined
} from '@ant-design/icons';
import zhCN from 'antd/locale/zh_CN';
import 'dayjs/locale/zh-cn';

// 页面组件（临时）
import Dashboard from './pages/Dashboard';
import QuantitativeSelection from './pages/QuantitativeSelection';
import Watchlist from './pages/Watchlist';

import './App.css';

const { Header, Content, Sider } = Layout;

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: <Link to="/">大盘监控</Link>,
  },
  {
    key: '/quantitative',
    icon: <FundOutlined />,
    label: <Link to="/quantitative">量化选股</Link>,
  },
  {
    key: '/watchlist',
    icon: <HeartOutlined />,
    label: <Link to="/watchlist">自选股</Link>,
  },
];

const AppContent: React.FC = () => {
  const location = useLocation();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={200} style={{ background: colorBgContainer }}>
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          fontSize: '18px',
          fontWeight: 'bold',
          borderBottom: '1px solid #f0f0f0'
        }}>
          量化选股系统
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          style={{ height: '100%', borderRight: 0 }}
          items={menuItems}
        />
      </Sider>
      <Layout>
        <Header style={{ 
          padding: '0 24px', 
          background: colorBgContainer,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0'
        }}>
          <h2 style={{ margin: 0 }}>
            {location.pathname === '/' && '大盘监控'}
            {location.pathname === '/quantitative' && '量化选股'}
            {location.pathname === '/watchlist' && '自选股管理'}
          </h2>
          <div style={{ color: '#666' }}>
            系统状态: 正常 | 最后更新: {new Date().toLocaleTimeString()}
          </div>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/quantitative" element={<QuantitativeSelection />} />
            <Route path="/watchlist" element={<Watchlist />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <AppContent />
      </Router>
    </ConfigProvider>
  );
};

export default App;
