import { useEffect, useState } from 'react'
import { Table, Tag, Button, Space } from 'antd'
import { http } from '../../api/client'
import { useNavigate } from 'react-router-dom'

export default function FactorListPage() {
  const [loading, setLoading] = useState(false)
  const [rows, setRows] = useState<any[]>([])
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

  return (
    <div>
      <div style={{ marginBottom: 12 }}><Button type="primary" onClick={()=>navigate('/factors/new')}>新增因子</Button></div>
      <Table
      rowKey="id"
      loading={loading}
      dataSource={rows}
      columns={[
        { title: '名称', dataIndex: 'name' },
        { title: '分类', dataIndex: 'tags', render: (tags: string[]) => (tags || []).map(t => <Tag key={t}>{t}</Tag>) },
        { title: '字段数', render: (_: any, r: any) => (r.fields_used || []).length },
        { title: '创建时间', dataIndex: 'created_at' },
        { title: '操作', render: (_:any, r:any) => <Space><Button onClick={()=>navigate(`/factors/${r.id}`)}>详情</Button></Space> },
      ]}
      pagination={{ pageSize: 10 }}
    />
    </div>
  )
}