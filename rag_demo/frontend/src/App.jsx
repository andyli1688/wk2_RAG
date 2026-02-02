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
          'Vector database not found or is empty.\n\nWould you like to index company/EDU/company_data.pdf now?\n\nThis will take a few minutes.'
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
        setError(response.data.message || 'Indexing failed')
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Indexing failed')
    } finally {
      setIndexing(false)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    // Check file type
    const validExtensions = ['.pdf', '.docx', '.txt']
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
    if (!validExtensions.includes(fileExtension)) {
      setError('Only PDF, DOCX, and TXT files are supported')
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
            setUploadProgress(Math.max(percentCompleted, 5)) // Show at least 5% progress
          } else {
            // If total size cannot be obtained, show at least some progress
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
      setError(err.response?.data?.detail || err.message || 'Upload failed')
      setUploadProgress(0)
    } finally {
      setLoading(false)
    }
  }

  const handleExtractClaims = async () => {
    if (!reportId) {
      setError('Please upload a report first')
      return
    }

    setExtractingClaims(true)
    setError(null)
    setExtractProgress(0)

    // Simulate progress updates
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
      setError(err.response?.data?.detail || err.message || 'Extraction failed')
    } finally {
      setExtractingClaims(false)
    }
  }

  const handleVerifyEvidence = async () => {
    if (!reportId || claims.length === 0) {
      setError('Please complete claim extraction first')
      return
    }

    setVerifyingEvidence(true)
    setError(null)
    setVerifyProgress(0)

    // Simulate progress updates
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
      // Evidence verification only marks status, does not generate report
      // Actual analysis and report generation happens on the rebuttal generation page
      await new Promise(resolve => setTimeout(resolve, 3000)) // Simulate verification process
      clearInterval(progressInterval)
      setVerifyProgress(100)
      setEvidenceVerified(true)
      setError(null)
    } catch (err) {
      clearInterval(progressInterval)
      setVerifyProgress(0)
      setError(err.response?.data?.detail || err.message || 'Evidence verification failed')
    } finally {
      setVerifyingEvidence(false)
    }
  }

  // Auto-trigger claim extraction when user navigates to extract tab
  useEffect(() => {
    if (activeTab === 'extract' && reportId && claims.length === 0 && !extractingClaims) {
      handleExtractClaims()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, reportId, claims.length])

  // Auto-trigger evidence verification when user enters verify tab and verification not yet done
  useEffect(() => {
    if (activeTab === 'verify' && claims.length > 0 && !evidenceVerified && !verifyingEvidence) {
      handleVerifyEvidence()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, claims.length, evidenceVerified])

  const handleGenerateRebuttal = async () => {
    if (!reportId || claims.length === 0) {
      setError('Please complete claim extraction first')
      return
    }

    if (!evidenceVerified) {
      setError('Please complete evidence verification first')
      return
    }

    setGeneratingRebuttal(true)
    setError(null)
    setRebuttalProgress(0)

    // Simulate progress updates
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
        setError('Rebuttal generation timeout. Please try again later or reduce the number of claims to analyze')
      } else {
        setError(err.response?.data?.detail || err.message || 'Rebuttal generation failed')
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
      setError(err.response?.data?.detail || err.message || 'Download failed')
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔍 Short Report Rebuttal Assistant</h1>
      </header>

      <nav className="tabs">
        <div 
          className={`tab-status ${activeTab === 'upload' ? 'active' : ''} ${reportId ? 'completed' : ''}`}
          onClick={() => setActiveTab('upload')}
          style={{ cursor: 'pointer' }}
        >
          📤 Report Upload
        </div>
        <div 
          className={`tab-status ${activeTab === 'extract' ? 'active' : ''} ${claims.length > 0 ? 'completed' : ''}`}
          onClick={() => setActiveTab('extract')}
          style={{ cursor: 'pointer' }}
        >
          🔍 Claim Extraction
        </div>
        <div 
          className={`tab-status ${activeTab === 'verify' ? 'active' : ''} ${evidenceVerified ? 'completed' : ''}`}
          onClick={() => setActiveTab('verify')}
          style={{ cursor: 'pointer' }}
        >
          ✅ Evidence Verification
        </div>
        <div 
          className={`tab-status ${activeTab === 'rebuttal' ? 'active' : ''} ${analysis ? 'completed' : ''}`}
          onClick={() => setActiveTab('rebuttal')}
          style={{ cursor: 'pointer' }}
        >
          📝 Rebuttal Generation
        </div>
        <div 
          className={`tab-status ${activeTab === 'export' ? 'active' : ''} ${analysis ? 'completed' : ''}`}
          onClick={() => setActiveTab('export')}
          style={{ cursor: 'pointer' }}
        >
          📥 Report Export
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
            <h2>Report Upload</h2>
            <p className="help-text">Please upload a short report file</p>
            <div className="upload-area">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileUpload}
                disabled={loading}
                id="file-input"
              />
              <label htmlFor="file-input" className="upload-label">
                {loading ? 'Uploading...' : 'Choose File'}
              </label>
              <p style={{ 
                marginTop: '0.5rem', 
                fontSize: '0.85rem', 
                color: '#666',
                textAlign: 'center'
              }}>
                Supports PDF, DOCX and TXT file types
              </p>
              
              {/* Upload progress bar */}
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
                    {uploadProgress > 0 ? `${uploadProgress}%` : 'Uploading...'}
                  </p>
                </div>
              )}

              {/* Upload success message */}
              {uploadSuccess && !loading && (
                <div className="success-message" style={{ 
                  marginTop: '1rem', 
                  padding: '1rem', 
                  background: '#d4edda', 
                  borderRadius: '5px',
                  textAlign: 'center'
                }}>
                  ✓ Upload Successful!
                </div>
              )}
            </div>

            {/* Navigation buttons */}
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
                Next →
              </button>
            </div>
          </div>
        )}

        {activeTab === 'extract' && (
          <div className="tab-content">
            <h2>Claim Extraction</h2>
            {reportId ? (
              <>
                {claims.length === 0 ? (
                  <>
                    <p className="help-text">Extract claims from the uploaded report. The system will use AI to analyze the report content</p>

                    {/* Extraction progress bar */}
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
                          {extractProgress < 100 ? `Extracting claims... ${extractProgress}%` : 'Extraction complete!'}
                        </p>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div className="success-message" style={{ marginBottom: '1rem', padding: '1rem', background: '#d4edda', borderRadius: '5px' }}>
                      ✓ Successfully extracted {claims.length} claims
                    </div>
                    <div className="claims-list">
                      <h3>Extracted Claims List</h3>
                      <div className="claims-list-container">
                        {claims.map((claim, index) => (
                          <div key={index} className="claim-item">
                            <strong>{claim.claim_id}:</strong> {claim.claim_text}
                            <div className="claim-meta">
                              Type: {claim.claim_type} | Pages: {claim.page_numbers.join(', ')}
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
                Please complete report upload first
              </div>
            )}

            {/* Navigation buttons */}
            <div className="navigation-buttons">
              <button
                className="nav-button"
                onClick={() => setActiveTab('upload')}
              >
                ← Previous
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
                Next →
              </button>
            </div>
          </div>
        )}

        {activeTab === 'verify' && (
          <div className="tab-content">
            <h2>Evidence Verification</h2>
            {claims.length > 0 ? (
              <>
                <p className="help-text">Retrieve relevant evidence from internal document library and verify the support for each claim</p>

                {/* Evidence verification progress bar */}
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
                      {verifyProgress < 100 ? `Verifying evidence... ${verifyProgress}%` : 'Verification complete!'}
                    </p>
                  </div>
                )}

                {evidenceVerified && (
                  <div className="success-message" style={{ marginTop: '2rem', padding: '1rem', background: '#d4edda', borderRadius: '5px' }}>
                    ✓ Evidence verification complete!
                  </div>
                )}

              </>
            ) : (
              <div className="error-message">
                Please complete claim extraction first
              </div>
            )}

            {/* Navigation buttons */}
            <div className="navigation-buttons">
              <button
                className="nav-button"
                onClick={() => setActiveTab('extract')}
                disabled={claims.length === 0}
              >
                ← Previous
              </button>
              <button
                className="nav-button"
                onClick={() => setActiveTab('rebuttal')}
                disabled={!evidenceVerified}
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {activeTab === 'rebuttal' && (
          <div className="tab-content">
            <h2>Rebuttal Generation</h2>
            {evidenceVerified ? (
              <>
                {!analysis ? (
                  <>
                    <p className="help-text">Generate a complete rebuttal analysis report based on verified evidence</p>
                    <div className="config-section">
                      <label>
                        Number of Retrieved Documents:
                        <input
                          type="number"
                          min="3"
                          max="20"
                          value={topK}
                          onChange={(e) => setTopK(parseInt(e.target.value))}
                        />
                      </label>
                      <label>
                        Maximum Claims to Analyze:
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
                      {generatingRebuttal ? 'Generating...' : '📝 Start Rebuttal Generation'}
                    </button>

                    {/* Rebuttal generation progress bar */}
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
                          {rebuttalProgress < 100 ? `Generating rebuttal analysis... ${rebuttalProgress}%` : 'Generation complete!'}
                        </p>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div className="success-message" style={{ marginBottom: '1rem', padding: '1rem', background: '#d4edda', borderRadius: '5px' }}>
                      ✓ Rebuttal generation complete! Generated rebuttal analysis for {analysis.summary.total_claims} claims
                    </div>
                    <div className="analysis-results">
                      <h3>Executive Summary</h3>
                      <div className="summary-stats">
                        <div className="stat">
                          <div className="stat-value">{analysis.summary.total_claims}</div>
                          <div className="stat-label">Total Claims</div>
                        </div>
                        <div className="stat">
                          <div className="stat-value">{analysis.summary.fully_addressed}</div>
                          <div className="stat-label">Fully Addressed</div>
                        </div>
                        <div className="stat">
                          <div className="stat-value">{analysis.summary.partially_addressed}</div>
                          <div className="stat-label">Partially Addressed</div>
                        </div>
                        <div className="stat">
                          <div className="stat-value">{analysis.summary.not_addressed}</div>
                          <div className="stat-label">Not Addressed</div>
                        </div>
                      </div>

                      <h3 style={{ marginTop: '2rem' }}>Detailed Rebuttal Analysis</h3>
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
                                    {claimAnalysis.coverage === 'fully_addressed' ? 'Fully Addressed' :
                                     claimAnalysis.coverage === 'partially_addressed' ? 'Partially Addressed' : 'Not Addressed'}
                                  </span>
                                  <span className="confidence-badge">
                                    Confidence: {claimAnalysis.confidence}/100
                                  </span>
                                </div>
                              </div>

                              <div className="claim-analysis-content">
                                <div className="reasoning-section">
                                  <h4>Rebuttal Analysis</h4>
                                  <div className="reasoning-text">{claimAnalysis.reasoning}</div>
                                </div>

                                {claimAnalysis.citations && claimAnalysis.citations.length > 0 && (
                                  <div className="citations-section">
                                    <h4>Supporting Evidence ({claimAnalysis.citations.length})</h4>
                                    <div className="citations-list">
                                      {claimAnalysis.citations.map((citation, citIndex) => (
                                        <div key={citIndex} className="citation-card">
                                          <div className="citation-header">
                                            <span className="citation-number">#{citIndex + 1}</span>
                                            <strong className="citation-title">{citation.doc_title}</strong>
                                            {citation.similarity_score !== undefined && (
                                              <span className="similarity-badge">
                                                Similarity: {(citation.similarity_score * 100).toFixed(1)}%
                                              </span>
                                            )}
                                          </div>
                                          <div className="citation-meta">
                                            Document ID: {citation.doc_id} | Chunk ID: {citation.chunk_id}
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
                                    <h4>Evidence Gaps</h4>
                                    <ul>
                                      {claimAnalysis.gaps.map((gap, gapIndex) => (
                                        <li key={gapIndex}>{gap}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}

                                {claimAnalysis.recommended_actions && claimAnalysis.recommended_actions.length > 0 && (
                                  <div className="actions-section">
                                    <h4>Recommended Actions</h4>
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
                Please complete evidence verification first
              </div>
            )}

            {/* Navigation buttons */}
            <div className="navigation-buttons">
              <button
                className="nav-button"
                onClick={() => setActiveTab('verify')}
                disabled={!evidenceVerified}
              >
                ← Previous
              </button>
              <button
                className="nav-button"
                onClick={() => setActiveTab('export')}
                disabled={!analysis}
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {activeTab === 'export' && (
          <div className="tab-content">
            <h2>Report Export</h2>
            {analysis ? (
              <>
                <p className="help-text">Choose export format and download the complete analysis report</p>
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
                    📄 Export PDF Report
                  </button>
                  <button
                    onClick={() => handleDownload('md')}
                    className="export-button"
                    style={{ minWidth: '200px' }}
                  >
                    📝 Export Markdown Report
                  </button>
                  <button
                    onClick={() => handleDownload('json')}
                    className="export-button"
                    style={{ minWidth: '200px' }}
                  >
                    📋 Export JSON Report
                  </button>
                </div>
              </>
            ) : (
              <div className="error-message">
                Please complete rebuttal generation first
              </div>
            )}

            {/* Navigation buttons */}
            <div className="navigation-buttons">
              <button
                className="nav-button"
                onClick={() => setActiveTab('rebuttal')}
                disabled={!analysis}
              >
                ← Previous
              </button>
              <button
                className="nav-button"
                disabled={true}
                style={{ opacity: 0.5, cursor: 'default' }}
              >
                Complete
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
