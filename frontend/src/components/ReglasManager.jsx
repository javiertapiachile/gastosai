/**
 * Gestor de reglas de clasificación manual.
 * Permite crear reglas tipo "si descripción contiene X → categoría Y".
 */

import { useState } from "react";
import client from "../api/client";

const TIPOS_MATCH = [
  { id: "contiene", label: "contiene" },
  { id: "empieza",  label: "empieza con" },
  { id: "exacto",   label: "es exactamente" },
];

export default function ReglasManager({ reglas, categorias, onActualizado, onActualizarDefault }) {
  const [creando, setCreando] = useState(false);
  const [form, setForm] = useState({ patron: "", tipo_match: "contiene", categoria_id: "", descripcion_regla: "", prioridad: 0 });
  const [probando, setProbando] = useState("");
  const [resultadoPrueba, setResultadoPrueba] = useState(null);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);

  async function guardar() {
    if (!form.patron.trim()) return setError("El patrón es obligatorio");
    if (!form.categoria_id) return setError("Selecciona una categoría");

    setGuardando(true);
    setError(null);
    try {
      await client.post("/reglas/", {
        ...form,
        categoria_id: Number(form.categoria_id),
        prioridad: Number(form.prioridad),
      });
      setCreando(false);
      setForm({ patron: "", tipo_match: "contiene", categoria_id: "", descripcion_regla: "", prioridad: 0 });
      onActualizado?.();
    } catch (err) {
      setError(err.response?.data?.detail || "Error al guardar");
    } finally {
      setGuardando(false);
    }
  }

  async function toggleActiva(regla) {
    try {
      await client.patch(`/reglas/${regla.id}`, { activa: !regla.activa });
      onActualizado?.();
    } catch { /* silencioso */ }
  }

  async function eliminar(regla) {
    if (!confirm(`¿Eliminar la regla "${regla.patron}"?`)) return;
    try {
      await client.delete(`/reglas/${regla.id}`);
      onActualizado?.();
    } catch { /* silencioso */ }
  }

  async function probar() {
    if (!probando.trim()) return;
    try {
      const { data } = await client.post("/reglas/probar", { descripcion: probando });
      setResultadoPrueba(data);
    } catch { /* silencioso */ }
  }

  return (
    <div style={styles.seccion}>
      <div style={styles.header}>
        <div>
          <h2 style={styles.titulo}>Reglas de clasificación</h2>
          <p style={styles.desc}>Se aplican antes del LLM — mayor prioridad y velocidad.</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {onActualizarDefault && (
            <button
              style={{ ...styles.btnCrear, backgroundColor: "var(--bg-secondary)", color: "var(--text-secondary)", border: "1px solid var(--border-default)" }}
              onClick={onActualizarDefault}
              title="Sincroniza los últimos comercios conocidos de Chile"
            >
              🔄 Actualizar lista
            </button>
          )}
          <button style={styles.btnCrear} onClick={() => { setCreando(true); setError(null); }}>
            + Nueva regla
          </button>
        </div>
      </div>

      {/* Formulario de creación */}
      {creando && (
        <div style={styles.formBox}>
          <div style={styles.formGrid}>
            <div style={styles.campo}>
              <label style={styles.label}>Si la descripción...</label>
              <select
                style={styles.select}
                value={form.tipo_match}
                onChange={e => setForm({ ...form, tipo_match: e.target.value })}
              >
                {TIPOS_MATCH.map(t => (
                  <option key={t.id} value={t.id}>{t.label}</option>
                ))}
              </select>
            </div>

            <div style={styles.campo}>
              <label style={styles.label}>Patrón de texto</label>
              <input
                autoFocus
                style={styles.input}
                placeholder="ej: COPEC, RAPPI*, AMZN"
                value={form.patron}
                onChange={e => setForm({ ...form, patron: e.target.value })}
                onKeyDown={e => e.key === "Enter" && guardar()}
              />
            </div>

            <div style={styles.campo}>
              <label style={styles.label}>Asignar categoría</label>
              <select
                style={styles.select}
                value={form.categoria_id}
                onChange={e => setForm({ ...form, categoria_id: e.target.value })}
              >
                <option value="">Seleccionar...</option>
                {(categorias || []).map(c => (
                  <option key={c.id} value={c.id}>{c.nombre}</option>
                ))}
              </select>
            </div>

            <div style={styles.campo}>
              <label style={styles.label}>Prioridad (0-100)</label>
              <input
                type="number"
                min={0} max={100}
                style={{ ...styles.input, width: 70 }}
                value={form.prioridad}
                onChange={e => setForm({ ...form, prioridad: e.target.value })}
              />
            </div>
          </div>

          <div style={styles.campo}>
            <label style={styles.label}>Descripción (opcional)</label>
            <input
              style={styles.input}
              placeholder="ej: Estaciones de bencina Copec"
              value={form.descripcion_regla}
              onChange={e => setForm({ ...form, descripcion_regla: e.target.value })}
            />
          </div>

          {error && <div style={styles.errorBox}>{error}</div>}

          <div style={styles.formAcciones}>
            <button style={styles.btnGuardar} onClick={guardar} disabled={guardando}>
              {guardando ? "Guardando..." : "Guardar regla"}
            </button>
            <button style={styles.btnCancelar} onClick={() => { setCreando(false); setError(null); }}>
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Probador de reglas */}
      <div style={styles.probadorBox}>
        <div style={styles.probadorRow}>
          <input
            style={{ ...styles.input, flex: 1 }}
            placeholder="Prueba una descripción: COPEC RUTA5 #2341"
            value={probando}
            onChange={e => { setProbando(e.target.value); setResultadoPrueba(null); }}
            onKeyDown={e => e.key === "Enter" && probar()}
          />
          <button style={styles.btnProbar} onClick={probar}>Probar</button>
        </div>
        {resultadoPrueba && (
          <div style={{
            ...styles.resultadoPrueba,
            backgroundColor: resultadoPrueba.coincide ? "var(--success-light)" : "var(--bg-secondary)",
            color: resultadoPrueba.coincide ? "var(--success)" : "var(--text-secondary)",
          }}>
            {resultadoPrueba.coincide
              ? `✅ Coincide → ${resultadoPrueba.categoria_nombre}`
              : "❌ Sin coincidencia — usaría el LLM"}
          </div>
        )}
      </div>

      {/* Lista de reglas */}
      {(!reglas || reglas.length === 0) ? (
        <div style={styles.vacio}>No hay reglas definidas. Las reglas aceleran la clasificación.</div>
      ) : (
        <div style={styles.lista}>
          {reglas.map(r => (
            <div key={r.id} style={{ ...styles.item, opacity: r.activa ? 1 : 0.5 }}>
              <div style={styles.itemLeft}>
                <div style={styles.itemPatron}>
                  <span style={styles.chipTipo}>{TIPOS_MATCH.find(t => t.id === r.tipo_match)?.label}</span>
                  <code style={styles.patron}>{r.patron}</code>
                  <span style={styles.flecha}>→</span>
                  <span style={{
                    fontSize: 11, fontWeight: 600, padding: "2px 8px",
                    borderRadius: 99, backgroundColor: `${r.categoria?.color || "#888"}22`,
                    color: r.categoria?.color || "var(--text-secondary)",
                  }}>
                    {r.categoria?.nombre || "Sin categoría"}
                  </span>
                  {r.prioridad > 0 && (
                    <span style={styles.chipPrioridad}>p{r.prioridad}</span>
                  )}
                </div>
                {r.descripcion_regla && (
                  <span style={styles.itemDesc}>{r.descripcion_regla}</span>
                )}
              </div>
              <div style={styles.itemAcciones}>
                <button style={styles.btnAccion} onClick={() => toggleActiva(r)} title={r.activa ? "Desactivar" : "Activar"}>
                  {r.activa ? "🔕" : "🔔"}
                </button>
                <button style={styles.btnAccion} onClick={() => eliminar(r)} title="Eliminar">🗑️</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  seccion: {
    backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)", padding: "24px", marginBottom: 16,
  },
  header: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 },
  titulo: { fontSize: 15, fontWeight: 600, marginBottom: 4 },
  desc: { fontSize: 12, color: "var(--text-secondary)" },
  btnCrear: {
    fontSize: 13, fontWeight: 500, backgroundColor: "var(--accent)", color: "white",
    border: "none", borderRadius: "var(--radius-md)", padding: "7px 14px", cursor: "pointer",
    whiteSpace: "nowrap",
  },
  formBox: {
    backgroundColor: "var(--bg-secondary)", borderRadius: "var(--radius-md)",
    padding: "16px", marginBottom: 16,
  },
  formGrid: { display: "grid", gridTemplateColumns: "1fr 1.5fr 1fr 80px", gap: 10, marginBottom: 10 },
  campo: { display: "flex", flexDirection: "column", gap: 4 },
  label: { fontSize: 12, fontWeight: 500, color: "var(--text-secondary)" },
  input: {
    padding: "7px 10px", fontSize: 13, border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)", backgroundColor: "var(--bg-primary)",
    color: "var(--text-primary)", outline: "none",
  },
  select: {
    padding: "7px 10px", fontSize: 13, border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)", backgroundColor: "var(--bg-primary)",
    color: "var(--text-primary)", outline: "none", cursor: "pointer",
  },
  errorBox: {
    backgroundColor: "var(--danger-light)", color: "var(--danger)",
    borderRadius: "var(--radius-md)", padding: "8px 12px", fontSize: 13, marginBottom: 10,
  },
  formAcciones: { display: "flex", gap: 8 },
  btnGuardar: {
    fontSize: 13, fontWeight: 500, backgroundColor: "var(--accent)", color: "white",
    border: "none", borderRadius: "var(--radius-md)", padding: "7px 16px", cursor: "pointer",
  },
  btnCancelar: {
    fontSize: 13, border: "1px solid var(--border-default)", borderRadius: "var(--radius-md)",
    padding: "7px 14px", cursor: "pointer", backgroundColor: "var(--bg-primary)",
    color: "var(--text-secondary)",
  },
  probadorBox: { marginBottom: 16 },
  probadorRow: { display: "flex", gap: 8 },
  btnProbar: {
    fontSize: 13, fontWeight: 500, border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)", padding: "7px 14px", cursor: "pointer",
    backgroundColor: "var(--bg-secondary)", color: "var(--text-primary)",
  },
  resultadoPrueba: {
    fontSize: 13, fontWeight: 500, padding: "8px 14px",
    borderRadius: "var(--radius-md)", marginTop: 8,
  },
  lista: {},
  item: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "10px 0", borderBottom: "1px solid var(--border-default)",
  },
  itemLeft: { display: "flex", flexDirection: "column", gap: 3 },
  itemPatron: { display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" },
  chipTipo: {
    fontSize: 10, backgroundColor: "var(--bg-secondary)", color: "var(--text-secondary)",
    padding: "2px 6px", borderRadius: 4,
  },
  patron: {
    fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 600,
    color: "var(--text-primary)",
  },
  flecha: { color: "var(--text-tertiary)", fontSize: 12 },
  chipPrioridad: {
    fontSize: 10, backgroundColor: "var(--warning-light)", color: "var(--warning)",
    padding: "2px 5px", borderRadius: 4,
  },
  itemDesc: { fontSize: 11, color: "var(--text-tertiary)" },
  itemAcciones: { display: "flex", gap: 4, flexShrink: 0 },
  btnAccion: {
    background: "none", border: "none", cursor: "pointer", fontSize: 14,
    padding: "3px 6px", borderRadius: "var(--radius-sm)", opacity: 0.7,
  },
  vacio: { fontSize: 13, color: "var(--text-tertiary)", textAlign: "center", padding: "20px 0" },
};
