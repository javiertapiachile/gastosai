/**
 * Hook genérico para fetch de datos con estado de carga y error.
 * Recarga automáticamente cuando cambian los parámetros.
 */

import { useState, useEffect, useCallback } from "react";
import client from "../api/client";

export function useFetch(url, params = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const clave = JSON.stringify({ url, params });

  const fetchData = useCallback(async () => {
    if (!url) return;
    setLoading(true);
    setError(null);
    try {
      const { data: resultado } = await client.get(url, { params });
      setData(resultado);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Error de red");
    } finally {
      setLoading(false);
    }
  }, [clave]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
