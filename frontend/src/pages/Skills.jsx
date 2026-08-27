import { useEffect, useState } from 'react'
import api from '../api/client'
import Loading from '../components/Loading'

export default function Skills() {
  const [skills, setSkills] = useState([])
  const [jobs, setJobs] = useState([])
  const [newSkill, setNewSkill] = useState('')
  const [selectedJobId, setSelectedJobId] = useState('')
  const [gap, setGap] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  function loadSkills() {
    api.get('/skills/me').then((res) => setSkills(res.data))
  }

  useEffect(() => {
    Promise.all([api.get('/skills/me'), api.get('/jobs')]).then(([s, j]) => {
      setSkills(s.data); setJobs(j.data); setLoading(false)
    })
  }, [])

  async function handleAddSkill(e) {
    e.preventDefault()
    if (!newSkill.trim()) return
    await api.post(`/skills/me/${encodeURIComponent(newSkill.trim())}`)
    setNewSkill('')
    loadSkills()
  }

  async function handleGapAnalysis() {
    if (!selectedJobId) return
    setAnalyzing(true)
    setError('')
    setGap(null)
    try {
      const res = await api.post('/skills/gap-analysis', { job_id: Number(selectedJobId) })
      setGap(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not run skill gap analysis.')
    } finally {
      setAnalyzing(false)
    }
  }

  if (loading) return <Loading label="Loading skills..." />

  return (
    <div className="page">
      <h1>Skills</h1>

      <form className="form-card inline-form" onSubmit={handleAddSkill}>
        <input placeholder="e.g. FastAPI" value={newSkill} onChange={(e) => setNewSkill(e.target.value)} />
        <button type="submit">Add Skill</button>
      </form>

      <div className="chip-list">
        {skills.map((s) => <span key={s.id} className="chip">{s.name}</span>)}
        {skills.length === 0 && <p className="empty-state">No skills added yet.</p>}
      </div>

      <h2>Skill Gap Analysis</h2>
      {error && <div className="alert-error">{error}</div>}
      <div className="form-card inline-form">
        <select value={selectedJobId} onChange={(e) => setSelectedJobId(e.target.value)}>
          <option value="">Select a job description...</option>
          {jobs.map((j) => <option key={j.id} value={j.id}>{j.title || `Job #${j.id}`}</option>)}
        </select>
        <button onClick={handleGapAnalysis} disabled={!selectedJobId || analyzing}>
          {analyzing ? 'Analyzing...' : 'Run Gap Analysis'}
        </button>
      </div>

      {gap && (
        <div className="analysis-card">
          <h3>Already possessed</h3>
          <ul>{(gap.already_possessed || []).map((s, i) => <li key={i}>{s}</li>)}</ul>
          <h3>Missing skills</h3>
          {(gap.missing_skills || []).map((m, i) => (
            <div key={i} className="skill-gap-row">
              <strong>{m.skill}</strong> <span className={`priority priority-${m.priority}`}>{m.priority}</span>
              <p>{m.reason}</p>
              <p className="muted">Action: {m.suggested_action}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
