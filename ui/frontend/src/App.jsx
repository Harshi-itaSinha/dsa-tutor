import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Session from './pages/Session'
import Editor from './pages/Editor'

function App() {
  return (
    <>
      <Navbar />
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/session/:name" element={<Session />} />
          <Route path="/session/:name/:slot" element={<Editor />} />
        </Routes>
      </main>
    </>
  )
}

export default App
