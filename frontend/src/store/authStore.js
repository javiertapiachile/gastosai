/**
 * Store de autenticación.
 * Persiste el token en localStorage para mantener la sesión entre recargas.
 */

import { create } from "zustand";
import client from "../api/client";

const TOKEN_KEY = "gastosai_token";
const USER_KEY = "gastosai_user";

export const useAuthStore = create((set, get) => ({
  token: localStorage.getItem(TOKEN_KEY) || null,
  usuario: JSON.parse(localStorage.getItem(USER_KEY) || "null"),
  cargando: false,
  error: null,

  get autenticado() {
    return !!get().token;
  },

  setToken: (token, usuario) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(usuario));
    // Inyectar token en todas las peticiones axios
    client.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    set({ token, usuario, error: null });
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    delete client.defaults.headers.common["Authorization"];
    set({ token: null, usuario: null, error: null });
  },

  inicializar: () => {
    // Restaurar token al arrancar la app
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      client.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    }
  },

  login: async (email, password) => {
    set({ cargando: true, error: null });
    try {
      const { data } = await client.post("/auth/login", { email, password });
      get().setToken(data.access_token, data.usuario);
      return true;
    } catch (err) {
      const msg = err.response?.data?.detail || "Error al iniciar sesión";
      set({ error: msg });
      return false;
    } finally {
      set({ cargando: false });
    }
  },

  registro: async (email, nombre, password) => {
    set({ cargando: true, error: null });
    try {
      const { data } = await client.post("/auth/registro", { email, nombre, password });
      get().setToken(data.access_token, data.usuario);
      return true;
    } catch (err) {
      const msg = err.response?.data?.detail || "Error al registrarse";
      set({ error: msg });
      return false;
    } finally {
      set({ cargando: false });
    }
  },
}));
