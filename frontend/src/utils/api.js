import axios from "axios";

const BASE_URL = "http://localhost:8000";

export const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post(`${BASE_URL}/upload`, formData);
  return response.data;
};

export const generateKPICharts = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post(`${BASE_URL}/generate_kpis`, formData);
  return response.data;
};

export const fetchGeneratedCharts = async () => {
  const response = await axios.get(`${BASE_URL}/charts`);
  return response.data;
};
