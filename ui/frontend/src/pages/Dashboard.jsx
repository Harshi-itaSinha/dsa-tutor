import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { fetchDashboard, startSession } from '../api'

function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: '#161b22', border: '1px solid #30363d', borderRadius: 8,
      padding: '16px 20px', flex: '1 1 0', minWidth: 140,
    }}>
      <div style={{ fontSize: 28, fontWeight: 700, color: color || '#f0f6fc' }}>{value}</div>
      <div style={{ color: '#8b949e', fontSize: 13, marginTop: 4 }}>{label}</div>
    </div>
  )
}

function ComfortBar({ pattern, comfort, comfort_pct, attempted, solved, priority }) {
  const barColor = priority === 'HIGH' ? '#f85149' : comfort_pct >= 70 ? '#3fb950' : '#58a6ff'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '6px 0' }}>
      <div style={{ width: 180, fontSize: 13, color: '#c9d1d9', flexShrink: 0 }}>{pattern}</div>
      <div style={{ flex: 1, background: '#21262d', borderRadius: 4, height: 16, overflow: 'hidden' }}>
        <div style={{
          width: `${Math.max(comfort_pct, 2)}%`, background: barColor,
          height: '100%', borderRadius: 4, transition: 'width 0.3s',
        }} />
      </div>
      <div style={{ width: 40, textAlign: 'right', fontSize: 13, color: '#8b949e' }}>{comfort}</div>
      <div style={{ width: 50, fontSize: 12, color: '#8b949e' }}>{solved}/{attempted}</div>
      {priority === 'HIGH' && <span className="badge badge-high">HIGH</span>}
      {priority === 'LOW' && <span className="badge badge-low">LOW</span>}
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [form, setForm] = useState({ type: 'practice', company_topic: '', duration: 60, num_problems: 4 })
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchDashboard().then(d => { setData(d); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const handleStart = async () => {
    setCreating(true)
    setError('')
    try {
      const res = await startSession(form)
      if (res.ok) {
        navigate(`/session/${res.session_name}`)
      } else {
        setError(res.error || 'Failed to create session')
      }
    } catch (e) {
      setError(e.message)
    }
    setCreating(false)
  }

  if (loading) return <div style={{ padding: 40, color: '#8b949e' }}>Loading...</div>
  if (!data) return <div style={{ padding: 40, color: '#f85149' }}>Failed to load dashboard</div>

  const { sessions, patterns, stats } = data

  return (
    <div style={{ padding: '24px 32px', maxWidth: 1100, margin: '0 auto', width: '100%' }}>
      {/* Stats row */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
        <StatCard label="Sessions" value={stats.session_count} />
        <StatCard label="Problems Loaded" value={stats.problems_loaded} />
        <StatCard label="HIGH Priority Topics" value={stats.high_priority} color="#f85149" />
      </div>

      {/* Start session */}
      <div style={{ marginBottom: 24 }}>
        {!formOpen ? (
          <button className="btn-primary" onClick={() => setFormOpen(true)}
            style={{ fontSize: 15, padding: '10px 24px' }}>
            + Start New Session
          </button>
        ) : (
          <div style={{
            background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 20,
          }}>
            <h3 style={{ color: '#f0f6fc', marginBottom: 16, fontSize: 16 }}>Start New Session</h3>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, color: '#8b949e', marginBottom: 4 }}>Type</label>
                <select value={form.type} onChange={e => setForm({ ...form, type: e.target.value })}
                  style={{ width: 140 }}>
                  <option value="practice">Practice</option>
                  <option value="contest">Contest</option>
                  <option value="doubt">Doubt</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, color: '#8b949e', marginBottom: 4 }}>
                  {form.type === 'contest' ? 'Company' : 'Topic'}
                </label>
                <input value={form.company_topic} onChange={e => setForm({ ...form, company_topic: e.target.value })}
                  placeholder={form.type === 'contest' ? 'e.g. Google' : 'e.g. dp'}
                  style={{ width: 180 }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, color: '#8b949e', marginBottom: 4 }}>Duration</label>
                <input type="number" value={form.duration}
                  onChange={e => setForm({ ...form, duration: parseInt(e.target.value) || 60 })}
                  style={{ width: 80 }} />
              </div>
              {form.type === 'practice' && (
                <div>
                  <label style={{ display: 'block', fontSize: 12, color: '#8b949e', marginBottom: 4 }}>Problems</label>
                  <input type="number" value={form.num_problems}
                    onChange={e => setForm({ ...form, num_problems: parseInt(e.target.value) || 4 })}
                    style={{ width: 60 }} />
                </div>
              )}
              <button className="btn-green" onClick={handleStart} disabled={creating}
                style={{ height: 34 }}>
                {creating ? 'Creating...' : 'Start'}
              </button>
              <button onClick={() => setFormOpen(false)} style={{ height: 34 }}>Cancel</button>
            </div>
            {error && <div style={{ color: '#f85149', marginTop: 12, fontSize: 13 }}>{error}</div>}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: 24 }}>
        {/* Sessions list */}
        <div style={{ flex: '1 1 45%' }}>
          <h3 style={{ color: '#f0f6fc', marginBottom: 12, fontSize: 15 }}>Recent Sessions</h3>
          {sessions.length === 0 ? (
            <div style={{ color: '#8b949e', fontSize: 13 }}>No sessions yet. Start one above!</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {sessions.map(s => (
                <Link key={s.name} to={`/session/${s.name}`} style={{ textDecoration: 'none' }}>
                  <div style={{
                    background: '#161b22', border: '1px solid #30363d', borderRadius: 8,
                    padding: '12px 16px', transition: 'border-color 0.15s',
                  }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = '#58a6ff'}
                    onMouseLeave={e => e.currentTarget.style.borderColor = '#30363d'}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <span className={`badge badge-${s.type === 'contest' ? 'medium' : s.type === 'doubt' ? 'hard' : 'easy'}`}
                          style={{ marginRight: 8 }}>{s.type}</span>
                        <span style={{ color: '#f0f6fc', fontSize: 14 }}>{s.name}</span>
                      </div>
                      <span style={{ color: '#8b949e', fontSize: 12 }}>{s.problem_count} problems</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Comfort scores */}
        <div style={{ flex: '1 1 55%' }}>
          <h3 style={{ color: '#f0f6fc', marginBottom: 12, fontSize: 15 }}>Topic Comfort Scores</h3>
          <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16 }}>
            {patterns.map(p => <ComfortBar key={p.pattern} {...p} />)}
          </div>
        </div>
      </div>
    </div>
  )
}
