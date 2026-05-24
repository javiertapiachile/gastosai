/**
 * Página de importación con historial y botón de reclasificación manual.
 */

import { useState, useRef, useCallback, useEffect } from "react";
import client from "../api/client";

const ESTADOS_TEXTO = {
  pendiente:    "Esperando procesamiento...",
  procesando:   "Parseando archivo...",
  clasificando: "Clasificando con IA...",
  completado:   "¡Importación completada!",
  error:        "Error en la importación",
};

const ESTADOS_COLOR = {
  pendiente:    "var(--text-secondary)",
  procesando:   "var(--accent)",
  clasificando: "#7F77DD",
  completado:   "var(--success)",
  error:        "var(--danger)",
};

export default function ImportarPage() {
  const [arrastrandoSobre, setArrastrandoSobre] = useState(false);
  const [subiendo, setSubiendo] = useState(false);
  const [batch, setBatch] = useState(null);
  const [error, setError] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [reclasificando, setReclasificando] = useState(null);
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

  function iniciarPolling(batchId) {
    pollingRef.current = setInterval(async () => {
      try {
        const { data } = await client.get(`/uploads/${batchId}`);
        setBatch(data);
        if (data.estado === "completado" || data.estado === "error") {
          clearInterval(pollingRef.current);
          setSubiendo(false);
          cargarHistorial();
        }
      } catch {
        clearInterval(pollingRef.current);
        setSubiendo(false);
      }
    }, 1500);
  }

  async function subirArchivo(archivo) {
    setError(null);
    setBatch(null);

    const ext = archivo.name.split(".").pop().toLowerCase();
    if (!["csv", "xlsx", "pdf"].includes(ext)) {
      setError(`Formato .${ext} no soportado. Usa CSV, XLSX o PDF.`);
      return;
    }
    if (archivo.size > 50 * 1024 * 1024) {
      setError(`Archivo demasiado grande. Máximo 50 MB.`);
      return;
    }

    setSubiendo(true);
    const formData = new FormData();
    formData.append("file", archivo);

    try {
      const { data } = await client.post("/uploads/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setBatch(data);
      iniciarPolling(data.id);
    } catch (err) {
      setError(err.response?.data?.detail || "Error al subir el archivo");
      setSubiendo(false);
    }
  }

  async function reclasificar(batchId) {
    setReclasificando(batchId);
    try {
      await client.post(`/uploads/reclasificar/${batchId}`);
      setTimeout(cargarHistorial, 2000);
    } catch (err) {
      alert(err.response?.data?.detail || "Error al reclasificar");
    } finally {
      setTimeout(() => setReclasificando(null), 3000);
    }
  }

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setArrastrandoSobre(false);
    const archivo = e.dataTransfer.files[0];
    if (archivo) subirArchivo(archivo);
  }, []);

  return (
    <div style={styles.wrapper}>
      <h1 style={styles.titulo}>Importar extracto</h1>
      <p style={styles.subtitulo}>
        Sube tu estado de cuenta y GastosAI clasificará cada transacción automáticamente.
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
          {subiendo ? "Procesando archivo..." : "Arrastra tu extracto aquí"}
        </p>
        <p style={styles.dropSub}>CSV · XLSX · PDF — hasta 50 MB</p>

        {!subiendo && (
          <>
            <button style={styles.botonSeleccionar} onClick={() => inputRef.current?.click()}>
              Seleccionar archivo
            </button>
            <input
              ref={inputRef}
              type="file"
              accept=".csv,.xlsx,.pdf"
              style={{ display: "none" }}
              onChange={(e) => { const f = e.target.files[0]; if (f) subirArchivo(f); e.target.value = ""; }}
            />
          </>
        )}
      </div>

      {error && (
        <div style={styles.errorBox}>⚠️ {error}</div>
      )}

      {batch && (
        <div style={styles.progresoBox}>
          <div style={styles.progresoHeader}>
            <span style={styles.progresoNombre}>{batch.nombre_archivo}</span>
            <span style={{ color: ESTADOS_COLOR[batch.estado], fontSize: 13, fontWeight: 500 }}>
              {ESTADOS_TEXTO[batch.estado]}
            </span>
          </div>
          <div style={styles.barraTrack}>
            <div style={{
              ...styles.barraFill,
              width: `${batch.progreso}%`,
              backgroundColor: ESTADOS_COLOR[batch.estado],
            }} />
          </div>
          <div style={styles.progresoDetalle}>
            {batch.estado === "completado" ? (
              <span style={{ color: "var(--success)" }}>
                ✅ {batch.total_transacciones} transacciones importadas y clasificadas
              </span>
            ) : batch.estado === "error" ? (
              <span style={{ color: "var(--danger)" }}>❌ {batch.mensaje_error}</span>
            ) : (
              <span style={{ color: "var(--text-secondary)" }}>
                {batch.transacciones_procesadas} de {batch.total_transacciones || "?"} · {Math.round(batch.progreso)}%
              </span>
            )}
          </div>
        </div>
      )}

      {historial.length > 0 && (
        <div style={styles.historialBox}>
          <h2 style={styles.historialTitulo}>Historial de importaciones</h2>
          {historial.map((h) => (
            <div key={h.id} style={styles.historialItem}>
              <div style={styles.historialLeft}>
                <span style={styles.historialNombre}>{h.nombre_archivo}</span>
                <span style={styles.historialFecha}>
                  {new Date(h.creado_en).toLocaleDateString("es-CL", { day: "2-digit", month: "short", year: "numeric" })}
                </span>
              </div>
              <div style={styles.historialRight}>
                <span style={styles.historialCount}>{h.total_transacciones} tx</span>
                <span style={{
                  ...styles.historialEstado,
                  color: ESTADOS_COLOR[h.estado],
                  backgroundColor: `${ESTADOS_COLOR[h.estado]}18`,
                }}>
                  {h.estado}
                </span>
                {/* Botón de reclasificación manual */}
                <button
                  style={styles.btnReclasificar}
                  onClick={() => reclasificar(h.id)}
                  disabled={reclasificando === h.id}
                  title="Reclasificar todas las transacciones de este archivo con LLM"
                >
                  {reclasificando === h.id ? "⏳" : "🔄"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  wrapper: { maxWidth: 640, margin: "0 auto" },
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
  dropTitulo: { fontSize: 15, fontWeight: 600, marginBottom: 6 },
  dropSub: { fontSize: 13, color: "var(--text-secondary)", marginBottom: 20 },
  botonSeleccionar: {
    backgroundColor: "var(--accent)", color: "white", border: "none",
    borderRadius: "var(--radius-md)", padding: "9px 20px", fontSize: 13,
    fontWeight: 500, cursor: "pointer",
  },
  errorBox: {
    backgroundColor: "var(--danger-light)", color: "var(--danger)",
    borderRadius: "var(--radius-md)", padding: "12px 16px", fontSize: 13, marginBottom: 16,
  },
  progresoBox: {
    backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)", padding: "16px 20px", marginBottom: 24,
  },
  progresoHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 },
  progresoNombre: { fontSize: 13, fontWeight: 500 },
  barraTrack: { height: 6, backgroundColor: "var(--bg-secondary)", borderRadius: "var(--radius-full)", overflow: "hidden", marginBottom: 8 },
  barraFill: { height: "100%", borderRadius: "var(--radius-full)", transition: "width 0.5s ease" },
  progresoDetalle: { fontSize: 12 },
  historialBox: {
    backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)", overflow: "hidden",
  },
  historialTitulo: { fontSize: 13, fontWeight: 600, padding: "14px 20px", borderBottom: "1px solid var(--border-default)", color: "var(--text-secondary)" },
  historialItem: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 20px", borderBottom: "1px solid var(--border-default)" },
  historialLeft: { display: "flex", flexDirection: "column", gap: 2 },
  historialNombre: { fontSize: 13, fontWeight: 500 },
  historialFecha: { fontSize: 11, color: "var(--text-tertiary)" },
  historialRight: { display: "flex", alignItems: "center", gap: 10 },
  historialCount: { fontSize: 12, color: "var(--text-secondary)" },
  historialEstado: { fontSize: 11, fontWeight: 500, padding: "2px 8px", borderRadius: "var(--radius-full)" },
  btnReclasificar: {
    background: "none", border: "1px solid var(--border-default)", borderRadius: "var(--radius-sm)",
    padding: "3px 8px", cursor: "pointer", fontSize: 13,
  },
};
