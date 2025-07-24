// src/App.jsx

import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import Sidebar from './components/Sidebar';
import Header from './components/Header';

// Page components
import Dashboard from './pages/Dashboard';
import FinancialAnalysis from './pages/FinancialAnalysis';
import RiskAssessment from './pages/RiskAssessment';
import OperationalEfficiency from './pages/OperationalEfficiency';
import DemoGraphic from './pages/DemoGraphic';
import Customer_Insight from './pages/CustomerInsights';
import Reports from './pages/Reports';

export default function App() {
  const [points, setPoints] = useState(1); // Global AI usage points

  return (
    <div className="flex h-screen">
      <Sidebar />

      <div className="flex-1 flex flex-col bg-[#0b0d17]">
        {/* Header gets points to display them */}
        <Header points={points} />

        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route
              path="/financial-analysis"
              element={<FinancialAnalysis points={points} setPoints={setPoints} />}
            />
            <Route
              path="/risk-assessment"
              element={<RiskAssessment points={points} setPoints={setPoints} />}
            />
            <Route
              path="/operational-efficiency"
              element={<OperationalEfficiency points={points} setPoints={setPoints} />}
            />
            <Route
              path="/demographic"
              element={<DemoGraphic points={points} setPoints={setPoints} />}
            />
            <Route
              path="/CustomerInsights"
              element={<Customer_Insight points={points} setPoints={setPoints} />}
            />
            <Route
              path="/reports"
              element={<Reports points={points} setPoints={setPoints} />}
            />
            <Route path="*" element={<h2 className="p-8 text-white">Page Not Found</h2>} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
