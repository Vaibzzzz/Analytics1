import React, { useEffect, useState, useRef } from 'react'
import axios from 'axios'
import ReactECharts from 'echarts-for-react'
import * as echarts from 'echarts'
import usaJson from '../usa.json'  // ✅ Add usa.json import

const filterOptions = [
  'YTD', 'MTD', 'Monthly', 'Weekly', 'Daily', 'Yesterday', 'Today', 'custom'
]

export default function Demographic() {
  const [metrics, setMetrics] = useState([])
  const [charts, setCharts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('YTD')
  const [customStart, setCustomStart] = useState('')
  const [customEnd, setCustomEnd] = useState('')
  const [insights, setInsights] = useState({})
  const [loadingInsightId, setLoadingInsightId] = useState(null)

  useEffect(() => {
    fetchDemographicData()
  }, [filter, customStart, customEnd])

  const fetchDemographicData = async () => {
    setLoading(true)
    try {
      const params = { filter_type: filter }
      if (filter === 'custom' && customStart && customEnd) {
        params.start = customStart
        params.end = customEnd
      }
      const res = await axios.get('http://localhost:8001/api/demographic', { params })
      setMetrics(res.data.metrics || [])
      setCharts(res.data.charts || [])
      setInsights({})
    } catch (err) {
      console.error('Error fetching demographic data:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchInsight = async (chart, i) => {
    setLoadingInsightId(i)
    try {
      const params = { filter_type: filter, chart_title: chart.title }
      if (filter === 'custom' && customStart && customEnd) {
        params.start = customStart
        params.end = customEnd
      }
      const res = await axios.get('http://localhost:8001/api/demographic/insight', { params })
      setInsights(prev => ({ ...prev, [i]: res.data.insight }))
    } catch (err) {
      console.error('Error fetching insight:', err)
      setInsights(prev => ({ ...prev, [i]: 'Failed to generate insight.' }))
    } finally {
      setLoadingInsightId(null)
    }
  }

  const buildBarOption = chart => ({
    title: { text: chart.title, left: 'center', textStyle: { color: '#fff' } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'category', data: chart.x, axisLabel: { color: '#fff' }, axisLine: { lineStyle: { color: '#888' } } },
    yAxis: { type: 'value', axisLabel: { color: '#fff' }, axisLine: { lineStyle: { color: '#888' } } },
    series: [{ data: chart.y, type: 'bar', itemStyle: { color: '#3B82F6', borderRadius: [5,5,0,0] }, label: { show: true, position: 'top', color: '#fff' } }],
    backgroundColor: '#111827'
  })

  const buildHorizontalBarOption = chart => ({
    title: { text: chart.title, left: 'center', textStyle: { color: '#fff' } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 100, right: 30, top: 60, bottom: 40 },
    xAxis: { type: 'value', axisLine: { lineStyle: { color: '#888' } }, axisLabel: { color: '#fff' } },
    yAxis: { type: 'category', data: chart.y, axisLine: { lineStyle: { color: '#888' } }, axisLabel: { color: '#fff' } },
    series: chart.series.map(s => ({ name: s.name, type: 'bar', data: s.data, itemStyle: { borderRadius: [0,5,5,0], color: '#3B82F6' }, label: { show: true, position: 'right', color: '#fff' } })),
    backgroundColor: '#111827'
  })

  const buildPieOption = chart => ({
    title: { text: chart.title, left: 'center', textStyle: { color: '#fff' } },
    tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
    legend: { bottom: 10, textStyle: { color: '#fff' }, data: chart.data.map(d => d.name) },
    series: [{ name: chart.title, type: 'pie', radius: ['40%', '70%'], label: { show: true, formatter: '{b}: {d}%' }, emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' } }, data: chart.data }],
    backgroundColor: '#111827'
  })

  if (loading) return <div className="text-white p-8">Loading…</div>

  return (
    <div className="p-8 space-y-6">
      {/* Filter Controls */}
      <div className="flex items-center space-x-4 mb-4">
        <select value={filter} onChange={e => setFilter(e.target.value)} className="bg-[#1f2937] text-white border-gray-600 px-3 py-2 rounded">
          {filterOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
        </select>
        {filter === 'custom' && <>
          <input type="date" value={customStart} onChange={e => setCustomStart(e.target.value)} className="bg-[#1f2937] text-white border-gray-600 px-3 py-2 rounded" />
          <span className="text-white">to</span>
          <input type="date" value={customEnd} onChange={e => setCustomEnd(e.target.value)} className="bg-[#1f2937] text-white border-gray-600 px-3 py-2 rounded" />
        </>}
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-5">
        {metrics.map((m, i) => (
          <div key={i} className="bg-[#111827] p-6 rounded-lg flex flex-col">
            <div className="text-gray-400 text-sm">{m.title}</div>
            <div className="text-white text-3xl font-semibold">{m.value}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {charts.map((chart, i) => (
          <div key={i} className="bg-[#111827] p-4 rounded-lg space-y-2">
            {chart.type === 'bar' && <ReactECharts option={buildBarOption(chart)} style={{ height: 400 }} />}
            {chart.type === 'pie' && <ReactECharts option={buildPieOption(chart)} style={{ height: 400 }} />}
            {chart.type === 'horizontal_bar' && chart.title !== 'Transactions by State or Province' && (
              <ReactECharts option={buildHorizontalBarOption(chart)} style={{ height: 400 }} />
            )}
            {chart.type === 'horizontal_bar' && chart.title === 'Transactions by State or Province' && (
              <MapToggleChart title={chart.title} data={chart.series[0].data.map((val, idx) => ({
                name: chart.y[idx],
                value: val
              }))} />
            )}

            {/* AI Insight Button */}
            <button
              className="mt-2 text-sm text-blue-400 hover:underline"
              disabled={loadingInsightId === i}
              onClick={() => fetchInsight(chart, i)}
            >
              {loadingInsightId === i ? 'Generating insight...' : 'Generate Insight'}
            </button>
            {insights[i] && <div className="text-gray-300 text-sm mt-1">{insights[i]}</div>}
          </div>
        ))}
      </div>
    </div>
  )
}

// Map+Bar Toggle for US States
function MapToggleChart({ title, data }) {
  const chartRef = useRef(null)
  const [option, setOption] = useState({})
  const [showMap, setShowMap] = useState(true)

  useEffect(() => {
    echarts.registerMap('USA', usaJson, {
      Alaska: { left: -131, top: 25, width: 15 },
      Hawaii: { left: -110, top: 28, width: 5 },
      'Puerto Rico': { left: -76, top: 26, width: 2 }
    })

    const formatted = data.map(d => ({
      name: stateNameMap[d.name] || d.name,
      value: d.value
    }))

    const mapOption = {
      title: { text: title, left: 'center', textStyle: { color: '#fff' } },
      backgroundColor: '#111827',
      visualMap: {
        left: 'right',
        min: 0,
        max: Math.max(...formatted.map(d => d.value)),
        inRange: { color: ['#e0f3f8', '#74add1', '#4575b4'] },
        text: ['High', 'Low'],
        calculable: true,
        textStyle: { color: '#fff' }
      },
      series: [{
        id: 'state-data',
        type: 'map',
        map: 'USA',
        roam: true,
        universalTransition: true,
        data: formatted
      }]
    }

    const barOption = {
      title: { text: title, left: 'center', textStyle: { color: '#fff' } },
      backgroundColor: '#111827',
      xAxis: { type: 'value', axisLabel: { color: '#fff' } },
      yAxis: { type: 'category', data: formatted.map(d => d.name), axisLabel: { rotate: 30, color: '#fff' } },
      series: [{ id: 'state-data', type: 'bar', data: formatted.map(d => d.value), universalTransition: true, itemStyle: { color: '#3b82f6' } }]
    }

    setOption(showMap ? mapOption : barOption)

    const iv = setInterval(() => {
      setShowMap(prev => !prev)
      setOption(prev => (prev === mapOption ? barOption : mapOption))
    }, 10000)

    return () => clearInterval(iv)
  }, [data])

  return <ReactECharts ref={chartRef} option={option} style={{ height: 600 }} />
}

const stateNameMap = {
  NJ: 'New Jersey', NH: 'New Hampshire', WI: 'Wisconsin', FL: 'Florida',
  OK: 'Oklahoma', UT: 'Utah', IA: 'Iowa', IL: 'Illinois', ND: 'North Dakota',
  MP: 'Northern Mariana Islands', MH: 'Marshall Islands', HI: 'Hawaii',
  PW: 'Palau', VI: 'Virgin Islands', CT: 'Connecticut', AZ: 'Arizona',
  GA: 'Georgia', NE: 'Nebraska', MO: 'Missouri', NV: 'Nevada'
}
