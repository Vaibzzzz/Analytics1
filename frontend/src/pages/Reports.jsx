import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';

const FILTER_OPTIONS = [
  'YTD', 'MTD', 'Weekly', 'Daily', 'Monthly', 'Yesterday', 'Today', 'Custom'
];

export default function GatewayFeeAnalysis() {
  const [data, setData] = useState({ charts: [], insight: '' });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('YTD');              
  const [start, setStart] = useState('');                  
  const [end, setEnd] = useState('');                  
  
  useEffect(() => {
    fetchData();
  }, [filter, start, end]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = { filter_type: filter };
      if (filter === 'Custom' && start && end) {
        params.start_date = start;
        params.end_date = end;
      }

      const res = await axios.get('http://localhost:8001/api/gateway-fee', { params });
      setData(res.data);
    } catch (err) {
      console.error('Error fetching gateway fee analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (value) => {
    setFilter(value);
    if (value !== 'Custom') {
      setStart('');
      setEnd('');
    }
  };

  const handleStartChange = (value) => setStart(value);
  const handleEndChange = (value) => setEnd(value);

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

  if (loading) return <div className="text-white p-8">Loading…</div>;

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

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {data.charts.map((chart, i) => (
          <div key={i} className="bg-[#111827] p-4 rounded-lg">
            <ReactECharts option={buildBarOption(chart)} style={{ height: 400 }} />
          </div>
        ))}
      </div>

      {/* AI Insight */}
      {data.insight && (
        <div className="text-gray-300 mt-6 p-4 bg-[#1f2937] rounded">
          <h3 className="text-white font-semibold mb-2">AI Insight:</h3>
          <p>{data.insight}</p>
        </div>
      )}
    </div>
  );
}

