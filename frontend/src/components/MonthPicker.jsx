/**
 * Selector de mes y año. Usado en el dashboard y en la tabla de transacciones.
 */

const MESES = [
  "Enero","Febrero","Marzo","Abril","Mayo","Junio",
  "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"
];

export default function MonthPicker({ mes, anio, onChange }) {
  const anioActual = new Date().getFullYear();
  const anios = Array.from({ length: 5 }, (_, i) => anioActual - i);

  return (
    <div style={styles.wrapper}>
      <select
        value={mes ?? ""}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null, anio)}
        style={styles.select}
      >
        <option value="">Todos los meses</option>
        {MESES.map((nombre, i) => (
          <option key={i + 1} value={i + 1}>{nombre}</option>
        ))}
      </select>

      <select
        value={anio ?? ""}
        onChange={(e) => onChange(mes, e.target.value ? Number(e.target.value) : null)}
        style={styles.select}
      >
        <option value="">Todos los años</option>
        {anios.map((a) => (
          <option key={a} value={a}>{a}</option>
        ))}
      </select>
    </div>
  );
}

const styles = {
  wrapper: { display: "flex", gap: 8 },
  select: {
    fontSize: 13,
    color: "var(--text-secondary)",
    backgroundColor: "var(--bg-primary)",
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)",
    padding: "6px 10px",
    cursor: "pointer",
    outline: "none",
  },
};
