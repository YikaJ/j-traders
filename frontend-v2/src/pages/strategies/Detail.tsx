import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { http } from '../../api/client'
import { Button, Card, Form, Input, InputNumber, Space, Table, message, Select, Checkbox } from 'antd'

export default function StrategyDetailPage() {
  const { id } = useParams()
  const [rec, setRec] = useState<any>(null)
  const [factors, setFactors] = useState<any[]>([])
  const [results, setResults] = useState<any[]>([])

  const load = async () => {
    try {
      const [s, f] = await Promise.all([
        http.get(`/strategies/${id}`),
        http.get('/factors'),
      ])
      setRec(s.data)
      setFactors(f.data || [])
    } finally {}
  }
  useEffect(() => { load() }, [id])

  const onSaveNorm = async (values: any) => {
    try {
      await http.put(`/strategies/${id}/normalization`, { normalization: values })
      message.success('已保存标准化')
      load()
    } catch {}
  }

  const onSaveWeights = async (values: any) => {
    try {
      const weights = (values.weights || []).map((w: any) => ({ factor_id: w.factor_id, weight: Number(w.weight) }))
      await http.put(`/strategies/${id}/weights`, { weights })
      message.success('已保存权重')
      load()
    } catch {}
  }

  const [runForm] = Form.useForm()
  const onRun = async () => {
    try {
      const body = runForm.getFieldsValue()
      const { data } = await http.post(`/strategies/${id}/run`, body)
      setResults(data.results || [])
      message.success('已运行')
    } catch {}
  }

  if (!rec) return null

  return (
    <div>
      <Card size="small" title={`策略：${rec.name}`} style={{ marginBottom: 12 }}>
        创建时间：{rec.created_at}
      </Card>

      <Card size="small" title="标准化策略">
        <Form layout="inline" onFinish={onSaveNorm} initialValues={rec.normalization || { method: 'zscore', winsor: [0.01,0.99], fill: 'median' }}>
          <Form.Item name="method" label="方法"><Select style={{ width: 140 }} options={[{value:'zscore',label:'zscore'}]} /></Form.Item>
          <Form.Item name="winsor" label="winsor"><Input placeholder="如 0.01,0.99" /></Form.Item>
          <Form.Item name="fill" label="fill"><Select style={{ width: 120 }} options={[{value:'median',label:'median'},{value:'zero',label:'zero'}]} /></Form.Item>
          <Form.Item><Button type="primary" htmlType="submit">保存</Button></Form.Item>
        </Form>
      </Card>

      <Card size="small" title="因子与权重">
        <Form onFinish={onSaveWeights} initialValues={{ weights: rec.weights || [] }}>
          <Form.List name="weights">
            {(fields, { add, remove }) => (
              <div>
                {fields.map(field => (
                  <Space key={field.key} style={{ display:'flex', marginBottom: 8 }}>
                    <Form.Item name={[field.name, 'factor_id']} rules={[{ required: true }] }>
                      <Select style={{ width: 240 }} placeholder="选择因子" options={factors.map((f:any)=>({ value: f.id, label: `${f.id}-${f.name}` }))} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'weight']} rules={[{ required: true }]}>
                      <InputNumber style={{ width: 140 }} placeholder="权重（可正负）" />
                    </Form.Item>
                    <Button onClick={() => remove(field.name)}>移除</Button>
                  </Space>
                ))}
                <Button onClick={() => add()}>新增</Button>
                <Button type="primary" htmlType="submit" style={{ marginLeft: 8 }}>保存</Button>
              </div>
            )}
          </Form.List>
        </Form>
      </Card>

      <Card size="small" title="运行">
        <Form form={runForm} layout="inline" initialValues={{ top_n: 5, diagnostics: { enabled: true } }}>
          <Form.Item name="ts_codes" label="ts_codes"><Input placeholder="逗号分隔" /></Form.Item>
          <Form.Item name="industry" label="industry"><Input placeholder="如 银行" /></Form.Item>
          <Form.Item name="all" valuePropName="checked"><Checkbox>全量</Checkbox></Form.Item>
          <Form.Item name="start_date" label="start"><Input placeholder="20210101" /></Form.Item>
          <Form.Item name="end_date" label="end"><Input placeholder="20210108" /></Form.Item>
          <Form.Item name="top_n" label="TopN"><InputNumber min={1} /></Form.Item>
          <Form.Item><Button type="primary" onClick={onRun}>运行</Button></Form.Item>
        </Form>
        <Table rowKey={(r)=>`${r.ts_code}-${r.trade_date||r.end_date||''}`} dataSource={results} columns={[{title:'ts_code',dataIndex:'ts_code'},{title:'date',dataIndex:'trade_date'},{title:'score',dataIndex:'score'}]} pagination={{ pageSize: 10 }} style={{ marginTop: 12 }} />
      </Card>
    </div>
  )
}