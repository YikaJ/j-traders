import { useEffect, useState } from 'react'
import { Table, Button, Space } from 'antd'
import { http } from '../../api/client'
import { useNavigate } from 'react-router-dom'

export default function StrategyListPage() {
  const [loading, setLoading] = useState(false)
  const [rows, setRows] = useState<any[]>([])
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

  return (
    <div>
      <div style={{ marginBottom: 12 }}><Button type="primary" onClick={()=>navigate('/strategies/new')}>新建策略</Button></div>
      <Table
      rowKey="id"
      loading={loading}
      dataSource={rows}
      columns={[
        { title: '名称', dataIndex: 'name' },
        { title: '创建时间', dataIndex: 'created_at' },
        { title: '操作', render: (_: any, r:any) => <Space><Button onClick={()=>navigate(`/strategies/${r.id}`)}>详情</Button></Space> },
      ]}
      pagination={{ pageSize: 10 }}
    />
    </div>
  )
}