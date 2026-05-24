/**
 * Store de autenticación con Zustand v5.
 */

import { create } from "zustand";
import client from "../api/client";

const TOKEN_KEY = "gastosai_token";
const USER_KEY  = "gastosai_user";

export const useAuthStore = create((set, get) => ({
  token:    localStorage.getItem(TOKEN_KEY) || null,
  usuario:  JSON.parse(localStorage.getItem(USER_KEY) || "null"),
  cargando: false,
  error:    null,

  inicializar: () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      client.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    }
  },

  setToken: (token, usuario) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(usuario));
    client.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    set({ token, usuario, error: null });
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    delete client.defaults.headers.common["Authorization"];
    set({ token: null, usuario: null, error: null });
  },

  login: async (email, password) => {
    set({ cargando: true, error: null });
    try {
      const { data } = await client.post("/auth/login", { email, password });
      // setToken actualiza el store — React re-renderiza y RutaProtegida redirige
      get().setToken(data.access_token, data.usuario);
      return true;
    } catch (err) {
      const msg = err.response?.data?.detail || "Email o contraseña incorrectos";
      set({ error: msg, cargando: false });
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
      set({ error: msg, cargando: false });
      return false;
    } finally {
      set({ cargando: false });
    }
  },
}));
