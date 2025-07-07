import React, { useEffect, useState } from 'react'
import axios from 'axios'
import ReactECharts from 'echarts-for-react'

export default function FinancialAnalysis() {
  const [data, setData]       = useState({ metrics: [], charts: [] })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('http://localhost:8001/api/financial-analysis')
      .then(res => {
        setData(res.data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error fetching financial analysis data:', err)
      })
  }, [])

  if (loading) {
    return <div className="text-white p-8">Loading…</div>
  }

  const { metrics, charts } = data

  // Build ECharts option for each chart
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
      orient: 'horizontal',
      bottom: 10,
      textStyle: { color: '#fff' },
      data: chart.data.map(d => d.name)
    },
    series: [{
      name: chart.title,
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
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

  return (
    <div className="p-8 space-y-6">
      {/* 1) Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-5">
        {metrics.map((m, i) => (
          <div
            key={i}
            className="bg-[#111827] p-6 rounded-lg min-h-[140px] flex flex-col justify-center"
          >
            <div className="text-gray-400 text-sm mb-2">{m.title}</div>
            <div className="text-white text-3xl font-semibold">{m.value}</div>
          </div>
        ))}
      </div>

      {/* 2) Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {charts.map((c, idx) => (
          <div key={idx} className="bg-[#111827] p-4 rounded-lg">
            {c.type === 'pie' && (
              <ReactECharts
                option={buildPieOption(c)}
                style={{ height: '350px', width: '100%' }}
              />
            )}
            {/* If you later add bar charts, you can check for c.type==='bar' here */}
          </div>
        ))}
      </div>
    </div>
  )
}