/**
 * Dashboard principal — KPIs, gráfico de torta y evolución mensual.
 */

import { useFiltersStore } from "../store/filtersStore";
import { useFetch } from "../hooks/useFetch";
import KPICard from "../components/KPICard";
import MonthPicker from "../components/MonthPicker";
import PieChartCategories from "../components/charts/PieChartCategories";
import MonthlyChart from "../components/charts/MonthlyChart";

function formatearMonto(valor) {
  return new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0,
  }).format(valor ?? 0);
}

export default function DashboardPage() {
  const { mes, anio, setFiltros } = useFiltersStore();

  const params = {};
  if (mes) params.mes = mes;
  if (anio) params.anio = anio;

  const { data: kpis, loading: kpiLoading } = useFetch("/transactions/kpis", params);
  const { data: porCategoria, loading: catLoading } = useFetch("/transactions/charts/por-categoria", params);
  const { data: evolucion, loading: evolLoading } = useFetch("/transactions/charts/evolucion-mensual", anio ? { anio } : {});

  function handleFiltroChange(nuevoMes, nuevoAnio) {
    setFiltros(nuevoMes, nuevoAnio);
  }

  return (
    <div>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.titulo}>Dashboard</h1>
          <p style={styles.subtitulo}>Resumen de tus gastos personales</p>
        </div>
        <MonthPicker mes={mes} anio={anio} onChange={handleFiltroChange} />
      </div>

      {/* KPIs */}
      <div style={styles.kpiGrid}>
        <KPICard
          label="Gastos del período"
          valor={formatearMonto(kpis?.total_gastos)}
          sub={`${kpis?.total_transacciones ?? 0} transacciones`}
          icono="💸"
          cargando={kpiLoading}
        />
        <KPICard
          label="Ingresos del período"
          valor={formatearMonto(kpis?.total_ingresos)}
          color="var(--success)"
          icono="💰"
          cargando={kpiLoading}
        />
        <KPICard
          label="Categoría top"
          valor={kpis?.categoria_top ?? "—"}
          sub={kpis?.gasto_categoria_top ? formatearMonto(kpis.gasto_categoria_top) : ""}
          icono="🏆"
          cargando={kpiLoading}
        />
        <KPICard
          label="Clasificadas por IA"
          valor={`${kpis?.pct_clasificadas ?? 0}%`}
          sub={`${kpis?.transacciones_clasificadas ?? 0} de ${kpis?.total_transacciones ?? 0}`}
          color={kpis?.pct_clasificadas >= 95 ? "var(--success)" : "var(--warning)"}
          icono="🤖"
          cargando={kpiLoading}
        />
      </div>

      {/* Gráficos */}
      <div style={styles.chartsGrid}>
        {/* Gráfico de torta */}
        <div style={styles.chartCard}>
          <div style={styles.chartHeader}>
            <h2 style={styles.chartTitulo}>Por categoría</h2>
            <span style={styles.chartSub}>
              {porCategoria?.length ?? 0} categorías activas
            </span>
          </div>
          <PieChartCategories datos={porCategoria} cargando={catLoading} />
        </div>

        {/* Evolución mensual */}
        <div style={styles.chartCard}>
          <div style={styles.chartHeader}>
            <h2 style={styles.chartTitulo}>Evolución mensual</h2>
            <span style={styles.chartSub}>{anio ?? new Date().getFullYear()}</span>
          </div>
          <MonthlyChart datos={evolucion} mesActual={mes} cargando={evolLoading} />
        </div>
      </div>

      {/* Tabla resumen por categoría */}
      {porCategoria && porCategoria.length > 0 && (
        <div style={styles.tablaCard}>
          <h2 style={styles.chartTitulo}>Desglose por categoría</h2>
          <table style={styles.tabla}>
            <thead>
              <tr>
                <th style={styles.th}>Categoría</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Total</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Transacciones</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Promedio</th>
              </tr>
            </thead>
            <tbody>
              {porCategoria.map((cat) => (
                <tr key={cat.nombre} style={styles.tr}>
                  <td style={styles.td}>
                    <span style={{
                      display: "inline-block",
                      width: 10,
                      height: 10,
                      borderRadius: "50%",
                      backgroundColor: cat.color,
                      marginRight: 8,
                    }} />
                    {cat.nombre}
                  </td>
                  <td style={{ ...styles.td, textAlign: "right", fontWeight: 500 }}>
                    {formatearMonto(cat.total)}
                  </td>
                  <td style={{ ...styles.td, textAlign: "right", color: "var(--text-secondary)" }}>
                    {cat.cantidad}
                  </td>
                  <td style={{ ...styles.td, textAlign: "right", color: "var(--text-secondary)" }}>
                    {formatearMonto(cat.total / cat.cantidad)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const styles = {
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 24,
    gap: 16,
    flexWrap: "wrap",
  },
  titulo: { fontSize: 22, fontWeight: 600, marginBottom: 4 },
  subtitulo: { fontSize: 13, color: "var(--text-secondary)" },

  kpiGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: 12,
    marginBottom: 20,
  },

  chartsGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1.4fr",
    gap: 16,
    marginBottom: 20,
  },

  chartCard: {
    backgroundColor: "var(--bg-primary)",
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)",
    padding: "20px 24px",
  },
  chartHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "baseline",
    marginBottom: 16,
  },
  chartTitulo: { fontSize: 14, fontWeight: 600, color: "var(--text-primary)" },
  chartSub: { fontSize: 12, color: "var(--text-tertiary)" },

  tablaCard: {
    backgroundColor: "var(--bg-primary)",
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)",
    padding: "20px 24px",
    overflowX: "auto",
  },
  tabla: { width: "100%", borderCollapse: "collapse", marginTop: 16, fontSize: 13 },
  th: {
    padding: "8px 12px",
    textAlign: "left",
    fontSize: 11,
    fontWeight: 600,
    color: "var(--text-tertiary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    borderBottom: "1px solid var(--border-default)",
  },
  tr: { borderBottom: "1px solid var(--border-default)" },
  td: { padding: "10px 12px", color: "var(--text-primary)" },
};
