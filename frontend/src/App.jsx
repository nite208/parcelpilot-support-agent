import { Routes, Route, Navigate } from 'react-router-dom'
import { useState } from 'react'
import Login from './pages/Login.jsx'
import Chat from './pages/Chat.jsx'

export default function App() {
  const [session, setSession] = useState(null)

  const handleLogin = (data) => {
    setSession(data)
  }

  const handleLogout = () => {
    setSession(null)
  }

  return (
    <Routes>
      <Route
        path="/"
        element={session ? <Navigate to="/chat" /> : <Login onLogin={handleLogin} />}
      />
      <Route
        path="/chat"
        element={session ? <Chat session={session} onLogout={handleLogout} /> : <Navigate to="/" />}
      />
    </Routes>
  )
}