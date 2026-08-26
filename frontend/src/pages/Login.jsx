import { useState } from 'react'
import { login } from '../api.js'

const MOCK_USERS = [
  { label: 'Northstar Logistics (Customer)', username: 'northstar_user', password: 'northstar123' },
  { label: 'LumenWorks (Customer)', username: 'lumenworks_user', password: 'lumen123' },
  { label: 'Support Agent (Internal)', username: 'support_agent', password: 'internal123' },
]

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await login(username, password)
      onLogin(data)
    } catch {
      setError('Invalid username or password')
    } finally {
      setLoading(false)
    }
  }

  const fillUser = (user) => {
    setUsername(user.username)
    setPassword(user.password)
    setError('')
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.logo}>
          <span style={styles.logoIcon}>📦</span>
          <h1 style={styles.title}>ParcelPilot</h1>
          <p style={styles.subtitle}>Support Agent</p>
        </div>

        <div style={styles.quickLogin}>
          <p style={styles.quickLabel}>Quick login</p>
          <div style={styles.quickButtons}>
            {MOCK_USERS.map((u) => (
              <button key={u.username} style={styles.quickBtn} onClick={() => fillUser(u)}>
                {u.label}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleLogin} style={styles.form}>
          <input
            style={styles.input}
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            style={styles.input}
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p style={styles.error}>{error}</p>}
          <button style={styles.loginBtn} type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    background: '#0f1117',
  },
  card: {
    background: '#1a1d27',
    border: '1px solid #2a2d3e',
    borderRadius: '16px',
    padding: '40px',
    width: '420px',
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  logo: {
    textAlign: 'center',
  },
  logoIcon: {
    fontSize: '40px',
  },
  title: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#fff',
    marginTop: '8px',
  },
  subtitle: {
    color: '#6b7280',
    fontSize: '14px',
    marginTop: '4px',
  },
  quickLabel: {
    fontSize: '12px',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginBottom: '8px',
  },
  quickButtons: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  quickBtn: {
    background: '#242736',
    border: '1px solid #2a2d3e',
    borderRadius: '8px',
    color: '#a0aec0',
    padding: '10px 14px',
    cursor: 'pointer',
    fontSize: '13px',
    textAlign: 'left',
    transition: 'all 0.15s',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  input: {
    background: '#242736',
    border: '1px solid #2a2d3e',
    borderRadius: '8px',
    color: '#e2e8f0',
    padding: '12px 14px',
    fontSize: '14px',
    outline: 'none',
  },
  error: {
    color: '#fc8181',
    fontSize: '13px',
  },
  loginBtn: {
    background: '#4f46e5',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    padding: '12px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    marginTop: '4px',
  },
}