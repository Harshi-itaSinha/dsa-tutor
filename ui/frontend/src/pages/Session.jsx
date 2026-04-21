import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchSession } from '../api'

function ProblemCard({ sessionName, problem }) {
  const { slot, title, difficulty, tags, is_stub, notes, platform } = problem
  const conf = notes?.confidence ? parseInt(notes.confidence) : 0

  const diffClass = difficulty?.toLowerCase().includes('easy') ? 'easy' :
    difficulty?.toLowerCase().includes('hard') ? 'hard' : 'medium'

  return (
    <Link to={`/session/${sessionName}/${slot}`} style={{ textDecoration: 'none' }}>
      <div style={{
        background: '#161b22', border: '1px solid #30363d', borderRadius: 8,
        padding: 20, transition: 'border-color 0.15s, transform 0.1s',
        cursor: 'pointer', height: '100%',
      }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = '#58a6ff'; e.currentTarget.style.transform = 'translateY(-2px)' }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = '#30363d'; e.currentTarget.style.transform = 'none' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
          <span style={{ color: '#8b949e', fontSize: 12, fontWeight: 700, textTransform: 'uppercase' }}>{slot}</span>
          {is_stub && <span className="badge badge-stub">STUB</span>}
          {!is_stub && difficulty && <span className={`badge badge-${diffClass}`}>{difficulty}</span>}
        </div>
        <div style={{ color: '#f0f6fc', fontSize: 15, fontWeight: 600, marginBottom: 8 }}>
          {is_stub ? 'Problem TBD' : title}
        </div>
        {tags && <div style={{ color: '#8b949e', fontSize: 12, marginBottom: 8 }}>{tags}</div>}
        {platform && <span className="badge badge-platform" style={{ marginRight: 6 }}>{platform}</span>}
        {conf > 0 && (
          <div style={{ marginTop: 8, color: '#d29922', fontSize: 14, letterSpacing: 2 }}>
            {'★'.repeat(conf)}{'☆'.repeat(5 - conf)}
          </div>
        )}
      </div>
    </Link>
  )
}

export default function Session() {
  const { name } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSession(name).then(d => { setData(d); setLoading(false) }).catch(() => setLoading(false))
  }, [name])

  if (loading) return <div style={{ padding: 40, color: '#8b949e' }}>Loading session...</div>
  if (!data || data.error) return <div style={{ padding: 40, color: '#f85149' }}>Session not found</div>

  return (
    <div style={{ padding: '24px 32px', maxWidth: 1000, margin: '0 auto', width: '100%' }}>
      <div style={{ marginBottom: 20 }}>
        <Link to="/" style={{ color: '#8b949e', fontSize: 13 }}>&larr; Dashboard</Link>
      </div>
      <h2 style={{ color: '#f0f6fc', marginBottom: 4, fontSize: 20 }}>{name}</h2>
      <div style={{ color: '#8b949e', fontSize: 13, marginBottom: 24 }}>
        {data.problems.length} problems &middot; Click a problem to open the editor
      </div>

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
        gap: 16,
      }}>
        {data.problems.map(p => (
          <ProblemCard key={p.filename} sessionName={name} problem={p} />
        ))}
      </div>
    </div>
  )
}
