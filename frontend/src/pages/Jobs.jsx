import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import Loading from '../components/Loading'

export default function Jobs() {
  const [jobs, setJobs] = useState([])
  const [title, setTitle] = useState('')
  const [company, setCompany] = useState('')
  const [rawText, setRawText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  function loadJobs() {
    api.get('/jobs').then((res) => { setJobs(res.data); setLoading(false) })
  }

  useEffect(loadJobs, [])

  async function handleSubmit(e) {
    e.preventDefault()
    if (!rawText.trim()) return
    setSubmitting(true)
    setError('')
    try {
      await api.post('/jobs', { title, company, raw_text: rawText })
      setTitle(''); setCompany(''); setRawText('')
      loadJobs()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not analyze job description.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <Loading label="Loading jobs..." />

  return (
    <div className="page">
      <h1>Job Descriptions</h1>
      <p className="page-subtitle">Paste a job description to get an AI breakdown, then compare it against your resume.</p>

      {error && <div className="alert-error">{error}</div>}

      <form className="form-card" onSubmit={handleSubmit}>
        <div className="form-grid">
          <div>
            <label>Job title (optional)</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div>
            <label>Company (optional)</label>
            <input value={company} onChange={(e) => setCompany(e.target.value)} />
          </div>
        </div>
        <label>Job description text</label>
        <textarea rows={8} value={rawText} onChange={(e) => setRawText(e.target.value)} required />
        <button type="submit" disabled={submitting}>{submitting ? 'Analyzing with AI...' : 'Analyze Job Description'}</button>
      </form>

      <div className="list-card">
        <h3>Saved jobs</h3>
        {jobs.length === 0 && <p className="empty-state">No job descriptions saved yet.</p>}
        {jobs.map((j) => (
          <div key={j.id} className="list-row">
            <div>
              <strong>{j.title || 'Untitled role'}</strong>
              {j.company && <span className="muted"> at {j.company}</span>}
            </div>
            <Link to={`/jobs/${j.id}/match`}>View & match →</Link>
          </div>
        ))}
      </div>
    </div>
  )
}
