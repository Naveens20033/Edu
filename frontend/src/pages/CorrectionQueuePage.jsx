import { useCallback, useEffect, useState } from 'react'
import { api, getApiError } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'

export default function CorrectionQueuePage() {
  const { user, logout } = useAuth()
  const [items, setItems] = useState([])
  const [filter, setFilter] = useState('PENDING')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [comments, setComments] = useState({})
  const [busyId, setBusyId] = useState(null)
  const [reload, setReload] = useState(0)

  const load = useCallback(() => {
    let active = true
    setLoading(true)
    setError('')
    api.get('/corrections/', { params: filter ? { status: filter } : {} }).then(({ data }) => {
      if (active) setItems(data.results || [])
    }).catch((requestError) => {
      if (active) setError(getApiError(requestError, 'Could not load correction requests.'))
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [filter, reload])

  useEffect(() => load(), [load])

  async function review(item, decision) {
    setBusyId(item.id)
    setError('')
    setNotice('')
    try {
      await api.post(`/corrections/${item.id}/review/`, {
        decision,
        review_comment: comments[item.id] || '',
      })
      setNotice(`Request #${item.id} ${decision === 'APPROVE' ? 'approved' : 'rejected'}.`)
      load()
    } catch (requestError) {
      setError(getApiError(requestError, 'The request could not be reviewed.'))
    } finally {
      setBusyId(null)
    }
  }

  return <main className="attendance-shell">
    <header className="workspace-header"><a className="workspace-brand" href="/corrections"><span className="brand-mark small">A</span><span>Attend<span className="brand-light">ance</span></span></a><div className="workspace-user"><span className="user-avatar">{user?.first_name?.[0] || user?.username?.[0] || 'A'}</span><span className="user-name">{user?.first_name || user?.username}</span><button className="logout-button" onClick={logout} type="button">Sign out</button></div></header>
    <section className="attendance-content"><div className="page-heading"><div><p className="eyebrow">ADMINISTRATION</p><h1>Correction requests</h1><p className="intro">Review proposed changes while keeping the original attendance history auditable.</p></div></div>
      <section className="roster-card history-card"><div className="roster-heading"><div className="selection-title"><span className="step-number">{items.length}</span><div><h2>Request queue</h2><p>Approve a correction or reject it with a short explanation.</p></div></div><select className="correction-filter" value={filter} onChange={(event) => setFilter(event.target.value)}><option value="PENDING">Pending</option><option value="APPROVED">Approved</option><option value="REJECTED">Rejected</option><option value="">All requests</option></select></div>
        {loading ? <p className="table-empty">Loading requests…</p> : items.length === 0 ? <p className="table-empty">No requests in this queue.</p> : <div className="correction-list">{items.map((item) => <article className="correction-card" key={item.id}><div className="correction-topline"><div><span className="subject-kicker">{item.subject_code} · {item.session_date}</span><h3>{item.student_name} <span>({item.student_id})</span></h3></div><span className={`history-status ${item.status === 'PENDING' ? 'history-pending' : item.status === 'APPROVED' ? 'history-present' : 'history-absent'}`}>{item.status}</span></div><p className="correction-reason">“{item.reason}”</p><div className="correction-values"><span>Current: <b>{item.current_status}</b></span><span>Requested: <b>{item.requested_status}</b></span><span>Requested by: {item.requester_name}</span></div>{item.status === 'PENDING' ? <div className="review-controls"><input aria-label={`Review comment for request ${item.id}`} onChange={(event) => setComments((current) => ({ ...current, [item.id]: event.target.value }))} placeholder="Review comment (required to reject)" value={comments[item.id] || ''} /><button className="approve-button" disabled={busyId === item.id} onClick={() => review(item, 'APPROVE')} type="button">Approve</button><button className="reject-button" disabled={busyId === item.id || !(comments[item.id] || '').trim()} onClick={() => review(item, 'REJECT')} type="button">Reject</button></div> : <p className="reviewed-note">Reviewed by {item.reviewer_name || 'admin'} · {item.review_comment || 'No comment'}</p>}</article>)}</div>}
      </section>
      {error && <div className="notice error-notice" role="alert"><span>{error}</span><button className="retry-button" onClick={() => { setLoading(true); setReload((value) => value + 1) }} type="button">Try again</button></div>}{notice && <p className="notice success-notice" role="status">{notice}</p>}
    </section>
  </main>
}
