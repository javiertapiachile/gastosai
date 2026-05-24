/**
 * Gráfico de torta (donut) con distribución de gastos por categoría.
 * Usa Recharts PieChart con tooltip personalizado.
 */

import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend
} from "recharts";

function formatearMonto(valor) {
  return new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0,
  }).format(valor);
}

function TooltipPersonalizado({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div style={styles.tooltip}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{d.name}</div>
      <div>{formatearMonto(d.value)}</div>
      <div style={{ color: "var(--text-secondary)", fontSize: 11 }}>
        {d.payload.porcentaje}% del total
      </div>
    </div>
  );
}

export default function PieChartCategories({ datos, cargando }) {
  if (cargando) {
    return (
      <div style={styles.wrapper}>
        <div style={styles.skeletonCircle} />
      </div>
    );
  }

  if (!datos || datos.length === 0) {
    return (
      <div style={{ ...styles.wrapper, ...styles.vacio }}>
        <span>Sin datos para el período seleccionado</span>
      </div>
    );
  }

  const total = datos.reduce((s, d) => s + d.total, 0);
  const datosConPct = datos.map((d) => ({
    ...d,
    name: d.nombre,
    value: d.total,
    porcentaje: total > 0 ? ((d.total / total) * 100).toFixed(1) : 0,
  }));

  return (
    <div style={styles.wrapper}>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={datosConPct}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
            dataKey="value"
          >
            {datosConPct.map((entry, i) => (
              <Cell
                key={`cell-${i}`}
                fill={entry.color || "#888780"}
                stroke="none"
              />
            ))}
          </Pie>
          <Tooltip content={<TooltipPersonalizado />} />
          <Legend
            formatter={(value) => (
              <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

const styles = {
  wrapper: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: 260,
  },
  vacio: {
    color: "var(--text-tertiary)",
    fontSize: 13,
  },
  tooltip: {
    backgroundColor: "var(--bg-primary)",
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)",
    padding: "10px 14px",
    fontSize: 13,
    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
  },
  skeletonCircle: {
    width: 200,
    height: 200,
    borderRadius: "50%",
    backgroundColor: "var(--bg-secondary)",
  },
};
