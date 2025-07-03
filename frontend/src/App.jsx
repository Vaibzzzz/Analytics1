import React, { useEffect, useState } from 'react';
import { Box, Typography, Card, CardContent, Grid, Container } from '@mui/material';
import * as echarts from 'echarts';

const Chart = ({ title, x, y }) => {
  const chartId = `chart-${title.replace(/\s+/g, '-')}`;

  useEffect(() => {
    const chartDom = document.getElementById(chartId);
    if (!chartDom) return;

    const chart = echarts.init(chartDom);
    const option = {
      title: { text: title },
      tooltip: {},
      xAxis: { data: x },
      yAxis: {},
      series: [{ type: 'bar', data: y }],
    };

    chart.setOption(option);
    return () => chart.dispose();
  }, [x, y, title]);

  return <div id={chartId} style={{ width: '100%', height: 400, marginTop: 20 }} />;
};

function App() {
  const [metrics, setMetrics] = useState([]);
  const [charts, setCharts] = useState([]);

  useEffect(() => {
    fetch('http://localhost:8000/generate_kpis')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch KPIs');
        return res.json();
      })
      .then((data) => {
        setMetrics(data.metrics || []);
        setCharts(data.charts || []);
      })
      .catch((err) => {
        console.error(err);
      });
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        KPI Dashboard
      </Typography>

      <Grid container spacing={2}>
        {metrics.map((metric, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Card sx={{ backgroundColor: '#f4f6f8', borderRadius: 2 }}>
              <CardContent>
                <Typography variant="h6">{metric.title}</Typography>
                <Typography variant="h5" fontWeight="bold">
                  {metric.value}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {charts.map((chart, index) => (
        <Chart key={index} title={chart.title} x={chart.x} y={chart.y} />
      ))}
    </Container>
  );
}

export default App;
