import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'

import Sidebar from './components/Sidebar'
import Header  from './components/Header'

// our page stubs
import Dashboard         from './pages/Dashboard'
import FinancialAnalysis from './pages/FinancialAnalysis'
import RiskAssessment    from './pages/RiskAssessment'
import Performance       from './pages/Performance'
import AnalyticsPage     from './pages/Analytics'
import Reports           from './pages/Reports'

export default function App() {
  return (
    <div className="flex h-screen">
      <Sidebar />

      <div className="flex-1 flex flex-col bg-[#0b0d17]">
        <Header />

        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard"          element={<Dashboard />} />
            <Route path="/financial-analysis" element={<FinancialAnalysis />} />
            <Route path="/risk-assessment"    element={<RiskAssessment />} />
            <Route path="/performance"        element={<Performance />} />
            <Route path="/analytics"          element={<AnalyticsPage />} />
            <Route path="/reports"            element={<Reports />} />
            <Route path="*" element={<h2 className="p-8 text-white">Page Not Found</h2>} />
          </Routes>
        </main>
      </div>
    </div>
  )
}