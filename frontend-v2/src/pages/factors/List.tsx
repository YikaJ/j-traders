import { useEffect, useMemo, useState } from 'react'
import { Tag, Button, Card, Input, Skeleton, Empty, Typography, Row, Col, Space } from 'antd'
import { http } from '../../api/client'
import { useNavigate } from 'react-router-dom'

export default function FactorListPage() {
  const [loading, setLoading] = useState(false)
  const [rows, setRows] = useState<any[]>([])
  const [q, setQ] = useState<string>('')
  const navigate = useNavigate()

  const fetchData = async () => {
    setLoading(true)
    try {
      const { data } = await http.get('/factors')
      setRows(data || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const filtered = useMemo(() => {
    const kw = q.trim().toLowerCase()
    if (!kw) return rows
    return rows.filter((r: any) => {
      const tagStr = (r.tags || []).join(',')
      return String(r.name || '').toLowerCase().includes(kw) || tagStr.toLowerCase().includes(kw)
    })
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
          <Button key="detail" size="small" onClick={() => navigate(`/factors/${r.id}`)}>详情</Button>,
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
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              字段数：{(r.fields_used || []).length}
            </Typography.Text>
            {Array.isArray(r.fields_used) && r.fields_used.length > 0 ? (
              <Typography.Text style={{ fontSize: 12 }}>
                预览：{(r.fields_used || []).slice(0, 4).map((x: any) => String(x)).join(', ')}
              </Typography.Text>
            ) : null}
            {r.normalization ? (
              <Typography.Text style={{ fontSize: 12 }}>标准化：是</Typography.Text>
            ) : (
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>标准化：无</Typography.Text>
            )}
          </Space>

          <div>
            {(r.tags || []).slice(0, 5).map((t: string) => (
              <Tag key={t}>{t}</Tag>
            ))}
            {(r.tags || []).length > 5 ? <Tag>+{(r.tags || []).length - 5}</Tag> : null}
          </div>
        </Space>
      </Card>
    </Col>
  )), [filtered, navigate])

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
        <Typography.Title level={5} style={{ margin: 0 }}>因子列表</Typography.Title>
        <Space.Compact>
          <Input.Search placeholder="搜索名称或标签" allowClear onSearch={(val)=>setQ(val)} onChange={(e)=>setQ(e.target.value)} style={{ width: 280 }} />
          <Button type="primary" onClick={() => navigate('/factors/new')}>新增因子</Button>
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
          <Empty description="暂无因子数据" />
        </Card>
      ) : (
        <Row gutter={[16, 16]}>
          {cards}
        </Row>
      )}
    </div>
  )
}
