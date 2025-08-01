import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Space, Button, message } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, ReloadOutlined } from '@ant-design/icons';
import Plot from 'react-plotly.js';
import { marketApi, watchlistApi, MarketIndex, WatchlistStock } from '../services/api';

const Dashboard: React.FC = () => {
  const [indices, setIndices] = useState<MarketIndex[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistStock[]>([]);
  const [loading, setLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(true);

  // 加载市场指数数据
  const loadMarketIndices = async () => {
    try {
      const data = await marketApi.getMarketIndices();
      setIndices(data);
    } catch (error) {
      console.error('获取市场指数失败:', error);
      message.error('获取市场指数失败，请检查网络连接');
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

  // 加载自选股数据
  const loadWatchlist = async () => {
    try {
      const data = await watchlistApi.getWatchlist();
      setWatchlist(data);
    } catch (error) {
      console.error('获取自选股失败:', error);
      message.error('获取自选股失败，请检查网络连接');
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
      setDataLoading(true);
      await Promise.all([loadMarketIndices(), loadWatchlist()]);
      setDataLoading(false);
    };
    loadData();
  }, []);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await Promise.all([loadMarketIndices(), loadWatchlist()]);
      message.success('数据刷新成功');
    } catch (error) {
      message.error('数据刷新失败');
    } finally {
      setLoading(false);
    }
  };

  const watchlistColumns = [
    {
      title: '代码',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '现价',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '涨跌',
      dataIndex: 'change',
      key: 'change',
      render: (change: number) => (
        <span style={{ color: change >= 0 ? '#f5222d' : '#52c41a' }}>
          {change >= 0 ? '+' : ''}{change.toFixed(2)}
        </span>
      ),
    },
    {
      title: '涨跌幅',
      dataIndex: 'changePercent',
      key: 'changePercent',
      render: (changePercent: number) => (
        <Tag color={changePercent >= 0 ? 'red' : 'green'}>
          {changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%
        </Tag>
      ),
    }
  ];

  // 生成示例K线图数据
  const generateChartData = () => {
    const dates = [];
    const prices = [];
    const basePrice = 3200;
    
    for (let i = 30; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      dates.push(date.toISOString().split('T')[0]);
      prices.push(basePrice + Math.random() * 100 - 50);
    }
    
    return { dates, prices };
  };

  const { dates, prices } = generateChartData();

  return (
    <div>
      <Row gutter={[16, 16]}>
        {/* 市场指数卡片 */}
        {indices.map((index) => (
          <Col xs={24} sm={12} lg={8} key={index.symbol}>
            <Card>
              <Statistic
                title={index.name}
                value={index.price}
                precision={2}
                valueStyle={{ 
                  color: index.change >= 0 ? '#f5222d' : '#52c41a',
                  fontSize: '24px'
                }}
                prefix={index.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                suffix={
                  <div style={{ fontSize: '14px', marginTop: '8px' }}>
                    <div>
                      {index.change >= 0 ? '+' : ''}{index.change.toFixed(2)} 
                      ({index.change >= 0 ? '+' : ''}{index.changePercent.toFixed(2)}%)
                    </div>
                    <div style={{ color: '#666', fontSize: '12px' }}>
                      成交量: {(index.volume / 100000000).toFixed(2)}亿
                    </div>
                  </div>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
        {/* 上证指数走势图 */}
        <Col xs={24} lg={16}>
          <Card 
            title="上证指数走势" 
            extra={
              <Button 
                icon={<ReloadOutlined />} 
                onClick={handleRefresh}
                loading={loading}
              >
                刷新
              </Button>
            }
          >
            <Plot
              data={[
                {
                  x: dates,
                  y: prices,
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
                xaxis: { title: '日期' },
                yaxis: { title: '点数' },
                showlegend: false
              }}
              config={{ responsive: true }}
              style={{ width: '100%' }}
            />
          </Card>
        </Col>

        {/* 自选股监控 */}
        <Col xs={24} lg={8}>
          <Card title="自选股监控" extra={<a href="/watchlist">查看全部</a>}>
            <Table
              dataSource={watchlist}
              columns={watchlistColumns}
              pagination={false}
              size="small"
              rowKey="symbol"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;