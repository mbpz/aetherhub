import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Header from './components/Header'
import ProtectedRoute from './components/ProtectedRoute'
import { ToastContainer } from './components/Toast'

import LoginPage from './pages/LoginPage'
import AuthCallbackPage from './pages/AuthCallbackPage'
import SkillSquarePage from './pages/SkillSquarePage'
import SkillDetailPage from './pages/SkillDetailPage'
import MySkillsPage from './pages/MySkillsPage'
import UploadSkillPage from './pages/UploadSkillPage'

function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        {children}
      </main>
      <footer className="bg-white border-t border-gray-200 py-6 text-center text-sm text-gray-400">
        © 2026 AetherHub · 大模型技能管理平台
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/skills" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />

        <Route path="/skills" element={<Layout><SkillSquarePage /></Layout>} />
        <Route path="/skills/upload" element={
          <ProtectedRoute>
            <Layout><UploadSkillPage /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/skills/:id" element={<Layout><SkillDetailPage /></Layout>} />

        <Route path="/mine" element={
          <ProtectedRoute>
            <Layout><MySkillsPage /></Layout>
          </ProtectedRoute>
        } />

        <Route path="*" element={<Navigate to="/skills" replace />} />
      </Routes>
      <ToastContainer />
    </BrowserRouter>
  )
}
