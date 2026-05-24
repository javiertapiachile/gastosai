/**
 * Botón de exportación de datos en CSV o JSON.
 * Construye la URL con los filtros activos y abre la descarga.
 */

export default function ExportButton({ mes, anio, categoriaId }) {
  function buildUrl(formato) {
    const params = new URLSearchParams();
    if (mes) params.set("mes", mes);
    if (anio) params.set("anio", anio);
    if (categoriaId) params.set("categoria_id", categoriaId);

    const base = import.meta.env.VITE_API_URL
      ? `${import.meta.env.VITE_API_URL}/api/v1`
      : "/api/v1";

    return `${base}/export/${formato}?${params.toString()}`;
  }

  return (
    <div style={styles.wrapper}>
      <span style={styles.label}>Exportar:</span>
      <a href={buildUrl("csv")} download style={styles.btn}>
        ⬇ CSV
      </a>
      <a href={buildUrl("json")} download style={{ ...styles.btn, ...styles.btnJson }}>
        ⬇ JSON
      </a>
    </div>
  );
}

const styles = {
  wrapper: { display: "flex", alignItems: "center", gap: 8 },
  label: { fontSize: 12, color: "var(--text-secondary)" },
  btn: {
    fontSize: 12,
    fontWeight: 500,
    padding: "5px 12px",
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)",
    backgroundColor: "var(--bg-primary)",
    color: "var(--text-secondary)",
    textDecoration: "none",
    cursor: "pointer",
  },
  btnJson: {
    backgroundColor: "var(--bg-secondary)",
  },
};
