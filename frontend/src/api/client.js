/**
 * Cliente HTTP centralizado con manejo automático de 401.
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : "/api/v1";

const client = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 minutos para clasificaciones lentas con Ollama
  headers: { "Content-Type": "application/json" },
});

// Interceptor de respuesta: si el servidor devuelve 401, limpiar sesión
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado o inválido — limpiar y redirigir a login
      localStorage.removeItem("gastosai_token");
      localStorage.removeItem("gastosai_user");
      delete client.defaults.headers.common["Authorization"];
      window.location.href = "/login";
    }
    const mensaje = error.response?.data?.detail || error.message || "Error desconocido";
    console.error(`[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}: ${mensaje}`);
    return Promise.reject(error);
  }
);

export default client;
