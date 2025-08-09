import { useState } from 'react'
import { Button, Card, Form, Input, Space, message } from 'antd'
import Editor from '@monaco-editor/react'
import SelectionPicker from '../../components/SelectionPicker'
import { http } from '../../api/client'
import { useNavigate } from 'react-router-dom'

export default function FactorNewPage() {
  const [selectionSlug, setSelectionSlug] = useState<string>()
  const [spec, setSpec] = useState<string>('统计过去一周 pe_ttm 的逆序并输出为 factor 列')
  const [code, setCode] = useState<string>('')
  const [genLoading, setGenLoading] = useState(false)
  const navigate = useNavigate()

  const onGen = async () => {
    if (!selectionSlug) { message.warning('请选择 Selection'); return }
    setGenLoading(true)
    try {
      const { data } = await http.post('/factors/codegen', { selection_slug: selectionSlug, user_factor_spec: spec })
      setCode(data.code_text || '')
      message.success('已生成代码')
    } finally { setGenLoading(false) }
  }

  const onValidate = async () => {
    try {
      const { data: sel } = await http.get(`/catalog/selections/${selectionSlug}`)
      const { data } = await http.post('/factors/validate', { selection: sel, code_text: code })
      if (data.ok) message.success('校验通过')
      else message.error('校验失败：' + (data.errors || []).join('; '))
    } catch {}
  }

  const onSave = async (values: any) => {
    try {
      const { data: sel } = await http.get(`/catalog/selections/${selectionSlug}`)
      const { data } = await http.post('/factors', {
        name: values.name,
        desc: values.desc,
        tags: (values.tags || '').split(',').map((s: string) => s.trim()).filter(Boolean),
        code_text: code,
        fields_used: [],
        normalization: null,
        selection: sel,
      })
      message.success('已创建')
      navigate(`/factors/${data.id}`)
    } catch {}
  }

  return (
    <Form layout="vertical" onFinish={onSave}>
      <Form.Item label="名称" name="name" rules={[{ required: true }]}><Input /></Form.Item>
      <Form.Item label="标签（逗号分隔）" name="tags"><Input /></Form.Item>
      <Form.Item label="描述" name="desc"><Input /></Form.Item>
      <Card size="small" title="选择 Selection">
        <SelectionPicker value={selectionSlug} onChange={setSelectionSlug} />
      </Card>
      <Card size="small" title="需求说明">
        <Space.Compact style={{ width: '100%' }}>
          <Input value={spec} onChange={e=>setSpec(e.target.value)} />
          <Button type="primary" onClick={onGen} loading={genLoading}>生成代码</Button>
        </Space.Compact>
      </Card>
      <Card size="small" title="代码">
        <Editor height="360px" defaultLanguage="python" value={code} onChange={(v)=>setCode(v||'')} options={{ minimap: { enabled: false } }} />
        <Space style={{ marginTop: 12 }}>
          <Button onClick={onValidate}>校验</Button>
          <Button type="primary" htmlType="submit">保存</Button>
        </Space>
      </Card>
    </Form>
  )
}