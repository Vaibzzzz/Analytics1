import axios from "axios";

const BASE_URL = "http://localhost:8000";

// Upload CSV file (if needed)
export const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post(`${BASE_URL}/upload`, formData);
  return response.data;
};

// Generate KPIs from connected DB (GET)
export const generateKPICharts = async () => {
  const response = await axios.get(`${BASE_URL}/generate_kpis`);
  return response.data;
};

// Fetch previously generated charts (if applicable)
export const fetchGeneratedCharts = async () => {
  const response = await axios.get(`${BASE_URL}/charts`);
  return response.data;
};
