import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import CodeMirror from '@uiw/react-codemirror'
import { cpp } from '@codemirror/lang-cpp'
import { fetchProblem, saveCode, runTests, fetchFromUrl } from '../api'

function Toast({ message, type, onClose }) {
  useEffect(() => { const t = setTimeout(onClose, 3000); return () => clearTimeout(t) }, [onClose])
  return <div className={`toast toast-${type}`}>{message}</div>
}

function TestResult({ test }) {
  const colors = { pass: '#3fb950', fail: '#f85149', tle: '#d29922', error: '#f85149', info: '#8b949e', summary: '#58a6ff' }
  const icons = { pass: '✓', fail: '✗', tle: '⏱', error: '✗', info: '●', summary: '─' }
  return (
    <div style={{ padding: '3px 0' }}>
      <div style={{ color: colors[test.status] || '#8b949e', fontFamily: 'var(--mono)', fontSize: 13 }}>
        {icons[test.status] || ''} {test.line}
      </div>
      {test.details?.map((d, i) => (
        <div key={i} style={{ color: '#8b949e', fontFamily: 'var(--mono)', fontSize: 12, paddingLeft: 24 }}>
          {d}
        </div>
      ))}
    </div>
  )
}

export default function Editor() {
  const { name, slot } = useParams()
  const navigate = useNavigate()
  const [problem, setProblem] = useState(null)
  const [allProblems, setAllProblems] = useState([])
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [running, setRunning] = useState(false)
  const [testResults, setTestResults] = useState(null)
  const [toast, setToast] = useState(null)
  const [showTier1, setShowTier1] = useState(false)
  const [showTier2, setShowTier2] = useState(false)
  const [fetchUrl, setFetchUrl] = useState('')
  const [fetching, setFetching] = useState(false)
  const [notes, setNotes] = useState({ approach: '', edge_cases: '', confidence: '' })
  const autoSaveRef = useRef(null)

  useEffect(() => {
    setLoading(true)
    fetchProblem(name, slot).then(d => {
      if (d.problem) {
        setProblem(d.problem)
        setCode(d.problem.code || '')
        setNotes({
          approach: d.problem.notes?.approach || '',
          edge_cases: d.problem.notes?.edge_cases || '',
          confidence: d.problem.notes?.confidence || '',
        })
      }
      setAllProblems(d.all_problems || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [name, slot])

  // auto-save every 60s
  useEffect(() => {
    autoSaveRef.current = setInterval(() => {
      if (problem?.filepath && code) {
        saveCode(problem.filepath, code, notes).catch(() => {})
      }
    }, 60000)
    return () => clearInterval(autoSaveRef.current)
  }, [problem, code, notes])

  const handleSave = useCallback(async () => {
    if (!problem?.filepath) return
    setSaving(true)
    try {
      await saveCode(problem.filepath, code, notes)
      setToast({ message: 'Saved!', type: 'success' })
    } catch {
      setToast({ message: 'Save failed', type: 'error' })
    }
    setSaving(false)
  }, [problem, code, notes])

  const handleRun = useCallback(async () => {
    if (!problem?.filepath) return
    setRunning(true)
    setTestResults(null)
    try {
      const res = await runTests(problem.filepath, code, notes)
      setTestResults(res)
      if (res.ok) {
        setToast({ message: `${res.summary?.passed || 0}/${res.summary?.total || 0} passed`, type: res.summary?.passed === res.summary?.total ? 'success' : 'error' })
      } else {
        setToast({ message: res.error || 'Run failed', type: 'error' })
      }
    } catch (e) {
      setToast({ message: e.message, type: 'error' })
    }
    setRunning(false)
  }, [problem, code, notes])

  const handleFetch = async () => {
    if (!fetchUrl || !problem?.filepath) return
    setFetching(true)
    try {
      const res = await fetchFromUrl(problem.filepath, fetchUrl)
      if (res.ok) {
        setToast({ message: 'Problem fetched! Reloading...', type: 'success' })
        setTimeout(() => window.location.reload(), 1000)
      } else {
        setToast({ message: res.error || 'Fetch failed', type: 'error' })
      }
    } catch (e) {
      setToast({ message: e.message, type: 'error' })
    }
    setFetching(false)
  }

  // keyboard shortcut: Cmd+S to save, Cmd+Enter to run
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') { e.preventDefault(); handleSave() }
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); handleRun() }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [handleSave, handleRun])

  if (loading) return <div style={{ padding: 40, color: '#8b949e' }}>Loading editor...</div>
  if (!problem) return <div style={{ padding: 40, color: '#f85149' }}>Problem not found</div>

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 48px)', overflow: 'hidden' }}>
      {/* Sidebar — problem list */}
      <div style={{
        width: 130, background: '#161b22', borderRight: '1px solid #30363d',
        padding: '12px 0', flexShrink: 0, overflow: 'auto',
      }}>
        <Link to={`/session/${name}`} style={{ display: 'block', padding: '6px 16px', fontSize: 12, color: '#8b949e' }}>
          &larr; Back
        </Link>
        <div style={{ borderTop: '1px solid #30363d', margin: '8px 0' }} />
        {allProblems.map(p => (
          <div key={p.filename}
            onClick={() => navigate(`/session/${name}/${p.slot}`)}
            style={{
              padding: '8px 16px', cursor: 'pointer', fontSize: 13,
              background: p.slot === slot ? '#21262d' : 'transparent',
              borderLeft: p.slot === slot ? '2px solid #58a6ff' : '2px solid transparent',
              color: p.slot === slot ? '#f0f6fc' : '#8b949e',
              transition: 'all 0.1s',
            }}
            onMouseEnter={e => { if (p.slot !== slot) e.currentTarget.style.background = '#1c2128' }}
            onMouseLeave={e => { if (p.slot !== slot) e.currentTarget.style.background = 'transparent' }}>
            <div style={{ fontWeight: 600, textTransform: 'uppercase' }}>{p.slot}</div>
            <div style={{ fontSize: 11, color: '#8b949e', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {p.is_stub ? 'TBD' : p.title}
            </div>
            {p.confidence && <div style={{ fontSize: 11, color: '#d29922' }}>{'★'.repeat(parseInt(p.confidence))}</div>}
          </div>
        ))}
      </div>

      {/* Problem panel */}
      <div style={{
        width: '38%', minWidth: 280, borderRight: '1px solid #30363d',
        overflow: 'auto', padding: 20, flexShrink: 0,
      }}>
        {/* Title + badges */}
        <h2 style={{ color: '#f0f6fc', fontSize: 17, marginBottom: 8 }}>{problem.title}</h2>
        <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
          {problem.difficulty && (
            <span className={`badge badge-${problem.difficulty.toLowerCase().includes('easy') ? 'easy' : problem.difficulty.toLowerCase().includes('hard') ? 'hard' : 'medium'}`}>
              {problem.difficulty}
            </span>
          )}
          {problem.platform && <span className="badge badge-platform">{problem.platform}</span>}
          {problem.is_stub && <span className="badge badge-stub">STUB</span>}
        </div>
        {problem.tags && <div style={{ color: '#8b949e', fontSize: 12, marginBottom: 16 }}>{problem.tags}</div>}
        {problem.url && <a href={problem.url} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>Open on platform &rarr;</a>}

        {/* Fetch from URL (for stubs) */}
        {problem.is_stub && (
          <div style={{ background: '#21262d', borderRadius: 8, padding: 12, marginTop: 16 }}>
            <div style={{ fontSize: 12, color: '#8b949e', marginBottom: 6 }}>Fetch problem from URL</div>
            <div style={{ display: 'flex', gap: 8 }}>
              <input value={fetchUrl} onChange={e => setFetchUrl(e.target.value)}
                placeholder="https://leetcode.com/problems/..."
                style={{ flex: 1, fontSize: 12 }} />
              <button onClick={handleFetch} disabled={fetching} style={{ fontSize: 12, padding: '4px 12px' }}>
                {fetching ? '...' : 'Fetch'}
              </button>
            </div>
          </div>
        )}

        {/* Problem statement */}
        {problem.statement && (
          <div style={{ marginTop: 20 }}>
            <h4 style={{ color: '#f0f6fc', fontSize: 13, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>Problem Statement</h4>
            <pre style={{
              color: '#c9d1d9', fontSize: 13, lineHeight: 1.6, whiteSpace: 'pre-wrap',
              fontFamily: 'var(--font)', background: '#0d1117', borderRadius: 8, padding: 16,
              border: '1px solid #21262d', maxHeight: 300, overflow: 'auto',
            }}>{problem.statement}</pre>
          </div>
        )}

        {/* Hints */}
        <div style={{ marginTop: 16 }}>
          <button onClick={() => setShowTier1(!showTier1)}
            style={{ width: '100%', textAlign: 'left', padding: '8px 12px', marginBottom: 8, fontSize: 13, background: showTier1 ? '#1c2128' : '#161b22' }}>
            {showTier1 ? '▾' : '▸'} Tier 1 Hint — Nudge
          </button>
          {showTier1 && (
            <pre style={{ color: '#d29922', fontSize: 13, padding: '8px 12px', whiteSpace: 'pre-wrap', fontFamily: 'var(--font)', marginBottom: 8 }}>
              {problem.tier1 || 'No hint available'}
            </pre>
          )}

          <button onClick={() => setShowTier2(!showTier2)}
            style={{ width: '100%', textAlign: 'left', padding: '8px 12px', fontSize: 13, background: showTier2 ? '#1c2128' : '#161b22' }}>
            {showTier2 ? '▾' : '▸'} Tier 2 Hint — Approach
          </button>
          {showTier2 && (
            <pre style={{ color: '#f85149', fontSize: 13, padding: '8px 12px', whiteSpace: 'pre-wrap', fontFamily: 'var(--font)' }}>
              {problem.tier2 || 'No hint available'}
            </pre>
          )}
        </div>

        {/* Notes */}
        <div style={{ marginTop: 20, borderTop: '1px solid #30363d', paddingTop: 16 }}>
          <h4 style={{ color: '#f0f6fc', fontSize: 13, marginBottom: 12, textTransform: 'uppercase', letterSpacing: 0.5 }}>Your Notes</h4>

          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 12, color: '#8b949e', display: 'block', marginBottom: 4 }}>Confidence</label>
            <div style={{ display: 'flex', gap: 4 }}>
              {[1, 2, 3, 4, 5].map(n => (
                <button key={n} onClick={() => setNotes({ ...notes, confidence: String(n) })}
                  style={{
                    width: 36, height: 36, padding: 0, fontSize: 18, borderRadius: 6,
                    background: parseInt(notes.confidence) >= n ? '#4d2600' : '#21262d',
                    color: parseInt(notes.confidence) >= n ? '#d29922' : '#30363d',
                    border: parseInt(notes.confidence) >= n ? '1px solid #d29922' : '1px solid #30363d',
                  }}>
                  ★
                </button>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 12, color: '#8b949e', display: 'block', marginBottom: 4 }}>Approach tried</label>
            <textarea value={notes.approach} onChange={e => setNotes({ ...notes, approach: e.target.value })}
              rows={2} style={{ width: '100%', resize: 'vertical' }} />
          </div>

          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 12, color: '#8b949e', display: 'block', marginBottom: 4 }}>Edge cases missed</label>
            <textarea value={notes.edge_cases} onChange={e => setNotes({ ...notes, edge_cases: e.target.value })}
              rows={2} style={{ width: '100%', resize: 'vertical' }} />
          </div>

          <button onClick={handleSave} disabled={saving} style={{ fontSize: 12 }}>
            {saving ? 'Saving...' : 'Save Notes'}
          </button>
        </div>
      </div>

      {/* Code panel */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Toolbar */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px',
          background: '#161b22', borderBottom: '1px solid #30363d',
        }}>
          <span style={{ color: '#8b949e', fontSize: 12, fontFamily: 'var(--mono)', flex: 1 }}>
            {problem.filename}
          </span>
          <span style={{ color: '#30363d', fontSize: 11 }}>Cmd+S save &middot; Cmd+Enter run</span>
          <button onClick={handleSave} disabled={saving} style={{ fontSize: 12, padding: '4px 12px' }}>
            {saving ? '...' : '💾 Save'}
          </button>
          <button className="btn-green" onClick={handleRun} disabled={running}
            style={{ fontSize: 13, padding: '4px 16px' }}>
            {running ? '⏳ Running...' : '▶ Run Tests'}
          </button>
        </div>

        {/* Code editor */}
        <div style={{ flex: 1, overflow: 'auto' }}>
          <CodeMirror
            value={code}
            onChange={setCode}
            extensions={[cpp()]}
            theme="dark"
            height="100%"
            style={{ height: '100%', fontSize: 14 }}
            basicSetup={{
              lineNumbers: true,
              foldGutter: true,
              highlightActiveLine: true,
              bracketMatching: true,
              autocompletion: true,
              tabSize: 4,
              indentUnit: 4,
            }}
          />
        </div>

        {/* Test results */}
        <div style={{
          height: testResults ? 220 : 40, background: '#0d1117',
          borderTop: '1px solid #30363d', overflow: 'auto', padding: '8px 16px',
          transition: 'height 0.2s',
        }}>
          {!testResults ? (
            <div style={{ color: '#8b949e', fontSize: 13 }}>Test results will appear here after running</div>
          ) : !testResults.ok ? (
            <div style={{ color: '#f85149', fontSize: 13, fontFamily: 'var(--mono)' }}>
              Error: {testResults.error}
            </div>
          ) : (
            <div>
              {testResults.summary && (
                <div style={{
                  fontSize: 14, fontWeight: 700, marginBottom: 8,
                  color: testResults.summary.passed === testResults.summary.total ? '#3fb950' : '#f85149',
                }}>
                  {testResults.summary.passed}/{testResults.summary.total} tests passed
                  {testResults.summary.passed === testResults.summary.total && ' ✓'}
                </div>
              )}
              {testResults.tests?.map((t, i) => <TestResult key={i} test={t} />)}
            </div>
          )}
        </div>
      </div>

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  )
}
