import { Button, Form, Input, message } from 'antd'
import { http } from '../../api/client'
import { useNavigate } from 'react-router-dom'

export default function StrategyNewPage() {
  const navigate = useNavigate()
  const onSave = async (values: any) => {
    try {
      const { data } = await http.post('/strategies', { name: values.name, normalization: null })
      message.success('已创建')
      navigate(`/strategies/${data.id}`)
    } catch {}
  }
  return (
    <Form layout="vertical" onFinish={onSave} style={{ maxWidth: 480 }}>
      <Form.Item label="名称" name="name" rules={[{ required: true }]}><Input /></Form.Item>
      <Form.Item><Button type="primary" htmlType="submit">保存</Button></Form.Item>
    </Form>
  )
}
