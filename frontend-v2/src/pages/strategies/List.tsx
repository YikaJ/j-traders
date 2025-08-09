import { useEffect, useMemo, useState } from 'react'
import { Button, Card, Input, Skeleton, Empty, Typography, Row, Col, Space } from 'antd'
import { http } from '../../api/client'
import { useNavigate } from 'react-router-dom'

export default function StrategyListPage() {
  const [loading, setLoading] = useState(false)
  const [rows, setRows] = useState<any[]>([])
  const [q, setQ] = useState<string>('')
  const navigate = useNavigate()

  const fetchData = async () => {
    setLoading(true)
    try {
      const { data } = await http.get('/strategies')
      setRows(data || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const filtered = useMemo(() => {
    const kw = q.trim().toLowerCase()
    if (!kw) return rows
    return rows.filter((r: any) => String(r.name || '').toLowerCase().includes(kw))
  }, [rows, q])

  const cards = useMemo(() => filtered.map((r: any) => (
    <Col key={r.id} xs={24} sm={12} lg={8} xl={6}>
      <Card
        hoverable
        title={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography.Text strong ellipsis>{r.name}</Typography.Text>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>{r.created_at}</Typography.Text>
          </div>
        }
        actions={[
          <Button key="detail" size="small" onClick={() => navigate(`/strategies/${r.id}`)}>详情</Button>,
        ]}
      >
        <Space direction="vertical" size={8} style={{ width: '100%' }}>
          {r.desc ? (
            <Typography.Paragraph type="secondary" ellipsis={{ rows: 2 }} style={{ marginBottom: 0 }}>
              {r.desc}
            </Typography.Paragraph>
          ) : null}
          <Space size={[8, 8]} wrap>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>ID：{r.id}</Typography.Text>
            {r.normalization ? (
              <Typography.Text style={{ fontSize: 12 }}>标准化：{String(r.normalization?.method || 'zscore')}</Typography.Text>
            ) : (
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>标准化：无</Typography.Text>
            )}
            {Array.isArray(r.weights) ? (
              <Typography.Text style={{ fontSize: 12 }}>因子数：{r.weights.length}</Typography.Text>
            ) : null}
          </Space>
        </Space>
      </Card>
    </Col>
  )), [filtered, navigate])

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
        <Typography.Title level={5} style={{ margin: 0 }}>策略列表</Typography.Title>
        <Space.Compact>
          <Input.Search placeholder="搜索名称" allowClear onSearch={(val)=>setQ(val)} onChange={(e)=>setQ(e.target.value)} style={{ width: 280 }} />
          <Button type="primary" onClick={() => navigate('/strategies/new')}>新建策略</Button>
        </Space.Compact>
      </div>

      {loading ? (
        <Row gutter={[16, 16]}>
          {Array.from({ length: 8 }).map((_, i) => (
            <Col key={i} xs={24} sm={12} lg={8} xl={6}>
              <Card>
                <Skeleton active paragraph={{ rows: 2 }} />
              </Card>
            </Col>
          ))}
        </Row>
      ) : filtered.length === 0 ? (
        <Card>
          <Empty description="暂无策略数据" />
        </Card>
      ) : (
        <Row gutter={[16, 16]}>
          {cards}
        </Row>
      )}
    </div>
  )
}
