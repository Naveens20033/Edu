import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getApiError } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(username.trim(), password)
      navigate('/dashboard', { replace: true })
    } catch (requestError) {
      setError(getApiError(requestError, 'We could not sign you in. Check your details and try again.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-card" aria-labelledby="login-title">
        <div className="brand-mark" aria-hidden="true">A</div>
        <p className="eyebrow">CAMPUS PORTAL</p>
        <h1 id="login-title">Welcome back</h1>
        <p className="intro">Sign in to manage and review attendance.</p>
        <form onSubmit={handleSubmit}>
          <label htmlFor="username">Username or email</label>
          <input
            autoComplete="username"
            id="username"
            name="username"
            onChange={(event) => setUsername(event.target.value)}
            placeholder="you@college.edu or username"
            required
            value={username}
          />
          <label htmlFor="password">Password</label>
          <input
            autoComplete="current-password"
            id="password"
            name="password"
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter your password"
            required
            type="password"
            value={password}
          />
          {error && <p className="form-error" role="alert">{error}</p>}
          <button disabled={submitting} type="submit">{submitting ? 'Signing in…' : 'Sign in'} <span aria-hidden="true">→</span></button>
        </form>
        <p className="login-note">Use your college account to continue.</p>
      </section>
      <footer>SMART ATTENDANCE <span>•</span> COLLEGE MANAGEMENT</footer>
    </main>
  )
}
