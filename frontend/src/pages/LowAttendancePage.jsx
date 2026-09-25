import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, getApiError } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'

export default function LowAttendancePage() {
  const { user, logout } = useAuth()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [reload, setReload] = useState(0)
  const isStudent = user?.role === 'STUDENT'
  const isFaculty = user?.role === 'FACULTY'
  const includeSubject = isFaculty || user?.role === 'ADMIN' || user?.is_superuser

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    api.get('/reports/low-attendance/', { params: { page } })
      .then(({ data }) => { if (active) setReport(data) })
      .catch((requestError) => { if (active) setError(getApiError(requestError, 'Could not load the low-attendance report.')) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [page, reload])

  function retry() {
    setLoading(true)
    setError('')
    setReload((value) => value + 1)
  }

  return (
    <main className="attendance-shell">
      <header className="workspace-header">
        <Link className="workspace-brand" to="/dashboard"><span className="brand-mark small">A</span><span>Attend<span className="brand-light">ance</span></span></Link>
        <div className="workspace-user"><span className="user-avatar">{user?.first_name?.[0] || user?.username?.[0] || 'A'}</span><span className="user-name">{user?.first_name || user?.username}</span><button className="logout-button" onClick={logout} type="button">Sign out</button></div>
      </header>
      <section className="attendance-content">
        <div className="page-heading"><div><p className="eyebrow">REPORTS</p><h1>{isStudent ? 'Attendance warnings' : 'Low-attendance report'}</h1><p className="intro">{isStudent ? 'Subjects where your attendance is below the current requirement.' : 'Students below the threshold in your accessible classes.'}</p></div></div>
        {loading && <p className="table-empty" role="status">Loading report…</p>}
        {error && <div className="notice error-notice" role="alert"><span>{error}</span><button className="retry-button" onClick={retry} type="button">Try again</button></div>}
        {report && <section className="roster-card">
          <div className="roster-summary"><span>Required threshold <b>{report.threshold}%</b></span><span>Records below <b>{report.count}</b></span></div>
          <div className="student-table-wrap"><table className="student-table">
            <thead><tr>{isStudent ? <><th>SUBJECT</th><th>ATTENDED</th><th>ATTENDANCE</th></> : <><th>STUDENT</th>{includeSubject && <th>SUBJECT</th>}<th>SECTION</th><th>ATTENDED</th><th>ATTENDANCE</th></>}</tr></thead>
            <tbody>
              {report.results.map((item, index) => <tr key={`${item.student_id || ''}-${item.subject_code || ''}-${index}`}>
                {isStudent ? <><td><b>{item.subject_code}</b> · {item.subject_name}</td><td>{item.present_count} / {item.total_classes}</td><td><span className="warning-number">{item.percentage}%</span></td></> : <>
                  <td><b>{item.student_name}</b><small className="table-subtext">{item.student_id}</small></td>
                  {includeSubject && <td><b>{item.subject_code}</b> · {item.subject_name}</td>}
                  <td>{item.section_name}</td><td>{item.present_count} / {item.total_classes}</td><td><span className="warning-number">{item.percentage}%</span></td>
                </>}
              </tr>)}
              {report.results.length === 0 && <tr><td colSpan={isStudent ? 3 : includeSubject ? 5 : 4} className="table-empty">No low-attendance records at this time.</td></tr>}
            </tbody>
          </table></div>
          {report.count > 50 && <div className="history-pagination"><button className="bulk-button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)} type="button">Previous</button><span>Page {page}</span><button className="bulk-button" disabled={page * 50 >= report.count} onClick={() => setPage((current) => current + 1)} type="button">Next</button></div>}
        </section>}
        <p className="back-link"><Link to="/dashboard">← Back to dashboard</Link></p>
      </section>
    </main>
  )
}
