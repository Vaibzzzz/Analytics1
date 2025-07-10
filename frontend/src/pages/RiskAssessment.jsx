import React, { useEffect, useState } from 'react'
import axios from 'axios'
import ReactECharts from 'echarts-for-react'

const filterOptions = ['YTD', 'MTD', 'Weekly', 'Daily', 'Monthly', 'Yesterday', 'Today', 'custom']

export default function RiskAndFraud() {
  const [data, setData]       = useState({ metrics: [], charts: [] })
  const [loading, setLoading] = useState(true)
  const [filter, setFilter]   = useState(() => localStorage.getItem('rf_filter') || 'YTD')
  const [start, setStart]     = useState(() => localStorage.getItem('rf_start') || '')
  const [end, setEnd]         = useState(() => localStorage.getItem('rf_end') || '')

  useEffect(() => {
    fetchData()
  }, [filter, start, end])

  const fetchData = async () => {
    setLoading(true)
    try {
      const params = { filter_type: filter }
      if (filter === 'custom' && start && end) {
        params.start = start
        params.end = end
      }

      const res = await axios.get('http://localhost:8001/api/risk-and-fraud', { params })
      setData(res.data)
    } catch (err) {
      console.error('Error fetching risk & fraud data:', err)
    } finally {
      setLoading(false)
    }
  }

  const buildBarOption = (chart) => ({
    title: {
      text: chart.title,
      left: 'center',
      textStyle: { color: '#fff' }
    },
    tooltip: { trigger: 'axis', formatter: '{b}: {c}%' },
    xAxis: {
      type: 'category',
      data: chart.x,
      axisLabel: { color: '#fff', rotate: 20 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#fff', formatter: '{value}%' }
    },
    series: [{
      data: chart.y,
      type: 'bar',
      barWidth: '50%',
      itemStyle: { color: '#f97316' }
    }],
    backgroundColor: '#111827'
  })

  if (loading) return <div className="text-white p-8">Loading…</div>

  return (
    <div className="p-8 space-y-6">
      {/* Filter Controls */}
      <div className="flex items-center space-x-4 mb-4">
        <select
          className="bg-[#1f2937] text-white border border-gray-600 px-3 py-2 rounded text-sm"
          value={filter}
          onChange={e => {
            const val = e.target.value
            setFilter(val)
            localStorage.setItem('rf_filter', val)
            if (val !== 'custom') {
              setStart('')
              setEnd('')
              localStorage.removeItem('rf_start')
              localStorage.removeItem('rf_end')
            }
          }}
        >
          {filterOptions.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>

        {filter === 'custom' && (
          <>
            <input
              type="date"
              value={start}
              onChange={e => {
                setStart(e.target.value)
                localStorage.setItem('rf_start', e.target.value)
              }}
              className="bg-[#1f2937] text-white border border-gray-600 rounded px-2 py-1"
            />
            <span className="text-white">to</span>
            <input
              type="date"
              value={end}
              onChange={e => {
                setEnd(e.target.value)
                localStorage.setItem('rf_end', e.target.value)
              }}
              className="bg-[#1f2937] text-white border border-gray-600 rounded px-2 py-1"
            />
          </>
        )}
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-5">
        {data.metrics.map((m, i) => (
          <div
            key={i}
            className="bg-[#111827] p-6 rounded-lg min-h-[140px] flex flex-col justify-center"
          >
            <div className="text-gray-400 text-sm mb-2">{m.title}</div>
            <div className="text-white text-3xl font-semibold">{m.value}</div>
            {m.diff != null && (
              <div className={`text-sm mt-2 ${m.diff >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {m.diff >= 0 ? '+' : ''}{m.diff}% vs previous
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {data.charts.map((chart, idx) => (
          <div key={idx} className="bg-[#111827] p-4 rounded-lg">
            <ReactECharts
              option={buildBarOption(chart)}
              style={{ height: '350px', width: '100%' }}
            />
          </div>
        ))}
      </div>
    </div>
  )
}

