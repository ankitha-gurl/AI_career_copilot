import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const links = [
  ['/dashboard', 'Dashboard'],
  ['/profile', 'Profile'],
  ['/resume', 'Resume'],
  ['/jobs', 'Jobs'],
  ['/skills', 'Skills'],
  ['/roadmap', 'Roadmap'],
  ['/interview', 'Interview'],
  ['/copilot', 'Copilot'],
]

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  if (!user) return null

  return (
    <nav className="navbar">
      <div className="navbar-brand">AI Career Copilot</div>
      <div className="navbar-links">
        {links.map(([path, label]) => (
          <Link key={path} to={path}>{label}</Link>
        ))}
      </div>
      <div className="navbar-user">
        <span>{user.full_name}</span>
        <button onClick={() => { logout(); navigate('/login') }}>Logout</button>
      </div>
    </nav>
  )
}
