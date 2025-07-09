import React, { useEffect, useState } from 'react'
import axios from 'axios'
import ReactECharts from 'echarts-for-react'

const filterOptions = [
  'YTD', 'MTD', 'Weekly', 'Daily', 'Monthly', 'Yesterday', 'Today'
]

export default function FinancialAnalysis() {
  const [data, setData] = useState({ metrics: [], charts: [] })
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('YTD')

  useEffect(() => {
    fetchData(filter)
  }, [filter])

  const fetchData = async (filter_type) => {
    setLoading(true)
    try {
      const res = await axios.get(`http://localhost:8001/api/financial-performance?filter_type=${filter_type}`)
      setData(res.data)
    } catch (err) {
      console.error('Error fetching financial analysis data:', err)
    } finally {
      setLoading(false)
    }
  }

  const buildPieOption = (chart) => ({
    title: {
      text: chart.title,
      left: 'center',
      textStyle: { color: '#fff' }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {d}%'
    },
    legend: {
      bottom: 10,
      textStyle: { color: '#fff' },
      data: chart.data.map(d => d.name)
    },
    series: [{
      name: chart.title,
      type: 'pie',
      radius: ['40%', '70%'],
      label: {
        show: true,
        position: 'outside',
        formatter: '{b}: {d}%'
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      data: chart.data.map(d => ({ name: d.name, value: d.value }))
    }],
    backgroundColor: '#111827'
  })

  const buildBarOption = (chart) => ({
    title: {
      text: chart.title,
      left: 'center',
      textStyle: { color: '#fff' }
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: chart.x,
      axisLabel: { color: '#fff' }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#fff' }
    },
    series: [{
      data: chart.y,
      type: 'bar',
      itemStyle: {
        color: '#3b82f6' // Tailwind blue-500
      }
    }],
    grid: {
      left: '5%',
      right: '5%',
      bottom: '10%',
      containLabel: true
    },
    backgroundColor: '#111827'
  })

  if (loading) return <div className="text-white p-8">Loading…</div>

  return (
    <div className="p-8 space-y-6">
      {/* Filter dropdown */}
      <div className="mb-4 flex justify-end">
        <select
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="bg-[#1f2937] text-white border border-gray-600 rounded px-4 py-2"
        >
          {filterOptions.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
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
            {m.diff !== undefined && (
              <div className={`text-sm mt-2 ${m.diff >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {m.diff >= 0 ? '+' : ''}{m.diff}% vs previous
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {data.charts.map((chart, i) => (
          <div key={i} className="bg-[#111827] p-4 rounded-lg">
            {chart.type === 'pie' && (
              <ReactECharts option={buildPieOption(chart)} style={{ height: 350 }} />
            )}
            {chart.type === 'bar' && (
              <ReactECharts option={buildBarOption(chart)} style={{ height: 350 }} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
