import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';

const FILTER_OPTIONS = ['YTD', 'MTD', 'Weekly', 'Daily', 'Monthly', 'Yesterday', 'Today', 'custom'];
const CHART_TYPES = [
  { value: 'pie', label: 'Pie Chart' },
  { value: 'horizontal_bar', label: 'Horizontal Bar' },
  { value: 'vertical_bar', label: 'Vertical Bar' },
  { value: 'line', label: 'Line Chart' },
  { value: 'area', label: 'Area Chart' },
  { value: 'donut', label: 'Donut Chart' }
];

export default function FinancialAnalysis({ points, setPoints }) {
  const [data, setData] = useState({ metrics: [], charts: [] });
  const [loading, setLoading] = useState(true);
  const [loadingInsight, setLoadingInsight] = useState({});
  const [insights, setInsights] = useState({});
  const [filter, setFilter] = useState(() => localStorage?.getItem('financial_filter') || 'YTD');
  const [start, setStart] = useState(() => localStorage?.getItem('financial_start') || '');
  const [end, setEnd] = useState(() => localStorage?.getItem('financial_end') || '');
  
  // State to track selected chart type for each chart
  const [chartTypes, setChartTypes] = useState({});

  useEffect(() => {
    fetchData();
  }, [filter, start, end]);

  const fetchData = async () => {
    setLoading(true);
    setInsights({});
    try {
      const params = { filter_type: filter };
      if (filter === 'custom' && start && end) {
        params.start = start;
        params.end = end;
      }
      const res = await axios.get('http://localhost:8001/api/financial-performance', { params });
      setData(res.data);
      
      // Initialize chart types with default values from API
      const initialChartTypes = {};
      res.data.charts.forEach(chart => {
        initialChartTypes[chart.title] = chart.type;
      });
      setChartTypes(initialChartTypes);
    } catch (err) {
      console.error('Error fetching financial analysis data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchInsight = async (chartId) => {
    if (points <= 0) {
      alert('You have no AI points left!');
      return;
    }

    setLoadingInsight(prev => ({ ...prev, [chartId]: true }));
    try {
      const params = { filter_type: filter, chart_id: chartId };
      if (filter === 'custom' && start && end) {
        params.start = start;
        params.end = end;
      }

      const res = await axios.get('http://localhost:8001/api/financial-performance/insights', { params });

      setInsights(prev => ({
        ...prev,
        [chartId]: res.data?.insight || 'No insight available',
      }));

      setPoints(prev => prev - 1);
    } catch (err) {
      console.error('Error generating insight:', err);
      setInsights(prev => ({ ...prev, [chartId]: 'Error generating insight.' }));
    } finally {
      setLoadingInsight(prev => ({ ...prev, [chartId]: false }));
    }
  };

  const handleFilterChange = (value) => {
    setFilter(value);
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('financial_filter', value);
    }
    if (value !== 'custom') {
      setStart('');
      setEnd('');
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem('financial_start');
        localStorage.removeItem('financial_end');
      }
    }
  };

  const handleStartChange = (value) => {
    setStart(value);
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('financial_start', value);
    }
  };

  const handleEndChange = (value) => {
    setEnd(value);
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('financial_end', value);
    }
  };

  const handleChartTypeChange = (chartTitle, newType) => {
    setChartTypes(prev => ({
      ...prev,
      [chartTitle]: newType
    }));
  };

  const buildPieOption = (chart) => ({
    title: { text: chart.title, left: 'center', textStyle: { color: '#fff' } },
    tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
    legend: {
      bottom: 10,
      textStyle: { color: '#fff' },
      data: chart.data?.map(d => d.name) || chart.y || []
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
      data: chart.data ? 
        chart.data.map(d => ({ name: d.name, value: d.value })) :
        chart.y?.map((name, idx) => ({ 
          name, 
          value: chart.series?.[0]?.data?.[idx] || 0 
        })) || []
    }],
    backgroundColor: '#111827'
  });

  const buildDonutOption = (chart) => ({
    title: { text: chart.title, left: 'center', textStyle: { color: '#fff' } },
    tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
    legend: {
      bottom: 10,
      textStyle: { color: '#fff' },
      data: chart.data?.map(d => d.name) || chart.y || []
    },
    series: [{
      name: chart.title,
      type: 'pie',
      radius: ['50%', '80%'],
      label: {
        show: true,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '30',
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: chart.data ? 
        chart.data.map(d => ({ name: d.name, value: d.value })) :
        chart.y?.map((name, idx) => ({ 
          name, 
          value: chart.series?.[0]?.data?.[idx] || 0 
        })) || []
    }],
    backgroundColor: '#111827'
  });

  const buildHorizontalBarOption = (chart) => ({
    title: { text: chart.title, left: 'center', textStyle: { color: '#fff' } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#fff' }
    },
    yAxis: {
      type: 'category',
      data: chart.y || chart.data?.map(d => d.name) || [],
      axisLabel: { color: '#fff' }
    },
    series: chart.series ? chart.series.map(series => ({
      name: series.name,
      data: series.data,
      type: 'bar',
      barWidth: '60%',
      itemStyle: { color: '#3b82f6' },
      label: {
        show: true,
        position: 'right',
        color: '#fff'
      }
    })) : [{
      name: chart.title,
      data: chart.data?.map(d => d.value) || [],
      type: 'bar',
      barWidth: '60%',
      itemStyle: { color: '#3b82f6' },
      label: {
        show: true,
        position: 'right',
        color: '#fff'
      }
    }],
    legend: {
      show: chart.series ? chart.series.length > 1 : false,
      textStyle: { color: '#fff' }
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '10%',
      containLabel: true
    },
    backgroundColor: '#111827'
  });

  const buildVerticalBarOption = (chart) => ({
    title: { text: chart.title, left: 'center', textStyle: { color: '#fff' } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: {
      type: 'category',
      data: chart.y || chart.data?.map(d => d.name) || [],
      axisLabel: { color: '#fff', rotate: 45 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#fff' }
    },
    series: chart.series ? chart.series.map(series => ({
      name: series.name,
      data: series.data,
      type: 'bar',
      barWidth: '60%',
      itemStyle: { color: '#3b82f6' },
      label: {
        show: true,
        position: 'top',
        color: '#fff'
      }
    })) : [{
      name: chart.title,
      data: chart.data?.map(d => d.value) || [],
      type: 'bar',
      barWidth: '60%',
      itemStyle: { color: '#3b82f6' },
      label: {
        show: true,
        position: 'top',
        color: '#fff'
      }
    }],
    legend: {
      show: chart.series ? chart.series.length > 1 : false,
      textStyle: { color: '#fff' }
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '15%',
      containLabel: true
    },
    backgroundColor: '#111827'
  });

  const buildLineOption = (chart) => ({
    title: { text: chart.title, left: 'center', textStyle: { color: '#fff' } },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: chart.y || chart.data?.map(d => d.name) || [],
      axisLabel: { color: '#fff' }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#fff' }
    },
    series: chart.series ? chart.series.map((series, idx) => ({
      name: series.name,
      data: series.data,
      type: 'line',
      smooth: true,
      itemStyle: { color: idx === 0 ? '#3b82f6' : '#10b981' },
      lineStyle: { color: idx === 0 ? '#3b82f6' : '#10b981' }
    })) : [{
      name: chart.title,
      data: chart.data?.map(d => d.value) || [],
      type: 'line',
      smooth: true,
      itemStyle: { color: '#3b82f6' },
      lineStyle: { color: '#3b82f6' }
    }],
    legend: {
      show: chart.series ? chart.series.length > 1 : false,
      textStyle: { color: '#fff' }
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '10%',
      containLabel: true
    },
    backgroundColor: '#111827'
  });

  const buildAreaOption = (chart) => ({
    title: { text: chart.title, left: 'center', textStyle: { color: '#fff' } },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: chart.y || chart.data?.map(d => d.name) || [],
      axisLabel: { color: '#fff' }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#fff' }
    },
    series: chart.series ? chart.series.map((series, idx) => ({
      name: series.name,
      data: series.data,
      type: 'line',
      smooth: true,
      areaStyle: { opacity: 0.6 },
      itemStyle: { color: idx === 0 ? '#3b82f6' : '#10b981' },
      lineStyle: { color: idx === 0 ? '#3b82f6' : '#10b981' }
    })) : [{
      name: chart.title,
      data: chart.data?.map(d => d.value) || [],
      type: 'line',
      smooth: true,
      areaStyle: { opacity: 0.6 },
      itemStyle: { color: '#3b82f6' },
      lineStyle: { color: '#3b82f6' }
    }],
    legend: {
      show: chart.series ? chart.series.length > 1 : false,
      textStyle: { color: '#fff' }
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '10%',
      containLabel: true
    },
    backgroundColor: '#111827'
  });

  const getChartOption = (chart, selectedType) => {
    switch (selectedType) {
      case 'pie':
        return buildPieOption(chart);
      case 'donut':
        return buildDonutOption(chart);
      case 'horizontal_bar':
        return buildHorizontalBarOption(chart);
      case 'vertical_bar':
        return buildVerticalBarOption(chart);
      case 'line':
        return buildLineOption(chart);
      case 'area':
        return buildAreaOption(chart);
      default:
        return buildPieOption(chart);
    }
  };

  if (loading) return <div className="text-white p-8">Loading…</div>;

  return (
    <div className="p-8 space-y-6">
      {/* Filter Controls */}
      <div className="mb-4 flex items-center space-x-4">
        <select
          value={filter}
          onChange={(e) => handleFilterChange(e.target.value)}
          className="bg-[#1f2937] text-white border border-gray-600 rounded px-4 py-2"
        >
          {FILTER_OPTIONS.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>

        {filter === 'custom' && (
          <>
            <input
              type="date"
              value={start}
              onChange={e => handleStartChange(e.target.value)}
              className="bg-[#1f2937] text-white border border-gray-600 rounded px-2 py-1"
            />
            <span className="text-white">to</span>
            <input
              type="date"
              value={end}
              onChange={e => handleEndChange(e.target.value)}
              className="bg-[#1f2937] text-white border border-gray-600 rounded px-2 py-1"
            />
          </>
        )}
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-5">
        {data.metrics.map((m, i) => (
          <div key={i} className="bg-[#111827] p-6 rounded-lg min-h-[140px] flex flex-col justify-center">
            <div className="text-gray-400 text-sm mb-2">{m.title}</div>
            <div className="text-white text-3xl font-semibold">
              {typeof m.value === 'number'
                ? (
                  ['Total Transaction Volume', 'Average Transaction Value'].includes(m.title)
                    ? `$${new Intl.NumberFormat('en-US').format(m.value)}`
                    : new Intl.NumberFormat('en-US').format(m.value)
                )
                : m.value}
            </div>
            {m.diff !== undefined && (
              <div className={`text-sm mt-2 ${m.diff >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {m.diff >= 0 ? '+' : ''}{m.diff}% vs previous
              </div>
            )}
            {m.insight && (
              <div className="mt-3 text-xs text-blue-300 italic leading-snug">
                {m.insight}
                <br />
                <span className="text-gray-500">(z = {m.z_score}, p = {m.p_value})</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Charts with AI Buttons, Chart Type Selector and Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {data.charts.map((chart, i) => (
          <div key={i} className="bg-[#111827] p-4 rounded-lg">
            <div className="flex justify-between items-center mb-4">
              <div className="text-sm text-gray-400">{chart.title}</div>
              <div className="flex items-center space-x-2">
                {/* Chart Type Selector */}
                <select
                  value={chartTypes[chart.title] || chart.type}
                  onChange={(e) => handleChartTypeChange(chart.title, e.target.value)}
                  className="bg-[#1f2937] text-white border border-gray-600 rounded px-2 py-1 text-xs"
                >
                  {CHART_TYPES.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
                
                {/* AI Insight Button */}
                <button
                  onClick={() => fetchInsight(chart.title)}
                  className="text-xs bg-green-600 hover:bg-green-700 px-2 py-1 rounded text-white disabled:opacity-50"
                  disabled={loadingInsight[chart.title]}
                >
                  {loadingInsight[chart.title] ? 'Thinking…' : '✨ AI Insight'}
                </button>
              </div>
            </div>

            {/* Dynamic Chart Rendering */}
            <ReactECharts 
              option={getChartOption(chart, chartTypes[chart.title] || chart.type)} 
              style={{ height: 400 }} 
            />

            {/* AI Insights */}
            {insights[chart.title] && (
              <div className="mt-4 text-sm text-blue-200 border-t border-gray-700 pt-2">
                {insights[chart.title]}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}