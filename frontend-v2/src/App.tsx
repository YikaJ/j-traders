import { Layout, Menu, Button, message, Breadcrumb } from 'antd'
import { useMemo, useState } from 'react'
import { Link, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import axios from 'axios'
import FactorListPage from './pages/factors/List'
import FactorDetailPage from './pages/factors/Detail'
import FactorNewPage from './pages/factors/New'
import StrategyListPage from './pages/strategies/List'
import StrategyDetailPage from './pages/strategies/Detail'
import StrategyNewPage from './pages/strategies/New'
// Removed selections module

const { Header, Sider, Content } = Layout

const API_BASE = (import.meta as any).env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const http = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
})

function useBreadcrumbs() {
  const location = useLocation()
  const crumbs = useMemo(() => {
    const parts = location.pathname.split('/').filter(Boolean)
    const nodes = [] as { path: string; label: string }[]
    let acc = ''
    for (const p of parts) {
      acc += `/${p}`
      nodes.push({ path: acc, label: p })
    }
    return nodes
  }, [location.pathname])
  return crumbs
}

function Dashboard() {
  return <div>Dashboard（占位）</div>
}

export default function App() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const crumbs = useBreadcrumbs()

  const selectedKeys = useMemo(() => {
    if (location.pathname.startsWith('/factors')) return ['/factors/list']
    if (location.pathname.startsWith('/strategies')) return ['/strategies/list']
    
    return ['/dashboard']
  }, [location.pathname])

  const [tushareInfo, setTushareInfo] = useState<{ configured?: boolean; expire_date?: string; expire_score?: number } | null>(null)

  const onHealthCheck = async () => {
    try {
      const { data } = await http.get('/health')
      const info = (data?.tushare?.detail) || {}
      setTushareInfo({
        configured: !!info.configured,
        expire_date: info.expire_date || undefined,
        expire_score: typeof info.expire_score === 'number' ? info.expire_score : undefined,
      })
      if (info.configured) {
        const msg = `后端健康；TuShare 已配置，最近到期：${info.expire_date || '-'}，到期积分：${info.expire_score ?? '-'}。`
        message.success(msg)
      } else {
        message.warning('后端健康；但未检测到 TuShare Token')
      }
    } catch (e: any) {
      message.error(`后端不可用：${e?.response?.status || ''}`)
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div style={{ height: 48, margin: 16, color: '#fff' }}>J-Traders</div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={selectedKeys}
          onClick={({ key }) => navigate(String(key))}
          items={[
            { key: '/dashboard', label: 'Dashboard' },
            { key: '/factors/list', label: '因子库' },
            
            { key: '/strategies/list', label: '策略库' },
          ]}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Breadcrumb items={[{ title: <Link to="/">Home</Link> }, ...crumbs.map(c => ({ title: <Link to={c.path}>{c.label}</Link> }))]} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {tushareInfo?.configured ? (
              <span style={{ color: '#666' }}>
                TuShare 最晚到期：<b>{tushareInfo.expire_date || '-'}</b>，到期积分：<b>{tushareInfo.expire_score ?? '-'}</b>
              </span>
            ) : null}
            <Button onClick={onHealthCheck}>健康检查</Button>
          </div>
        </Header>
        <Content style={{ margin: 16, background: '#fff', padding: 16 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/factors/list" element={<FactorListPage />} />
            <Route path="/factors/new" element={<FactorNewPage />} />
            <Route path="/factors/:id" element={<FactorDetailPage />} />
            
            <Route path="/strategies/list" element={<StrategyListPage />} />
            <Route path="/strategies/new" element={<StrategyNewPage />} />
            <Route path="/strategies/:id" element={<StrategyDetailPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

