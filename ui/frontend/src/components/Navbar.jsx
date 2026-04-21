import { Link, useLocation } from 'react-router-dom'

const style = {
  nav: {
    background: '#161b22',
    borderBottom: '1px solid #30363d',
    padding: '0 24px',
    height: 48,
    display: 'flex',
    alignItems: 'center',
    gap: 24,
  },
  logo: {
    color: '#f0f6fc',
    fontSize: 16,
    fontWeight: 700,
    textDecoration: 'none',
    letterSpacing: -0.5,
  },
  link: {
    color: '#8b949e',
    textDecoration: 'none',
    fontSize: 14,
  },
  active: {
    color: '#f0f6fc',
  },
}

export default function Navbar() {
  const location = useLocation()
  const isHome = location.pathname === '/'

  return (
    <nav style={style.nav}>
      <Link to="/" style={style.logo}>DSA Tutor</Link>
      <Link to="/" style={{ ...style.link, ...(isHome ? style.active : {}) }}>Dashboard</Link>
    </nav>
  )
}
