import { useState } from 'react'
import { Button, Input, Space, message } from 'antd'
import Editor from '@monaco-editor/react'
import { http } from '../../api/client'

export default function SelectionEditorPage() {
  const [slug, setSlug] = useState<string>('')
  const [jsonText, setJsonText] = useState<string>('')

  const load = async () => {
    if (!slug) return
    try {
      const { data } = await http.get(`/catalog/selections/${slug}`)
      setJsonText(JSON.stringify(data, null, 2))
    } catch {
      message.warning('未找到，创建将写入新文件')
      setJsonText('')
    }
  }

  const doCreate = async () => {
    try {
      const body = JSON.parse(jsonText)
      await http.post('/catalog/selections', body)
      message.success('已创建')
    } catch (e: any) {
      message.error('创建失败：' + (e?.message || ''))
    }
  }

  const doUpdate = async () => {
    try {
      const body = JSON.parse(jsonText)
      await http.put(`/catalog/selections/${slug}`, body)
      message.success('已更新')
    } catch (e: any) {
      message.error('更新失败：' + (e?.message || ''))
    }
  }

  return (
    <div>
      <Space style={{ marginBottom: 12 }}>
        <Input placeholder="factor_slug（文件名）" value={slug} onChange={e => setSlug(e.target.value)} style={{ width: 280 }} />
        <Button onClick={load}>读取</Button>
        <Button type="primary" onClick={doCreate}>创建</Button>
        <Button onClick={doUpdate}>更新</Button>
      </Space>
      <Editor
        height="480px"
        defaultLanguage="json"
        value={jsonText}
        onChange={(v) => setJsonText(v || '')}
        options={{ minimap: { enabled: false } }}
      />
    </div>
  )
}