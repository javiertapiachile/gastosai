/**
 * Store global con Zustand.
 * Centraliza el estado de filtros de fecha para que
 * Dashboard y Transacciones estén sincronizados.
 */

import { create } from "zustand";

const ahora = new Date();

export const useFiltersStore = create((set) => ({
  mes: ahora.getMonth() + 1,   // 1-12
  anio: ahora.getFullYear(),

  setMes: (mes) => set({ mes }),
  setAnio: (anio) => set({ anio }),
  setFiltros: (mes, anio) => set({ mes, anio }),
  limpiarFiltros: () => set({ mes: null, anio: null }),
}));
