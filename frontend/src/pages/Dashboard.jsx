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

  const { metrics, charts } = data;

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
      data: chart.data.map(d => d.name)
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
      data: chart.data.map(d => ({ name: d.name, value: d.value }))
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
      data: chart.x,
      axisLabel: { color: '#bbb', rotate: 20 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#bbb' }
    },
    series: [{
      data: chart.y,
      type: 'bar',
      itemStyle: { color: '#00aaff' },
      barWidth: '50%'
    }],
    backgroundColor: '#111827'
  });

  if (loading && !data.metrics.length) {
    return <div className="text-white p-8">Loading…</div>;
  }

  return (
    <div className="p-8 space-y-6">
      {/* 1) Unified Metrics Row */}
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

      {/* 2) Section Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <NavLink
          to="/financial-analysis"
          className="border border-green-500 text-white p-6 rounded-lg flex items-center space-x-4 hover:bg-green-50/10 transition"
        >
          <span className="text-green-500 text-2xl">💰</span>
          <div>
            <div className="font-semibold">Financial Analysis</div>
            <div className="text-gray-400 text-sm">Revenue & Currency Insights</div>
          </div>
        </NavLink>

        <NavLink
          to="/risk-assessment"
          className="border border-red-500 text-white p-6 rounded-lg flex items-center space-x-4 hover:bg-red-50/10 transition"
        >
          <span className="text-red-500 text-2xl">⚠️</span>
          <div>
            <div className="font-semibold">Risk Assessment</div>
            <div className="text-gray-400 text-sm">Fraud Detection & Prevention</div>
          </div>
        </NavLink>

        <NavLink
          to="/operational-efficiency"
          className="border border-blue-500 text-white p-6 rounded-lg flex items-center space-x-4 hover:bg-blue-50/10 transition"
        >
          <span className="text-blue-500 text-2xl">📈</span>
          <div>
            <div className="font-semibold">Operational Efficiency</div>
            <div className="text-gray-400 text-sm">Real-time Operational Metrics</div>
          </div>
        </NavLink>
      </div>

      {/* 3) Chart Display */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {charts.map((c, idx) => (
          <div key={idx} className="bg-[#111827] p-4 rounded-lg">
            {c.type === 'pie' && (
              <ReactECharts
                option={buildPieOption(c)}
                style={{ height: '350px', width: '100%' }}
              />
            )}
            {c.type === 'bar' && (
              <ReactECharts
                option={buildBarOption(c)}
                style={{ height: '350px', width: '100%' }}
              />
            )}
            {c.type === 'list' && (
              <ul className="space-y-2 max-h-56 overflow-auto mt-2">
                {c.data.map((item, i) =>
                  typeof item === 'string' ? (
                    <li key={i} className="text-gray-200">{item}</li>
                  ) : (
                    <li key={i} className="flex justify-between items-center text-gray-200">
                      <span className="bg-[#00aaff] text-[#001f3f] px-2 py-1 rounded text-xs mr-2">
                        {item.type}
                      </span>
                      <span className="flex-1">{item.message}</span>
                      <span className="text-gray-500 text-xs ml-2">
                        {new Date(item.time).toLocaleTimeString()}
                      </span>
                    </li>
                  )
                )}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
