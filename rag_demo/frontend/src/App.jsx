import { useState } from 'react'
import axios from 'axios'
import './App.css'

const API_BASE_URL = 'http://localhost:8000/api'

function App() {
  const [activeTab, setActiveTab] = useState('upload')
  const [reportId, setReportId] = useState(null)
  const [claims, setClaims] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [topK, setTopK] = useState(6)
  const [maxClaims, setMaxClaims] = useState(30)

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    if (!file.name.endsWith('.pdf')) {
      setError('只支持PDF文件')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(`${API_BASE_URL}/upload_report`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setReportId(response.data.report_id)
      setClaims(response.data.claims)
      setError(null)
      alert(`✓ 成功上传! 提取了 ${response.data.claims.length} 个论点`)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '上传失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async () => {
    if (!reportId) {
      setError('请先上传报告')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(
        `${API_BASE_URL}/analyze`,
        {
          report_id: reportId,
          top_k: topK,
          max_claims: maxClaims,
        },
        {
          timeout: 1800000, // 30 minutes
        }
      )

      setAnalysis(response.data.report)
      setError(null)
      alert('✓ 分析完成!')
    } catch (err) {
      if (err.code === 'ECONNABORTED') {
        setError('分析超时，请稍后重试或减少分析的论点数')
      } else {
        setError(err.response?.data?.detail || err.message || '分析失败')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (format) => {
    if (!reportId) return

    try {
      const response = await axios.get(
        `${API_BASE_URL}/download_report/${reportId}?format=${format}`,
        {
          responseType: 'blob',
        }
      )

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `report_${reportId}.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '下载失败')
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>📊 空头报告反驳助手</h1>
      </header>

      <nav className="tabs">
        <button
          className={activeTab === 'upload' ? 'active' : ''}
          onClick={() => setActiveTab('upload')}
        >
          📤 上传报告
        </button>
        <button
          className={activeTab === 'analyze' ? 'active' : ''}
          onClick={() => setActiveTab('analyze')}
          disabled={!reportId}
        >
          🔍 分析
        </button>
        <button
          className={activeTab === 'download' ? 'active' : ''}
          onClick={() => setActiveTab('download')}
          disabled={!analysis}
        >
          📥 下载报告
        </button>
      </nav>

      <main className="main-content">
        {error && (
          <div className="error-message">
            ❌ {error}
          </div>
        )}

        {activeTab === 'upload' && (
          <div className="tab-content">
            <h2>上传空头报告</h2>
            <div className="upload-area">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                disabled={loading}
                id="file-input"
              />
              <label htmlFor="file-input" className="upload-label">
                {loading ? '处理中...' : '选择PDF文件'}
              </label>
              <p className="help-text">仅处理前3页内容</p>
            </div>

            {claims.length > 0 && (
              <div className="claims-list">
                <h3>提取的论点 ({claims.length})</h3>
                {claims.map((claim, index) => (
                  <div key={index} className="claim-item">
                    <strong>{claim.claim_id}:</strong> {claim.claim_text.substring(0, 100)}...
                    <div className="claim-meta">
                      类型: {claim.claim_type} | 页码: {claim.page_numbers.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'analyze' && (
          <div className="tab-content">
            <h2>分析论点</h2>
            {reportId && (
              <>
                <div className="config-section">
                  <label>
                    检索文档数量:
                    <input
                      type="number"
                      min="3"
                      max="20"
                      value={topK}
                      onChange={(e) => setTopK(parseInt(e.target.value))}
                    />
                  </label>
                  <label>
                    最大分析论点数:
                    <input
                      type="number"
                      min="5"
                      max="50"
                      value={maxClaims}
                      onChange={(e) => setMaxClaims(parseInt(e.target.value))}
                    />
                  </label>
                </div>
                <button
                  onClick={handleAnalyze}
                  disabled={loading}
                  className="primary-button"
                >
                  {loading ? '分析中...' : '🔍 开始分析'}
                </button>

                {analysis && (
                  <div className="analysis-results">
                    <h3>执行摘要</h3>
                    <div className="summary-stats">
                      <div className="stat">
                        <div className="stat-value">{analysis.summary.total_claims}</div>
                        <div className="stat-label">总论点</div>
                      </div>
                      <div className="stat">
                        <div className="stat-value">{analysis.summary.fully_addressed}</div>
                        <div className="stat-label">完全解决</div>
                      </div>
                      <div className="stat">
                        <div className="stat-value">{analysis.summary.partially_addressed}</div>
                        <div className="stat-label">部分解决</div>
                      </div>
                      <div className="stat">
                        <div className="stat-value">{analysis.summary.not_addressed}</div>
                        <div className="stat-label">未解决</div>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'download' && (
          <div className="tab-content">
            <h2>下载报告</h2>
            {analysis && (
              <>
                <button
                  onClick={() => handleDownload('md')}
                  className="primary-button"
                >
                  📄 下载Markdown报告
                </button>
                <button
                  onClick={() => handleDownload('json')}
                  className="primary-button"
                >
                  📋 下载JSON报告
                </button>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
