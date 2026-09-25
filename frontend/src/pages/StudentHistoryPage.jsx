import { useCallback, useEffect, useState } from 'react'
import { api, getApiError } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'

export default function StudentHistoryPage() {
  const { user, logout } = useAuth()
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [requesting, setRequesting] = useState(null)
  const [reason, setReason] = useState('')
  const [notice, setNotice] = useState('')
  const [reload, setReload] = useState(0)
  const [page, setPage] = useState(1)
  const [count, setCount] = useState(0)

  const loadHistory = useCallback(() => {
    let active = true
    setLoading(true)
    setError('')
    const params = {}
    params.page = page
    if (from) params.from = from
    if (to) params.to = to
    api.get('/attendance/history/', { params }).then(({ data }) => {
      if (active) { setSessions(data.results || []); setCount(data.count || 0) }
    }).catch((requestError) => {
      if (active) setError(getApiError(requestError, 'Could not load your attendance history.'))
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [from, to, reload, page])

  useEffect(() => loadHistory(), [loadHistory])

  async function submitCorrection(record) {
    if (!reason.trim()) return
    setError('')
    setNotice('')
    try {
      await api.post('/corrections/', {
        attendance_record_id: record.id,
        requested_status: record.status === 'PRESENT' ? 'ABSENT' : 'PRESENT',
        reason: reason.trim(),
      })
      setNotice('Correction request submitted for admin review.')
      setRequesting(null)
      setReason('')
    } catch (requestError) {
      setError(getApiError(requestError, 'Correction request could not be submitted.'))
    }
  }

  return (
    <main className="attendance-shell">
      <header className="workspace-header">
        <a className="workspace-brand" href="/dashboard"><span className="brand-mark small">A</span><span>Attend<span className="brand-light">ance</span></span></a>
        <div className="workspace-user"><span className="user-avatar">{user?.first_name?.[0] || user?.username?.[0] || 'S'}</span><span className="user-name">{user?.first_name || user?.username}</span><a className="header-link" href="/dashboard">Dashboard</a><button className="logout-button" onClick={logout} type="button">Sign out</button></div>
      </header>
      <section className="attendance-content">
        <div className="page-heading"><div><p className="eyebrow">STUDENT WORKSPACE</p><h1>My attendance</h1><p className="intro">Review your recorded attendance by subject and class date.</p></div></div>
        <section className="roster-card history-card">
          <div className="roster-heading"><div className="selection-title"><span className="step-number">✓</span><div><h2>Attendance history</h2><p>Only records associated with your account are shown.</p></div></div></div>
          <form className="history-filters" onSubmit={(event) => event.preventDefault()}><label>From<input type="date" value={from} onChange={(event) => { setFrom(event.target.value); setPage(1) }} /></label><label>To<input type="date" value={to} onChange={(event) => { setTo(event.target.value); setPage(1) }} /></label><button type="button" className="bulk-button" onClick={() => { setFrom(''); setTo(''); setPage(1) }}>Clear filters</button><span className="history-count">{count} sessions</span></form>
          <div className="student-table-wrap"><table className="student-table"><thead><tr><th>DATE</th><th>SUBJECT</th><th>SECTION</th><th>FACULTY</th><th>STATUS</th><th>ACTION</th></tr></thead><tbody>
            {loading && <tr><td className="table-empty" colSpan="6">Loading your history…</td></tr>}
            {!loading && sessions.flatMap((session) => session.records.map((record) => <tr key={record.id}><td>{session.date}</td><td><b>{session.subject_code}</b> · {session.subject_name}</td><td>{session.section_name}</td><td>{session.faculty_name}</td><td><span className={`history-status ${record.status === 'PRESENT' ? 'history-present' : 'history-absent'}`}>{record.status === 'PRESENT' ? 'Present' : 'Absent'}</span></td><td><button className="request-link" type="button" onClick={() => setRequesting(requesting === record.id ? null : record.id)}>Request correction</button>{requesting === record.id && <div className="correction-inline"><input aria-label="Reason for correction" minLength="10" onChange={(event) => setReason(event.target.value)} placeholder="Explain what should change" value={reason} /><button className="submit-button" type="button" disabled={reason.trim().length < 10} onClick={() => submitCorrection(record)}>Send request</button></div>}</td></tr>))}
            {!loading && sessions.length === 0 && <tr><td className="table-empty" colSpan="6">No attendance has been recorded for this period.</td></tr>}
          </tbody></table></div>
          {count > 25 && <div className="history-pagination"><button className="bulk-button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)} type="button">Previous</button><span>Page {page}</span><button className="bulk-button" disabled={page * 25 >= count} onClick={() => setPage((current) => current + 1)} type="button">Next</button></div>}
        </section>
        {error && <div className="notice error-notice" role="alert"><span>{error}</span><button className="retry-button" onClick={() => { setLoading(true); setReload((value) => value + 1) }} type="button">Try again</button></div>}
        {notice && <p className="notice success-notice" role="status">{notice}</p>}
      </section>
    </main>
  )
}
