/**
 * Página de importación con subida por lote, progreso individual,
 * reclasificación y eliminación de archivos.
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

function FilaProgreso({ batch, onEliminar, onReclasificar, accionando }) {
  const color = ESTADOS_COLOR[batch.estado];
  const enProgreso = ["pendiente", "procesando", "clasificando"].includes(batch.estado);
  const completado = batch.estado === "completado";
  const conError = batch.estado === "error";

  return (
    <div style={styles.filaProgreso}>
      <div style={styles.filaTop}>
        <span style={styles.filaNombre} title={batch.nombre_archivo}>
          {batch.nombre_archivo.length > 35
            ? batch.nombre_archivo.slice(0, 32) + "..."
            : batch.nombre_archivo}
        </span>
        <span style={{ color, fontSize: 12, fontWeight: 500, whiteSpace: "nowrap" }}>
          {ESTADOS_TEXTO[batch.estado]}
        </span>
      </div>

      {/* Barra de progreso */}
      <div style={styles.barraTrack}>
        <div style={{
          ...styles.barraFill,
          width: completado ? "100%" : enProgreso ? "100%" : `${batch.progreso}%`,
          backgroundColor: color,
          opacity: enProgreso && batch.estado !== "procesando" ? 0.7 : 1,
          backgroundImage: batch.estado === "clasificando"
            ? "repeating-linear-gradient(90deg, transparent, transparent 10px, rgba(255,255,255,0.2) 10px, rgba(255,255,255,0.2) 20px)"
            : "none",
          transition: "width 0.4s ease",
        }} />
      </div>

      <div style={styles.filaBottom}>
        {completado && (
          <span style={{ color: "var(--success)", fontSize: 11 }}>
            ✓ {batch.total_transacciones} transacciones
          </span>
        )}
        {conError && (
          <span style={{ color: "var(--danger)", fontSize: 11 }} title={batch.mensaje_error}>
            ✗ {(batch.mensaje_error || "Error desconocido").slice(0, 60)}
          </span>
        )}
        {enProgreso && (
          <span style={{ color: "var(--text-tertiary)", fontSize: 11 }}>
            {batch.estado === "clasificando"
              ? "Esto puede tomar varios minutos..."
              : `${batch.transacciones_procesadas}/${batch.total_transacciones || "?"}`}
          </span>
        )}

        <div style={styles.filaBotones}>
          <button
            style={{ ...styles.btnIcono, opacity: accionando ? 0.4 : 1 }}
            onClick={() => onReclasificar(batch.id)}
            disabled={!!accionando}
            title="Reclasificar con IA"
          >🔄</button>
          <button
            style={{ ...styles.btnIcono, ...styles.btnEliminar, opacity: accionando ? 0.4 : 1 }}
            onClick={() => onEliminar(batch)}
            disabled={!!accionando}
            title="Eliminar archivo y transacciones"
          >🗑️</button>
        </div>
      </div>
    </div>
  );
}

export default function ImportarPage() {
  const [arrastrandoSobre, setArrastrandoSobre] = useState(false);
  const [subiendo, setSubiendo] = useState(false);
  const [batchesActivos, setBatchesActivos] = useState([]); // batches en progreso
  const [historial, setHistorial] = useState([]);
  const [error, setError] = useState(null);
  const [accionando, setAccionando] = useState(null);
  const inputRef = useRef(null);
  const pollingRef = useRef(null);

  useEffect(() => {
    cargarHistorial();
    return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
  }, []);

  async function cargarHistorial() {
    try {
      const { data } = await client.get("/uploads/");
      setHistorial(data);
    } catch { /* silencioso */ }
  }

  function iniciarPollingLote(batchIds) {
    if (pollingRef.current) clearInterval(pollingRef.current);

    pollingRef.current = setInterval(async () => {
      try {
        // Hacer polling de todos los batches activos en paralelo
        const resultados = await Promise.all(
          batchIds.map(id => client.get(`/uploads/${id}`).then(r => r.data))
        );

        setBatchesActivos(resultados);

        // Si todos terminaron, detener polling y recargar historial
        const todosTerminaron = resultados.every(
          b => b.estado === "completado" || b.estado === "error"
        );

        if (todosTerminaron) {
          clearInterval(pollingRef.current);
          setSubiendo(false);
          setTimeout(() => {
            setBatchesActivos([]);
            cargarHistorial();
          }, 2000);
        }
      } catch {
        clearInterval(pollingRef.current);
        setSubiendo(false);
      }
    }, 2000);
  }

  async function subirArchivos(archivos) {
    setError(null);

    // Validar cada archivo en el cliente
    const validos = [];
    const rechazados = [];

    for (const archivo of archivos) {
      const ext = archivo.name.split(".").pop().toLowerCase();
      if (!["csv", "xlsx", "pdf"].includes(ext)) {
        rechazados.push(`${archivo.name}: formato .${ext} no soportado`);
      } else if (archivo.size > 50 * 1024 * 1024) {
        rechazados.push(`${archivo.name}: supera 50 MB`);
      } else {
        validos.push(archivo);
      }
    }

    if (rechazados.length > 0) {
      setError(`Archivos ignorados: ${rechazados.join(" · ")}`);
    }

    if (validos.length === 0) return;

    setSubiendo(true);

    const formData = new FormData();
    for (const archivo of validos) {
      formData.append("files", archivo);
    }

    try {
      const endpoint = validos.length === 1 ? "/uploads/" : "/uploads/lote";

      let batches;
      if (validos.length === 1) {
        // Endpoint original para 1 archivo
        formData.delete("files");
        formData.append("file", validos[0]);
        const { data } = await client.post(endpoint, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        batches = [data];
      } else {
        // Endpoint de lote para múltiples
        const { data } = await client.post(endpoint, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        batches = data;
      }

      setBatchesActivos(batches);
      iniciarPollingLote(batches.map(b => b.id));
    } catch (err) {
      setError(err.response?.data?.detail || "Error al subir los archivos");
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
      `¿Eliminar "${batch.nombre_archivo}"?\n\nSe borrarán también las ${batch.total_transacciones} transacciones asociadas.`
    )) return;

    setAccionando(batch.id);
    try {
      await client.delete(`/uploads/${batch.id}`);
      setHistorial(h => h.filter(x => x.id !== batch.id));
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

  const onChangeInput = (e) => {
    const archivos = Array.from(e.target.files);
    if (archivos.length > 0) subirArchivos(archivos);
    e.target.value = "";
  };

  return (
    <div style={styles.wrapper}>
      <style>{`
        @keyframes stripe {
          0% { background-position: 0 0; }
          100% { background-position: 40px 0; }
        }
      `}</style>

      <h1 style={styles.titulo}>Importar extractos</h1>
      <p style={styles.subtitulo}>
        Arrastra uno o varios archivos a la vez. GastosAI procesará cada uno automáticamente.
      </p>

      {/* Zona de drop */}
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
        <p style={styles.dropTitulo}>
          {subiendo ? "Procesando archivos..." : "Arrastra tus extractos aquí"}
        </p>
        <p style={styles.dropSub}>
          CSV · XLSX · PDF — hasta 50 MB por archivo · múltiples archivos a la vez
        </p>

        {!subiendo && (
          <>
            <button style={styles.botonSeleccionar} onClick={() => inputRef.current?.click()}>
              Seleccionar archivos
            </button>
            <input
              ref={inputRef}
              type="file"
              accept=".csv,.xlsx,.pdf"
              multiple
              style={{ display: "none" }}
              onChange={onChangeInput}
            />
          </>
        )}
      </div>

      {error && <div style={styles.errorBox}>⚠️ {error}</div>}

      {/* Progreso de batches activos */}
      {batchesActivos.length > 0 && (
        <div style={styles.loteBox}>
          <div style={styles.loteHeader}>
            <span style={styles.loteTitulo}>
              Procesando {batchesActivos.length} {batchesActivos.length === 1 ? "archivo" : "archivos"}
            </span>
            <span style={styles.loteResumen}>
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

      {/* Historial */}
      {historial.length > 0 && (
        <div style={styles.historialBox}>
          <div style={styles.historialHeader}>
            <h2 style={styles.historialTitulo}>Historial de importaciones</h2>
            <span style={styles.historialCount}>
              {historial.length} archivos · {historial.reduce((s, h) => s + h.total_transacciones, 0)} transacciones
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
                <span style={styles.historialTx}>{h.total_transacciones} tx</span>
                <span style={{
                  ...styles.estadoBadge,
                  color: ESTADOS_COLOR[h.estado],
                  backgroundColor: `${ESTADOS_COLOR[h.estado]}18`,
                }}>
                  {ESTADOS_TEXTO[h.estado]}
                </span>
                <button
                  style={{ ...styles.btnIcono, opacity: accionando === h.id ? 0.4 : 1 }}
                  onClick={() => reclasificar(h.id)}
                  disabled={accionando === h.id}
                  title="Reclasificar con IA"
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
        </div>
      )}

      {historial.length === 0 && !subiendo && (
        <div style={styles.vacio}>
          Aún no has importado ningún extracto. Sube tu primer archivo arriba.
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
    border: "2px dashed var(--border-strong)",
    borderRadius: "var(--radius-xl)",
    padding: "40px 32px",
    textAlign: "center",
    cursor: "pointer",
    transition: "all 0.2s ease",
    backgroundColor: "var(--bg-primary)",
    marginBottom: 20,
  },
  dropZoneActiva: { borderColor: "var(--accent)", backgroundColor: "var(--accent-light)" },
  dropZoneSubiendo: { cursor: "default", opacity: 0.8 },
  dropIcono: { fontSize: 36, marginBottom: 12 },
  dropTitulo: { fontSize: 15, fontWeight: 600, marginBottom: 6, color: "var(--text-primary)" },
  dropSub: { fontSize: 13, color: "var(--text-secondary)", marginBottom: 20 },
  botonSeleccionar: {
    backgroundColor: "var(--accent)", color: "white", border: "none",
    borderRadius: "var(--radius-md)", padding: "9px 20px",
    fontSize: 13, fontWeight: 500, cursor: "pointer",
  },

  errorBox: {
    backgroundColor: "var(--danger-light)", color: "var(--danger)",
    borderRadius: "var(--radius-md)", padding: "12px 16px",
    fontSize: 13, marginBottom: 16,
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
  loteTitulo: { fontSize: 13, fontWeight: 600, color: "var(--text-primary)" },
  loteResumen: { fontSize: 12, color: "var(--text-tertiary)" },

  filaProgreso: {
    padding: "12px 16px",
    borderBottom: "1px solid var(--border-default)",
  },
  filaTop: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 },
  filaNombre: { fontSize: 13, fontWeight: 500, color: "var(--text-primary)" },
  barraTrack: {
    height: 4, backgroundColor: "var(--bg-secondary)",
    borderRadius: "var(--radius-full)", overflow: "hidden", marginBottom: 6,
  },
  barraFill: { height: "100%", borderRadius: "var(--radius-full)", transition: "width 0.4s ease" },
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
  historialCount: { fontSize: 12, color: "var(--text-tertiary)" },
  historialItem: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "11px 20px", borderBottom: "1px solid var(--border-default)",
  },
  historialLeft: { display: "flex", flexDirection: "column", gap: 3 },
  historialNombre: { fontSize: 13, fontWeight: 500, color: "var(--text-primary)" },
  historialFecha: { fontSize: 11, color: "var(--text-tertiary)" },
  historialRight: { display: "flex", alignItems: "center", gap: 8 },
  historialTx: { fontSize: 12, color: "var(--text-secondary)", minWidth: 40, textAlign: "right" },
  estadoBadge: {
    fontSize: 11, fontWeight: 500, padding: "2px 8px",
    borderRadius: "var(--radius-full)", whiteSpace: "nowrap",
  },
  btnIcono: {
    background: "none", border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-sm)", padding: "3px 7px",
    cursor: "pointer", fontSize: 13, lineHeight: 1,
  },
  btnEliminar: { borderColor: "var(--danger-light)" },
  vacio: {
    textAlign: "center", padding: "32px",
    color: "var(--text-tertiary)", fontSize: 13,
  },
};
