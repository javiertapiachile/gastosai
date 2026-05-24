/**
 * Dashboard principal con soporte multi-período.
 * Permite comparar dos meses lado a lado.
 */

import { useState } from "react";
import { useFiltersStore } from "../store/filtersStore";
import { useFetch } from "../hooks/useFetch";
import KPICard from "../components/KPICard";
import MonthPicker from "../components/MonthPicker";
import PieChartCategories from "../components/charts/PieChartCategories";
import MonthlyChart from "../components/charts/MonthlyChart";

function formatearMonto(valor) {
  return new Intl.NumberFormat("es-CL", {
    style: "currency", currency: "CLP", maximumFractionDigits: 0,
  }).format(valor ?? 0);
}

function variacion(actual, anterior) {
  if (!anterior || anterior === 0) return null;
  const pct = ((actual - anterior) / anterior) * 100;
  const signo = pct >= 0 ? "▲" : "▼";
  const color = pct >= 0 ? "var(--danger)" : "var(--success)";
  return { texto: `${signo} ${Math.abs(pct).toFixed(1)}% vs período anterior`, color };
}

export default function DashboardPage() {
  const { mes, anio, setFiltros } = useFiltersStore();
  const [comparando, setComparando] = useState(false);
  const [mesComp, setMesComp] = useState(null);
  const [anioComp, setAnioComp] = useState(null);

  const params = {};
  if (mes) params.mes = mes;
  if (anio) params.anio = anio;

  const paramsComp = {};
  if (mesComp) paramsComp.mes = mesComp;
  if (anioComp) paramsComp.anio = anioComp;

  const { data: kpis,          loading: kpiLoading }  = useFetch("/transactions/kpis", params);
  const { data: porCategoria,  loading: catLoading }   = useFetch("/transactions/charts/por-categoria", params);
  const { data: evolucion,     loading: evolLoading }  = useFetch("/transactions/charts/evolucion-mensual", anio ? { anio } : {});
  const { data: kpisComp }                             = useFetch(comparando ? "/transactions/kpis" : null, paramsComp);
  const { data: porCatComp }                           = useFetch(comparando ? "/transactions/charts/por-categoria" : null, paramsComp);

  const var1 = kpis && kpisComp ? variacion(kpis.total_gastos, kpisComp.total_gastos) : null;

  return (
    <div>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.titulo}>Dashboard</h1>
          <p style={styles.subtitulo}>Resumen de tus gastos personales</p>
        </div>
        <div style={styles.controles}>
          <MonthPicker mes={mes} anio={anio} onChange={(m, a) => setFiltros(m, a)} />
          <button
            style={{ ...styles.btnComparar, ...(comparando ? styles.btnCompararActivo : {}) }}
            onClick={() => {
              setComparando(!comparando);
              if (!comparando) {
                // Preseleccionar mes anterior
                const mAnt = mes ? (mes === 1 ? 12 : mes - 1) : null;
                const aAnt = mes === 1 ? (anio ? anio - 1 : null) : anio;
                setMesComp(mAnt);
                setAnioComp(aAnt);
              }
            }}
          >
            {comparando ? "✕ Cerrar comparación" : "⇄ Comparar período"}
          </button>
        </div>
      </div>

      {/* Selector período de comparación */}
      {comparando && (
        <div style={styles.compBox}>
          <span style={styles.compLabel}>Comparar con:</span>
          <MonthPicker mes={mesComp} anio={anioComp} onChange={(m, a) => { setMesComp(m); setAnioComp(a); }} />
        </div>
      )}

      {/* KPIs — uno o dos columnas según modo */}
      <div style={{ ...styles.kpiWrapper, gridTemplateColumns: comparando ? "1fr 1fr" : "1fr" }}>

        {/* Período principal */}
        <div>
          {comparando && (
            <div style={styles.periodoLabel}>
              {mes ? `${["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"][mes-1]} ${anio || ""}` : "Período principal"}
            </div>
          )}
          <div style={styles.kpiGrid}>
            <KPICard label="Gastos" valor={formatearMonto(kpis?.total_gastos)}
              sub={var1 ? var1.texto : `${kpis?.total_transacciones ?? 0} transacciones`}
              subColor={var1?.color} icono="💸" cargando={kpiLoading} />
            <KPICard label="Ingresos" valor={formatearMonto(kpis?.total_ingresos)}
              color="var(--success)" icono="💰" cargando={kpiLoading} />
            <KPICard label="Categoría top" valor={kpis?.categoria_top ?? "—"}
              sub={kpis?.gasto_categoria_top ? formatearMonto(kpis.gasto_categoria_top) : ""}
              icono="🏆" cargando={kpiLoading} />
            <KPICard label="Clasificadas IA" valor={`${kpis?.pct_clasificadas ?? 0}%`}
              sub={`${kpis?.transacciones_clasificadas ?? 0} de ${kpis?.total_transacciones ?? 0}`}
              color={kpis?.pct_clasificadas >= 95 ? "var(--success)" : "var(--warning)"}
              icono="🤖" cargando={kpiLoading} />
          </div>
        </div>

        {/* Período de comparación */}
        {comparando && (
          <div>
            <div style={{ ...styles.periodoLabel, backgroundColor: "var(--warning-light)", color: "var(--warning)" }}>
              {mesComp ? `${["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"][mesComp-1]} ${anioComp || ""}` : "Período comparación"}
            </div>
            <div style={styles.kpiGrid}>
              <KPICard label="Gastos" valor={formatearMonto(kpisComp?.total_gastos)}
                sub={`${kpisComp?.total_transacciones ?? 0} transacciones`} icono="💸" />
              <KPICard label="Ingresos" valor={formatearMonto(kpisComp?.total_ingresos)}
                color="var(--success)" icono="💰" />
              <KPICard label="Categoría top" valor={kpisComp?.categoria_top ?? "—"}
                sub={kpisComp?.gasto_categoria_top ? formatearMonto(kpisComp.gasto_categoria_top) : ""}
                icono="🏆" />
              <KPICard label="Clasificadas IA" valor={`${kpisComp?.pct_clasificadas ?? 0}%`}
                icono="🤖" />
            </div>
          </div>
        )}
      </div>

      {/* Gráficos */}
      <div style={{ ...styles.chartsGrid, gridTemplateColumns: comparando ? "1fr 1fr" : "1fr 1.4fr" }}>
        <div style={styles.chartCard}>
          <div style={styles.chartHeader}>
            <h2 style={styles.chartTitulo}>Por categoría</h2>
            {comparando && <span style={styles.chartSub}>Período principal</span>}
          </div>
          <PieChartCategories datos={porCategoria} cargando={catLoading} />
        </div>

        {comparando ? (
          <div style={styles.chartCard}>
            <div style={styles.chartHeader}>
              <h2 style={styles.chartTitulo}>Por categoría</h2>
              <span style={styles.chartSub}>Período comparación</span>
            </div>
            <PieChartCategories datos={porCatComp} cargando={false} />
          </div>
        ) : (
          <div style={styles.chartCard}>
            <div style={styles.chartHeader}>
              <h2 style={styles.chartTitulo}>Evolución mensual</h2>
              <span style={styles.chartSub}>{anio ?? new Date().getFullYear()}</span>
            </div>
            <MonthlyChart datos={evolucion} mesActual={mes} cargando={evolLoading} />
          </div>
        )}
      </div>

      {/* Evolución cuando está comparando */}
      {comparando && (
        <div style={{ ...styles.chartCard, marginTop: 16 }}>
          <div style={styles.chartHeader}>
            <h2 style={styles.chartTitulo}>Evolución mensual</h2>
            <span style={styles.chartSub}>{anio ?? new Date().getFullYear()}</span>
          </div>
          <MonthlyChart datos={evolucion} mesActual={mes} cargando={evolLoading} />
        </div>
      )}

      {/* Tabla resumen por categoría */}
      {porCategoria && porCategoria.length > 0 && (
        <div style={{ ...styles.chartCard, marginTop: 16, overflowX: "auto" }}>
          <h2 style={{ ...styles.chartTitulo, marginBottom: 14 }}>Desglose por categoría</h2>
          <table style={styles.tabla}>
            <thead>
              <tr>
                <th style={styles.th}>Categoría</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Total</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Tx</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Promedio</th>
                {comparando && porCatComp && <th style={{ ...styles.th, textAlign: "right" }}>Anterior</th>}
                {comparando && porCatComp && <th style={{ ...styles.th, textAlign: "right" }}>Δ</th>}
              </tr>
            </thead>
            <tbody>
              {porCategoria.map((cat) => {
                const comp = porCatComp?.find(c => c.nombre === cat.nombre);
                const delta = comp ? cat.total - comp.total : null;
                return (
                  <tr key={cat.nombre} style={styles.tr}>
                    <td style={styles.td}>
                      <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", backgroundColor: cat.color, marginRight: 8 }} />
                      {cat.nombre}
                    </td>
                    <td style={{ ...styles.td, textAlign: "right", fontWeight: 500 }}>{formatearMonto(cat.total)}</td>
                    <td style={{ ...styles.td, textAlign: "right", color: "var(--text-secondary)" }}>{cat.cantidad}</td>
                    <td style={{ ...styles.td, textAlign: "right", color: "var(--text-secondary)" }}>{formatearMonto(cat.total / cat.cantidad)}</td>
                    {comparando && porCatComp && (
                      <td style={{ ...styles.td, textAlign: "right", color: "var(--text-secondary)" }}>
                        {comp ? formatearMonto(comp.total) : "—"}
                      </td>
                    )}
                    {comparando && porCatComp && (
                      <td style={{ ...styles.td, textAlign: "right", fontWeight: 500, color: delta === null ? "var(--text-tertiary)" : delta > 0 ? "var(--danger)" : "var(--success)" }}>
                        {delta === null ? "—" : `${delta > 0 ? "+" : ""}${formatearMonto(delta)}`}
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const styles = {
  header: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16, gap: 16, flexWrap: "wrap" },
  titulo: { fontSize: 22, fontWeight: 600, marginBottom: 4 },
  subtitulo: { fontSize: 13, color: "var(--text-secondary)" },
  controles: { display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" },
  btnComparar: {
    fontSize: 13, fontWeight: 500, border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)", padding: "6px 14px", cursor: "pointer",
    backgroundColor: "var(--bg-primary)", color: "var(--text-secondary)", whiteSpace: "nowrap",
  },
  btnCompararActivo: {
    backgroundColor: "var(--warning-light)", color: "var(--warning)",
    borderColor: "var(--warning)",
  },
  compBox: {
    display: "flex", alignItems: "center", gap: 12,
    backgroundColor: "var(--warning-light)", borderRadius: "var(--radius-md)",
    padding: "10px 16px", marginBottom: 16,
  },
  compLabel: { fontSize: 13, fontWeight: 500, color: "var(--warning)", whiteSpace: "nowrap" },
  kpiWrapper: { display: "grid", gap: 16, marginBottom: 16 },
  periodoLabel: {
    fontSize: 12, fontWeight: 600, textAlign: "center", padding: "4px 12px",
    borderRadius: "var(--radius-md)", backgroundColor: "var(--accent-light)",
    color: "var(--accent-text)", marginBottom: 10,
  },
  kpiGrid: { display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10 },
  chartsGrid: { display: "grid", gap: 16 },
  chartCard: {
    backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)", padding: "20px 24px",
  },
  chartHeader: { display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 16 },
  chartTitulo: { fontSize: 14, fontWeight: 600 },
  chartSub: { fontSize: 12, color: "var(--text-tertiary)" },
  tabla: { width: "100%", borderCollapse: "collapse", fontSize: 13 },
  th: {
    padding: "8px 12px", textAlign: "left", fontSize: 11, fontWeight: 600,
    color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.05em",
    borderBottom: "1px solid var(--border-default)",
  },
  tr: { borderBottom: "1px solid var(--border-default)" },
  td: { padding: "10px 12px" },
};
