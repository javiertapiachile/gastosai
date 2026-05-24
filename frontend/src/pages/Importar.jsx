/**
 * Página de importación con progreso real, historial paginado,
 * reclasificación y eliminación.
 */

import { useState, useRef, useCallback, useEffect } from "react";
import client from "../api/client";

const ESTADOS_TEXTO = {
  pendiente:    "En cola...",
  procesando:   "Parseando...",
  clasificando: "Clasificando con IA...",
  completado:   "Completado",
  error:        "Error",
};

const ESTADOS_COLOR = {
  pendiente:    "var(--text-tertiary)",
  procesando:   "var(--accent)",
  clasificando: "#7F77DD",
  completado:   "var(--success)",
  error:        "var(--danger)",
};

const POR_PAGINA = 10;

function FilaProgreso({ batch, onEliminar, onReclasificar, accionando }) {
  const color = ESTADOS_COLOR[batch.estado];
  const enClasificando = batch.estado === "clasificando";
  const enProcesando = batch.estado === "procesando";
  const completado = batch.estado === "completado";
  const conError = batch.estado === "error";

  // Progreso real: durante clasificación usamos transacciones_procesadas/total
  const pct = completado ? 100
    : enClasificando && batch.total_transacciones > 0
      ? Math.round((batch.transacciones_procesadas / batch.total_transacciones) * 100)
    : enProcesando ? Math.round(batch.progreso)
    : 0;

  return (
    <div style={styles.filaProgreso}>
      <div style={styles.filaTop}>
        <span style={styles.filaNombre} title={batch.nombre_archivo}>
          {batch.nombre_archivo.length > 38
            ? batch.nombre_archivo.slice(0, 35) + "..."
            : batch.nombre_archivo}
        </span>
        <span style={{ color, fontSize: 12, fontWeight: 500, whiteSpace: "nowrap" }}>
          {ESTADOS_TEXTO[batch.estado]}
        </span>
      </div>

      <div style={styles.barraTrack}>
        <div style={{
          ...styles.barraFill,
          width: `${pct}%`,
          backgroundColor: color,
          transition: "width 0.6s ease",
        }} />
      </div>

      <div style={styles.filaBottom}>
        <span style={{ fontSize: 11, color: "var(--text-tertiary)" }}>
          {completado && `✓ ${batch.total_transacciones} transacciones`}
          {conError && (
            <span>
              ✗ {(batch.mensaje_error || "Error").slice(0, 55)}
              {batch.total_transacciones === 0 && " — presiona 🔄 para reprocesar"}
            </span>
          )}
          {enClasificando && batch.total_transacciones > 0 &&
            `${batch.transacciones_procesadas} / ${batch.total_transacciones} clasificadas · ${pct}%`}
          {enClasificando && batch.total_transacciones === 0 && "Iniciando clasificación..."}
          {enProcesando && `Parseando... ${pct}%`}
        </span>
        <div style={styles.filaBotones}>
          <button
            style={{ ...styles.btnIcono, opacity: accionando ? 0.4 : 1 }}
            onClick={() => onReclasificar(batch.id)}
            disabled={!!accionando}
            title={batch.total_transacciones === 0 ? "Reprocesar archivo completo" : "Reclasificar con IA"}
          >🔄</button>
          <button
            style={{ ...styles.btnIcono, ...styles.btnEliminar, opacity: accionando ? 0.4 : 1 }}
            onClick={() => onEliminar(batch)}
            disabled={!!accionando}
            title="Eliminar"
          >🗑️</button>
        </div>
      </div>
    </div>
  );
}

export default function ImportarPage() {
  const [arrastrandoSobre, setArrastrandoSobre] = useState(false);
  const [subiendo, setSubiendo] = useState(false);
  const [batchesActivos, setBatchesActivos] = useState([]);
  const [historial, setHistorial] = useState([]);
  const [totalHistorial, setTotalHistorial] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [error, setError] = useState(null);
  const [accionando, setAccionando] = useState(null);
  const inputRef = useRef(null);
  const pollingRef = useRef(null);

  useEffect(() => {
    cargarHistorial(pagina);
    return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
  }, [pagina]);

  async function cargarHistorial(pag = 1) {
    try {
      const [{ data: items }, { data: meta }] = await Promise.all([
        client.get("/uploads/", { params: { pagina: pag, por_pagina: POR_PAGINA } }),
        client.get("/uploads/meta"),
      ]);
      setHistorial(items);
      setTotalHistorial(meta.total);
    } catch { /* silencioso */ }
  }

  function iniciarPollingLote(batchIds) {
    if (pollingRef.current) clearInterval(pollingRef.current);

    pollingRef.current = setInterval(async () => {
      try {
        // Una sola llamada para todos los batches activos
        const ids = batchIds.join(",");
        const { data: resultados } = await client.get(`/uploads/bulk/estado?ids=${ids}`);

        setBatchesActivos(resultados);

        const todosTerminaron = resultados.every(
          b => b.estado === "completado" || b.estado === "error"
        );

        if (todosTerminaron) {
          clearInterval(pollingRef.current);
          setSubiendo(false);
          setTimeout(() => {
            setBatchesActivos([]);
            cargarHistorial(1);
            setPagina(1);
          }, 2000);
        }
      } catch {
        clearInterval(pollingRef.current);
        setSubiendo(false);
      }
    }, 1500);
  }

  async function subirArchivos(archivos) {
    setError(null);
    const validos = [];
    const rechazados = [];

    for (const archivo of archivos) {
      const ext = archivo.name.split(".").pop().toLowerCase();
      if (!["csv", "xlsx", "pdf"].includes(ext)) {
        rechazados.push(`${archivo.name}: formato no soportado`);
      } else if (archivo.size > 50 * 1024 * 1024) {
        rechazados.push(`${archivo.name}: supera 50 MB`);
      } else {
        validos.push(archivo);
      }
    }

    if (rechazados.length > 0) setError(`Ignorados: ${rechazados.join(" · ")}`);
    if (validos.length === 0) return;

    setSubiendo(true);
    const formData = new FormData();

    try {
      let batches;
      if (validos.length === 1) {
        formData.append("file", validos[0]);
        const { data } = await client.post("/uploads/", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        batches = [data];
      } else {
        validos.forEach(f => formData.append("files", f));
        const { data } = await client.post("/uploads/lote", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        batches = data;
      }

      setBatchesActivos(batches);
      iniciarPollingLote(batches.map(b => b.id));
    } catch (err) {
      setError(err.response?.data?.detail || "Error al subir");
      setSubiendo(false);
    }
  }

  async function reclasificar(batchId) {
    setAccionando(batchId);
    try {
      await client.post(`/uploads/${batchId}/reclasificar`);
      const { data } = await client.get(`/uploads/${batchId}`);
      setBatchesActivos([data]);
      iniciarPollingLote([batchId]);
    } catch (err) {
      setError(err.response?.data?.detail || "Error al reclasificar");
    } finally {
      setAccionando(null);
    }
  }

  async function eliminar(batch) {
    if (!confirm(
      `¿Eliminar "${batch.nombre_archivo}"?\n\nSe borrarán las ${batch.total_transacciones} transacciones asociadas.`
    )) return;

    setAccionando(batch.id);
    try {
      await client.delete(`/uploads/${batch.id}`);
      cargarHistorial(pagina);
    } catch (err) {
      setError(err.response?.data?.detail || "Error al eliminar");
    } finally {
      setAccionando(null);
    }
  }

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setArrastrandoSobre(false);
    const archivos = Array.from(e.dataTransfer.files);
    if (archivos.length > 0) subirArchivos(archivos);
  }, []);

  const totalPaginas = Math.ceil(totalHistorial / POR_PAGINA);

  return (
    <div style={styles.wrapper}>
      <h1 style={styles.titulo}>Importar extractos</h1>
      <p style={styles.subtitulo}>
        Arrastra uno o varios archivos. GastosAI clasificará cada transacción automáticamente.
      </p>

      {/* Drop zone */}
      <div
        style={{
          ...styles.dropZone,
          ...(arrastrandoSobre ? styles.dropZoneActiva : {}),
          ...(subiendo ? styles.dropZoneSubiendo : {}),
        }}
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setArrastrandoSobre(true); }}
        onDragLeave={() => setArrastrandoSobre(false)}
      >
        <div style={styles.dropIcono}>{subiendo ? "⏳" : "📂"}</div>
        <p style={styles.dropTitulo}>{subiendo ? "Procesando..." : "Arrastra tus extractos aquí"}</p>
        <p style={styles.dropSub}>CSV · XLSX · PDF — hasta 50 MB · múltiples archivos</p>
        {!subiendo && (
          <>
            <button style={styles.botonSeleccionar} onClick={() => inputRef.current?.click()}>
              Seleccionar archivos
            </button>
            <input
              ref={inputRef} type="file" accept=".csv,.xlsx,.pdf" multiple
              style={{ display: "none" }}
              onChange={(e) => {
                const f = Array.from(e.target.files);
                if (f.length > 0) subirArchivos(f);
                e.target.value = "";
              }}
            />
          </>
        )}
      </div>

      {error && <div style={styles.errorBox}>⚠️ {error}</div>}

      {/* Batches activos con progreso */}
      {batchesActivos.length > 0 && (
        <div style={styles.loteBox}>
          <div style={styles.loteHeader}>
            <span style={styles.loteTitulo}>
              Procesando {batchesActivos.length} {batchesActivos.length === 1 ? "archivo" : "archivos"}
            </span>
            <span style={{ fontSize: 12, color: "var(--text-tertiary)" }}>
              {batchesActivos.filter(b => b.estado === "completado").length} completados
            </span>
          </div>
          {batchesActivos.map(batch => (
            <FilaProgreso
              key={batch.id}
              batch={batch}
              onEliminar={eliminar}
              onReclasificar={reclasificar}
              accionando={accionando === batch.id}
            />
          ))}
        </div>
      )}

      {/* Historial paginado */}
      {(historial.length > 0 || totalHistorial > 0) && (
        <div style={styles.historialBox}>
          <div style={styles.historialHeader}>
            <h2 style={styles.historialTitulo}>Historial de importaciones</h2>
            <span style={{ fontSize: 12, color: "var(--text-tertiary)" }}>
              {totalHistorial} archivos · {historial.reduce((s, h) => s + (h.total_transacciones || 0), 0)} tx en esta página
            </span>
          </div>

          {historial.map((h) => (
            <div key={h.id} style={styles.historialItem}>
              <div style={styles.historialLeft}>
                <span style={styles.historialNombre}>{h.nombre_archivo}</span>
                <span style={styles.historialFecha}>
                  {new Date(h.creado_en).toLocaleDateString("es-CL", {
                    day: "2-digit", month: "short", year: "numeric"
                  })}
                </span>
              </div>
              <div style={styles.historialRight}>
                <span style={{ fontSize: 12, color: "var(--text-secondary)", minWidth: 40, textAlign: "right" }}>
                  {h.total_transacciones} tx
                </span>
                <span style={{
                  fontSize: 11, fontWeight: 500, padding: "2px 8px",
                  borderRadius: "var(--radius-full)", whiteSpace: "nowrap",
                  color: ESTADOS_COLOR[h.estado],
                  backgroundColor: `${ESTADOS_COLOR[h.estado]}18`,
                }}>
                  {ESTADOS_TEXTO[h.estado]}
                </span>
                <button
                  style={{ ...styles.btnIcono, opacity: accionando === h.id ? 0.4 : 1 }}
                  onClick={() => reclasificar(h.id)}
                  disabled={accionando === h.id}
                  title={h.total_transacciones === 0 ? "Reprocesar archivo" : "Reclasificar con IA"}
                >🔄</button>
                <button
                  style={{ ...styles.btnIcono, ...styles.btnEliminar, opacity: accionando === h.id ? 0.4 : 1 }}
                  onClick={() => eliminar(h)}
                  disabled={accionando === h.id}
                  title="Eliminar"
                >🗑️</button>
              </div>
            </div>
          ))}

          {/* Paginación */}
          {totalPaginas > 1 && (
            <div style={styles.paginacion}>
              <button
                style={styles.btnPag}
                disabled={pagina <= 1}
                onClick={() => setPagina(p => p - 1)}
              >← Anterior</button>
              <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                {pagina} / {totalPaginas}
              </span>
              <button
                style={styles.btnPag}
                disabled={pagina >= totalPaginas}
                onClick={() => setPagina(p => p + 1)}
              >Siguiente →</button>
            </div>
          )}
        </div>
      )}

      {historial.length === 0 && !subiendo && totalHistorial === 0 && (
        <div style={{ textAlign: "center", padding: 32, color: "var(--text-tertiary)", fontSize: 13 }}>
          Aún no has importado ningún extracto.
        </div>
      )}
    </div>
  );
}

const styles = {
  wrapper: { maxWidth: 720, margin: "0 auto" },
  titulo: { fontSize: 22, fontWeight: 600, marginBottom: 8 },
  subtitulo: { color: "var(--text-secondary)", marginBottom: 28, fontSize: 14 },
  dropZone: {
    border: "2px dashed var(--border-strong)", borderRadius: "var(--radius-xl)",
    padding: "40px 32px", textAlign: "center", cursor: "pointer",
    transition: "all 0.2s ease", backgroundColor: "var(--bg-primary)", marginBottom: 20,
  },
  dropZoneActiva: { borderColor: "var(--accent)", backgroundColor: "var(--accent-light)" },
  dropZoneSubiendo: { cursor: "default", opacity: 0.8 },
  dropIcono: { fontSize: 36, marginBottom: 12 },
  dropTitulo: { fontSize: 15, fontWeight: 600, marginBottom: 6 },
  dropSub: { fontSize: 13, color: "var(--text-secondary)", marginBottom: 20 },
  botonSeleccionar: {
    backgroundColor: "var(--accent)", color: "white", border: "none",
    borderRadius: "var(--radius-md)", padding: "9px 20px", fontSize: 13, fontWeight: 500, cursor: "pointer",
  },
  errorBox: {
    backgroundColor: "var(--danger-light)", color: "var(--danger)",
    borderRadius: "var(--radius-md)", padding: "12px 16px", fontSize: 13, marginBottom: 16,
  },
  loteBox: {
    backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)", overflow: "hidden", marginBottom: 20,
  },
  loteHeader: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "12px 16px", borderBottom: "1px solid var(--border-default)",
    backgroundColor: "var(--bg-secondary)",
  },
  loteTitulo: { fontSize: 13, fontWeight: 600 },
  filaProgreso: { padding: "12px 16px", borderBottom: "1px solid var(--border-default)" },
  filaTop: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 },
  filaNombre: { fontSize: 13, fontWeight: 500 },
  barraTrack: {
    height: 5, backgroundColor: "var(--bg-secondary)",
    borderRadius: "var(--radius-full)", overflow: "hidden", marginBottom: 5,
  },
  barraFill: { height: "100%", borderRadius: "var(--radius-full)" },
  filaBottom: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  filaBotones: { display: "flex", gap: 4 },
  historialBox: {
    backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)", overflow: "hidden",
  },
  historialHeader: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "12px 20px", borderBottom: "1px solid var(--border-default)",
  },
  historialTitulo: { fontSize: 13, fontWeight: 600, color: "var(--text-secondary)" },
  historialItem: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "11px 20px", borderBottom: "1px solid var(--border-default)",
  },
  historialLeft: { display: "flex", flexDirection: "column", gap: 3 },
  historialNombre: { fontSize: 13, fontWeight: 500 },
  historialFecha: { fontSize: 11, color: "var(--text-tertiary)" },
  historialRight: { display: "flex", alignItems: "center", gap: 8 },
  btnIcono: {
    background: "none", border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-sm)", padding: "3px 7px", cursor: "pointer", fontSize: 13,
  },
  btnEliminar: { borderColor: "var(--danger-light)" },
  paginacion: {
    display: "flex", justifyContent: "center", alignItems: "center",
    gap: 16, padding: "12px 20px",
  },
  btnPag: {
    fontSize: 13, border: "1px solid var(--border-default)", borderRadius: "var(--radius-md)",
    padding: "5px 14px", cursor: "pointer", backgroundColor: "var(--bg-secondary)",
    color: "var(--text-secondary)",
  },
};
