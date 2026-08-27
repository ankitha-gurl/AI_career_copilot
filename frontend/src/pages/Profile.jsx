import { useEffect, useState } from 'react'
import api from '../api/client'
import Loading from '../components/Loading'

const emptyProfile = {
  phone: '', location: '', degree: '', university: '', graduation_year: '',
  experience_years: '', preferred_roles: '', preferred_technologies: '', career_goals: '',
}

export default function Profile() {
  const [profile, setProfile] = useState(emptyProfile)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    api.get('/profile/me').then((res) => {
      setProfile({ ...emptyProfile, ...res.data })
      setLoading(false)
    })
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setMessage('')
    try {
      const payload = {
        ...profile,
        graduation_year: profile.graduation_year ? Number(profile.graduation_year) : null,
        experience_years: profile.experience_years ? Number(profile.experience_years) : null,
      }
      const res = await api.put('/profile/me', payload)
      setProfile({ ...emptyProfile, ...res.data })
      setMessage('Profile saved.')
    } catch (err) {
      setMessage('Could not save profile.')
    } finally {
      setSaving(false)
    }
  }

  function update(field, value) {
    setProfile((p) => ({ ...p, [field]: value }))
  }

  if (loading) return <Loading label="Loading profile..." />

  return (
    <div className="page">
      <h1>Career Profile</h1>
      <p className="page-subtitle">This information is used across resume analysis, job matching, and the AI Copilot.</p>
      {message && <div className="alert-success">{message}</div>}
      <form className="form-card" onSubmit={handleSubmit}>
        <div className="form-grid">
          <div>
            <label>Phone</label>
            <input value={profile.phone || ''} onChange={(e) => update('phone', e.target.value)} />
          </div>
          <div>
            <label>Location</label>
            <input value={profile.location || ''} onChange={(e) => update('location', e.target.value)} />
          </div>
          <div>
            <label>Degree</label>
            <input value={profile.degree || ''} onChange={(e) => update('degree', e.target.value)} />
          </div>
          <div>
            <label>University</label>
            <input value={profile.university || ''} onChange={(e) => update('university', e.target.value)} />
          </div>
          <div>
            <label>Graduation year</label>
            <input type="number" value={profile.graduation_year || ''} onChange={(e) => update('graduation_year', e.target.value)} />
          </div>
          <div>
            <label>Years of experience</label>
            <input type="number" value={profile.experience_years || ''} onChange={(e) => update('experience_years', e.target.value)} />
          </div>
          <div className="span-2">
            <label>Preferred roles</label>
            <input value={profile.preferred_roles || ''} onChange={(e) => update('preferred_roles', e.target.value)} placeholder="e.g. Backend Engineer, Full-stack Developer" />
          </div>
          <div className="span-2">
            <label>Preferred technologies</label>
            <input value={profile.preferred_technologies || ''} onChange={(e) => update('preferred_technologies', e.target.value)} placeholder="e.g. Python, FastAPI, React" />
          </div>
          <div className="span-2">
            <label>Career goals</label>
            <textarea rows={3} value={profile.career_goals || ''} onChange={(e) => update('career_goals', e.target.value)} />
          </div>
        </div>
        <button type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save profile'}</button>
      </form>
    </div>
  )
}
