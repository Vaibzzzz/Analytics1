import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';

export default function Dashboard() {
  const [data, setData] = useState(() => {
    const cached = localStorage.getItem('dashboard_data');
    return cached ? JSON.parse(cached) : { metrics: [], charts: [] };
  });
  const [loading, setLoading] = useState(true);
  const [insights, setInsights] = useState({});
  const [loadingInsights, setLoadingInsights] = useState({});

  useEffect(() => {
    axios.get('http://localhost:8001/api/dashboard')
      .then(res => {
        setData(res.data);
        localStorage.setItem('dashboard_data', JSON.stringify(res.data));
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const fetchInsight = async (chartTitle) => {
    setLoadingInsights(prev => ({ ...prev, [chartTitle]: true }));
    try {
      const res = await axios.get('http://localhost:8001/api/dashboard/insights', {
        params: { chart_id: chartTitle }
      });
      setInsights(prev => ({ ...prev, [chartTitle]: res.data.insight }));
    } catch (err) {
      console.error(err);
      setInsights(prev => ({ ...prev, [chartTitle]: 'Failed to generate insight.' }));
    } finally {
      setLoadingInsights(prev => ({ ...prev, [chartTitle]: false }));
    }
  };

  const buildPieOption = (chart) => ({
    title: {
      text: chart.title,
      left: 'center',
      textStyle: { color: '#fff' }
    },
    tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
    legend: {
      orient: 'horizontal',
      bottom: 10,
      textStyle: { color: '#fff' },
      data: chart.data?.map(d => d.name) || []
    },
    series: [{
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
      data: chart.data?.map(d => ({ name: d.name, value: d.value })) || []
    }],
    backgroundColor: '#111827'
  });

  const buildBarOption = (chart) => ({
    title: {
      text: chart.title,
      left: 'center',
      textStyle: { color: '#fff' }
    },
    tooltip: {},
    xAxis: {
      type: 'category',
      data: chart.x || [],
      axisLabel: { color: '#bbb', rotate: 20 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#bbb' }
    },
    series: [{
      data: chart.y || [],
      type: 'bar',
      itemStyle: { color: '#00aaff' },
      barWidth: '50%'
    }],
    backgroundColor: '#111827'
  });

  if (loading && !data.metrics.length) {
    return <div className="text-white p-8">Loading…</div>;
  }

  const { metrics, charts } = data;

  return (
    <div className="p-8 space-y-6">
      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-5">
        {metrics.map((m, i) => {
          const showDollar = ['Total Transaction Volume', 'Average Transaction Value'].includes(m.title);
          const formattedValue = typeof m.value === 'number'
            ? (showDollar
              ? `$${new Intl.NumberFormat('en-US').format(m.value)}`
              : new Intl.NumberFormat('en-US').format(m.value))
            : m.value;

          return (
            <div key={i} className="bg-[#111827] p-6 rounded-lg min-h-[140px] flex flex-col justify-center">
              <div className="text-gray-400 text-sm mb-2">{m.title}</div>
              <div className="text-white text-3xl font-semibold">{formattedValue}</div>
            </div>
          );
        })}
      </div>

      {/* Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <NavLink to="/financial-analysis" className="border border-green-500 text-white p-6 rounded-lg flex items-center space-x-4 hover:bg-green-50/10 transition">
          <span className="text-green-500 text-2xl">💰</span>
          <div>
            <div className="font-semibold">Financial Analysis</div>
            <div className="text-gray-400 text-sm">Revenue & Currency Insights</div>
          </div>
        </NavLink>

        <NavLink to="/risk-assessment" className="border border-red-500 text-white p-6 rounded-lg flex items-center space-x-4 hover:bg-red-50/10 transition">
          <span className="text-red-500 text-2xl">⚠️</span>
          <div>
            <div className="font-semibold">Risk Assessment</div>
            <div className="text-gray-400 text-sm">Fraud Detection & Prevention</div>
          </div>
        </NavLink>

        <NavLink to="/operational-efficiency" className="border border-blue-500 text-white p-6 rounded-lg flex items-center space-x-4 hover:bg-blue-50/10 transition">
          <span className="text-blue-500 text-2xl">📈</span>
          <div>
            <div className="font-semibold">Operational Efficiency</div>
            <div className="text-gray-400 text-sm">Real-time Operational Metrics</div>
          </div>
        </NavLink>
      </div>

      {/* Charts with AI Buttons and Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {charts.map((chart, i) => (
          <div key={i} className="bg-[#111827] p-4 rounded-lg">
            <div className="flex justify-between items-center mb-2">
              <div className="text-sm text-gray-400">{chart.title}</div>
              <button
                onClick={() => fetchInsight(chart.title)}
                className="text-xs bg-green-600 hover:bg-green-700 px-2 py-1 rounded text-white disabled:opacity-50"
                disabled={loadingInsights[chart.title]}
              >
                {loadingInsights[chart.title] ? 'Thinking…' : '✨ Pi AI'}
              </button>
            </div>

            {chart.type === 'bar' && <ReactECharts option={buildBarOption(chart)} style={{ height: 350 }} />}
            {chart.type === 'pie' && <ReactECharts option={buildPieOption(chart)} style={{ height: 350 }} />}

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
