import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:5000/api",
  timeout: 30000,
});

export function errorMessage(error) {
  return error.response?.data?.error || error.message || "The request could not be completed.";
}

export const api = {
  health: () => client.get("/health").then((response) => response.data),
  dashboard: (params = {}) => client.get("/dashboard", { params }).then((response) => response.data),
  analytics: (params = {}) => client.get("/analytics", { params }).then((response) => response.data),
  metrics: () => client.get("/model-metrics").then((response) => response.data),
  dataSummary: () => client.get("/data-summary").then((response) => response.data),
  predict: (features) => client.post("/predict", features).then((response) => response.data),
  batchPredict: (file) => {
    const body = new FormData();
    body.append("file", file);
    return client.post("/batch-predict", body, { headers: { "Content-Type": "multipart/form-data" } }).then((response) => response.data);
  },
  regenerate: () => client.post("/regenerate-demo", { confirmation: "REPLACE SYNTHETIC DATA" }).then((response) => response.data),
  datasetUrl: `${client.defaults.baseURL}/download-dataset`,
  exportUrl: (params = {}) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value));
    return `${client.defaults.baseURL}/export-csv${query.size ? `?${query}` : ""}`;
  },
  reportUrl: (params = {}) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value));
    return `${client.defaults.baseURL}/export-report${query.size ? `?${query}` : ""}`;
  },
};
