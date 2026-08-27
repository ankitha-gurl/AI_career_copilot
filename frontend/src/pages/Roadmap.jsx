import { useEffect, useState } from 'react'
import api from '../api/client'
import Loading from '../components/Loading'

export default function Roadmap() {
  const [roadmaps, setRoadmaps] = useState([])
  const [targetRole, setTargetRole] = useState('')
  const [generating, setGenerating] = useState(false)
  const [active, setActive] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/roadmap').then((res) => { setRoadmaps(res.data); setLoading(false) })
  }, [])

  async function handleGenerate(e) {
    e.preventDefault()
    if (!targetRole.trim()) return
    setGenerating(true)
    setError('')
    try {
      const res = await api.post('/roadmap', { target_role: targetRole })
      setActive(res.data)
      const list = await api.get('/roadmap')
      setRoadmaps(list.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not generate roadmap.')
    } finally {
      setGenerating(false)
    }
  }

  async function viewRoadmap(id) {
    const res = await api.get(`/roadmap/${id}`)
    setActive(res.data)
  }

  if (loading) return <Loading label="Loading roadmaps..." />

  return (
    <div className="page">
      <h1>Career Roadmap</h1>
      {error && <div className="alert-error">{error}</div>}

      <form className="form-card inline-form" onSubmit={handleGenerate}>
        <input placeholder="Target role, e.g. Backend Engineer" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} />
        <button type="submit" disabled={generating}>{generating ? 'Generating...' : 'Generate Roadmap'}</button>
      </form>

      <div className="list-card">
        <h3>Your roadmaps</h3>
        {roadmaps.length === 0 && <p className="empty-state">No roadmaps generated yet.</p>}
        {roadmaps.map((r) => (
          <div key={r.id} className="list-row">
            <div><strong>{r.target_role}</strong> <span className="muted">({r.num_phases} phases)</span></div>
            <button onClick={() => viewRoadmap(r.id)}>View →</button>
          </div>
        ))}
      </div>

      {active && (
        <div className="roadmap-timeline">
          <h3>Roadmap: {active.target_role}</h3>
          {active.items.map((item, i) => (
            <div key={i} className="roadmap-phase">
              <div className="roadmap-phase-number">{i + 1}</div>
              <div>
                <h4>{item.phase_title} {item.skill && <span className="muted">— {item.skill}</span>}</h4>
                <p><span className={`priority priority-${item.priority}`}>{item.priority}</span> · {item.difficulty}</p>
                {item.project_task && <p><strong>Project:</strong> {item.project_task}</p>}
                {item.success_criteria && <p className="muted"><strong>Success criteria:</strong> {item.success_criteria}</p>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
