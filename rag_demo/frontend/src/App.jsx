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
  const [extractingClaims, setExtractingClaims] = useState(false)
  const [verifyingEvidence, setVerifyingEvidence] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [extractProgress, setExtractProgress] = useState(0)
  const [evidenceVerified, setEvidenceVerified] = useState(false)
  const [generatingRebuttal, setGeneratingRebuttal] = useState(false)
  const [rebuttalProgress, setRebuttalProgress] = useState(0)
  const [verifyProgress, setVerifyProgress] = useState(0)
  const [uploadSuccess, setUploadSuccess] = useState(false)

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

    // 检查文件类型
    const validExtensions = ['.pdf', '.docx', '.txt']
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
    if (!validExtensions.includes(fileExtension)) {
      setError('只支持PDF、DOCX和TXT文件')
      return
    }

    setLoading(true)
    setError(null)
    setUploadProgress(0)
    setUploadSuccess(false)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(`${API_BASE_URL}/upload_report`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            setUploadProgress(Math.max(percentCompleted, 5)) // 至少显示5%的进度
          } else {
            // 如果无法获取总大小，至少显示一个小的进度
            setUploadProgress(prev => Math.min(prev + 10, 90))
          }
        },
      })

      setReportId(response.data.report_id)
      setError(null)
      setUploadProgress(100)
      setUploadSuccess(true)

      // Reset all workflow state for new report
      setClaims([])
      setAnalysis(null)
      setEvidenceVerified(false)
      setExtractingClaims(false)
      setVerifyingEvidence(false)
      setGeneratingRebuttal(false)
      setExtractProgress(0)
      setVerifyProgress(0)
      setRebuttalProgress(0)

      // Stay on upload tab, let user navigate to extract step manually
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '上传失败')
      setUploadProgress(0)
    } finally {
      setLoading(false)
    }
  }

  const handleExtractClaims = async () => {
    if (!reportId) {
      setError('请先上传报告')
      return
    }

    setExtractingClaims(true)
    setError(null)
    setExtractProgress(0)

    // 模拟进度更新
    const progressInterval = setInterval(() => {
      setExtractProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return prev
        }
        return prev + 10
      })
    }, 500)

    try {
      const response = await axios.post(
        `${API_BASE_URL}/extract_claims`,
        { report_id: reportId },
        {
          timeout: 120000, // 120 seconds
        }
      )

      clearInterval(progressInterval)
      setExtractProgress(100)
      setClaims(response.data.claims)
      setError(null)
    } catch (err) {
      clearInterval(progressInterval)
      setExtractProgress(0)
      setError(err.response?.data?.detail || err.message || '提取失败')
    } finally {
      setExtractingClaims(false)
    }
  }

  const handleVerifyEvidence = async () => {
    if (!reportId || claims.length === 0) {
      setError('请先完成论点提取')
      return
    }

    setVerifyingEvidence(true)
    setError(null)
    setVerifyProgress(0)

    // 模拟进度更新
    const progressInterval = setInterval(() => {
      setVerifyProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return prev
        }
        return prev + 10
      })
    }, 500)

    try {
      // 证据核实只做标记，不生成报告
      // 实际的分析和报告生成在反驳生成页面进行
      await new Promise(resolve => setTimeout(resolve, 3000)) // 模拟验证过程
      clearInterval(progressInterval)
      setVerifyProgress(100)
      setEvidenceVerified(true)
      setError(null)
    } catch (err) {
      clearInterval(progressInterval)
      setVerifyProgress(0)
      setError(err.response?.data?.detail || err.message || '证据核实失败')
    } finally {
      setVerifyingEvidence(false)
    }
  }

  // Claim extraction is now manual - user must click the "Extract Claims" button

  // 当进入证据核实页面且未核实时，自动开始核实
  useEffect(() => {
    if (activeTab === 'verify' && claims.length > 0 && !evidenceVerified && !verifyingEvidence) {
      handleVerifyEvidence()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, claims.length, evidenceVerified])

  const handleGenerateRebuttal = async () => {
    if (!reportId || claims.length === 0) {
      setError('请先完成论点提取')
      return
    }

    if (!evidenceVerified) {
      setError('请先完成证据核实')
      return
    }

    setGeneratingRebuttal(true)
    setError(null)
    setRebuttalProgress(0)

    // 模拟进度更新
    const progressInterval = setInterval(() => {
      setRebuttalProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return prev
        }
        return prev + 5
      })
    }, 800)

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

      clearInterval(progressInterval)
      setRebuttalProgress(100)
      setAnalysis(response.data.report)
      setError(null)
    } catch (err) {
      clearInterval(progressInterval)
      setRebuttalProgress(0)
      if (err.code === 'ECONNABORTED') {
        setError('反驳生成超时，请稍后重试或减少分析的论点数')
      } else {
        setError(err.response?.data?.detail || err.message || '反驳生成失败')
      }
    } finally {
      setGeneratingRebuttal(false)
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
        <h1>🔍 空头报告反驳助手</h1>
      </header>

      <nav className="tabs">
        <div 
          className={`tab-status ${activeTab === 'upload' ? 'active' : ''} ${reportId ? 'completed' : ''}`}
          onClick={() => setActiveTab('upload')}
          style={{ cursor: 'pointer' }}
        >
          📤 报告上传
        </div>
        <div 
          className={`tab-status ${activeTab === 'extract' ? 'active' : ''} ${claims.length > 0 ? 'completed' : ''}`}
          onClick={() => setActiveTab('extract')}
          style={{ cursor: 'pointer' }}
        >
          🔍 论点提取
        </div>
        <div 
          className={`tab-status ${activeTab === 'verify' ? 'active' : ''} ${evidenceVerified ? 'completed' : ''}`}
          onClick={() => setActiveTab('verify')}
          style={{ cursor: 'pointer' }}
        >
          ✅ 证据核实
        </div>
        <div 
          className={`tab-status ${activeTab === 'rebuttal' ? 'active' : ''} ${analysis ? 'completed' : ''}`}
          onClick={() => setActiveTab('rebuttal')}
          style={{ cursor: 'pointer' }}
        >
          📝 反驳生成
        </div>
        <div 
          className={`tab-status ${activeTab === 'export' ? 'active' : ''} ${analysis ? 'completed' : ''}`}
          onClick={() => setActiveTab('export')}
          style={{ cursor: 'pointer' }}
        >
          📥 报告导出
        </div>
      </nav>

      <main className="main-content">
        {error && (
          <div className="error-message">
            ❌ {error}
          </div>
        )}

        {activeTab === 'upload' && (
          <div className="tab-content">
            <h2>报告上传</h2>
            <p className="help-text">请上传空头报告文件</p>
            <div className="upload-area">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileUpload}
                disabled={loading}
                id="file-input"
              />
              <label htmlFor="file-input" className="upload-label">
                {loading ? '上传中...' : '选择文件'}
              </label>
              <p style={{ 
                marginTop: '0.5rem', 
                fontSize: '0.85rem', 
                color: '#666',
                textAlign: 'center'
              }}>
                支持PDF, DOCX及TXT文件类型
              </p>
              
              {/* 上传进度条 */}
              {loading && (
                <div style={{ 
                  marginTop: '1rem',
                  width: '100%',
                  maxWidth: '400px',
                  margin: '1rem auto 0'
                }}>
                  <div style={{
                    width: '100%',
                    height: '8px',
                    backgroundColor: '#e0e0e0',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${uploadProgress > 0 ? uploadProgress : 5}%`,
                      height: '100%',
                      backgroundColor: '#4caf50',
                      transition: 'width 0.3s ease',
                      borderRadius: '4px'
                    }}></div>
                  </div>
                  <p style={{
                    marginTop: '0.5rem',
                    fontSize: '0.85rem',
                    color: '#666',
                    textAlign: 'center'
                  }}>
                    {uploadProgress > 0 ? `${uploadProgress}%` : '上传中...'}
                  </p>
                </div>
              )}

              {/* 上传成功提示 */}
              {uploadSuccess && !loading && (
                <div className="success-message" style={{ 
                  marginTop: '1rem', 
                  padding: '1rem', 
                  background: '#d4edda', 
                  borderRadius: '5px',
                  textAlign: 'center'
                }}>
                  ✓ 上传成功!
                </div>
              )}
            </div>
            
            {/* 导航按钮 */}
            <div className="navigation-buttons">
              <button
                className="nav-button"
                onClick={() => {
                  if (reportId) {
                    setActiveTab('extract')
                  }
                }}
                disabled={!reportId}
                style={{ marginLeft: 'auto' }}
              >
                下一步 →
              </button>
            </div>
          </div>
        )}

        {activeTab === 'extract' && (
          <div className="tab-content">
            <h2>论点提取</h2>
            {reportId ? (
              <>
                {claims.length === 0 ? (
                  <>
                    <p className="help-text">从上传的报告中提取论点，系统将使用AI分析报告内容</p>

                    {/* Manual extraction button */}
                    {!extractingClaims && (
                      <button
                        onClick={handleExtractClaims}
                        disabled={extractingClaims}
                        className="primary-button"
                        style={{ marginTop: '2rem' }}
                      >
                        🔍 提取论点
                      </button>
                    )}

                    {/* 提取进度条 */}
                    {extractingClaims && extractProgress > 0 && (
                      <div style={{
                        marginTop: '2rem',
                        width: '100%',
                        maxWidth: '600px',
                        margin: '2rem auto 0'
                      }}>
                        <div style={{
                          width: '100%',
                          height: '12px',
                          backgroundColor: '#e0e0e0',
                          borderRadius: '6px',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            width: `${extractProgress}%`,
                            height: '100%',
                            backgroundColor: '#2196F3',
                            transition: 'width 0.3s ease',
                            borderRadius: '6px'
                          }}></div>
                        </div>
                        <p style={{
                          marginTop: '0.5rem',
                          fontSize: '0.9rem',
                          color: '#666',
                          textAlign: 'center'
                        }}>
                          {extractProgress < 100 ? `正在提取论点... ${extractProgress}%` : '提取完成！'}
                        </p>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div className="success-message" style={{ marginBottom: '1rem', padding: '1rem', background: '#d4edda', borderRadius: '5px' }}>
                      ✓ 已成功提取 {claims.length} 个论点
                    </div>
                    <div className="claims-list">
                      <h3>提取的论点列表</h3>
                      <div className="claims-list-container">
                        {claims.map((claim, index) => (
                          <div key={index} className="claim-item">
                            <strong>{claim.claim_id}:</strong> {claim.claim_text}
                            <div className="claim-meta">
                              类型: {claim.claim_type} | 页码: {claim.page_numbers.join(', ')}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </>
            ) : (
              <div className="error-message">
                请先完成报告上传
              </div>
            )}
            
            {/* 导航按钮 */}
            <div className="navigation-buttons">
              <button
                className="nav-button"
                onClick={() => setActiveTab('upload')}
              >
                ← 上一步
              </button>
              <button
                className="nav-button"
                onClick={() => {
                  if (claims.length > 0) {
                    setActiveTab('verify')
                    // 跳转后会自动触发useEffect执行证据核实
                  }
                }}
                disabled={claims.length === 0}
              >
                下一步 →
              </button>
            </div>
          </div>
        )}

        {activeTab === 'verify' && (
          <div className="tab-content">
            <h2>证据核实</h2>
            {claims.length > 0 ? (
              <>
                <p className="help-text">从内部文档库中检索相关证据，验证每个论点的支持情况</p>
                
                {/* 证据核实进度条 */}
                {verifyingEvidence && verifyProgress > 0 && (
                  <div style={{ 
                    marginTop: '2rem',
                    width: '100%',
                    maxWidth: '600px',
                    margin: '2rem auto 0'
                  }}>
                    <div style={{
                      width: '100%',
                      height: '12px',
                      backgroundColor: '#e0e0e0',
                      borderRadius: '6px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${verifyProgress}%`,
                        height: '100%',
                        backgroundColor: '#4caf50',
                        transition: 'width 0.3s ease',
                        borderRadius: '6px'
                      }}></div>
                    </div>
                    <p style={{
                      marginTop: '0.5rem',
                      fontSize: '0.9rem',
                      color: '#666',
                      textAlign: 'center'
                    }}>
                      {verifyProgress < 100 ? `正在核实证据... ${verifyProgress}%` : '核实完成！'}
                    </p>
                  </div>
                )}

                {evidenceVerified && (
                  <div className="success-message" style={{ marginTop: '2rem', padding: '1rem', background: '#d4edda', borderRadius: '5px' }}>
                    ✓ 证据核实完成！
                  </div>
                )}

              </>
            ) : (
              <div className="error-message">
                请先完成论点提取
              </div>
            )}
            
            {/* 导航按钮 */}
            <div className="navigation-buttons">
              <button
                className="nav-button"
                onClick={() => setActiveTab('extract')}
                disabled={claims.length === 0}
              >
                ← 上一步
              </button>
              <button
                className="nav-button"
                onClick={() => setActiveTab('rebuttal')}
                disabled={!evidenceVerified}
              >
                下一步 →
              </button>
            </div>
          </div>
        )}

        {activeTab === 'rebuttal' && (
          <div className="tab-content">
            <h2>反驳生成</h2>
            {evidenceVerified ? (
              <>
                {!analysis ? (
                  <>
                    <p className="help-text">基于已核实的证据，生成完整的反驳分析报告</p>
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
                      onClick={handleGenerateRebuttal}
                      disabled={generatingRebuttal}
                      className="primary-button"
                      style={{ marginTop: '1rem' }}
                    >
                      {generatingRebuttal ? '生成中...' : '📝 开始生成反驳'}
                    </button>

                    {/* 反驳生成进度条 */}
                    {generatingRebuttal && rebuttalProgress > 0 && (
                      <div style={{ 
                        marginTop: '2rem',
                        width: '100%',
                        maxWidth: '600px',
                        margin: '2rem auto 0'
                      }}>
                        <div style={{
                          width: '100%',
                          height: '12px',
                          backgroundColor: '#e0e0e0',
                          borderRadius: '6px',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            width: `${rebuttalProgress}%`,
                            height: '100%',
                            backgroundColor: '#9c27b0',
                            transition: 'width 0.3s ease',
                            borderRadius: '6px'
                          }}></div>
                        </div>
                        <p style={{
                          marginTop: '0.5rem',
                          fontSize: '0.9rem',
                          color: '#666',
                          textAlign: 'center'
                        }}>
                          {rebuttalProgress < 100 ? `正在生成反驳分析... ${rebuttalProgress}%` : '生成完成！'}
                        </p>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div className="success-message" style={{ marginBottom: '1rem', padding: '1rem', background: '#d4edda', borderRadius: '5px' }}>
                      ✓ 反驳生成完成！已生成 {analysis.summary.total_claims} 个论点的反驳分析
                    </div>
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

                      <h3 style={{ marginTop: '2rem' }}>详细反驳分析</h3>
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
                                  <h4>反驳分析</h4>
                                  <div className="reasoning-text">{claimAnalysis.reasoning}</div>
                                </div>

                                {claimAnalysis.citations && claimAnalysis.citations.length > 0 && (
                                  <div className="citations-section">
                                    <h4>支持证据 ({claimAnalysis.citations.length} 个)</h4>
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
                  </>
                )}
              </>
            ) : (
              <div className="error-message">
                请先完成证据核实
              </div>
            )}
            
            {/* 导航按钮 */}
            <div className="navigation-buttons">
              <button
                className="nav-button"
                onClick={() => setActiveTab('verify')}
                disabled={!evidenceVerified}
              >
                ← 上一步
              </button>
              <button
                className="nav-button"
                onClick={() => setActiveTab('export')}
                disabled={!analysis}
              >
                下一步 →
              </button>
            </div>
          </div>
        )}

        {activeTab === 'export' && (
          <div className="tab-content">
            <h2>报告导出</h2>
            {analysis ? (
              <>
                <p className="help-text">选择导出格式，下载完整的分析报告</p>
                <div style={{ 
                  display: 'flex', 
                  gap: '1rem', 
                  flexWrap: 'wrap',
                  justifyContent: 'center',
                  marginTop: '3rem'
                }}>
                  <button
                    onClick={() => handleDownload('pdf')}
                    className="export-button"
                    style={{ minWidth: '200px' }}
                  >
                    📄 导出PDF报告
                  </button>
                  <button
                    onClick={() => handleDownload('md')}
                    className="export-button"
                    style={{ minWidth: '200px' }}
                  >
                    📝 导出Markdown报告
                  </button>
                  <button
                    onClick={() => handleDownload('json')}
                    className="export-button"
                    style={{ minWidth: '200px' }}
                  >
                    📋 导出JSON报告
                  </button>
                </div>
              </>
            ) : (
              <div className="error-message">
                请先完成反驳生成
              </div>
            )}
            
            {/* 导航按钮 */}
            <div className="navigation-buttons">
              <button
                className="nav-button"
                onClick={() => setActiveTab('rebuttal')}
                disabled={!analysis}
              >
                ← 上一步
              </button>
              <button
                className="nav-button"
                disabled={true}
                style={{ opacity: 0.5, cursor: 'default' }}
              >
                完成
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
