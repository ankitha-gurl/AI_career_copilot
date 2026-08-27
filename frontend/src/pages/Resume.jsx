import { useEffect, useState } from 'react'
import api from '../api/client'
import Loading from '../components/Loading'

export default function Resume() {
  const [resumes, setResumes] = useState([])
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [analyzingId, setAnalyzingId] = useState(null)
  const [loading, setLoading] = useState(true)

  function loadResumes() {
    api.get('/resumes').then((res) => { setResumes(res.data); setLoading(false) })
  }

  useEffect(loadResumes, [])

  async function handleUpload(e) {
    e.preventDefault()
    if (!file) return
    setUploading(true)
    setError('')
    const formData = new FormData()
    formData.append('file', file)
    try {
      await api.post('/resumes', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      setFile(null)
      loadResumes()
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  async function handleAnalyze(id) {
    setAnalyzingId(id)
    setError('')
    setAnalysis(null)
    try {
      const res = await api.post(`/resumes/${id}/analyze`)
      setAnalysis(res.data)
      loadResumes()
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed.')
    } finally {
      setAnalyzingId(null)
    }
  }

  if (loading) return <Loading label="Loading resumes..." />

  return (
    <div className="page">
      <h1>Resume</h1>
      <p className="page-subtitle">Upload a PDF, DOCX, or TXT resume, then run AI analysis to extract skills, education, and experience.</p>

      {error && <div className="alert-error">{error}</div>}

      <form className="form-card" onSubmit={handleUpload}>
        <label>Choose file (.pdf, .docx, .txt)</label>
        <input type="file" accept=".pdf,.docx,.txt" onChange={(e) => setFile(e.target.files[0])} />
        <button type="submit" disabled={!file || uploading}>{uploading ? 'Uploading...' : 'Upload Resume'}</button>
      </form>

      <div className="list-card">
        <h3>Your resumes</h3>
        {resumes.length === 0 && <p className="empty-state">No resumes uploaded yet.</p>}
        {resumes.map((r) => (
          <div key={r.id} className="list-row">
            <div>
              <strong>{r.original_filename}</strong>
              <span className="muted"> ({r.file_type})</span>
              {r.has_analysis && <span className="badge">Analyzed</span>}
            </div>
            <button onClick={() => handleAnalyze(r.id)} disabled={analyzingId === r.id}>
              {analyzingId === r.id ? 'Analyzing...' : r.has_analysis ? 'Re-view analysis' : 'Analyze with AI'}
            </button>
          </div>
        ))}
      </div>

      {analysis && (
        <div className="analysis-card">
          <h3>AI Analysis</h3>
          <p><strong>Summary:</strong> {analysis.summary}</p>
          {Object.entries(analysis.analysis).map(([key, value]) => (
            Array.isArray(value) && value.length > 0 && (
              <div key={key} className="analysis-section">
                <h4>{key.replaceAll('_', ' ')}</h4>
                <ul>{value.map((v, i) => <li key={i}>{v}</li>)}</ul>
              </div>
            )
          ))}
        </div>
      )}
    </div>
  )
}
