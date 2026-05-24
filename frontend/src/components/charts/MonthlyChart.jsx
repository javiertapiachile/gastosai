/**
 * Gráfico de barras de evolución mensual de gastos.
 * Muestra hasta 12 meses con tooltip de monto y variación.
 */

import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Cell
} from "recharts";

function formatearMonto(valor) {
  if (valor >= 1_000_000) return `$${(valor / 1_000_000).toFixed(1)}M`;
  if (valor >= 1_000) return `$${(valor / 1_000).toFixed(0)}k`;
  return `$${valor}`;
}

function formatearMontoCompleto(valor) {
  return new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0,
  }).format(valor);
}

function TooltipPersonalizado({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={styles.tooltip}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
      <div>{formatearMontoCompleto(payload[0].value)}</div>
    </div>
  );
}

export default function MonthlyChart({ datos, mesActual, cargando }) {
  if (cargando) {
    return (
      <div style={styles.skeleton}>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} style={{ ...styles.skeletonBar, height: `${40 + Math.random() * 60}%` }} />
        ))}
      </div>
    );
  }

  if (!datos || datos.length === 0) {
    return (
      <div style={styles.vacio}>Sin datos de evolución disponibles</div>
    );
  }

  const datosFormateados = datos.map((d) => ({
    ...d,
    nombre: d.mes_nombre,
    esActual: d.mes === mesActual,
  }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={datosFormateados} barSize={28} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--border-default)" strokeDasharray="3 0" />
        <XAxis
          dataKey="nombre"
          tick={{ fontSize: 11, fill: "var(--text-tertiary)" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={formatearMonto}
          tick={{ fontSize: 11, fill: "var(--text-tertiary)" }}
          axisLine={false}
          tickLine={false}
          width={48}
        />
        <Tooltip content={<TooltipPersonalizado />} cursor={{ fill: "var(--bg-secondary)" }} />
        <Bar dataKey="total" radius={[4, 4, 0, 0]}>
          {datosFormateados.map((entry, i) => (
            <Cell
              key={`cell-${i}`}
              fill={entry.esActual ? "var(--accent)" : "var(--bg-tertiary)"}
              stroke={entry.esActual ? "var(--accent)" : "var(--border-default)"}
              strokeWidth={1}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

const styles = {
  tooltip: {
    backgroundColor: "var(--bg-primary)",
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)",
    padding: "10px 14px",
    fontSize: 13,
    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
  },
  skeleton: {
    display: "flex",
    alignItems: "flex-end",
    gap: 8,
    height: 240,
    padding: "0 8px",
  },
  skeletonBar: {
    flex: 1,
    backgroundColor: "var(--bg-secondary)",
    borderRadius: "4px 4px 0 0",
  },
  vacio: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: 240,
    color: "var(--text-tertiary)",
    fontSize: 13,
  },
};
