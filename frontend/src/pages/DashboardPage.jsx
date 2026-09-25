import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, getApiError } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'

function Metric({ label, value, hint }) {
  return <article className="metric-card"><span>{label}</span><strong>{value ?? '—'}</strong>{hint && <small>{hint}</small>}</article>
}

function formatRate(value) {
  return value == null ? 'No attendance recorded' : `${value}%`
}

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [threshold, setThreshold] = useState('')
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState('')
  const [reload, setReload] = useState(0)

  useEffect(() => {
    let active = true
    api.get('/dashboard/').then(({ data: result }) => {
      if (active) { setData(result); setThreshold(String(result.threshold || 75)) }
    }).catch((requestError) => { if (active) setError(getApiError(requestError, 'Could not load the dashboard.')) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [reload])

  function retryDashboard() {
    setError('')
    setLoading(true)
    setReload((value) => value + 1)
  }

  async function saveThreshold(event) {
    event.preventDefault()
    setSaving(true)
    setNotice('')
    setError('')
    try {
      const { data: result } = await api.patch('/settings/attendance-threshold/', { attendance_threshold: Number(threshold) })
      setThreshold(String(result.attendance_threshold))
      setNotice('Attendance threshold updated.')
      const refreshed = await api.get('/dashboard/')
      setData(refreshed.data)
    } catch (requestError) {
      setError(getApiError(requestError, 'Threshold could not be updated.'))
    } finally { setSaving(false) }
  }

  const role = data?.role || user?.role
  const title = role === 'ADMIN' ? 'College overview' : role === 'FACULTY' ? 'Faculty overview' : 'My attendance'

  return <main className="attendance-shell"><header className="workspace-header"><Link className="workspace-brand" to="/dashboard"><span className="brand-mark small">A</span><span>Attend<span className="brand-light">ance</span></span></Link><div className="workspace-user"><span className="user-avatar">{user?.first_name?.[0] || user?.username?.[0] || 'A'}</span><span className="user-name">{user?.first_name || user?.username}</span>{role === 'FACULTY' && <Link className="header-link" to="/attendance">Record</Link>}{role === 'FACULTY' && <Link className="header-link" to="/attendance/history">History</Link>}{role === 'STUDENT' && <Link className="header-link" to="/student/history">History</Link>}{role === 'ADMIN' && <Link className="header-link" to="/corrections">Corrections</Link>}{role === 'ADMIN' && <Link className="header-link" to="/attendance/history">Sessions</Link>}<button className="logout-button" onClick={logout} type="button">Sign out</button></div></header>
    <section className="attendance-content dashboard-content"><div className="page-heading"><div><p className="eyebrow">{role || 'CAMPUS'} DASHBOARD</p><h1>{title}</h1><p className="intro">A clear view of attendance activity and follow-up needs.</p></div></div>
      {loading && <p className="table-empty">Loading your dashboard…</p>}{error && <div className="notice error-notice" role="alert"><span>{error}</span><button className="retry-button" onClick={retryDashboard} type="button">Try again</button></div>}{notice && <p className="notice success-notice" role="status">{notice}</p>}
      {data && role === 'ADMIN' && <>
        <div className="metrics-grid"><Metric label="Students" value={data.total_students.toLocaleString()} /><Metric label="Faculty" value={data.total_faculty.toLocaleString()} /><Metric label="Departments" value={data.total_departments} /><Metric label="Subjects" value={data.total_subjects} /></div>
        <div className="dashboard-grid"><section className="roster-card dashboard-panel"><div className="panel-heading"><h2>Today’s attendance</h2><span>{data.today.sessions} sessions</span></div><div className="attendance-rate">{formatRate(data.today.percentage)}</div><p className="panel-caption">{data.today.present_records} present from {data.today.total_records} recorded student marks.</p><div className="panel-divider" /><div className="panel-heading"><h3>Below threshold</h3><span className="warning-number">{data.low_attendance_count}</span></div><p className="panel-caption">Students below the current {data.threshold}% attendance requirement.</p><Link className="panel-link" to="/reports/low-attendance">View low-attendance report →</Link></section>
          <section className="roster-card dashboard-panel"><div className="panel-heading"><h2>Recent sessions</h2><Link className="panel-link" to="/attendance/history">View all →</Link></div>{data.recent_sessions.length ? <div className="compact-list">{data.recent_sessions.map((item) => <div className="compact-row" key={item.id}><span><b>{item.subject__code}</b> · {item.subject__name}<small>{item.section__name} · {item.faculty__name}</small></span><time>{item.date}</time></div>)}</div> : <p className="table-empty">No sessions have been recorded yet.</p>}</section></div>
        <section className="roster-card trend-panel"><div className="panel-heading"><h2>Recent attendance trend</h2><span>By recorded class date</span></div><div className="trend-bars">{data.attendance_trend.map((item) => <div className="trend-column" key={item.date}><span>{item.percentage}%</span><div className="trend-track"><i style={{ height: `${item.percentage}%` }} /></div><time>{item.date.slice(5)}</time></div>)}</div></section>
        <form className="threshold-form roster-card" onSubmit={saveThreshold}><div><h2>Attendance threshold</h2><p>Students below this percentage are flagged in reports.</p></div><label><span className="sr-only">Threshold percent</span><input max="100" min="1" onChange={(event) => setThreshold(event.target.value)} required type="number" value={threshold} /><span>%</span></label><button className="submit-button" disabled={saving} type="submit">{saving ? 'Saving…' : 'Save threshold'}</button></form>
      </>}
      {data && role === 'FACULTY' && <><div className="metrics-grid faculty-metrics"><Metric label="Teaching assignments" value={data.assignments} /><Metric label="Sections" value={data.sections} /><Metric label="Sessions today" value={data.today_sessions} /><Metric label="Low-attendance students" value={(data.low_attendance || []).length} hint="Across your assigned classes" /></div><div className="dashboard-grid"><section className="roster-card dashboard-panel"><div className="panel-heading"><h2>Assigned classes</h2><Link className="panel-link" to="/attendance">Take attendance →</Link></div>{(data.assigned_classes || []).length ? <div className="compact-list">{data.assigned_classes.map((item) => <div className="compact-row" key={item.assignment_id}><span><b>{item.subject_code}</b> · {item.subject_name}<small>Section {item.section_name}</small></span><Link className="panel-link" to="/attendance">Record</Link></div>)}</div> : <p className="table-empty">No teaching assignments are set up yet.</p>}</section><section className="roster-card dashboard-panel"><div className="panel-heading"><h2>Low attendance</h2><Link className="panel-link" to="/reports/low-attendance">View report →</Link></div>{(data.low_attendance || []).length ? <div className="compact-list">{data.low_attendance.map((item) => <div className="compact-row" key={`${item.student_id}-${item.subject_code}`}><span><b>{item.student_name}</b><small>{item.student_id} · {item.subject_code} · {item.section_name}</small></span><span className="warning-number">{item.percentage}%</span></div>)}</div> : <p className="table-empty">No students are below the threshold in your classes.</p>}</section></div></>}
      {data && role === 'STUDENT' && <><div className="student-overview"><section className="roster-card student-rate-card"><span className="rate-label">OVERALL ATTENDANCE</span><strong>{formatRate(data.summary.percentage)}</strong><p>{data.summary.present_count} present of {data.summary.total_classes} recorded classes</p>{data.summary.percentage != null && data.summary.percentage < data.threshold && <span className="warning-banner">Below required {data.threshold}% attendance</span>}</section><div className="student-mini-metrics"><Metric label="Present" value={data.summary.present_count} /><Metric label="Absent" value={data.summary.absent_count} /><Metric label="Subjects" value={data.subjects.length} /></div></div><div className="dashboard-grid"><section className="roster-card dashboard-panel"><div className="panel-heading"><h2>Subject-wise attendance</h2><Link className="panel-link" to="/student/history">Full history →</Link></div>{data.subjects.length ? <div className="subject-list">{data.subjects.map((item) => <div className="subject-row" key={item.subject_id}><div><b>{item.subject_code}</b><span>{item.subject_name}</span></div><div className="subject-rate"><strong className={item.below_threshold ? 'below-rate' : ''}>{formatRate(item.percentage)}</strong><small>{item.present_count}/{item.total_classes} classes</small></div></div>)}</div> : <p className="table-empty">No attendance has been recorded yet.</p>}</section><section className="roster-card dashboard-panel"><div className="panel-heading"><h2>Recent attendance</h2><Link className="panel-link" to="/student/history">View history →</Link></div>{data.recent_attendance.length ? <div className="compact-list">{data.recent_attendance.map((item, index) => <div className="compact-row" key={`${item.date}-${item.subject_code}-${index}`}><span><b>{item.subject_code}</b> · {item.subject_name}<small>{item.date}</small></span><span className={`history-status ${item.status === 'PRESENT' ? 'history-present' : 'history-absent'}`}>{item.status}</span></div>)}</div> : <p className="table-empty">No recent classes to show.</p>}</section></div></>}
    </section>
  </main>
}
