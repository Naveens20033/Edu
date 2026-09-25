import { useCallback, useEffect, useState } from 'react'
import { api, getApiError } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'

export default function FacultyHistoryPage() {
  const { user, logout } = useAuth()
  const [sessions, setSessions] = useState([])
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [page, setPage] = useState(1)
  const [count, setCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reload, setReload] = useState(0)

  const load = useCallback(() => {
    let active = true
    setLoading(true)
    setError('')
    const params = { page }
    if (from) params.from = from
    if (to) params.to = to
    api.get('/attendance/faculty-history/', { params }).then(({ data }) => {
      if (active) { setSessions(data.results || []); setCount(data.count || 0) }
    }).catch((requestError) => { if (active) setError(getApiError(requestError, 'Could not load class history.')) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [from, to, page, reload])

  useEffect(() => load(), [load])

  return <main className="attendance-shell">
    <header className="workspace-header"><a className="workspace-brand" href="/attendance"><span className="brand-mark small">A</span><span>Attend<span className="brand-light">ance</span></span></a><div className="workspace-user"><span className="user-avatar">{user?.first_name?.[0] || user?.username?.[0] || 'F'}</span><span className="user-name">{user?.first_name || user?.username}</span><a className="header-link" href="/attendance">Record attendance</a><button className="logout-button" onClick={logout} type="button">Sign out</button></div></header>
    <section className="attendance-content"><div className="page-heading"><div><p className="eyebrow">FACULTY WORKSPACE</p><h1>Attendance history</h1><p className="intro">Review sessions for your assigned classes.</p></div></div>
      <section className="roster-card history-card"><form className="history-filters" onSubmit={(event) => event.preventDefault()}><label>From<input type="date" value={from} onChange={(event) => { setFrom(event.target.value); setPage(1) }} /></label><label>To<input type="date" value={to} onChange={(event) => { setTo(event.target.value); setPage(1) }} /></label><button type="button" className="bulk-button" onClick={() => { setFrom(''); setTo(''); setPage(1) }}>Clear filters</button><span className="history-count">{count} sessions</span></form>
        <div className="student-table-wrap"><table className="student-table"><thead><tr><th>DATE</th><th>SUBJECT</th><th>SECTION</th><th>ATTENDANCE</th><th>ROSTER</th></tr></thead><tbody>{loading && <tr><td colSpan="5" className="table-empty">Loading history…</td></tr>}{!loading && sessions.map((session) => <tr key={session.id}><td>{session.date}</td><td><b>{session.subject_code}</b> · {session.subject_name}</td><td>{session.section_name}</td><td>{session.records.filter((record) => record.status === 'PRESENT').length} present · {session.records.filter((record) => record.status === 'ABSENT').length} absent</td><td><a className="request-link" href={`/attendance/sessions/${session.id}`}>View {session.record_count} students</a></td></tr>)}{!loading && sessions.length === 0 && <tr><td colSpan="5" className="table-empty">No sessions found for these filters.</td></tr>}</tbody></table></div>
        <div className="history-pagination"><button className="bulk-button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)} type="button">Previous</button><span>Page {page}</span><button className="bulk-button" disabled={page * 25 >= count} onClick={() => setPage((current) => current + 1)} type="button">Next</button></div>
      </section>{error && <div className="notice error-notice" role="alert"><span>{error}</span><button className="retry-button" onClick={() => { setLoading(true); setReload((value) => value + 1) }} type="button">Try again</button></div>}
    </section>
  </main>
}
