import React, { useState, useEffect } from 'react';
import {
  PlusIcon,
  PlayIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { factorApi, strategyApi, watchlistApi, Factor, StrategyResult } from '../services/api';

const QuantitativeSelection: React.FC = () => {
  const [factors, setFactors] = useState<Factor[]>([]);
  const [results, setResults] = useState<StrategyResult[]>([]);
  const [isFactorModalVisible, setIsFactorModalVisible] = useState(false);
  const [isStrategyModalVisible, setIsStrategyModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [factorsLoading, setFactorsLoading] = useState(true);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null);

  // Form states
  const [factorForm, setFactorForm] = useState({
    name: '',
    description: '',
    category: '',
    code: ''
  });

  const [strategyForm, setStrategyForm] = useState({
    factors: [] as string[],
    maxResults: 50
  });

  // 消息提示函数
  const showMessage = (type: 'success' | 'error' | 'info', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  // 加载因子数据
  const loadFactors = async () => {
    try {
      setFactorsLoading(true);
      const data = await factorApi.getFactors();
      setFactors(data);
    } catch (error) {
      console.error('获取因子列表失败:', error);
      showMessage('error', '获取因子列表失败，请检查网络连接');
      // 如果API调用失败，使用模拟数据作为备用
      setFactors([
        {
          id: '1',
          name: 'PE倍数因子',
          description: '基于市盈率的估值因子',
          category: '估值',
          code: `def calculate(data):
    pe_ratio = data['market_cap'] / data['net_income']
    return 1 / pe_ratio  # PE倍数越低，得分越高`
        },
        {
          id: '2',
          name: '动量因子',
          description: '基于价格动量的技术因子',
          category: '技术',
          code: `def calculate(data):
    returns_20d = data['close'].pct_change(20)
    return returns_20d.fillna(0)`
        }
      ]);
    } finally {
      setFactorsLoading(false);
    }
  };

  useEffect(() => {
    loadFactors();
  }, []);

  const handleCreateFactor = () => {
    setIsFactorModalVisible(true);
    setFactorForm({
      name: '',
      description: '',
      category: '',
      code: ''
    });
  };

  const handleFactorSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 简单的表单验证
    if (!factorForm.name || !factorForm.description || !factorForm.category || !factorForm.code) {
      showMessage('error', '请填写所有必填项');
      return;
    }

    try {
      setLoading(true);
      const newFactor = await factorApi.createFactor(factorForm);
      setFactors([...factors, newFactor]);
      setIsFactorModalVisible(false);
      setFactorForm({ name: '', description: '', category: '', code: '' });
      showMessage('success', '因子创建成功');
    } catch (error) {
      console.error('创建因子失败:', error);
      showMessage('error', '因子创建失败，请检查网络连接');
    } finally {
      setLoading(false);
    }
  };

  const handleRunStrategy = () => {
    setIsStrategyModalVisible(true);
    setStrategyForm({
      factors: [],
      maxResults: 50
    });
  };

  const handleStrategySubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (strategyForm.factors.length === 0) {
      showMessage('error', '请选择至少一个因子');
      return;
    }

    try {
      setLoading(true);
      const results = await strategyApi.executeStrategy({
        factors: strategyForm.factors,
        maxResults: strategyForm.maxResults
      });
      setResults(results);
      setIsStrategyModalVisible(false);
      setStrategyForm({ factors: [], maxResults: 50 });
      showMessage('success', `策略执行成功，共选出 ${results.length} 只股票`);
    } catch (error) {
      console.error('策略执行失败:', error);
      showMessage('error', '策略执行失败，请检查网络连接');
      // 如果API调用失败，使用模拟数据作为备用
      setResults([
        {
          symbol: '000001.SZ',
          name: '平安银行',
          score: 0.85,
          rank: 1,
          price: 15.23,
          changePercent: 3.04
        },
        {
          symbol: '600036.SH',
          name: '招商银行',
          score: 0.82,
          rank: 2,
          price: 42.15,
          changePercent: 3.01
        },
        {
          symbol: '000002.SZ',
          name: '万科A',
          score: 0.78,
          rank: 3,
          price: 18.67,
          changePercent: -1.22
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFactor = async (id: string) => {
    try {
      await factorApi.deleteFactor(id);
      setFactors(factors.filter(f => f.id !== id));
      showMessage('success', '因子删除成功');
    } catch (error) {
      console.error('删除因子失败:', error);
      showMessage('error', '删除因子失败，请检查网络连接');
    }
  };

  const handleAddToWatchlist = async (stock: StrategyResult) => {
    try {
      await watchlistApi.addToWatchlist(stock.symbol, stock.name);
      showMessage('success', `${stock.name} 已添加到自选股`);
    } catch (error) {
      console.error('添加自选股失败:', error);
      showMessage('error', '添加自选股失败，请检查网络连接');
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case '估值': return 'badge-primary';
      case '技术': return 'badge-secondary';
      case '基本面': return 'badge-accent';
      case '情绪': return 'badge-info';
      default: return 'badge-ghost';
    }
  };

  const getRankColor = (rank: number) => {
    if (rank <= 3) return 'badge-warning';
    return 'badge-ghost';
  };

  return (
    <div className="space-y-6">
      {/* 消息提示 */}
      {message && (
        <div className={`alert ${
          message.type === 'success' ? 'alert-success' :
          message.type === 'error' ? 'alert-error' : 'alert-info'
        }`}>
          <span>{message.text}</span>
        </div>
      )}

      {/* 因子管理 */}
      <div className="card bg-base-100 shadow-xl">
        <div className="card-body">
          <div className="flex justify-between items-center mb-6">
            <h2 className="card-title text-xl">因子管理</h2>
            <button
              className="btn btn-primary"
              onClick={handleCreateFactor}
            >
              <PlusIcon className="w-4 h-4" />
              创建因子
            </button>
          </div>

          {factorsLoading ? (
            <div className="flex justify-center py-8">
              <div className="loading loading-spinner loading-lg"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>因子名称</th>
                    <th>描述</th>
                    <th>分类</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {factors.map((factor) => (
                    <tr key={factor.id}>
                      <td className="font-medium">{factor.name}</td>
                      <td>{factor.description}</td>
                      <td>
                        <div className={`badge ${getCategoryColor(factor.category)}`}>
                          {factor.category}
                        </div>
                      </td>
                      <td>
                        <div className="flex gap-2">
                          <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => showMessage('info', '编辑功能待实现')}
                          >
                            <PencilIcon className="w-4 h-4" />
                            编辑
                          </button>
                          <button
                            className="btn btn-ghost btn-sm text-error"
                            onClick={() => handleDeleteFactor(factor.id)}
                          >
                            <TrashIcon className="w-4 h-4" />
                            删除
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* 策略执行 */}
      <div className="card bg-base-100 shadow-xl">
        <div className="card-body">
          <div className="flex justify-between items-center mb-6">
            <h2 className="card-title text-xl">策略执行</h2>
            <button
              className="btn btn-primary"
              onClick={handleRunStrategy}
            >
              <PlayIcon className="w-4 h-4" />
              执行策略
            </button>
          </div>

          {results.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>排名</th>
                    <th>代码</th>
                    <th>名称</th>
                    <th>综合得分</th>
                    <th>现价</th>
                    <th>涨跌幅</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((stock) => (
                    <tr key={stock.symbol}>
                      <td>
                        <div className={`badge ${getRankColor(stock.rank)}`}>
                          {stock.rank}
                        </div>
                      </td>
                      <td className="font-mono text-sm">{stock.symbol}</td>
                      <td className="font-medium">{stock.name}</td>
                      <td>{stock.score.toFixed(3)}</td>
                      <td>¥{stock.price?.toFixed(2)}</td>
                      <td>
                        <div className={`badge badge-sm ${
                          stock.changePercent >= 0 ? 'badge-success' : 'badge-error'
                        }`}>
                          {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                        </div>
                      </td>
                      <td>
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={() => handleAddToWatchlist(stock)}
                        >
                          加自选
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-base-content/60">
              暂无选股结果，请先执行策略
            </div>
          )}
        </div>
      </div>

      {/* 创建因子弹窗 */}
      {isFactorModalVisible && (
        <div className="modal modal-open">
          <div className="modal-box w-11/12 max-w-4xl">
            <h3 className="font-bold text-lg mb-4">创建因子</h3>

            <form onSubmit={handleFactorSubmit} className="space-y-4">
              <div className="form-control">
                <label className="label">
                  <span className="label-text">因子名称 *</span>
                </label>
                <input
                  type="text"
                  className="input input-bordered"
                  placeholder="请输入因子名称"
                  value={factorForm.name}
                  onChange={(e) => setFactorForm({...factorForm, name: e.target.value})}
                  required
                />
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">因子描述 *</span>
                </label>
                <textarea
                  className="textarea textarea-bordered h-20"
                  placeholder="请输入因子描述"
                  value={factorForm.description}
                  onChange={(e) => setFactorForm({...factorForm, description: e.target.value})}
                  required
                />
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">因子分类 *</span>
                </label>
                <select
                  className="select select-bordered"
                  value={factorForm.category}
                  onChange={(e) => setFactorForm({...factorForm, category: e.target.value})}
                  required
                >
                  <option value="">请选择因子分类</option>
                  <option value="估值">估值</option>
                  <option value="技术">技术</option>
                  <option value="基本面">基本面</option>
                  <option value="情绪">情绪</option>
                </select>
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">因子代码 *</span>
                </label>
                <textarea
                  className="textarea textarea-bordered h-40 font-mono text-sm"
                  placeholder={`请输入Python代码，例如：
def calculate(data):
    # data包含股票的历史数据
    # 返回因子值
    return data['close'].pct_change(20)`}
                  value={factorForm.code}
                  onChange={(e) => setFactorForm({...factorForm, code: e.target.value})}
                  required
                />
              </div>

              <div className="modal-action">
                <button
                  type="button"
                  className="btn"
                  onClick={() => setIsFactorModalVisible(false)}
                  disabled={loading}
                >
                  取消
                </button>
                <button
                  type="submit"
                  className={`btn btn-primary ${loading ? 'loading' : ''}`}
                  disabled={loading}
                >
                  创建因子
                </button>
              </div>
            </form>
          </div>
          <div className="modal-backdrop" onClick={() => !loading && setIsFactorModalVisible(false)}></div>
        </div>
      )}

      {/* 策略配置弹窗 */}
      {isStrategyModalVisible && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg mb-4">策略配置</h3>

            <form onSubmit={handleStrategySubmit} className="space-y-4">
              <div className="form-control">
                <label className="label">
                  <span className="label-text">选择因子 *</span>
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {factors.map((factor) => (
                    <label key={factor.id} className="cursor-pointer label justify-start gap-3">
                      <input
                        type="checkbox"
                        className="checkbox checkbox-primary"
                        checked={strategyForm.factors.includes(factor.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setStrategyForm({
                              ...strategyForm,
                              factors: [...strategyForm.factors, factor.id]
                            });
                          } else {
                            setStrategyForm({
                              ...strategyForm,
                              factors: strategyForm.factors.filter(id => id !== factor.id)
                            });
                          }
                        }}
                      />
                      <span className="label-text">{factor.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">结果数量</span>
                </label>
                <select
                  className="select select-bordered"
                  value={strategyForm.maxResults}
                  onChange={(e) => setStrategyForm({...strategyForm, maxResults: parseInt(e.target.value)})}
                >
                  <option value={20}>前20名</option>
                  <option value={50}>前50名</option>
                  <option value={100}>前100名</option>
                </select>
              </div>

              <div className="modal-action">
                <button
                  type="button"
                  className="btn"
                  onClick={() => setIsStrategyModalVisible(false)}
                  disabled={loading}
                >
                  取消
                </button>
                <button
                  type="submit"
                  className={`btn btn-primary ${loading ? 'loading' : ''}`}
                  disabled={loading}
                >
                  执行策略
                </button>
              </div>
            </form>
          </div>
          <div className="modal-backdrop" onClick={() => !loading && setIsStrategyModalVisible(false)}></div>
        </div>
      )}
    </div>
  );
};

export default QuantitativeSelection;