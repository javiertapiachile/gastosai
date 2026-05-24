/**
 * Página de transacciones — tabla paginada con búsqueda y filtros.
 */

import { useState, useCallback } from "react";
import { useFetch } from "../hooks/useFetch";
import { useFiltersStore } from "../store/filtersStore";
import TransactionTable from "../components/TransactionTable";
import MonthPicker from "../components/MonthPicker";
import client from "../api/client";

export default function TransaccionesPage() {
  const { mes, anio, setFiltros } = useFiltersStore();
  const [pagina, setPagina] = useState(1);
  const [busqueda, setBusqueda] = useState("");
  const [busquedaInput, setBusquedaInput] = useState("");
  const [categoriaId, setCategoriaId] = useState(null);
  const [soloCargas, setSoloCargas] = useState(null);
  const [recargar, setRecargar] = useState(0);

  const POR_PAGINA = 50;

  // Construir parámetros de la query
  const params = { pagina, por_pagina: POR_PAGINA };
  if (mes) params.mes = mes;
  if (anio) params.anio = anio;
  if (busqueda) params.busqueda = busqueda;
  if (categoriaId) params.categoria_id = categoriaId;
  if (soloCargas !== null) params.solo_cargos = soloCargas;

  const { data: resultado, loading, refetch } = useFetch(
    "/transactions/",
    { ...params, _r: recargar }
  );
  const { data: categorias } = useFetch("/categories/", { solo_activas: true });

  function handleBuscar(e) {
    e.preventDefault();
    setBusqueda(busquedaInput);
    setPagina(1);
  }

  function handleFiltroChange(nuevoMes, nuevoAnio) {
    setFiltros(nuevoMes, nuevoAnio);
    setPagina(1);
  }

  function handleCategoriaChange(e) {
    setCategoriaId(e.target.value ? Number(e.target.value) : null);
    setPagina(1);
  }

  async function exportarCSV() {
    const exportParams = new URLSearchParams();
    if (mes) exportParams.set("mes", mes);
    if (anio) exportParams.set("anio", anio);
    if (busqueda) exportParams.set("busqueda", busqueda);
    if (categoriaId) exportParams.set("categoria_id", categoriaId);

    try {
      const { data } = await client.get(`/transactions/?por_pagina=10000&pagina=1&${exportParams}`, {
        responseType: "blob",
      });
      // Convertir a CSV manualmente desde los datos
      window.open(`http://localhost:8000/api/v1/transactions/?por_pagina=10000&${exportParams}`, "_blank");
    } catch (err) {
      console.error("Error exportando:", err);
    }
  }

  const totalPaginas = resultado?.total_paginas ?? 0;
  const total = resultado?.total ?? 0;

  return (
    <div>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.titulo}>Transacciones</h1>
          <p style={styles.subtitulo}>
            {total > 0 ? `${total} transacciones encontradas` : "Sin resultados"}
          </p>
        </div>
      </div>

      {/* Barra de filtros */}
      <div style={styles.filtrosBar}>
        {/* Búsqueda */}
        <form onSubmit={handleBuscar} style={styles.busquedaForm}>
          <input
            type="text"
            placeholder="Buscar transacción..."
            value={busquedaInput}
            onChange={(e) => setBusquedaInput(e.target.value)}
            style={styles.inputBusqueda}
          />
          <button type="submit" style={styles.btnBuscar}>Buscar</button>
        </form>

        {/* Filtro categoría */}
        <select style={styles.select} value={categoriaId ?? ""} onChange={handleCategoriaChange}>
          <option value="">Todas las categorías</option>
          {(categorias || []).map((c) => (
            <option key={c.id} value={c.id}>{c.nombre}</option>
          ))}
        </select>

        {/* Filtro tipo */}
        <select
          style={styles.select}
          value={soloCargas === null ? "" : soloCargas.toString()}
          onChange={(e) => {
            setSoloCargas(e.target.value === "" ? null : e.target.value === "true");
            setPagina(1);
          }}
        >
          <option value="">Cargos y abonos</option>
          <option value="true">Solo cargos</option>
          <option value="false">Solo abonos</option>
        </select>

        {/* Período */}
        <MonthPicker mes={mes} anio={anio} onChange={handleFiltroChange} />
      </div>

      {/* Tabla */}
      <TransactionTable
        transacciones={resultado?.items ?? []}
        categorias={categorias ?? []}
        cargando={loading}
        onCategoriaActualizada={() => setRecargar((r) => r + 1)}
      />

      {/* Paginación */}
      {totalPaginas > 1 && (
        <div style={styles.paginacion}>
          <button
            style={styles.btnPag}
            disabled={pagina <= 1}
            onClick={() => setPagina((p) => p - 1)}
          >
            ← Anterior
          </button>
          <span style={styles.paginaInfo}>
            Página {pagina} de {totalPaginas}
          </span>
          <button
            style={styles.btnPag}
            disabled={pagina >= totalPaginas}
            onClick={() => setPagina((p) => p + 1)}
          >
            Siguiente →
          </button>
        </div>
      )}
    </div>
  );
}

const styles = {
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 20,
  },
  titulo: { fontSize: 22, fontWeight: 600, marginBottom: 4 },
  subtitulo: { fontSize: 13, color: "var(--text-secondary)" },

  filtrosBar: {
    display: "flex",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 16,
    alignItems: "center",
  },
  busquedaForm: { display: "flex", gap: 4 },
  inputBusqueda: {
    fontSize: 13,
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)",
    padding: "6px 12px",
    backgroundColor: "var(--bg-primary)",
    color: "var(--text-primary)",
    outline: "none",
    width: 220,
  },
  btnBuscar: {
    fontSize: 13,
    fontWeight: 500,
    backgroundColor: "var(--accent)",
    color: "white",
    border: "none",
    borderRadius: "var(--radius-md)",
    padding: "6px 14px",
    cursor: "pointer",
  },
  select: {
    fontSize: 13,
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)",
    padding: "6px 10px",
    backgroundColor: "var(--bg-primary)",
    color: "var(--text-secondary)",
    cursor: "pointer",
    outline: "none",
  },

  paginacion: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    gap: 16,
    marginTop: 20,
  },
  btnPag: {
    fontSize: 13,
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)",
    padding: "6px 14px",
    cursor: "pointer",
    backgroundColor: "var(--bg-primary)",
    color: "var(--text-secondary)",
  },
  paginaInfo: { fontSize: 13, color: "var(--text-secondary)" },
};
