import { useEffect, useMemo, useState } from 'react'
import { Button, Card, Form, Input, Select, Space, Steps, Tag, Typography, message, Table } from 'antd'
import type { SelectProps } from 'antd'
import Editor from '@monaco-editor/react'
import { http } from '../../api/client'
import { useNavigate } from 'react-router-dom'

// Ephemeral selection builder types
type EndpointMeta = {
  name: string
  axis?: string
  description?: string
  fields?: { name: string; desc?: string }[]
  params?: { name: string; type: string; required?: boolean; desc?: string }[]
}

type SourceState = {
  endpoint?: string
  fields: string[]
  params: Record<string, { type: 'arg' | 'fixed'; value?: any }>
}

type EphemeralSelection = {
  slug?: string
  title?: string
  description?: string
  join_keys: string[]
  sources: SourceState[]
  constraints?: { winsor?: [number, number]; zscore_axis?: string }
  params_schema?: Record<string, { type: 'string' | 'number' | 'boolean' | 'date'; required?: boolean; default?: any }>
}

function useEndpoints() {
  const [loading, setLoading] = useState(false)
  const [list, setList] = useState<EndpointMeta[]>([])

  const fetchList = async () => {
    setLoading(true)
    try {
      const { data } = await http.get('/catalog/endpoints')
      setList(data || [])
    } finally { setLoading(false) }
  }

  const fetchOne = async (name: string): Promise<EndpointMeta | undefined> => {
    try {
      const { data } = await http.get(`/catalog/endpoints/${name}`)
      return data
    } catch { return undefined }
  }

  return { loading, list, fetchList, fetchOne }
}

function SourceEditor({ idx, value, onChange, endpointMeta }: { idx: number; value: SourceState; onChange: (v: SourceState) => void; endpointMeta?: EndpointMeta }) {
  const [local, setLocal] = useState<SourceState>(value)
  useEffect(() => setLocal(value), [value])
  const fieldsOptions: SelectProps['options'] = (endpointMeta?.fields || []).map(f => ({ value: f.name, label: `${f.name}${f?.desc ? ` (${f.desc})` : ''}` }))
  const allParams = (endpointMeta?.params || [])
  const requiredParams = allParams.filter(p => p.required).map(p => ({ name: p.name, desc: p.desc }))
  const optionalParams = allParams.filter(p => !p.required).map(p => ({ name: p.name, desc: p.desc }))
  const ensureParam = (k: string) => setLocal(prev => ({ ...prev, params: { ...prev.params, [k]: prev.params?.[k] || { type: 'arg' } } }))
  // auto include required params
  useEffect(() => {
    if (!endpointMeta) return
    setLocal(prev => {
      const next = { ...prev, params: { ...prev.params } }
      let changed = false
      requiredParams.forEach(r => { if (!next.params[r.name]) { next.params[r.name] = { type: 'arg' }; changed = true } })
      if (changed) onChange(next)
      return next
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [endpointMeta?.name])

  const selectedOptional = Object.keys(local.params || {}).filter(k => !requiredParams.find(r => r.name === k))
  const addableOptions = optionalParams.filter(op => !selectedOptional.includes(op.name)).map(op => ({ value: op.name, label: `${op.name}${op.desc ? ` (${op.desc})` : ''}` }))

  return (
    <Card size="small" title={`数据源 #${idx + 1}`}
      extra={<Button size="small" onClick={() => onChange({ ...local, fields: [], params: {} })}>清空</Button>}
      style={{ marginBottom: 12 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        {endpointMeta ? (
          <div>
            <Typography.Text strong>{endpointMeta.name}</Typography.Text>
            {endpointMeta?.description ? (
              <Typography.Text type="secondary"> （{endpointMeta.description}）</Typography.Text>
            ) : null}
            <div style={{ marginTop: 4 }}>
              <Typography.Text type="secondary">
                更新时间：{(endpointMeta as any).update_time || '-'}，时间轴：{endpointMeta.axis || '-'}
              </Typography.Text>
            </div>
            {(endpointMeta as any)?.notes ? (
              <Typography.Paragraph type="secondary" style={{ marginTop: 4, marginBottom: 0 }}>
                说明：{(endpointMeta as any).notes}
              </Typography.Paragraph>
            ) : null}
          </div>
        ) : null}
        <div>
          <Typography.Text>字段</Typography.Text>
          <Select
            mode="multiple"
            style={{ width: '100%', marginTop: 6 }}
            placeholder="选择需要的字段"
            options={fieldsOptions}
            value={local.fields}
            onChange={(v) => { const next = { ...local, fields: v as string[] }; setLocal(next); onChange(next) }}
            showSearch
          />
        </div>
        <div>
          <Typography.Text>参数（仅保留必填，可按需添加可选项）</Typography.Text>
          <div style={{ marginTop: 6 }}>
            {/* required params (non-removable) */}
            {requiredParams.map(({ name: k, desc }) => (
              <Tag key={`req-${k}`} color="blue" style={{ marginBottom: 6 }}>{`${k}${desc ? ` (${desc})` : ''}`}</Tag>
            ))}
            {/* selected optional params (removable) */}
            {selectedOptional.map(k => {
              const meta = optionalParams.find(op => op.name === k)
              const label = `${k}${meta?.desc ? ` (${meta.desc})` : ''}`
              return (
                <Tag key={`opt-${k}`} closable onClose={(e) => { e.preventDefault(); setLocal(prev => { const next = { ...prev, params: { ...prev.params } }; delete next.params[k]; onChange(next); return next }) }} style={{ marginBottom: 6 }}>{label}</Tag>
              )
            })}
            {/* add optional param */}
            <div style={{ marginTop: 6 }}>
              <Select
                placeholder="添加可选参数"
                style={{ width: 260 }}
                options={addableOptions}
                value={undefined as any}
                onChange={(name) => { ensureParam(name as string); onChange({ ...local, params: { ...local.params, [name as string]: { type: 'arg' } } }) }}
                showSearch
              />
            </div>
          </div>
        </div>
      </Space>
    </Card>
  )
}

export default function FactorNewPage() {
  const [step, setStep] = useState(0)
  const navigate = useNavigate()

  // Data selection state
  const { list: endpoints, fetchList, fetchOne } = useEndpoints()
  const [endpointMetaMap, setEndpointMetaMap] = useState<Record<string, EndpointMeta>>({})
  const [sel, setSel] = useState<EphemeralSelection>({ join_keys: ['ts_code', 'trade_date'], sources: [] })

  // Codegen + validation + preview state
  const [spec, setSpec] = useState<string>('统计过去一周 pe_ttm 的逆序并输出为 factor 列')
  const [code, setCode] = useState<string>('')
  const [genLoading, setGenLoading] = useState(false)
  const [validResult, setValidResult] = useState<{ ok: boolean; fields_used: string[]; errors: string[] } | null>(null)
  const [previewing, setPreviewing] = useState(false)
  const [previewText, setPreviewText] = useState('')
  const [tsCodesInput, setTsCodesInput] = useState('000001.SZ,600000.SH')
  const [startDate, setStartDate] = useState('20210101')
  const [endDate, setEndDate] = useState('20210108')
  const [topN, setTopN] = useState(5)
  // 动态参数输入：根据 sources 中声明为 arg 的参数，联动生成输入框
  const argParamNames = useMemo(() => {
    const names = new Set<string>()
    for (const s of sel.sources || []) {
      for (const [k, v] of Object.entries(s.params || {})) {
        if ((v as any)?.type === 'arg') names.add(k)
      }
    }
    return Array.from(names)
  }, [sel])
  const [argInputs, setArgInputs] = useState<Record<string, string>>({})
  useEffect(() => {
    // 清理已移除的 key
    setArgInputs(prev => {
      const next: Record<string, string> = {}
      argParamNames.forEach(k => { next[k] = prev[k] || '' })
      return next
    })
  }, [argParamNames])
  const [sampleLoading, setSampleLoading] = useState(false)
  const [sampleData, setSampleData] = useState<Record<string, any[]>>({})
  const [sampleNotes, setSampleNotes] = useState<string>('')

  useEffect(() => { fetchList() }, [])

  const endpointOptions = useMemo(
    () => endpoints.map((e: any) => ({ value: e.name, label: `${e.name}${e?.description ? ` (${e.description})` : ''}` })),
    [endpoints]
  )

  // Join-key candidates based on selected endpoints' axis and timestamp-like fields
  const candidateJoinKeys = useMemo(() => {
    const keys = new Set<string>(['ts_code'])
    for (const s of sel.sources || []) {
      const meta = s.endpoint ? endpointMetaMap[s.endpoint] : undefined
      const axis = meta?.axis
      if (axis) keys.add(axis)
      const flds: any[] = (meta?.fields as any[]) || []
      for (const f of flds) {
        const name = (f as any)?.name
        const role = (f as any)?.role
        if (!name) continue
        if (role === 'timestamp' || name.endsWith('_date')) keys.add(name)
      }
    }
    return Array.from(keys)
  }, [sel.sources, endpointMetaMap])
  const joinKeyOptions = useMemo(() => candidateJoinKeys.map(k => ({ value: k, label: k })), [candidateJoinKeys])

  // Auto align join_keys to axis when user still using default ['ts_code','trade_date']
  useEffect(() => {
    const axes = Array.from(new Set((sel.sources || []).map(s => s.endpoint ? endpointMetaMap[s.endpoint]?.axis : null).filter(Boolean))) as string[]
    if (axes.length === 0) return
    const preferred = axes.includes('end_date') ? 'end_date' : (axes.includes('trade_date') ? 'trade_date' : axes[0])
    const isDefault = JSON.stringify(sel.join_keys) === JSON.stringify(['ts_code','trade_date'])
    if (isDefault && preferred && preferred !== sel.join_keys[1]) {
      setSel(prev => ({ ...prev, join_keys: ['ts_code', preferred] }))
    }
  }, [sel.sources, endpointMetaMap])

  const addSource = async () => {
    const endpoint = endpoints[0]?.name
    if (!endpoint) { message.warning('无端点可选'); return }
    const meta = endpointMetaMap[endpoint] || await fetchOne(endpoint)
    if (meta) setEndpointMetaMap({ ...endpointMetaMap, [endpoint]: meta })
    const next: SourceState = { endpoint, fields: [], params: {} }
    setSel(prev => ({ ...prev, sources: [...prev.sources, next] }))
  }

  const onEndpointChange = async (i: number, endpoint?: string) => {
    const sources = [...sel.sources]
    sources[i] = { endpoint, fields: [], params: {} }
    setSel({ ...sel, sources })
    if (endpoint && !endpointMetaMap[endpoint]) {
      const meta = await fetchOne(endpoint)
      if (meta) setEndpointMetaMap(prev => ({ ...prev, [endpoint]: meta }))
    }
  }

  const onSourceChange = (i: number, v: SourceState) => {
    const sources = [...sel.sources]
    sources[i] = v
    setSel({ ...sel, sources })
  }

  const activeSources = useMemo(() => (sel.sources || []).filter(s => !!s.endpoint && (s.fields || []).length > 0), [sel])

  const buildSelectionSpec = () => ({
    slug: sel.slug || 'temp',
    title: sel.title || 'temp',
    description: sel.description,
    join_keys: sel.join_keys,
    sources: activeSources.map(s => ({ endpoint: s.endpoint!, fields: s.fields, params: s.params })),
    constraints: sel.constraints,
    params_schema: sel.params_schema || {},
  })

  const allowedFields = useMemo(() => {
    const items: any[] = sel.sources || []
    return Array.from(new Set(items.flatMap((it: any) => it.fields || [])))
  }, [sel])

  const onGen = async () => {
    try {
      setGenLoading(true)
      const selection = buildSelectionSpec()
      const { data } = await http.post('/factors/codegen', { selection, user_factor_spec: spec })
      setCode(data.code_text || '')
      message.success('已生成代码')
    } catch (e: any) {
      message.error('生成失败：' + (e?.message || ''))
    } finally { setGenLoading(false) }
  }

  const onValidate = async () => {
    try {
      const selection = buildSelectionSpec()
      const { data } = await http.post('/factors/validate', { selection, code_text: code })
      setValidResult(data as any)
      if ((data as any).ok) message.success('校验通过')
      else message.error('校验失败')
    } catch {}
  }

  const onTestPreview = async () => {
    try {
      setPreviewing(true)
      const selection = buildSelectionSpec()
      const ts_codes = tsCodesInput.split(',').map(s => s.trim()).filter(Boolean)
      const { data } = await http.post('/factors/test', {
        selection,
        code_text: code,
        params: {},
        ts_codes,
        start_date: startDate,
        end_date: endDate,
        normalization: null,
        top_n: topN,
      })
      setPreviewText(JSON.stringify({ sample_rows: data.sample_rows, diagnosis: data.diagnosis }, null, 2))
    } catch (e: any) {
      message.error('预览失败：' + (e?.message || ''))
    } finally { setPreviewing(false) }
  }

  const onSample = async () => {
    try {
      setSampleLoading(true)
      const selection = buildSelectionSpec()
      const { data } = await http.post('/factors/sample', {
        selection,
        top_n: topN,
        request_args: argInputs,
      })
      setSampleData(data.data || {})
      setSampleNotes(data.notes || '')
    } catch (e: any) {
      message.error('预调用失败：' + (e?.message || ''))
    } finally { setSampleLoading(false) }
  }

  const navigateToDetail = (id: number) => navigate(`/factors/${id}`)

  const onSave = async (values: any) => {
    try {
      const selection = buildSelectionSpec()
      const { data } = await http.post('/factors', {
        name: values.name,
        desc: values.desc,
        tags: (values.tags || '').split(',').map((s: string) => s.trim()).filter(Boolean),
        code_text: code,
        fields_used: validResult?.fields_used || allowedFields,
        normalization: null,
        selection,
      })
      message.success('已创建')
      navigateToDetail(data.id)
    } catch {}
  }

  return (
    <div>
      <Steps
        current={step}
        items={[
          { title: '数据选择与生成代码' },
          { title: '校验与预览' },
          { title: '保存' },
        ]}
        style={{ marginBottom: 16 }}
      />

      {step === 0 && (
        <Card size="small" title="数据选择（源/字段/参数）与需求说明">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Card size="small" title="数据源（sources）">
              <Space direction="vertical" style={{ width: '100%' }}>
                {sel.sources.map((s, i) => (
                  <div key={i}>
                    <Space style={{ marginBottom: 8 }}>
                      <Select style={{ width: 360 }} value={s.endpoint} options={endpointOptions} onChange={(v) => onEndpointChange(i, v)} />
                      <Button onClick={() => { const next = [...sel.sources]; next.splice(i,1); setSel({ ...sel, sources: next }) }} danger>删除</Button>
                    </Space>
                    <SourceEditor idx={i} value={s} onChange={(v)=>onSourceChange(i, v)} endpointMeta={s.endpoint ? endpointMetaMap[s.endpoint] : undefined} />
                  </div>
                ))}
                <Button type="dashed" onClick={addSource}>+ 添加数据源</Button>
              </Space>
            </Card>

            <Card size="small" title="对齐键（join_keys）">
              <Typography.Paragraph type="secondary">建议使用 ts_code 与时间列（如 end_date / trade_date）。</Typography.Paragraph>
              <Typography.Paragraph type="secondary" style={{ marginTop: -8 }}>
                用途：
                <br />- 在合并多个数据源时，作为主键进行对齐（inner join）。
                <br />- 生成的 compute_factor 必须保留这些列作为输出索引。
                <br />- 标准化/分组处理默认按最后一个键分组。
              </Typography.Paragraph>
              <Select
                mode="tags"
                style={{ width: 480 }}
                value={sel.join_keys}
                onChange={(v) => setSel({ ...sel, join_keys: v as string[] })}
                tokenSeparators={[',', ' ']}
                placeholder="输入并回车添加"
                options={joinKeyOptions}
              />
            </Card>

            <Card size="small" title="数据预调用">
              <Space wrap style={{ marginBottom: 8 }}>
                <Input addonBefore="top_n" style={{ width: 160 }} value={topN} onChange={e=>setTopN(parseInt(e.target.value||'5'))} />
                {argParamNames.map(name => (
                  <Input key={name} addonBefore={name} style={{ width: 200 }} value={argInputs[name]}
                    onChange={e=>setArgInputs(prev=>({ ...prev, [name]: e.target.value }))} />
                ))}
                <Button type="primary" onClick={onSample} loading={sampleLoading} disabled={activeSources.length===0 || sel.join_keys.length===0}>
                  预调用数据
                </Button>
              </Space>
              {sampleNotes ? <Typography.Paragraph type="secondary" style={{ marginTop: 0, marginBottom: 8 }}>备注：{sampleNotes}</Typography.Paragraph> : null}
              {Object.keys(sampleData || {}).length === 0 ? (
                <Typography.Text type="secondary">点击“预调用数据”以查看各数据源的样例结果</Typography.Text>
              ) : (
                <Space direction="vertical" style={{ width: '100%' }}>
                  {Object.entries(sampleData).map(([endpoint, rows]) => {
                    const dataSource = (rows as any[]) || []
                    const columns = dataSource.length > 0 ? Object.keys(dataSource[0]).map(k => ({ title: k, dataIndex: k, key: k })) : []
                    return (
                      <div key={endpoint}>
                        <Typography.Title level={5} style={{ marginTop: 8 }}>{endpoint}</Typography.Title>
                        <Table size="small" rowKey={(_, i) => String(i)} dataSource={dataSource} columns={columns as any} pagination={{ pageSize: 5 }} />
                      </div>
                    )
                  })}
                </Space>
              )}
            </Card>


            <Card size="small" title="需求说明与代码生成">
              <Space.Compact style={{ width: '100%', marginBottom: 8 }}>
                <Input value={spec} onChange={e=>setSpec(e.target.value)} placeholder="例如：统计过去一周 pe_ttm 的逆序并输出为 factor 列" />
                <Button type="primary" onClick={onGen} loading={genLoading} disabled={sel.sources.length===0 || sel.join_keys.length===0}>生成代码</Button>
              </Space.Compact>
              <Editor height="360px" defaultLanguage="python" value={code} onChange={(v)=>setCode(v||'')} options={{ minimap: { enabled: false } }} />
              <Space style={{ marginTop: 12 }}>
                <Button type="primary" onClick={()=>setStep(1)} disabled={!code}>下一步</Button>
              </Space>
            </Card>
          </Space>
        </Card>
      )}

      {step === 1 && (
        <Card size="small" title="校验与预览">
          <Space style={{ marginBottom: 8 }}>
            <Button onClick={onValidate}>校验</Button>
            {validResult?.ok ? <Typography.Text type="success">通过</Typography.Text> : validResult ? <Typography.Text type="danger">未通过</Typography.Text> : null}
          </Space>
          {validResult ? (
            <>
              <Typography.Text>代码解析到的字段：</Typography.Text>
              <div>{(validResult.fields_used||[]).map(f => <Typography.Text key={f} code style={{ marginRight: 6 }}>{f}</Typography.Text>)}</div>
              {(validResult.errors||[]).length>0 ? (
                <div style={{ marginTop: 8 }}>
                  <Typography.Text type="danger">错误：</Typography.Text>
                  <ul style={{ paddingLeft: 20 }}>
                    {validResult.errors.map((e, i) => <li key={i}><Typography.Text type="danger">{e}</Typography.Text></li>)}
                  </ul>
                </div>
              ) : null}
            </>
          ) : <Typography.Text type="secondary">点击“校验”以检测代码字段边界与安全约束。</Typography.Text>}

          <Card size="small" title="测试 / 预览样例输出" style={{ marginTop: 12 }}>
            <Space wrap>
              <Input addonBefore="ts_codes" style={{ width: 360 }} value={tsCodesInput} onChange={e=>setTsCodesInput(e.target.value)} />
              <Input addonBefore="start_date" style={{ width: 200 }} value={startDate} onChange={e=>setStartDate(e.target.value)} />
              <Input addonBefore="end_date" style={{ width: 200 }} value={endDate} onChange={e=>setEndDate(e.target.value)} />
              <Input addonBefore="top_n" style={{ width: 160 }} value={topN} onChange={e=>setTopN(parseInt(e.target.value||'5'))} />
              <Button type="primary" onClick={onTestPreview} loading={previewing} disabled={!code}>预览样例输出</Button>
            </Space>
            {previewText ? (
              <Editor height="260px" defaultLanguage="json" value={previewText} options={{ readOnly: true, minimap: { enabled: false } }} />
            ) : (
              <Typography.Paragraph type="secondary" style={{ marginTop: 8 }}>运行后显示样例输出与诊断</Typography.Paragraph>
            )}
          </Card>

          <Space style={{ marginTop: 12 }}>
            <Button onClick={()=>setStep(0)}>上一步</Button>
            <Button type="primary" onClick={()=>setStep(2)} disabled={!validResult?.ok}>下一步</Button>
          </Space>
        </Card>
      )}

      {step === 2 && (
        <Card size="small" title="保存">
          <Form layout="vertical" onFinish={onSave}>
            <Form.Item label="名称" name="name" rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item label="标签（逗号分隔）" name="tags"><Input /></Form.Item>
            <Form.Item label="描述" name="desc"><Input /></Form.Item>
            <Space>
              <Button onClick={()=>setStep(1)}>上一步</Button>
              <Button type="primary" htmlType="submit">保存</Button>
            </Space>
          </Form>
        </Card>
      )}
    </div>
  )
}
