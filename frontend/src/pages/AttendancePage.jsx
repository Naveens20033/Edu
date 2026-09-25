import { useEffect, useMemo, useState } from 'react'
import { api, getApiError } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'

function todayISO() {
  const now = new Date()
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 10)
}

export default function AttendancePage() {
  const { user, logout } = useAuth()
  const [assignments, setAssignments] = useState([])
  const [assignmentId, setAssignmentId] = useState('')
  const [date, setDate] = useState(todayISO())
  const [roster, setRoster] = useState([])
  const [marks, setMarks] = useState({})
  const [loadingAssignments, setLoadingAssignments] = useState(true)
  const [loadingRoster, setLoadingRoster] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [assignmentReload, setAssignmentReload] = useState(0)
  const [rosterReload, setRosterReload] = useState(0)
  const [saved, setSaved] = useState(false)

  const selected = useMemo(
    () => assignments.find((assignment) => String(assignment.id) === String(assignmentId)),
    [assignments, assignmentId],
  )
  const presentCount = roster.filter((student) => marks[student.id] === 'PRESENT').length
  const absentCount = roster.length - presentCount

  useEffect(() => {
    let active = true
    api.get('/assignments/').then(({ data }) => {
      const results = Array.isArray(data) ? data : data.results || []
      if (active) {
        setAssignments(results)
        if (results.length) setAssignmentId(String(results[0].id))
      }
    }).catch((requestError) => {
      if (active) setError(getApiError(requestError, 'Could not load your teaching assignments.'))
    }).finally(() => {
      if (active) setLoadingAssignments(false)
    })
    return () => { active = false }
  }, [assignmentReload])

  useEffect(() => {
    if (!selected) {
      setRoster([])
      setMarks({})
      return undefined
    }
    let active = true
    setLoadingRoster(true)
    setError('')
    setNotice('')
    setSaved(false)
    api.get(`/sections/${selected.section}/students/`).then(({ data }) => {
      const students = Array.isArray(data) ? data : data.results || []
      if (active) {
        setRoster(students)
        setMarks(Object.fromEntries(students.map((student) => [student.id, 'PRESENT'])))
      }
    }).catch((requestError) => {
      if (active) {
        setRoster([])
        setError(getApiError(requestError, 'Could not load the section roster.'))
      }
    }).finally(() => {
      if (active) setLoadingRoster(false)
    })
    return () => { active = false }
  }, [selected, rosterReload])

  function setAll(status) {
    setMarks(Object.fromEntries(roster.map((student) => [student.id, status])))
    setSaved(false)
    setNotice('')
  }

  function setStudentStatus(studentId, status) {
    setMarks((current) => ({ ...current, [studentId]: status }))
    setSaved(false)
    setNotice('')
  }

  async function submitAttendance(event) {
    event.preventDefault()
    if (!selected || roster.length === 0) return
    setSaving(true)
    setError('')
    setNotice('')
    try {
      await api.post('/attendance/sessions/', {
        assignment_id: selected.id,
        date,
        records: roster.map((student) => ({ student_id: student.id, status: marks[student.id] })),
      })
      setNotice('Attendance saved. Students can now view their records.')
      setSaved(true)
    } catch (requestError) {
      setError(getApiError(requestError, 'Attendance could not be saved. Review the list and try again.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <main className="attendance-shell">
      <header className="workspace-header">
        <a className="workspace-brand" href="/attendance"><span className="brand-mark small">A</span><span>Attend<span className="brand-light">ance</span></span></a>
        <div className="workspace-user"><span className="user-avatar">{user?.first_name?.[0] || user?.username?.[0] || 'F'}</span><span className="user-name">{user?.first_name || user?.username}</span><a className="header-link" href="/attendance/history">History</a>{user?.role === 'ADMIN' && <a className="header-link" href="/corrections">Corrections</a>}<button className="logout-button" onClick={logout} type="button">Sign out</button></div>
      </header>

      <section className="attendance-content">
        <div className="page-heading">
          <div><p className="eyebrow">FACULTY WORKSPACE</p><h1>Record attendance</h1><p className="intro">Mark today’s class and submit the completed roster.</p></div>
          <div className="date-pill"><span className="date-dot" /> Attendance entry</div>
        </div>

        <form onSubmit={submitAttendance}>
          <section className="selection-card">
            <div className="selection-title"><span className="step-number">1</span><div><h2>Class details</h2><p>Choose one of your assigned classes.</p></div></div>
            <div className="selection-fields">
              <div className="field-group class-field"><label htmlFor="assignment">Subject and section</label>
                <select disabled={loadingAssignments || assignments.length === 0} id="assignment" onChange={(event) => { setAssignmentId(event.target.value); setSaved(false); setNotice('') }} value={assignmentId}>
                  {loadingAssignments && <option value="">Loading assignments…</option>}
                  {!loadingAssignments && assignments.length === 0 && <option value="">No assignments available</option>}
                  {assignments.map((item) => <option key={item.id} value={item.id}>{item.subject_code} · {item.subject_name} — {item.department_code} {item.section_name}, Sem {item.semester}</option>)}
                </select>
              </div>
              <div className="field-group date-field"><label htmlFor="attendance-date">Class date</label><input id="attendance-date" max={todayISO()} onChange={(event) => { setDate(event.target.value); setSaved(false); setNotice('') }} required type="date" value={date} /></div>
            </div>
            {selected && <div className="class-meta"><span><b>{selected.academic_year}</b> academic year</span><span><b>Semester {selected.semester}</b></span><span><b>{roster.length}</b> students enrolled</span></div>}
          </section>

          <section className="roster-card">
            <div className="roster-heading"><div className="selection-title"><span className="step-number">2</span><div><h2>Student roster</h2><p>Students start as present. Change any status as needed.</p></div></div>
              <div className="bulk-actions"><button className="bulk-button" onClick={() => setAll('PRESENT')} type="button"><span className="status-dot present-dot" />Mark all present</button><button className="bulk-button" onClick={() => setAll('ABSENT')} type="button"><span className="status-dot absent-dot" />Mark all absent</button></div>
            </div>
            <div className="roster-summary"><span><b>{roster.length}</b> students</span><span className="summary-present"><b>{presentCount}</b> present</span><span className="summary-absent"><b>{absentCount}</b> absent</span></div>
            <div className="student-table-wrap">
              <table className="student-table"><thead><tr><th>STUDENT</th><th>STUDENT ID</th><th>ATTENDANCE STATUS</th></tr></thead>
                <tbody>
                  {loadingRoster && <tr><td className="table-empty" colSpan="3">Loading class roster…</td></tr>}
                  {!loadingRoster && roster.map((student) => <tr key={student.id}><td><div className="student-cell"><span className="student-avatar">{student.name.split(' ').map((part) => part[0]).slice(0, 2).join('')}</span><span className="student-name">{student.name}</span></div></td><td className="student-id">{student.student_id}</td><td><div className="status-control" role="group" aria-label={`Attendance for ${student.name}`}><button aria-pressed={marks[student.id] === 'PRESENT'} className={marks[student.id] === 'PRESENT' ? 'status-choice active present-choice' : 'status-choice'} onClick={() => setStudentStatus(student.id, 'PRESENT')} type="button">Present</button><button aria-pressed={marks[student.id] === 'ABSENT'} className={marks[student.id] === 'ABSENT' ? 'status-choice active absent-choice' : 'status-choice'} onClick={() => setStudentStatus(student.id, 'ABSENT')} type="button">Absent</button></div></td></tr>)}
                  {!loadingRoster && roster.length === 0 && <tr><td className="table-empty" colSpan="3">{selected ? 'No students are enrolled in this section yet.' : 'Select an assigned class to load its roster.'}</td></tr>}
                </tbody>
              </table>
            </div>
            <div className="submit-row"><span className="submit-hint">Please review the roster before submitting.</span><button className="submit-button" disabled={saving || saved || loadingRoster || roster.length === 0} type="submit">{saving ? 'Saving attendance…' : saved ? 'Attendance saved' : 'Review & submit'} <span aria-hidden="true">→</span></button></div>
          </section>
        </form>
        {error && <div className="notice error-notice" role="alert"><span>{error}</span>{selected ? <button className="retry-button" onClick={() => { setError(''); setRosterReload((value) => value + 1) }} type="button">Reload roster</button> : <button className="retry-button" onClick={() => { setError(''); setLoadingAssignments(true); setAssignmentReload((value) => value + 1) }} type="button">Reload assignments</button>}</div>}
        {notice && <p className="notice success-notice" role="status">{notice}</p>}
      </section>
    </main>
  )
}
