/**
 * Cliente HTTP centralizado.
 * Todas las llamadas al backend pasan por aquí.
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : "/api/v1";

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor de respuesta: muestra errores en consola
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const mensaje = error.response?.data?.detail || error.message || "Error desconocido";
    console.error(`[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}: ${mensaje}`);
    return Promise.reject(error);
  }
);

export default client;
