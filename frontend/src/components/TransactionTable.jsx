/**
 * Tabla de transacciones con:
 * - Búsqueda por texto
 * - Filtro por categoría
 * - Paginación
 * - Edición inline de categoría (clic en badge)
 */

import { useState } from "react";
import client from "../api/client";
import CategoryBadge from "./CategoryBadge";

function formatearMonto(monto, esCargo) {
  const fmt = new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0,
  }).format(monto);
  return esCargo ? `-${fmt}` : `+${fmt}`;
}

function formatearFecha(fechaStr) {
  const [anio, mes, dia] = fechaStr.split("-");
  return `${dia}/${mes}/${anio}`;
}

export default function TransactionTable({
  transacciones,
  categorias,
  cargando,
  onCategoriaActualizada,
}) {
  const [editandoId, setEditandoId] = useState(null);
  const [guardando, setGuardando] = useState(false);

  async function cambiarCategoria(txId, categoriaId) {
    setGuardando(true);
    try {
      await client.patch(`/transactions/${txId}`, {
        categoria_id: categoriaId,
        revisado_por_usuario: true,
      });
      onCategoriaActualizada?.();
    } catch (err) {
      console.error("Error al actualizar categoría:", err);
    } finally {
      setGuardando(false);
      setEditandoId(null);
    }
  }

  if (cargando) {
    return (
      <div>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} style={styles.skeletonRow} />
        ))}
      </div>
    );
  }

  if (!transacciones || transacciones.length === 0) {
    return (
      <div style={styles.vacio}>
        No hay transacciones para los filtros aplicados.
      </div>
    );
  }

  return (
    <div style={styles.wrapper}>
      <table style={styles.tabla}>
        <thead>
          <tr>
            <th style={styles.th}>Descripción original</th>
            <th style={styles.th}>Comercio</th>
            <th style={{ ...styles.th, textAlign: "center" }}>Fecha</th>
            <th style={{ ...styles.th, textAlign: "right" }}>Monto</th>
            <th style={{ ...styles.th, textAlign: "center" }}>Categoría</th>
          </tr>
        </thead>
        <tbody>
          {transacciones.map((tx) => (
            <tr key={tx.id} style={styles.tr}>
              {/* Descripción original */}
              <td style={styles.td}>
                <span style={styles.descOriginal}>{tx.descripcion_original}</span>
                {tx.clasificado_por_cache && (
                  <span style={styles.cacheBadge} title="Clasificado desde caché">⚡</span>
                )}
              </td>

              {/* Comercio limpio */}
              <td style={styles.td}>
                <span style={styles.comercio}>
                  {tx.comercio_limpio || tx.descripcion_original}
                </span>
              </td>

              {/* Fecha */}
              <td style={{ ...styles.td, textAlign: "center", fontVariantNumeric: "tabular-nums" }}>
                {formatearFecha(tx.fecha)}
              </td>

              {/* Monto */}
              <td style={{
                ...styles.td,
                textAlign: "right",
                fontVariantNumeric: "tabular-nums",
                fontWeight: 500,
                color: tx.es_cargo ? "var(--danger)" : "var(--success)",
              }}>
                {formatearMonto(tx.monto, tx.es_cargo)}
              </td>

              {/* Categoría — editable */}
              <td style={{ ...styles.td, textAlign: "center" }}>
                {editandoId === tx.id ? (
                  <select
                    autoFocus
                    style={styles.selectCategoria}
                    disabled={guardando}
                    defaultValue={tx.categoria_id || ""}
                    onChange={(e) => cambiarCategoria(tx.id, e.target.value ? Number(e.target.value) : null)}
                    onBlur={() => setEditandoId(null)}
                  >
                    <option value="">Sin categoría</option>
                    {categorias.map((c) => (
                      <option key={c.id} value={c.id}>{c.nombre}</option>
                    ))}
                  </select>
                ) : (
                  <button
                    style={styles.badgeBtn}
                    onClick={() => setEditandoId(tx.id)}
                    title="Clic para editar categoría"
                  >
                    <CategoryBadge
                      nombre={tx.categoria?.nombre}
                      color={tx.categoria?.color}
                    />
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const styles = {
  wrapper: {
    overflowX: "auto",
    borderRadius: "var(--radius-lg)",
    border: "1px solid var(--border-default)",
  },
  tabla: {
    width: "100%",
    borderCollapse: "collapse",
    backgroundColor: "var(--bg-primary)",
    fontSize: 13,
  },
  th: {
    padding: "10px 16px",
    textAlign: "left",
    fontSize: 11,
    fontWeight: 600,
    color: "var(--text-tertiary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    borderBottom: "1px solid var(--border-default)",
    backgroundColor: "var(--bg-secondary)",
    whiteSpace: "nowrap",
  },
  tr: {
    borderBottom: "1px solid var(--border-default)",
    transition: "background-color 0.1s",
  },
  td: {
    padding: "10px 16px",
    color: "var(--text-primary)",
    verticalAlign: "middle",
  },
  descOriginal: {
    color: "var(--text-secondary)",
    fontSize: 12,
    fontFamily: "var(--font-mono)",
  },
  cacheBadge: {
    marginLeft: 4,
    fontSize: 10,
    opacity: 0.5,
    cursor: "help",
  },
  comercio: {
    fontWeight: 500,
  },
  badgeBtn: {
    background: "none",
    border: "none",
    cursor: "pointer",
    padding: 0,
  },
  selectCategoria: {
    fontSize: 12,
    border: "1px solid var(--border-strong)",
    borderRadius: "var(--radius-md)",
    padding: "3px 6px",
    backgroundColor: "var(--bg-primary)",
    color: "var(--text-primary)",
    outline: "none",
  },
  skeletonRow: {
    height: 44,
    backgroundColor: "var(--bg-secondary)",
    marginBottom: 2,
    borderRadius: "var(--radius-sm)",
  },
  vacio: {
    padding: "48px 24px",
    textAlign: "center",
    color: "var(--text-tertiary)",
    fontSize: 13,
  },
};
