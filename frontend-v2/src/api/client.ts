import axios from 'axios'
import { message } from 'antd'

const API_BASE = (import.meta as any).env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export const http = axios.create({ baseURL: API_BASE, timeout: 20000 })

http.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err?.response?.status
    const detail = err?.response?.data?.detail || err?.message
    message.error(`请求失败(${status || '-'})：${detail || '未知错误'}`)
    return Promise.reject(err)
  },
)