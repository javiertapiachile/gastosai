/**
 * Tarjeta de KPI para el dashboard.
 * Muestra un valor principal, una etiqueta y un subtexto opcional.
 */

export default function KPICard({ label, valor, sub, color, icono, cargando }) {
  if (cargando) {
    return (
      <div style={styles.card}>
        <div style={styles.skeleton} />
        <div style={{ ...styles.skeleton, width: "60%", height: 14, marginTop: 8 }} />
      </div>
    );
  }

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <span style={styles.label}>{label}</span>
        {icono && <span style={styles.icono}>{icono}</span>}
      </div>
      <div style={{ ...styles.valor, color: color || "var(--text-primary)" }}>
        {valor}
      </div>
      {sub && <div style={styles.sub}>{sub}</div>}
    </div>
  );
}

const styles = {
  card: {
    backgroundColor: "var(--bg-primary)",
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)",
    padding: "16px 20px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  label: {
    fontSize: 12,
    fontWeight: 500,
    color: "var(--text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  icono: { fontSize: 16 },
  valor: {
    fontSize: 26,
    fontWeight: 600,
    letterSpacing: "-0.02em",
    lineHeight: 1.2,
    marginBottom: 4,
  },
  sub: { fontSize: 12, color: "var(--text-secondary)" },
  skeleton: {
    height: 28,
    backgroundColor: "var(--bg-secondary)",
    borderRadius: "var(--radius-sm)",
    animation: "pulse 1.5s ease-in-out infinite",
  },
};
