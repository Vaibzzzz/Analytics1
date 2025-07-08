import React, { useEffect, useState } from 'react'
import axios from 'axios'
import ReactECharts from 'echarts-for-react'

const FILTER_OPTIONS = ['today', 'daily', 'yesterday', 'WEEKLY', 'MONTHLY', 'mtd', 'ytd', 'custom']

export default function OperationalEfficiency() {
  const [metrics, setMetrics] = useState([])
  const [charts, setCharts] = useState([])
  const [loading, setLoading] = useState(true)
  const [globalFilter, setGlobalFilter] = useState('ytd')

  useEffect(() => {
    fetchDashboardData(globalFilter)
  }, [globalFilter])

  const fetchDashboardData = async (filter) => {
    setLoading(true)
    try {
      const res = await axios.get('http://localhost:8001/api/operational-efficiency', {
        params: { range: filter }
      })
      setMetrics(res.data.metrics || [])
      setCharts(res.data.charts || [])
    } catch (err) {
      console.error('Error fetching data:', err)
    } finally {
      setLoading(false)
    }
  }

  const buildLineOption = (chart) => ({
    title: {
      text: chart.title,
      left: 'center',
      textStyle: { color: '#fff' }
    },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: chart.x,
      axisLabel: { color: '#fff' }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#fff' }
    },
    series: [
      {
        data: chart.y,
        type: 'line',
        smooth: true,
        areaStyle: {}
      }
    ],
    backgroundColor: '#111827'
  })

  const buildDoubleBarDualAxisOption = (chart) => ({
    title: {
      text: chart.title,
      left: 'center',
      textStyle: { color: '#fff' }
    },
    tooltip: { trigger: 'axis' },
    legend: {
      top: 30,
      textStyle: { color: '#fff' }
    },
    xAxis: {
      type: 'category',
      data: chart.x,
      axisLabel: { color: '#fff' }
    },
    yAxis: chart.yAxis.map(y => ({
      ...y,
      axisLabel: { color: '#fff' },
      splitLine: { show: false }
    })),
    series: chart.series,
    backgroundColor: '#111827'
  })

  const buildStackedBarOption = (chart) => ({
    title: {
      text: chart.title,
      left: 'center',
      textStyle: { color: '#fff' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      top: 30,
      textStyle: { color: '#fff' }
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
    series: chart.series.map(s => ({
      ...s,
      type: 'bar',
      stack: 'total',
      emphasis: { focus: 'series' }
    })),
    backgroundColor: '#111827'
  })

  const renderChartOption = (chart) => {
    if (chart.type === 'line') return buildLineOption(chart)
    if (chart.type === 'double_bar_dual_axis') return buildDoubleBarDualAxisOption(chart)
    if (chart.type === 'stacked_bar') return buildStackedBarOption(chart)
    return {}
  }

  if (loading) return <div className="text-white p-8">Loading…</div>

  return (
    <div className="p-8 space-y-6">
      {/* Global Filter Dropdown */}
      <div className="flex justify-start mb-4">
        <select
          className="bg-[#1f2937] text-white border border-gray-600 px-3 py-2 rounded text-sm"
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
        >
          {FILTER_OPTIONS.map(opt => (
            <option key={opt} value={opt}>
              {opt.replace(/_/g, ' ').toUpperCase()}
            </option>
          ))}
        </select>
      </div>

      {/* KPI Metrics with % change */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-5">
        {metrics.map((m, i) => (
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

      {/* KPI Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {charts.map((chart, idx) => (
          <div key={idx} className="bg-[#111827] p-4 rounded-lg">
            <ReactECharts
              option={renderChartOption(chart)}
              style={{ height: '350px', width: '100%' }}
            />
          </div>
        ))}
      </div>
    </div>
  )
}
