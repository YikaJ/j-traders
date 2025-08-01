import React, { useState } from 'react';
import { Card, Table, Button, Space, Modal, Form, Input, Tag, message, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';

interface WatchlistStock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  addedAt: string;
  notes?: string;
}

interface SearchStock {
  symbol: string;
  name: string;
  price: number;
  changePercent: number;
}

const Watchlist: React.FC = () => {
  const [watchlist, setWatchlist] = useState<WatchlistStock[]>([]);
  const [isAddModalVisible, setIsAddModalVisible] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchStock[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [form] = Form.useForm();

  // 模拟自选股数据
  const mockWatchlist: WatchlistStock[] = [
    {
      symbol: '000001.SZ',
      name: '平安银行',
      price: 15.23,
      change: 0.45,
      changePercent: 3.04,
      addedAt: '2024-01-15',
      notes: '银行股龙头'
    },
    {
      symbol: '000002.SZ',
      name: '万科A',
      price: 18.67,
      change: -0.23,
      changePercent: -1.22,
      addedAt: '2024-01-14',
      notes: '地产行业'
    },
    {
      symbol: '600036.SH',
      name: '招商银行',
      price: 42.15,
      change: 1.23,
      changePercent: 3.01,
      addedAt: '2024-01-13'
    }
  ];

  // 模拟搜索结果
  const mockSearchResults: SearchStock[] = [
    {
      symbol: '600519.SH',
      name: '贵州茅台',
      price: 1678.50,
      changePercent: 2.15
    },
    {
      symbol: '000858.SZ',
      name: '五粮液',
      price: 145.32,
      changePercent: -0.85
    },
    {
      symbol: '300750.SZ',
      name: '宁德时代',
      price: 198.45,
      changePercent: 1.25
    }
  ];

  React.useEffect(() => {
    setWatchlist(mockWatchlist);
  }, []);

  const handleSearch = async (keyword: string) => {
    if (!keyword) return;
    
    setSearchLoading(true);
    // 模拟API搜索
    setTimeout(() => {
      const filtered = mockSearchResults.filter(
        stock => stock.name.includes(keyword) || stock.symbol.includes(keyword)
      );
      setSearchResults(filtered);
      setSearchLoading(false);
    }, 500);
  };

  const handleAddStock = (stock: SearchStock, notes?: string) => {
    const newStock: WatchlistStock = {
      ...stock,
      change: stock.price * (stock.changePercent / 100),
      addedAt: new Date().toISOString().split('T')[0],
      notes: notes || ''
    };

    // 检查是否已存在
    if (watchlist.some(item => item.symbol === stock.symbol)) {
      message.warning('该股票已在自选股中');
      return;
    }

    setWatchlist([...watchlist, newStock]);
    message.success(`${stock.name} 已添加到自选股`);
    setIsAddModalVisible(false);
    form.resetFields();
  };

  const handleRemoveStock = (symbol: string) => {
    setWatchlist(watchlist.filter(stock => stock.symbol !== symbol));
    message.success('已从自选股中移除');
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
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '涨跌',
      dataIndex: 'change',
      key: 'change',
      width: 80,
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
      width: 100,
      render: (changePercent: number) => (
        <Tag color={changePercent >= 0 ? 'red' : 'green'}>
          {changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%
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
            onConfirm={() => handleRemoveStock(record.symbol)}
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
      title: '现价',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `¥${price.toFixed(2)}`,
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
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => setIsAddModalVisible(true)}
          >
            添加股票
          </Button>
        }
      >
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