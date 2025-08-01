import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Modal, Form, Input, Tag, message, Popconfirm, Spin } from 'antd';
import { PlusOutlined, DeleteOutlined, SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import { watchlistApi, stockApi, WatchlistStock } from '../services/api';

interface SearchStock {
  symbol: string;
  name: string;
  industry?: string;
  area?: string;
  market?: string;
}

const Watchlist: React.FC = () => {
  const [watchlist, setWatchlist] = useState<WatchlistStock[]>([]);
  const [isAddModalVisible, setIsAddModalVisible] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchStock[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(true);
  const [form] = Form.useForm();

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
      message.error('搜索股票失败，请检查网络连接');
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleAddStock = async (stock: SearchStock) => {
    try {
      // 检查是否已存在
      if (watchlist.some(item => item.symbol === stock.symbol)) {
        message.warning('该股票已在自选股中');
        return;
      }

      const newStock = await watchlistApi.addToWatchlist(stock.symbol, stock.name);
      setWatchlist([...watchlist, newStock]);
      message.success(`${stock.name} 已添加到自选股`);
      setIsAddModalVisible(false);
      form.resetFields();
      setSearchResults([]); // 清空搜索结果
    } catch (error) {
      console.error('添加自选股失败:', error);
      message.error('添加自选股失败，请检查网络连接');
    }
  };

  const handleRemoveStock = async (id: number, name: string) => {
    try {
      await watchlistApi.removeFromWatchlist(id);
      setWatchlist(watchlist.filter(stock => stock.id !== id));
      message.success(`${name} 已从自选股中移除`);
    } catch (error) {
      console.error('删除自选股失败:', error);
      message.error('删除自选股失败，请检查网络连接');
    }
  };

  const watchlistColumns = [
    {
      title: '代码',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 120,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: '现价',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      render: (price: number) => `¥${(price || 0).toFixed(2)}`,
    },
    { 
      title: '涨跌',
      dataIndex: 'change',
      key: 'change',
      width: 80,
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
      width: 100,
      render: (changePercent: number) => (
        <Tag color={(changePercent || 0) >= 0 ? 'red' : 'green'}>
          {(changePercent || 0) >= 0 ? '+' : ''}{(changePercent || 0).toFixed(2)}%
        </Tag>
      ),
    },
    {
      title: '添加日期',
      dataIndex: 'addedAt',
      key: 'addedAt',
      width: 120,
    },
    {
      title: '备注',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
      render: (notes: string) => notes || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: WatchlistStock) => (
        <Space size="middle">
          <Button 
            type="link" 
            size="small"
            onClick={() => {
              // 查看详情
              message.info('股票详情功能待实现');
            }}
          >
            详情
          </Button>
          <Popconfirm
            title="确定要移除这只股票吗？"
            onConfirm={() => handleRemoveStock(record.id || 0, record.name)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="link" 
              danger
              size="small"
              icon={<DeleteOutlined />}
            >
              移除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const searchColumns = [
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
      title: '行业',
      dataIndex: 'industry',
      key: 'industry',
      render: (industry: string) => industry || '-',
    },
    {
      title: '地区',
      dataIndex: 'area',
      key: 'area',
      render: (area: string) => area || '-',
    },
    {
      title: '市场',
      dataIndex: 'market',
      key: 'market',
      render: (market: string) => (
        <Tag color={market === 'SH' ? 'red' : 'green'}>
          {market || '-'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: SearchStock) => (
        <Button 
          type="link"
          onClick={() => handleAddStock(record)}
        >
          添加
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Card 
        title={`自选股 (${watchlist.length})`}
        extra={
          <Space>
            <Button 
              icon={<ReloadOutlined />}
              onClick={async () => {
                setDataLoading(true);
                await loadWatchlist();
                setDataLoading(false);
                message.success('数据刷新成功');
              }}
              loading={dataLoading}
            >
              刷新
            </Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => setIsAddModalVisible(true)}
            >
              添加股票
            </Button>
          </Space>
        }
      >
        <Spin spinning={dataLoading}>
          <Table
            dataSource={watchlist}
            columns={watchlistColumns}
            rowKey="symbol"
            pagination={{ 
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 只股票`
            }}
            scroll={{ x: 800 }}
          />
        </Spin>
      </Card>

      {/* 添加股票弹窗 */}
      <Modal
        title="添加股票到自选股"
        open={isAddModalVisible}
        onCancel={() => {
          setIsAddModalVisible(false);
          form.resetFields();
          setSearchResults([]);
        }}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            label="搜索股票"
            name="keyword"
          >
            <Input.Search
              placeholder="请输入股票代码或名称"
              enterButton={<SearchOutlined />}
              onSearch={handleSearch}
              loading={searchLoading}
            />
          </Form.Item>

          {searchResults.length > 0 && (
            <Form.Item label="搜索结果">
              <Table
                dataSource={searchResults}
                columns={searchColumns}
                rowKey="symbol"
                pagination={false}
                size="small"
              />
            </Form.Item>
          )}

          <Form.Item
            label="备注"
            name="notes"
          >
            <Input.TextArea 
              placeholder="可选：为这只股票添加备注信息"
              rows={2}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Watchlist;