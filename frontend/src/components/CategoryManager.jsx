/**
 * Gestión de categorías: listar, crear, editar color/icono, activar/desactivar.
 * Las categorías del sistema (es_sistema=true) no se pueden eliminar.
 */

import { useState } from "react";
import client from "../api/client";

const COLORES_PRESET = [
  "#1D9E75", "#378ADD", "#EF9F27", "#7F77DD",
  "#D85A30", "#5DCAA5", "#185FA5", "#E85D24",
  "#639922", "#888780", "#C2456A", "#2563EB",
];

function ColorPicker({ valor, onChange }) {
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {COLORES_PRESET.map((c) => (
        <button
          key={c}
          onClick={() => onChange(c)}
          style={{
            width: 22,
            height: 22,
            borderRadius: "50%",
            backgroundColor: c,
            border: valor === c ? "2px solid var(--text-primary)" : "2px solid transparent",
            cursor: "pointer",
            padding: 0,
          }}
        />
      ))}
    </div>
  );
}

export default function CategoryManager({ categorias, onActualizado }) {
  const [creando, setCreando] = useState(false);
  const [editandoId, setEditandoId] = useState(null);
  const [form, setForm] = useState({ nombre: "", color: "#378ADD" });
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);

  function abrirCrear() {
    setForm({ nombre: "", color: "#378ADD" });
    setCreando(true);
    setEditandoId(null);
    setError(null);
  }

  function abrirEditar(cat) {
    setForm({ nombre: cat.nombre, color: cat.color });
    setEditandoId(cat.id);
    setCreando(false);
    setError(null);
  }

  function cancelar() {
    setCreando(false);
    setEditandoId(null);
    setError(null);
  }

  async function guardar() {
    if (!form.nombre.trim()) {
      setError("El nombre es obligatorio");
      return;
    }
    setGuardando(true);
    setError(null);
    try {
      if (creando) {
        await client.post("/categories/", { nombre: form.nombre.trim(), color: form.color });
      } else {
        await client.patch(`/categories/${editandoId}`, { nombre: form.nombre.trim(), color: form.color });
      }
      cancelar();
      onActualizado?.();
    } catch (err) {
      setError(err.response?.data?.detail || "Error al guardar");
    } finally {
      setGuardando(false);
    }
  }

  async function toggleActiva(cat) {
    try {
      await client.patch(`/categories/${cat.id}`, { activa: !cat.activa });
      onActualizado?.();
    } catch (err) {
      console.error("Error al actualizar:", err);
    }
  }

  async function eliminar(cat) {
    if (!confirm(`¿Eliminar la categoría "${cat.nombre}"? Esta acción no se puede deshacer.`)) return;
    try {
      await client.delete(`/categories/${cat.id}`);
      onActualizado?.();
    } catch (err) {
      alert(err.response?.data?.detail || "No se puede eliminar esta categoría");
    }
  }

  return (
    <div style={styles.seccion}>
      <div style={styles.header}>
        <h2 style={styles.titulo}>Categorías</h2>
        <button style={styles.btnCrear} onClick={abrirCrear}>
          + Nueva categoría
        </button>
      </div>

      {/* Formulario de creación/edición */}
      {(creando || editandoId) && (
        <div style={styles.formBox}>
          <div style={styles.formTitulo}>
            {creando ? "Nueva categoría" : "Editar categoría"}
          </div>

          <div style={styles.formCampo}>
            <label style={styles.label}>Nombre</label>
            <input
              autoFocus
              type="text"
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              placeholder="Ej: Mascotas"
              style={styles.input}
              onKeyDown={(e) => e.key === "Enter" && guardar()}
            />
          </div>

          <div style={styles.formCampo}>
            <label style={styles.label}>Color</label>
            <ColorPicker valor={form.color} onChange={(c) => setForm({ ...form, color: c })} />
          </div>

          {error && <div style={styles.errorBox}>{error}</div>}

          <div style={styles.formAcciones}>
            <button style={styles.btnGuardar} onClick={guardar} disabled={guardando}>
              {guardando ? "Guardando..." : "Guardar"}
            </button>
            <button style={styles.btnCancelar} onClick={cancelar}>
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Lista de categorías */}
      <div style={styles.lista}>
        {(categorias || []).map((cat) => (
          <div
            key={cat.id}
            style={{
              ...styles.item,
              opacity: cat.activa ? 1 : 0.5,
            }}
          >
            {/* Color dot + nombre */}
            <div style={styles.itemLeft}>
              <div style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                backgroundColor: cat.color,
                flexShrink: 0,
              }} />
              <span style={styles.itemNombre}>{cat.nombre}</span>
              {cat.es_sistema && (
                <span style={styles.badgeSistema}>sistema</span>
              )}
              {!cat.activa && (
                <span style={styles.badgeInactiva}>inactiva</span>
              )}
            </div>

            {/* Acciones */}
            <div style={styles.itemAcciones}>
              <button
                style={styles.btnAccion}
                onClick={() => abrirEditar(cat)}
                title="Editar"
              >
                ✏️
              </button>
              <button
                style={styles.btnAccion}
                onClick={() => toggleActiva(cat)}
                title={cat.activa ? "Desactivar" : "Activar"}
              >
                {cat.activa ? "🔕" : "🔔"}
              </button>
              {!cat.es_sistema && (
                <button
                  style={{ ...styles.btnAccion, color: "var(--danger)" }}
                  onClick={() => eliminar(cat)}
                  title="Eliminar"
                >
                  🗑️
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const styles = {
  seccion: {
    backgroundColor: "var(--bg-primary)",
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)",
    padding: "24px",
    marginBottom: 16,
  },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 },
  titulo: { fontSize: 15, fontWeight: 600 },
  btnCrear: {
    fontSize: 13,
    fontWeight: 500,
    backgroundColor: "var(--accent)",
    color: "white",
    border: "none",
    borderRadius: "var(--radius-md)",
    padding: "7px 14px",
    cursor: "pointer",
  },

  formBox: {
    backgroundColor: "var(--bg-secondary)",
    borderRadius: "var(--radius-md)",
    padding: "16px",
    marginBottom: 16,
  },
  formTitulo: { fontSize: 13, fontWeight: 600, marginBottom: 12 },
  formCampo: { marginBottom: 12 },
  label: { display: "block", fontSize: 12, color: "var(--text-secondary)", marginBottom: 6, fontWeight: 500 },
  input: {
    width: "100%",
    fontSize: 13,
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)",
    padding: "7px 10px",
    backgroundColor: "var(--bg-primary)",
    color: "var(--text-primary)",
    outline: "none",
  },
  errorBox: {
    fontSize: 12,
    color: "var(--danger)",
    backgroundColor: "var(--danger-light)",
    padding: "8px 12px",
    borderRadius: "var(--radius-md)",
    marginBottom: 10,
  },
  formAcciones: { display: "flex", gap: 8 },
  btnGuardar: {
    fontSize: 13,
    fontWeight: 500,
    backgroundColor: "var(--accent)",
    color: "white",
    border: "none",
    borderRadius: "var(--radius-md)",
    padding: "7px 16px",
    cursor: "pointer",
  },
  btnCancelar: {
    fontSize: 13,
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)",
    padding: "7px 14px",
    cursor: "pointer",
    backgroundColor: "var(--bg-primary)",
    color: "var(--text-secondary)",
  },

  lista: {},
  item: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "10px 0",
    borderBottom: "1px solid var(--border-default)",
  },
  itemLeft: { display: "flex", alignItems: "center", gap: 10 },
  itemNombre: { fontSize: 13, fontWeight: 500 },
  badgeSistema: {
    fontSize: 10,
    color: "var(--text-tertiary)",
    backgroundColor: "var(--bg-secondary)",
    padding: "1px 6px",
    borderRadius: 99,
  },
  badgeInactiva: {
    fontSize: 10,
    color: "var(--warning)",
    backgroundColor: "var(--warning-light)",
    padding: "1px 6px",
    borderRadius: 99,
  },
  itemAcciones: { display: "flex", gap: 4 },
  btnAccion: {
    background: "none",
    border: "none",
    cursor: "pointer",
    fontSize: 14,
    padding: "4px 6px",
    borderRadius: "var(--radius-sm)",
    opacity: 0.7,
  },
};
