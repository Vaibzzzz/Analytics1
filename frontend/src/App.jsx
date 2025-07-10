// src/App.jsx

import React, { useEffect, useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'

import Sidebar from './components/Sidebar'
import Header  from './components/Header'

// our page stubs
import Dashboard             from './pages/Dashboard'
import FinancialAnalysis     from './pages/FinancialAnalysis'
import RiskAssessment        from './pages/RiskAssessment'
import OperationalEfficiency from './pages/OperationalEfficiency'
import DemoGraphic           from './pages/DemoGraphic'
import Customer_Insight      from './pages/CustomerInsights'
import Reports               from './pages/Reports'

export default function App() {
  // A rolling key we bump every X ms to force remount of all pages
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    // refresh every 5 minutes (300,000 ms)
    const id = setInterval(() => {
      setRefreshKey(k => k + 1)
    }, 3 * 60 * 1000)

    return () => clearInterval(id)
  }, [])

  return (
    // Using `key={refreshKey}` here makes React unmount & remount
    // everything inside whenever refreshKey changes
    <div className="flex h-screen" key={refreshKey}>
      <Sidebar />

      <div className="flex-1 flex flex-col bg-[#0b0d17]">
        <Header />

        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard"           element={<Dashboard />} />
            <Route path="/financial-analysis"  element={<FinancialAnalysis />} />
            <Route path="/risk-assessment"     element={<RiskAssessment />} />
            <Route path="/operational-efficiency" element={<OperationalEfficiency />} />
            <Route path="/demographic"         element={<DemoGraphic />} />
            <Route path="/CustomerInsights"    element={<Customer_Insight />} />
            <Route path="/reports"             element={<Reports />} />
            <Route path="*" element={<h2 className="p-8 text-white">Page Not Found</h2>} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
