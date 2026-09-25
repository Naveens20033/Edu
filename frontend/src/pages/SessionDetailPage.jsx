import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, getApiError } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'

export default function SessionDetailPage() {
  const { sessionId } = useParams()
  const { user, logout } = useAuth()
  const [session, setSession] = useState(null)
  const [error, setError] = useState('')
  const [reload, setReload] = useState(0)
  const [requestRecord, setRequestRecord] = useState(null)
  const [reason, setReason] = useState('')
  const [notice, setNotice] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let active = true
    setError('')
    api.get(`/attendance/sessions/${sessionId}/`).then(({ data }) => { if (active) setSession(data) })
      .catch((requestError) => { if (active) setError(getApiError(requestError, 'Could not load this session.')) })
    return () => { active = false }
  }, [sessionId, reload])

  async function submitCorrection(record) {
    setSubmitting(true)
    setError('')
    setNotice('')
    try {
      await api.post('/corrections/', {
        attendance_record_id: record.id,
        requested_status: record.status === 'PRESENT' ? 'ABSENT' : 'PRESENT',
        reason: reason.trim(),
      })
      setNotice(`Correction request submitted for ${record.student_name}.`)
      setRequestRecord(null)
      setReason('')
    } catch (requestError) {
      setError(getApiError(requestError, 'Correction request could not be submitted.'))
    } finally { setSubmitting(false) }
  }

  return (
    <main className="attendance-shell">
      <header className="workspace-header"><Link className="workspace-brand" to="/attendance/history"><span className="brand-mark small">A</span><span>Attend<span className="brand-light">ance</span></span></Link><div className="workspace-user"><span className="user-avatar">{user?.first_name?.[0] || user?.username?.[0] || 'F'}</span><span className="user-name">{user?.first_name || user?.username}</span><button className="logout-button" onClick={logout} type="button">Sign out</button></div></header>
      <section className="attendance-content">
        <p className="back-link"><Link to="/attendance/history">← Back to history</Link></p>
        {error && <div className="notice error-notice" role="alert"><span>{error}</span><button className="retry-button" onClick={() => setReload((value) => value + 1)} type="button">Try again</button></div>}
        {notice && <p className="notice success-notice" role="status">{notice}</p>}
        {!session && !error && <p className="table-empty" role="status">Loading session…</p>}
        {session && <>
          <div className="page-heading"><div><p className="eyebrow">{session.date} · {session.section_name}</p><h1>{session.subject_code} · {session.subject_name}</h1><p className="intro">Recorded by {session.faculty_name} · {session.record_count} students</p></div></div>
          <section className="roster-card"><div className="student-table-wrap"><table className="student-table"><thead><tr><th>STUDENT</th><th>STUDENT ID</th><th>STATUS</th>{user?.role === 'FACULTY' && <th>ACTION</th>}</tr></thead><tbody>
            {session.records.map((record) => <tr key={record.id}><td>{record.student_name}</td><td>{record.student_id}</td><td><span className={`history-status ${record.status === 'PRESENT' ? 'history-present' : 'history-absent'}`}>{record.status}</span></td>{user?.role === 'FACULTY' && <td><button className="request-link" onClick={() => { setRequestRecord(requestRecord === record.id ? null : record.id); setReason('') }} type="button">Request correction</button>{requestRecord === record.id && <div className="correction-inline"><input aria-label={`Reason for correction for ${record.student_name}`} minLength="10" onChange={(event) => setReason(event.target.value)} placeholder="Explain the requested change" value={reason} /><button className="submit-button" disabled={submitting || reason.trim().length < 10} onClick={() => submitCorrection(record)} type="button">{submitting ? 'Sending…' : 'Send request'}</button></div>}</td>}</tr>)}
          </tbody></table></div></section>
        </>}
      </section>
    </main>
  )
}
