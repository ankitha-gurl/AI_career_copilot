import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import Loading from '../components/Loading'

export default function Dashboard() {
  const { user } = useAuth()
  const [resumes, setResumes] = useState([])
  const [jobs, setJobs] = useState([])
  const [skills, setSkills] = useState([])
  const [roadmaps, setRoadmaps] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const [r, j, s, rm] = await Promise.all([
          api.get('/resumes'),
          api.get('/jobs'),
          api.get('/skills/me'),
          api.get('/roadmap'),
        ])
        setResumes(r.data)
        setJobs(j.data)
        setSkills(s.data)
        setRoadmaps(rm.data)
      } catch (err) {
        setError('Could not load dashboard data.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <Loading label="Loading your dashboard..." />

  const latestResume = resumes[0]

  return (
    <div className="page">
      <h1>Welcome back, {user?.full_name}</h1>
      {error && <div className="alert-error">{error}</div>}

      <div className="card-grid">
        <div className="stat-card">
          <h3>Resume status</h3>
          <p>{latestResume ? `${latestResume.original_filename} ${latestResume.has_analysis ? '(analyzed)' : '(not analyzed)'}` : 'No resume uploaded yet'}</p>
          <Link to="/resume">Manage resume →</Link>
        </div>

        <div className="stat-card">
          <h3>Skills tracked</h3>
          <p>{skills.length} skills</p>
          <Link to="/skills">View skills →</Link>
        </div>

        <div className="stat-card">
          <h3>Job descriptions</h3>
          <p>{jobs.length} saved</p>
          <Link to="/jobs">View jobs →</Link>
        </div>

        <div className="stat-card">
          <h3>Career roadmaps</h3>
          <p>{roadmaps.length} generated</p>
          <Link to="/roadmap">View roadmap →</Link>
        </div>

        <div className="stat-card">
          <h3>Interview prep</h3>
          <p>Practice technical & behavioral questions</p>
          <Link to="/interview">Start practicing →</Link>
        </div>

        <div className="stat-card highlight">
          <h3>AI Career Copilot</h3>
          <p>Ask anything about your career readiness</p>
          <Link to="/copilot">Chat now →</Link>
        </div>
      </div>
    </div>
  )
}
