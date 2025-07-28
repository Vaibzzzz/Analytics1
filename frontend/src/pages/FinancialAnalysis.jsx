import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';

const FILTER_OPTIONS = ['YTD', 'MTD', 'Weekly', 'Daily', 'Monthly', 'Yesterday', 'Today', 'custom'];

export default function FinancialAnalysis({ points, setPoints }) {
  const [data, setData] = useState({ metrics: [], charts: [] });
  const [loading, setLoading] = useState(true);
  const [loadingInsight, setLoadingInsight] = useState({});
  const [insights, setInsights] = useState({});
  const [filter, setFilter] = useState(() => localStorage.getItem('financial_filter') || 'YTD');
  const [start, setStart] = useState(() => localStorage.getItem('financial_start') || '');
  const [end, setEnd] = useState(() => localStorage.getItem('financial_end') || '');

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
    localStorage.setItem('financial_filter', value);
    if (value !== 'custom') {
      setStart('');
      setEnd('');
      localStorage.removeItem('financial_start');
      localStorage.removeItem('financial_end');
    }
  };

  const handleStartChange = (value) => {
    setStart(value);
    localStorage.setItem('financial_start', value);
  };

  const handleEndChange = (value) => {
    setEnd(value);
    localStorage.setItem('financial_end', value);
  };

  const buildPieOption = (chart) => ({
    title: { text: chart.title, left: 'center', textStyle: { color: '#fff' } },
    tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
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
      data: chart.y,
      axisLabel: { color: '#fff' }
    },
    series: chart.series.map(series => ({
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
    })),
    legend: {
      show: chart.series.length > 1,
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

      {/* Charts with AI Buttons and Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {data.charts.map((chart, i) => (
          <div key={i} className="bg-[#111827] p-4 rounded-lg">
            <div className="flex justify-between items-center mb-2">
              <div className="text-sm text-gray-400">{chart.title}</div>
              <button
                onClick={() => fetchInsight(chart.title)}
                className="text-xs bg-green-600 hover:bg-green-700 px-2 py-1 rounded text-white disabled:opacity-50"
              >
                {loadingInsight[chart.title] ? 'Thinking…' : '✨ AI Insight'}
              </button>
            </div>

            {chart.type === 'pie' && <ReactECharts option={buildPieOption(chart)} style={{ height: 350 }} />}
            {chart.type === 'horizontal_bar' && <ReactECharts option={buildHorizontalBarOption(chart)} style={{ height: 500 }} />}

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
