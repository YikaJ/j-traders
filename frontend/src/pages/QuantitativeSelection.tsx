import React, { useState } from 'react';
import { Card, Button, Table, Tag, Space, Modal, Form, Input, Select, message } from 'antd';
import { PlusOutlined, PlayCircleOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

interface Factor {
  id: string;
  name: string;
  description: string;
  category: string;
  code: string;
}

interface StrategyResult {
  symbol: string;
  name: string;
  score: number;
  rank: number;
  price: number;
  changePercent: number;
}

const QuantitativeSelection: React.FC = () => {
  const [factors, setFactors] = useState<Factor[]>([]);
  const [results, setResults] = useState<StrategyResult[]>([]);
  const [isFactorModalVisible, setIsFactorModalVisible] = useState(false);
  const [isStrategyModalVisible, setIsStrategyModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [strategyForm] = Form.useForm();

  // 模拟因子数据
  const mockFactors: Factor[] = [
    {
      id: '1',
      name: 'PE倍数因子',
      description: '基于市盈率的估值因子',
      category: '估值',
      code: `def calculate(data):
    pe_ratio = data['market_cap'] / data['net_income']
    return 1 / pe_ratio  # PE倍数越低，得分越高`
    },
    {
      id: '2',
      name: '动量因子',
      description: '基于价格动量的技术因子',
      category: '技术',
      code: `def calculate(data):
    returns_20d = data['close'].pct_change(20)
    return returns_20d.fillna(0)`
    }
  ];

  // 模拟选股结果
  const mockResults: StrategyResult[] = [
    {
      symbol: '000001.SZ',
      name: '平安银行',
      score: 0.85,
      rank: 1,
      price: 15.23,
      changePercent: 3.04
    },
    {
      symbol: '600036.SH',
      name: '招商银行',
      score: 0.82,
      rank: 2,
      price: 42.15,
      changePercent: 3.01
    },
    {
      symbol: '000002.SZ',
      name: '万科A',
      score: 0.78,
      rank: 3,
      price: 18.67,
      changePercent: -1.22
    }
  ];

  React.useEffect(() => {
    setFactors(mockFactors);
  }, []);

  const handleCreateFactor = () => {
    setIsFactorModalVisible(true);
    form.resetFields();
  };

  const handleFactorSubmit = async (values: any) => {
    try {
      // 这里会调用后端API创建因子
      const newFactor: Factor = {
        id: Date.now().toString(),
        ...values
      };
      setFactors([...factors, newFactor]);
      setIsFactorModalVisible(false);
      message.success('因子创建成功');
    } catch (error) {
      message.error('因子创建失败');
    }
  };

  const handleRunStrategy = () => {
    setIsStrategyModalVisible(true);
    strategyForm.resetFields();
  };

  const handleStrategySubmit = async (values: any) => {
    try {
      // 这里会调用后端API执行策略
      setResults(mockResults);
      setIsStrategyModalVisible(false);
      message.success('策略执行成功');
    } catch (error) {
      message.error('策略执行失败');
    }
  };

  const factorColumns = [
    {
      title: '因子名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag color={category === '估值' ? 'blue' : 'green'}>{category}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Factor) => (
        <Space size="middle">
          <Button 
            type="link" 
            icon={<EditOutlined />}
            onClick={() => {
              // 编辑因子
              message.info('编辑功能待实现');
            }}
          >
            编辑
          </Button>
          <Button 
            type="link" 
            danger
            icon={<DeleteOutlined />}
            onClick={() => {
              // 删除因子
              setFactors(factors.filter(f => f.id !== record.id));
              message.success('因子删除成功');
            }}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const resultColumns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 80,
      render: (rank: number) => (
        <Tag color={rank <= 3 ? 'gold' : 'default'}>{rank}</Tag>
      ),
    },
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
      title: '综合得分',
      dataIndex: 'score',
      key: 'score',
      render: (score: number) => score.toFixed(3),
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
      render: (_: any, record: StrategyResult) => (
        <Button 
          type="link"
          onClick={() => {
            // 添加到自选股
            message.success(`${record.name} 已添加到自选股`);
          }}
        >
          加自选
        </Button>
      ),
    },
  ];

  return (
    <div>
      {/* 因子管理 */}
      <Card 
        title="因子管理" 
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={handleCreateFactor}
          >
            创建因子
          </Button>
        }
        style={{ marginBottom: '24px' }}
      >
        <Table
          dataSource={factors}
          columns={factorColumns}
          rowKey="id"
          pagination={false}
        />
      </Card>

      {/* 策略执行 */}
      <Card 
        title="策略执行" 
        extra={
          <Button 
            type="primary" 
            icon={<PlayCircleOutlined />}
            onClick={handleRunStrategy}
          >
            执行策略
          </Button>
        }
        style={{ marginBottom: '24px' }}
      >
        {results.length > 0 ? (
          <Table
            dataSource={results}
            columns={resultColumns}
            rowKey="symbol"
            pagination={{ pageSize: 10 }}
          />
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
            暂无选股结果，请先执行策略
          </div>
        )}
      </Card>

      {/* 创建因子弹窗 */}
      <Modal
        title="创建因子"
        open={isFactorModalVisible}
        onCancel={() => setIsFactorModalVisible(false)}
        onOk={() => form.submit()}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleFactorSubmit}
        >
          <Form.Item
            name="name"
            label="因子名称"
            rules={[{ required: true, message: '请输入因子名称' }]}
          >
            <Input placeholder="请输入因子名称" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="因子描述"
            rules={[{ required: true, message: '请输入因子描述' }]}
          >
            <Input.TextArea placeholder="请输入因子描述" rows={2} />
          </Form.Item>
          
          <Form.Item
            name="category"
            label="因子分类"
            rules={[{ required: true, message: '请选择因子分类' }]}
          >
            <Select placeholder="请选择因子分类">
              <Select.Option value="估值">估值</Select.Option>
              <Select.Option value="技术">技术</Select.Option>
              <Select.Option value="基本面">基本面</Select.Option>
              <Select.Option value="情绪">情绪</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="code"
            label="因子代码"
            rules={[{ required: true, message: '请输入因子代码' }]}
          >
            <Input.TextArea 
              placeholder={`请输入Python代码，例如：
def calculate(data):
    # data包含股票的历史数据
    # 返回因子值
    return data['close'].pct_change(20)`}
              rows={8}
              style={{ fontFamily: 'Monaco, Consolas, monospace' }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 策略配置弹窗 */}
      <Modal
        title="策略配置"
        open={isStrategyModalVisible}
        onCancel={() => setIsStrategyModalVisible(false)}
        onOk={() => strategyForm.submit()}
      >
        <Form
          form={strategyForm}
          layout="vertical"
          onFinish={handleStrategySubmit}
        >
          <Form.Item
            name="factors"
            label="选择因子"
            rules={[{ required: true, message: '请选择至少一个因子' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择因子"
              options={factors.map(f => ({ label: f.name, value: f.id }))}
            />
          </Form.Item>
          
          <Form.Item
            name="maxResults"
            label="结果数量"
            initialValue={50}
          >
            <Select>
              <Select.Option value={20}>前20名</Select.Option>
              <Select.Option value={50}>前50名</Select.Option>
              <Select.Option value={100}>前100名</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default QuantitativeSelection;