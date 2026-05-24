/**
 * Página de importación con historial, reclasificación y eliminación de archivos.
 */

import { useState, useRef, useCallback, useEffect } from "react";
import client from "../api/client";

const ESTADOS_TEXTO = {
  pendiente:    "Esperando...",
  procesando:   "Parseando archivo...",
  clasificando: "Clasificando con IA...",
  completado:   "Completado",
  error:        "Error",
};

const ESTADOS_COLOR = {
  pendiente:    "var(--text-secondary)",
  procesando:   "var(--accent)",
  clasificando: "#7F77DD",
  completado:   "var(--success)",
  error:        "var(--danger)",
};

function BarraProgreso({ batch }) {
  const color = ESTADOS_COLOR[batch.estado];
  const enProgreso = ["procesando", "clasificando"].includes(batch.estado);

  return (
    <div style={styles.progresoBox}>
      <div style={styles.progresoHeader}>
        <span style={styles.progresoNombre}>{batch.nombre_archivo}</span>
        <span style={{ color, fontSize: 13, fontWeight: 500 }}>
          {ESTADOS_TEXTO[batch.estado]}
        </span>
      </div>
      <div style={styles.barraTrack}>
        <div style={{
          ...styles.barraFill,
          width: enProgreso ? "100%" : `${batch.progreso}%`,
          backgroundColor: color,
          transition: enProgreso ? "none" : "width 0.5s ease",
          backgroundImage: enProgreso
            ? "linear-gradient(90deg, transparent 25%, rgba(255,255,255,0.3) 50%, transparent 75%)"
            : "none",
          backgroundSize: "200% 100%",
          animation: enProgreso ? "shimmer 1.5s infinite" : "none",
        }} />
      </div>
      <div style={{ fontSize: 12, marginTop: 4 }}>
        {batch.estado === "completado" ? (
          <span style={{ color: "var(--success)" }}>
            ✅ {batch.total_transacciones} transacciones importadas y clasificadas
          </span>
        ) : batch.estado === "error" ? (
          <span style={{ color: "var(--danger)" }}>❌ {batch.mensaje_error}</span>
        ) : (
          <span style={{ color: "var(--text-secondary)" }}>
            {batch.estado === "clasificando"
              ? "Clasificando con IA — esto puede tomar varios minutos con Ollama..."
              : `${batch.transacciones_procesadas} de ${batch.total_transacciones || "?"} · ${Math.round(batch.progreso)}%`
            }
          </span>
        )}
      </div>
    </div>
  );
}

export default function ImportarPage() {
  const [arrastrandoSobre, setArrastrandoSobre] = useState(false);
  const [subiendo, setSubiendo] = useState(false);
  const [batchActivo, setBatchActivo] = useState(null);
  const [error, setError] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [accionando, setAccionando] = useState(null); // batch_id en acción
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
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = setInterval(async () => {
      try {
        const { data } = await client.get(`/uploads/${batchId}`);
        setBatchActivo(data);
        if (data.estado === "completado" || data.estado === "error") {
          clearInterval(pollingRef.current);
          setSubiendo(false);
          setAccionando(null);
          cargarHistorial();
        }
      } catch {
        clearInterval(pollingRef.current);
        setSubiendo(false);
        setAccionando(null);
      }
    }, 2000);
  }

  async function subirArchivo(archivo) {
    setError(null);
    setBatchActivo(null);

    const ext = archivo.name.split(".").pop().toLowerCase();
    if (!["csv", "xlsx", "pdf"].includes(ext)) {
      setError(`Formato .${ext} no soportado. Usa CSV, XLSX o PDF.`);
      return;
    }
    if (archivo.size > 50 * 1024 * 1024) {
      setError("Archivo demasiado grande. Máximo 50 MB.");
      return;
    }

    setSubiendo(true);
    const formData = new FormData();
    formData.append("file", archivo);

    try {
      const { data } = await client.post("/uploads/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setBatchActivo(data);
      iniciarPolling(data.id);
    } catch (err) {
      setError(err.response?.data?.detail || "Error al subir el archivo");
      setSubiendo(false);
    }
  }

  async function reclasificar(batchId) {
    setAccionando(batchId);
    setError(null);
    try {
      await client.post(`/uploads/${batchId}/reclasificar`);
      // Iniciar polling para mostrar progreso
      setBatchActivo(historial.find(h => h.id === batchId) || null);
      iniciarPolling(batchId);
    } catch (err) {
      setError(err.response?.data?.detail || "Error al reclasificar");
      setAccionando(null);
    }
  }

  async function eliminar(batch) {
    if (!confirm(
      `¿Eliminar "${batch.nombre_archivo}"?\n\nEsto borrará también las ${batch.total_transacciones} transacciones asociadas. Esta acción no se puede deshacer.`
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
    const archivo = e.dataTransfer.files[0];
    if (archivo) subirArchivo(archivo);
  }, []);

  return (
    <div style={styles.wrapper}>
      <style>{`
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>

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
              onChange={(e) => {
                const f = e.target.files[0];
                if (f) subirArchivo(f);
                e.target.value = "";
              }}
            />
          </>
        )}
      </div>

      {error && <div style={styles.errorBox}>⚠️ {error}</div>}

      {/* Progreso del batch activo */}
      {batchActivo && <BarraProgreso batch={batchActivo} />}

      {/* Historial */}
      {historial.length > 0 && (
        <div style={styles.historialBox}>
          <div style={styles.historialHeader}>
            <h2 style={styles.historialTitulo}>Historial de importaciones</h2>
            <span style={styles.historialCount}>{historial.length} archivos</span>
          </div>

          {historial.map((h) => {
            const enAccion = accionando === h.id;
            return (
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

                  {/* Botón reclasificar */}
                  <button
                    style={{
                      ...styles.btnIcono,
                      opacity: enAccion ? 0.4 : 1,
                    }}
                    onClick={() => reclasificar(h.id)}
                    disabled={enAccion}
                    title="Reclasificar todas las transacciones con IA"
                  >
                    {enAccion ? "⏳" : "🔄"}
                  </button>

                  {/* Botón eliminar */}
                  <button
                    style={{
                      ...styles.btnIcono,
                      ...styles.btnEliminar,
                      opacity: enAccion ? 0.4 : 1,
                    }}
                    onClick={() => eliminar(h)}
                    disabled={enAccion}
                    title="Eliminar archivo y todas sus transacciones"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            );
          })}
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
  wrapper: { maxWidth: 680, margin: "0 auto" },
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

  progresoBox: {
    backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)", padding: "16px 20px", marginBottom: 20,
  },
  progresoHeader: {
    display: "flex", justifyContent: "space-between",
    alignItems: "center", marginBottom: 10,
  },
  progresoNombre: { fontSize: 13, fontWeight: 500 },
  barraTrack: {
    height: 6, backgroundColor: "var(--bg-secondary)",
    borderRadius: "var(--radius-full)", overflow: "hidden", marginBottom: 8,
  },
  barraFill: { height: "100%", borderRadius: "var(--radius-full)" },

  historialBox: {
    backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)", overflow: "hidden",
  },
  historialHeader: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "14px 20px", borderBottom: "1px solid var(--border-default)",
  },
  historialTitulo: { fontSize: 13, fontWeight: 600, color: "var(--text-secondary)" },
  historialCount: { fontSize: 12, color: "var(--text-tertiary)" },
  historialItem: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "12px 20px", borderBottom: "1px solid var(--border-default)",
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
    borderRadius: "var(--radius-sm)", padding: "4px 8px",
    cursor: "pointer", fontSize: 14, lineHeight: 1,
  },
  btnEliminar: {
    borderColor: "var(--danger-light)",
  },
  vacio: {
    textAlign: "center", padding: "32px",
    color: "var(--text-tertiary)", fontSize: 13,
  },
};
