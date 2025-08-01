import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Space, Button, message, Modal, Spin } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, ReloadOutlined, SyncOutlined, DatabaseOutlined } from '@ant-design/icons';
import Plot from 'react-plotly.js';
import { marketApi, watchlistApi, stockApi, MarketIndex, WatchlistStock } from '../services/api';

const Dashboard: React.FC = () => {
  const [indices, setIndices] = useState<MarketIndex[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistStock[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncModalVisible, setSyncModalVisible] = useState(false);
  const [syncInfo, setSyncInfo] = useState<any>(null);
  const [syncing, setSyncing] = useState(false);
  const [chartData, setChartData] = useState<{ dates: string[], prices: number[] }>({ dates: [], prices: [] });

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

  // 加载上证指数历史数据
  const loadShanghaiIndexHistory = async () => {
    try {
      const historyData = await marketApi.getStockHistory('000001.SH', 30);
      if (historyData && historyData.data && historyData.data.length > 0) {
        const dates = historyData.data.map((item: any) => item.date);
        const prices = historyData.data.map((item: any) => item.close);
        setChartData({ dates, prices });
      } else {
        // 如果没有数据，使用空数组
        setChartData({ dates: [], prices: [] });
      }
    } catch (error) {
      console.error('获取上证指数历史数据失败:', error);
      // 如果获取失败，使用空数组
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
      await Promise.all([loadMarketIndices(), loadWatchlist(), loadSyncInfo(), loadShanghaiIndexHistory()]);
    };
    loadData();
  }, []);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await Promise.all([loadMarketIndices(), loadWatchlist(), loadShanghaiIndexHistory()]);
      message.success('数据刷新成功');
    } catch (error) {
      message.error('数据刷新失败');
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
      message.error('获取同步信息失败');
    }
  };

  // 执行股票数据同步
  const handleStockSync = async () => {
    setSyncing(true);
    try {
      const result = await stockApi.syncStockData();
      
      // 显示详细的同步结果
      message.success(
        `同步完成！共获取 ${result.total_fetched || 0} 只股票，` +
        `新增 ${result.new_stocks || 0} 只，更新 ${result.updated_stocks || 0} 只`
      );
      
      // 立即刷新一次，然后延迟再刷新一次确保数据更新
      await loadSyncInfo();
      
      setTimeout(async () => {
        await loadSyncInfo();
        console.log('延迟刷新同步信息完成');
      }, 2000);
      
    } catch (error) {
      console.error('股票数据同步失败:', error);
      message.error('股票数据同步失败');
    } finally {
      setSyncing(false);
    }
  };

  // 打开同步对话框
  const showSyncModal = async () => {
    setSyncModalVisible(true);
    await loadSyncInfo();
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
      render: (price: number) => `¥${(price || 0).toFixed(2)}`,
    },
    {
      title: '涨跌',
      dataIndex: 'change',
      key: 'change',
      render: (change: number) => (
        <span style={{ color: (change || 0) >= 0 ? '#f5222d' : '#52c41a' }}>
          {(change || 0) >= 0 ? '+' : ''}{(change || 0).toFixed(2)}
        </span>
      ),
    },
    {
      title: '涨跌幅',
      dataIndex: 'changePercent',
      key: 'changePercent',
      render: (changePercent: number) => (
        <Tag color={(changePercent || 0) >= 0 ? 'red' : 'green'}>
          {(changePercent || 0) >= 0 ? '+' : ''}{(changePercent || 0).toFixed(2)}%
        </Tag>
      ),
    }
  ];

  return (
    <div>
      <Row gutter={[16, 16]}>
        {/* 市场指数卡片 */}
        {indices.map((index) => (
          <Col xs={24} sm={12} lg={8} key={index.symbol}>
            <Card>
              <Statistic
                title={index.name}
                value={index.price || 0}
                precision={2}
                valueStyle={{ 
                  color: (index.change || 0) >= 0 ? '#f5222d' : '#52c41a',
                  fontSize: '24px'
                }}
                prefix={(index.change || 0) >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                suffix={
                  <div style={{ fontSize: '14px', marginTop: '8px' }}>
                    <div>
                      {(index.change || 0) >= 0 ? '+' : ''}{(index.change || 0).toFixed(2)} 
                      ({(index.changePercent || 0) >= 0 ? '+' : ''}{(index.changePercent || 0).toFixed(2)}%)
                    </div>
                    <div style={{ color: '#666', fontSize: '12px' }}>
                      成交量: {((index.volume || 0) / 100000000).toFixed(2)}亿
                    </div>
                  </div>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
        {/* 股票数据管理 */}
        <Col xs={24}>
          <Card 
            title="股票数据管理" 
            extra={
              <Space>
                <Button 
                  icon={<DatabaseOutlined />} 
                  onClick={showSyncModal}
                >
                  数据同步
                </Button>
                <Button 
                  icon={<ReloadOutlined />} 
                  onClick={async () => {
                    setLoading(true);
                    try {
                      await Promise.all([loadMarketIndices(), loadWatchlist(), loadSyncInfo()]);
                      message.success('数据刷新成功');
                    } catch (error) {
                      message.error('数据刷新失败');
                    } finally {
                      setLoading(false);
                    }
                  }}
                  loading={loading}
                >
                  刷新数据
                </Button>
              </Space>
            }
          >
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Statistic
                  title="股票总数"
                  value={syncInfo?.stock_count?.total || 0}
                  prefix={<DatabaseOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="活跃股票"
                  value={syncInfo?.stock_count?.active || 0}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="上交所"
                  value={syncInfo?.stock_count?.sh_market || 0}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="深交所"
                  value={syncInfo?.stock_count?.sz_market || 0}
                  valueStyle={{ color: '#389e0d' }}
                />
              </Col>
            </Row>
            {syncInfo?.last_sync_time && (
              <div style={{ marginTop: '16px', color: '#666', fontSize: '12px' }}>
                最后同步时间: {new Date(syncInfo.last_sync_time).toLocaleString()}
              </div>
            )}
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#999' }}>
              数据获取时间: {new Date().toLocaleString()}
            </div>
          </Card>
        </Col>
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
                  x: chartData.dates,
                  y: chartData.prices,
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
                xaxis: { title: { text: '日期' } },
                yaxis: { title: { text: '点数' } },
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

      {/* 股票数据同步对话框 */}
      <Modal
        title="股票数据同步"
        open={syncModalVisible}
        onCancel={() => setSyncModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setSyncModalVisible(false)}>
            取消
          </Button>,
          <Button 
            key="sync" 
            type="primary" 
            icon={<SyncOutlined />}
            loading={syncing}
            onClick={handleStockSync}
          >
            开始同步
          </Button>
        ]}
      >
        <div>
          <p>
            <strong>数据同步说明：</strong>
          </p>
          <ul>
            <li>同步操作将从数据源获取最新的股票列表信息</li>
            <li>包括股票代码、名称、行业、地区等基础信息</li>
            <li>同步过程可能需要几分钟时间，请耐心等待</li>
            <li>同步完成后，股票搜索功能将使用最新数据</li>
          </ul>
          
          {syncInfo && (
            <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
              <p><strong>当前数据状态：</strong></p>
              <p>股票总数: {syncInfo.stock_count?.total || 0}</p>
              <p>活跃股票: {syncInfo.stock_count?.active || 0}</p>
              <p>上交所: {syncInfo.stock_count?.sh_market || 0}</p>
              <p>深交所: {syncInfo.stock_count?.sz_market || 0}</p>
              {syncInfo.last_sync_time && (
                <p>最后同步: {new Date(syncInfo.last_sync_time).toLocaleString()}</p>
              )}
            </div>
          )}
          
          {syncing && (
            <div style={{ marginTop: '16px', textAlign: 'center' }}>
              <Spin size="large" />
              <p style={{ marginTop: '8px' }}>正在同步股票数据，请稍候...</p>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default Dashboard;