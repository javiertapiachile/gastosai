/**
 * Badge de categoría con color dinámico.
 * Se usa en la tabla de transacciones y en el dropdown de edición.
 */

export default function CategoryBadge({ nombre, color, size = "sm" }) {
  if (!nombre) {
    return (
      <span style={{ ...styles.base, ...styles[size], color: "var(--text-tertiary)", backgroundColor: "var(--bg-secondary)" }}>
        Sin categoría
      </span>
    );
  }

  const bg = color ? `${color}22` : "var(--bg-secondary)";
  const text = color || "var(--text-secondary)";

  return (
    <span style={{ ...styles.base, ...styles[size], backgroundColor: bg, color: text }}>
      {nombre}
    </span>
  );
}

const styles = {
  base: {
    display: "inline-block",
    borderRadius: "9999px",
    fontWeight: 500,
    whiteSpace: "nowrap",
  },
  sm: { fontSize: 11, padding: "2px 8px" },
  md: { fontSize: 12, padding: "4px 12px" },
  lg: { fontSize: 13, padding: "5px 14px" },
};
