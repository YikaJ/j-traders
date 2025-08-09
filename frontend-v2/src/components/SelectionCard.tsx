import { Card, Tag } from 'antd'

export function SelectionCard({ selection }: { selection: any }) {
  if (!selection) return null
  const output = selection.join_keys || []
  const items: any[] = selection.sources || []
  return (
    <Card size="small" title="Selection 摘要" style={{ marginTop: 8 }}>
      <div>输出索引：{output.map((k: string) => <Tag key={k}>{k}</Tag>)}</div>
      <div style={{ marginTop: 8 }}>
        数据端点：
        {items.map((it: any, idx: number) => (
          <Tag key={idx}>{it.endpoint}:{(it.fields||[]).length}</Tag>
        ))}
      </div>
    </Card>
  )
}
