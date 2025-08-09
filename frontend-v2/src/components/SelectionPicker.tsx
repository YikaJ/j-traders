import { useEffect, useState } from 'react'
import { Select, Spin } from 'antd'
import { http } from '../api/client'
import { SelectionCard } from './SelectionCard'

export default function SelectionPicker({ value, onChange }: { value?: string; onChange?: (v?: string) => void }) {
  const [loading, setLoading] = useState(false)
  const [options, setOptions] = useState<{ value: string; label: string }[]>([])
  const [detail, setDetail] = useState<any>(null)

  const fetchList = async () => {
    setLoading(true)
    try {
      const { data } = await http.get('/catalog/selections')
      const opts = (data || []).map((r: any) => ({ value: r.slug, label: r.slug }))
      setOptions(opts)
    } finally { setLoading(false) }
  }

  const fetchDetail = async (slug?: string) => {
    if (!slug) { setDetail(null); return }
    try {
      const { data } = await http.get(`/catalog/selections/${slug}`)
      setDetail(data)
    } catch { setDetail(null) }
  }

  useEffect(() => { fetchList() }, [])
  useEffect(() => { fetchDetail(value) }, [value])

  return (
    <div>
      <Select
        style={{ width: 360 }}
        placeholder="选择已有 Selection"
        options={options}
        value={value}
        loading={loading}
        onChange={(v) => onChange?.(v)}
        showSearch
        filterOption={(input, option) => (option?.label as string).toLowerCase().includes(input.toLowerCase())}
      />
      {loading ? <Spin size="small" style={{ marginLeft: 8 }} /> : null}
      <SelectionCard selection={detail} />
    </div>
  )
}