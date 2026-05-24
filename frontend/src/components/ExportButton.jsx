/**
 * Botón de exportación — usa rutas relativas para funcionar en red local.
 */

import { useAuthStore } from "../store/authStore";

export default function ExportButton({ mes, anio, categoriaId }) {
  const token = useAuthStore((state) => state.token);

  function descargar(formato) {
    const params = new URLSearchParams();
    if (mes) params.set("mes", mes);
    if (anio) params.set("anio", anio);
    if (categoriaId) params.set("categoria_id", categoriaId);

    // Usar ruta relativa — nginx proxy se encarga de redirigir al backend
    const url = `/api/v1/export/${formato}?${params.toString()}`;

    // Crear link temporal con el token en el header no es posible con <a>,
    // así que hacemos fetch con auth y descargamos el blob
    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Error al exportar");
        return res.blob();
      })
      .then((blob) => {
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        const fecha = new Date().toISOString().split("T")[0];
        link.download = `gastosai_${formato}_${fecha}.${formato}`;
        link.click();
        URL.revokeObjectURL(link.href);
      })
      .catch((err) => console.error("Export error:", err));
  }

  return (
    <div style={styles.wrapper}>
      <span style={styles.label}>Exportar:</span>
      <button style={styles.btn} onClick={() => descargar("csv")}>⬇ CSV</button>
      <button style={{ ...styles.btn, ...styles.btnJson }} onClick={() => descargar("json")}>⬇ JSON</button>
    </div>
  );
}

const styles = {
  wrapper: { display: "flex", alignItems: "center", gap: 8 },
  label: { fontSize: 12, color: "var(--text-secondary)" },
  btn: {
    fontSize: 12, fontWeight: 500, padding: "5px 12px",
    border: "1px solid var(--border-default)", borderRadius: "var(--radius-md)",
    backgroundColor: "var(--bg-primary)", color: "var(--text-secondary)",
    cursor: "pointer",
  },
  btnJson: { backgroundColor: "var(--bg-secondary)" },
};
