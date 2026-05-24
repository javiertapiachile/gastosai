/**
 * Cliente HTTP centralizado.
 * Usa rutas relativas (/api/v1/...) para que funcione desde cualquier
 * dispositivo en la red — el nginx del frontend hace el proxy al backend.
 */

import axios from "axios";

const client = axios.create({
  baseURL: "/api/v1",  // Siempre relativo — nginx se encarga del proxy
  timeout: 120000,
  headers: { "Content-Type": "application/json" },
});

// Si hay token guardado, inyectarlo en todas las peticiones
const token = localStorage.getItem("gastosai_token");
if (token) {
  client.defaults.headers.common["Authorization"] = `Bearer ${token}`;
}

// Interceptor: si el servidor devuelve 401, limpiar sesión
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
