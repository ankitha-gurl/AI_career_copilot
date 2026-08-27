import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client'
import Loading from '../components/Loading'

export default function JobMatch() {
  const { jobId } = useParams()
  const [job, setJob] = useState(null)
  const [matching, setMatching] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get(`/jobs/${jobId}`).then((res) => { setJob(res.data); setLoading(false) })
  }, [jobId])

  async function handleMatch() {
    setMatching(true)
    setError('')
    try {
      const res = await api.post(`/jobs/${jobId}/match`, {})
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not calculate match. Make sure you have an analyzed resume.')
    } finally {
      setMatching(false)
    }
  }

  if (loading) return <Loading label="Loading job..." />

  return (
    <div className="page">
      <h1>{job.title || 'Job details'}</h1>
      {job.company && <p className="page-subtitle">{job.company}</p>}

      {error && <div className="alert-error">{error}</div>}

      <button onClick={handleMatch} disabled={matching}>
        {matching ? 'Calculating match...' : 'Calculate Job Match'}
      </button>

      {job.analysis && (
        <div className="analysis-card">
          <h3>Job requirements (AI extracted)</h3>
          {Object.entries(job.analysis).map(([key, value]) => (
            Array.isArray(value) && value.length > 0 && (
              <div key={key} className="analysis-section">
                <h4>{key.replaceAll('_', ' ')}</h4>
                <ul>{value.map((v, i) => <li key={i}>{v}</li>)}</ul>
              </div>
            )
          ))}
        </div>
      )}

      {result && (
        <div className="analysis-card highlight">
          <h3>Match result (AI-assisted estimate)</h3>
          <div className="score-display">{Math.round(result.match_score)}%</div>
          <div className="analysis-section">
            <h4>Missing skills</h4>
            <ul>{(result.result.missing_skills || []).map((s, i) => <li key={i}>{s}</li>)}</ul>
          </div>
          <div className="analysis-section">
            <h4>Recommendations</h4>
            <ul>{(result.result.recommendations || []).map((s, i) => <li key={i}>{s}</li>)}</ul>
          </div>
        </div>
      )}
    </div>
  )
}
