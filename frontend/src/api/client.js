/**
 * Cliente HTTP centralizado.
 * Timeout extendido para clasificación de PDFs largos con Ollama.
 */

import axios from "axios";

const client = axios.create({
  baseURL: "/api/v1",
  timeout: 300000, // 5 minutos — PDFs largos con Ollama pueden tardar
  headers: { "Content-Type": "application/json" },
});

const token = localStorage.getItem("gastosai_token");
if (token) {
  client.defaults.headers.common["Authorization"] = `Bearer ${token}`;
}

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("gastosai_token");
      localStorage.removeItem("gastosai_user");
      delete client.defaults.headers.common["Authorization"];
      window.location.href = "/login";
    }
    const msg = error.response?.data?.detail || error.message || "Error desconocido";
    console.error(`[API] ${error.config?.method?.toUpperCase()} ${error.config?.url}: ${msg}`);
    return Promise.reject(error);
  }
);

export default client;
