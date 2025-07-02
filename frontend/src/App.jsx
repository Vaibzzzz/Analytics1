import React, { useState } from "react";
import axios from "axios";
import ReactECharts from "echarts-for-react";

function App() {
  const [kpis, setKpis] = useState(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:8000/upload", formData);
      if (response.data.success) {
        setKpis(response.data.kpis);
      } else {
        alert("Error: " + response.data.error);
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert("Failed to upload file.");
    }
  };

  const renderCard = (label, value) => (
    <div key={label} className="p-4 bg-white rounded shadow text-center w-64">
      <h3 className="text-gray-600 text-sm">{label}</h3>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );

  const getBarChartOption = (title, xData = [], yData = []) => ({
    title: { text: title },
    tooltip: {},
    xAxis: { type: "category", data: xData },
    yAxis: { type: "value" },
    series: [
      {
        data: yData,
        type: "bar",
        itemStyle: { color: "#5470C6" },
      },
    ],
  });

  const getLineChartOption = (title, xData = [], yData = []) => ({
    title: { text: title },
    tooltip: {},
    xAxis: { type: "category", data: xData },
    yAxis: { type: "value" },
    series: [
      {
        data: yData,
        type: "line",
        smooth: true,
        lineStyle: { color: "#91cc75" },
      },
    ],
  });

  const getGaugeOption = (title, value = 0) => ({
    title: { text: title },
    series: [
      {
        type: "gauge",
        progress: { show: true },
        detail: {
          valueAnimation: true,
          formatter: "{value}%",
        },
        data: [{ value: (parseFloat(value) * 100).toFixed(2), name: title }],
      },
    ],
  });

  return (
    <div className="p-10 space-y-6">
      <input type="file" accept=".csv" onChange={handleFileUpload} />

      {kpis && (
        <div className="flex flex-wrap gap-6">
          {renderCard("Avg Transaction Amount", `$${kpis.average_transaction_amount ?? "-"}`)}
          {renderCard("Transaction Volume", kpis.transaction_volume ?? "-")}
          {renderCard(
            "Conversion Rate",
            kpis.conversion_rate !== undefined
              ? `${(kpis.conversion_rate * 100).toFixed(2)}%`
              : "-"
          )}

          <ReactECharts
            key="fraud_rate"
            option={getGaugeOption("Fraud Rate", kpis.fraud_rate ?? 0)}
            style={{ height: 300, width: 300 }}
          />

          {kpis.transactions_per_day && (
            <ReactECharts
              key="per_day"
              option={getLineChartOption(
                "Transactions Per Day",
                kpis.transactions_per_day.day,
                kpis.transactions_per_day.count
              )}
              style={{ height: 300, width: 600 }}
            />
          )}

          {kpis.transactions_per_month && (
            <ReactECharts
              key="per_month"
              option={getBarChartOption(
                "Transactions Per Month",
                kpis.transactions_per_month.month,
                kpis.transactions_per_month.count
              )}
              style={{ height: 300, width: 600 }}
            />
          )}

          {kpis.top_cities && (
            <ReactECharts
              key="top_cities"
              option={getBarChartOption(
                "Top Cities",
                kpis.top_cities.labels,
                kpis.top_cities.values
              )}
              style={{ height: 300, width: 600 }}
            />
          )}

          {kpis.top_growing_cities && (
            <ReactECharts
              key="top_growing"
              option={getBarChartOption(
                "Top Growing Cities",
                kpis.top_growing_cities.cities,
                kpis.top_growing_cities.growth_rates
              )}
              style={{ height: 300, width: 600 }}
            />
          )}

          {kpis.most_risky_cities && (
            <ReactECharts
              key="risky_cities"
              option={getBarChartOption(
                "Most Risky Cities",
                kpis.most_risky_cities.cities,
                kpis.most_risky_cities.fraud_rates
              )}
              style={{ height: 300, width: 600 }}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default App;
