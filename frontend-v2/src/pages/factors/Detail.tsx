import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { http } from '../../api/client'
import { Button, Card, Form, Input, Space, message, Modal, InputNumber } from 'antd'
import Editor from '@monaco-editor/react'
import { SelectionCard } from '../../components/SelectionCard'

export default function FactorDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [rec, setRec] = useState<any>(null)
  const [code, setCode] = useState<string>('')

  const load = async () => {
    try {
      const { data } = await http.get(`/factors/${id}`)
      setRec(data)
      setCode(data.code_text || '')
    } finally {}
  }

  useEffect(() => { load() }, [id])

  const onSave = async (values: any) => {
    try {
      await http.put(`/factors/${id}`, {
        name: values.name,
        desc: values.desc,
        tags: (values.tags || '').split(',').map((s: string) => s.trim()).filter(Boolean),
        fields_used: rec?.fields_used || [],
        normalization: rec?.normalization || null,
        selection: rec?.selection || null,
        code_text: code,
      })
      message.success('已保存')
      load()
    } catch {}
  }

  const onDelete = async () => {
    Modal.confirm({
      title: '确认删除因子？',
      onOk: async () => {
        await http.delete(`/factors/${id}`)
        message.success('已删除')
        navigate('/factors/list')
      }
    })
  }

  const onValidate = async () => {
    try {
      const { data } = await http.post('/factors/validate', { selection: rec.selection, code_text: code })
      if (data.ok) message.success('校验通过')
      else message.error('校验失败：' + (data.errors || []).join('; '))
    } catch {}
  }

  const [testTopN, setTestTopN] = useState<number>(5)
  const onTest = async () => {
    try {
      const { data } = await http.post('/factors/test', { selection: rec.selection, code_text: code, top_n: testTopN })
      message.info('样例行：' + JSON.stringify(data.sample_rows || []).slice(0, 120) + '...')
    } catch {}
  }

  if (!rec) return null

  return (
    <div>
      <Form layout="vertical" initialValues={{ name: rec.name, desc: rec.desc, tags: (rec.tags || []).join(',') }} onFinish={onSave}>
        <Form.Item label="名称" name="name" rules={[{ required: true }]}><Input /></Form.Item>
        <Form.Item label="描述" name="desc"><Input /></Form.Item>
        <Form.Item label="标签（逗号分隔）" name="tags"><Input /></Form.Item>
        <SelectionCard selection={rec.selection} />
        <Card size="small" title="代码">
          <Editor height="400px" defaultLanguage="python" value={code} onChange={(v) => setCode(v || '')} options={{ minimap: { enabled: false } }} />
          <Space style={{ marginTop: 12 }}>
            <Button onClick={onValidate}>校验</Button>
            <InputNumber min={1} value={testTopN} onChange={(v)=>setTestTopN(Number(v)||5)} />
            <Button onClick={onTest}>快速测试</Button>
            <Button type="primary" htmlType="submit">保存</Button>
            <Button danger onClick={onDelete}>删除</Button>
          </Space>
        </Card>
      </Form>
    </div>
  )
}
