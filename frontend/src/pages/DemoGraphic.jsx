import React, { useEffect, useState } from 'react'
import axios from 'axios'
import ReactECharts from 'echarts-for-react'

export default function Demographic() {
  const [metrics, setMetrics] = useState([])
  const [charts, setCharts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDemographicData()
  }, [])

  const fetchDemographicData = async () => {
    setLoading(true)
    try {
      const res = await axios.get('http://localhost:8001/api/demographic')
      setMetrics(res.data.metrics || [])
      setCharts(res.data.charts || [])
    } catch (err) {
      console.error('Error fetching demographic data:', err)
    } finally {
      setLoading(false)
    }
  }

  const buildHorizontalBarOption = (chart) => ({
    title: {
      text: chart.title,
      left: 'center',
      textStyle: { color: '#fff' }
    },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: {
      left: 100,
      right: 30,
      top: 60,
      bottom: 40
    },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#888' } },
      axisLabel: { color: '#fff' }
    },
    yAxis: {
      type: 'category',
      data: chart.y,
      axisLine: { lineStyle: { color: '#888' } },
      axisLabel: { color: '#fff' }
    },
    series: chart.series.map((s) => ({
      name: s.name,
      type: 'bar',
      data: s.data,
      itemStyle: {
        borderRadius: [0, 5, 5, 0],
        color: '#3B82F6'
      },
      label: {
        show: true,
        position: 'right',
        color: '#fff'
      }
    })),
    backgroundColor: '#111827'
  })

  if (loading) return <div className="text-white p-8">Loading...</div>

  return (
    <div className="p-8 space-y-6">
      {/* Metrics */}
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

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {charts.map((chart, i) => (
          <div key={i} className="bg-[#111827] p-4 rounded-lg">
            {chart.type === 'horizontal_bar' && (
              <ReactECharts option={buildHorizontalBarOption(chart)} style={{ height: 500 }} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
