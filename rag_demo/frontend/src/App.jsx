import React, { useState, useEffect } from 'react'
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
  const [vectorDbStatus, setVectorDbStatus] = useState(null)
  const [indexing, setIndexing] = useState(false)

  // Check vector DB status on mount
  useEffect(() => {
    checkVectorDb()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const checkVectorDb = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL.replace('/api', '')}/health`)
      setVectorDbStatus({
        exists: response.data.chroma_db_exists,
        collectionExists: response.data.collection_exists || false,
        count: response.data.collection_count || 0
      })
      
      // If collection doesn't exist or is empty, prompt to index
      if (!response.data.collection_exists || response.data.collection_count === 0) {
        const shouldIndex = window.confirm(
          '向量数据库未找到或为空。\n\n是否现在索引 company/EDU/company_data.pdf？\n\n这将需要几分钟时间。'
        )
        if (shouldIndex) {
          await indexDocuments()
        }
      }
    } catch (err) {
      console.error('Failed to check vector DB:', err)
    }
  }

  const indexDocuments = async () => {
    setIndexing(true)
    setError(null)
    try {
      const response = await axios.post(`${API_BASE_URL.replace('/api', '')}/api/check_and_index`)
      if (response.data.indexed) {
        setVectorDbStatus({
          exists: true,
          collectionExists: true,
          count: response.data.count
        })
        alert(`✓ ${response.data.message}`)
      } else {
        setError(response.data.message || '索引失败')
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '索引失败')
    } finally {
      setIndexing(false)
    }
  }

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
        {/* Vector DB Status */}
        {vectorDbStatus && (
          <div className={`status-message ${vectorDbStatus.collectionExists && vectorDbStatus.count > 0 ? 'success' : 'warning'}`}>
            {vectorDbStatus.collectionExists && vectorDbStatus.count > 0 ? (
              <>✅ 向量数据库已就绪 ({vectorDbStatus.count} 个文档块)</>
            ) : (
              <>
                ⚠️ 向量数据库未就绪
                {!indexing && (
                  <button onClick={indexDocuments} className="index-button" style={{ marginLeft: '1rem' }}>
                    索引文档
                  </button>
                )}
              </>
            )}
            {indexing && <span style={{ marginLeft: '1rem' }}>正在索引中...</span>}
          </div>
        )}

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

                    <h3 style={{ marginTop: '2rem' }}>详细分析</h3>
                    <div className="claims-analysis">
                      {analysis.claim_analyses.map((claimAnalysis, index) => {
                        const claim = claims.find(c => c.claim_id === claimAnalysis.claim_id) || {}
                        const coverageIcon = {
                          'fully_addressed': '✅',
                          'partially_addressed': '⚠️',
                          'not_addressed': '❌'
                        }[claimAnalysis.coverage] || '❓'
                        
                        return (
                          <div key={index} className="claim-analysis-card">
                            <div className="claim-analysis-header">
                              <span className="coverage-icon">{coverageIcon}</span>
                              <div className="claim-analysis-title">
                                <strong>{claimAnalysis.claim_id}:</strong> {claim.claim_text || 'Unknown'}
                              </div>
                              <div className="claim-analysis-meta">
                                <span className={`coverage-badge coverage-${claimAnalysis.coverage}`}>
                                  {claimAnalysis.coverage === 'fully_addressed' ? '完全解决' :
                                   claimAnalysis.coverage === 'partially_addressed' ? '部分解决' : '未解决'}
                                </span>
                                <span className="confidence-badge">
                                  置信度: {claimAnalysis.confidence}/100
                                </span>
                              </div>
                            </div>

                            <div className="claim-analysis-content">
                              <div className="reasoning-section">
                                <h4>分析推理</h4>
                                <div className="reasoning-text">{claimAnalysis.reasoning}</div>
                              </div>

                              {claimAnalysis.citations && claimAnalysis.citations.length > 0 && (
                                <div className="citations-section">
                                  <h4>检索到的证据文档 ({claimAnalysis.citations.length} 个)</h4>
                                  <div className="citations-list">
                                    {claimAnalysis.citations.map((citation, citIndex) => (
                                      <div key={citIndex} className="citation-card">
                                        <div className="citation-header">
                                          <span className="citation-number">#{citIndex + 1}</span>
                                          <strong className="citation-title">{citation.doc_title}</strong>
                                          {citation.similarity_score !== undefined && (
                                            <span className="similarity-badge">
                                              相似度: {(citation.similarity_score * 100).toFixed(1)}%
                                            </span>
                                          )}
                                        </div>
                                        <div className="citation-meta">
                                          文档ID: {citation.doc_id} | 分块ID: {citation.chunk_id}
                                        </div>
                                        <div className="citation-quote">
                                          <em>"{citation.quote}"</em>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {claimAnalysis.gaps && claimAnalysis.gaps.length > 0 && (
                                <div className="gaps-section">
                                  <h4>证据缺口</h4>
                                  <ul>
                                    {claimAnalysis.gaps.map((gap, gapIndex) => (
                                      <li key={gapIndex}>{gap}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {claimAnalysis.recommended_actions && claimAnalysis.recommended_actions.length > 0 && (
                                <div className="actions-section">
                                  <h4>建议行动</h4>
                                  <ul>
                                    {claimAnalysis.recommended_actions.map((action, actionIndex) => (
                                      <li key={actionIndex}>{action}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </div>
                        )
                      })}
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
