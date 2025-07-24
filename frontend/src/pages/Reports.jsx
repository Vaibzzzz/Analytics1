import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';

const FILTER_OPTIONS = ['YTD', 'MTD', 'Weekly', 'Daily', 'Custom'];

export default function GatewayFeeAnalysis({ points, setPoints }) {
  const [data, setData] = useState({ metrics: [], charts: [] });
  const [insights, setInsights] = useState({});
  const [loadingInsight, setLoadingInsight] = useState({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('YTD');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');

  useEffect(() => {
    fetchChartData();
  }, [filter, start, end]);

  const fetchChartData = async () => {
    setLoading(true);
    try {
      const params = { filter_type: filter };
      if (filter === 'Custom' && start && end) {
        params.start_date = start;
        params.end_date = end;
      }
      const res = await axios.get('http://localhost:8001/api/gateway-fee', { params });
      setData({ metrics: res.data.metrics || [], charts: res.data.charts || [] });
      setInsights({});
    } catch (err) {
      console.error('Error fetching chart data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchInsightForChart = async (chartIndex) => {
    if (points <= 0) {
      alert("You don't have enough AI points left.");
      return;
    }

    setLoadingInsight(prev => ({ ...prev, [chartIndex]: true }));

    try {
      const params = { filter_type: filter };
      if (filter === 'Custom' && start && end) {
        params.start_date = start;
        params.end_date = end;
      }
      params.chart_index = chartIndex;

      const res = await axios.get('http://localhost:8001/api/gateway-fee/insight', { params });

      setInsights(prev => ({
        ...prev,
        [chartIndex]: res.data.insight || 'No insight available.'
      }));

      // Decrease points by 1 after successful call
      setPoints(prev => Math.max(prev - 1, 0));
    } catch (err) {
      console.error('Error fetching insight:', err);
      setInsights(prev => ({
        ...prev,
        [chartIndex]: 'Failed to fetch AI insight.'
      }));
    } finally {
      setLoadingInsight(prev => ({ ...prev, [chartIndex]: false }));
    }
  };

  const handleFilterChange = (value) => {
    setFilter(value);
    if (value !== 'Custom') {
      setStart('');
      setEnd('');
    }
  };

  const buildBarOption = (chart) => ({
    title: {
      text: chart.title,
      left: 'center',
      textStyle: { color: '#fff' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'category',
      data: chart.x,
      axisLabel: { color: '#fff', rotate: 45 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#fff' }
    },
    series: chart.series.map(series => ({
      name: series.name,
      type: 'bar',
      data: series.data,
      barWidth: '60%',
      itemStyle: { color: '#10b981' },
      label: {
        show: true,
        position: 'top',
        color: '#fff'
      }
    })),
    backgroundColor: '#111827',
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      containLabel: true
    }
  });

  if (loading) return <div className="text-white p-8">Loading charts…</div>;

  return (
    <div className="p-8 space-y-6">
      {/* Filter controls */}
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

        {filter === 'Custom' && (
          <>
            <input
              type="date"
              value={start}
              onChange={e => setStart(e.target.value)}
              className="bg-[#1f2937] text-white border border-gray-600 rounded px-2 py-1"
            />
            <span className="text-white">to</span>
            <input
              type="date"
              value={end}
              onChange={e => setEnd(e.target.value)}
              className="bg-[#1f2937] text-white border border-gray-600 rounded px-2 py-1"
            />
          </>
        )}
      </div>

      {/* Metric cards */}
      {data.metrics.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-5 mb-6">
          {data.metrics.map((metric, i) => (
            <div key={i} className="bg-[#111827] p-4 rounded-lg flex flex-col justify-between">
              <div className="text-gray-400 text-sm mb-2">{metric.title}</div>
              <div className="text-white text-2xl font-bold">{metric.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Chart cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {data.charts.map((chart, i) => (
          <div key={i} className="bg-[#111827] p-4 rounded-lg relative">
            <button
              onClick={() => fetchInsightForChart(i)}
              className="absolute top-2 right-2 z-10 bg-green-600 hover:bg-green-700 text-white px-5 py-2 rounded text-sm font-semibold shadow-md"
              disabled={loadingInsight[i]}
            >
              {loadingInsight[i] ? 'AI Thinking...' : '✨'}
            </button>

            <ReactECharts option={buildBarOption(chart)} style={{ height: 400, marginTop: '1.5rem' }} />

            {insights[i] && (
              <div className="mt-4 bg-[#1f2937] text-green-200 text-sm p-3 rounded">
                <h3 className="text-white font-medium mb-1">AI Insight:</h3>
                <p>{insights[i]}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
