/**
 * Página de configuración completa con reglas de clasificación.
 */

import { useState } from "react";
import { useFetch } from "../hooks/useFetch";
import LLMConfig from "../components/LLMConfig";
import CategoryManager from "../components/CategoryManager";
import ReglasManager from "../components/ReglasManager";

export default function ConfiguracionPage() {
  const [recargarConfig, setRecargarConfig] = useState(0);
  const [recargarCats, setRecargarCats] = useState(0);
  const [recargarReglas, setRecargarReglas] = useState(0);

  const { data: config, refetch: refetchConfig } = useFetch("/config/", { _r: recargarConfig });
  const { data: stats } = useFetch("/config/stats", { _r: recargarConfig });
  const { data: categorias, refetch: refetchCats } = useFetch("/categories/", { _r: recargarCats });
  const { data: reglas, refetch: refetchReglas } = useFetch("/reglas/", { _r: recargarReglas });

  return (
    <div style={styles.wrapper}>
      <div style={styles.header}>
        <h1 style={styles.titulo}>Configuración</h1>
        <p style={styles.subtitulo}>LLM, categorías y reglas de clasificación</p>
      </div>

      {/* Stats */}
      <div style={styles.statsBar}>
        {[
          { val: stats?.total_transacciones ?? "—", label: "Transacciones" },
          { val: stats?.total_importaciones ?? "—", label: "Importaciones" },
          { val: stats?.entradas_cache_llm ?? "—", label: "Caché LLM" },
          { val: reglas?.length ?? "—", label: "Reglas activas" },
          { val: stats?.proveedor_llm ?? "—", label: "Proveedor" },
        ].map((s, i) => (
          <div key={i} style={styles.statItem}>
            {i > 0 && <div style={styles.statDiv} />}
            <div style={styles.stat}>
              <span style={styles.statVal}>{s.val}</span>
              <span style={styles.statLabel}>{s.label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Reglas — ancho completo arriba */}
      <ReglasManager
        reglas={reglas}
        categorias={categorias}
        onActualizado={() => { setRecargarReglas(r => r + 1); refetchReglas(); }}
        onActualizarDefault={async () => {
          try {
            const { default: client } = await import("../api/client");
            await client.post("/reglas/actualizar-default");
            setRecargarReglas(r => r + 1);
            refetchReglas();
          } catch (e) { console.error(e); }
        }}
      />

      {/* LLM + Categorías en grid */}
      <div style={styles.grid}>
        <div>
          <LLMConfig
            configActual={config}
            onActualizado={() => { setRecargarConfig(r => r + 1); refetchConfig(); }}
          />
          <div style={styles.instruccionesBox}>
            <h3 style={styles.instrTitulo}>Persistencia permanente</h3>
            <p style={styles.instrDesc}>
              Los cambios desde la UI se aplican inmediatamente pero se pierden al reiniciar.
              Para hacerlos permanentes edita <code style={styles.code}>.env</code>:
            </p>
            <div style={styles.codeBlock}>docker compose down && docker compose up</div>
          </div>
        </div>
        <div>
          <CategoryManager
            categorias={categorias}
            onActualizado={() => { setRecargarCats(r => r + 1); refetchCats(); }}
          />
        </div>
      </div>
    </div>
  );
}

const styles = {
  wrapper: { maxWidth: 1100 },
  header: { marginBottom: 24 },
  titulo: { fontSize: 22, fontWeight: 600, marginBottom: 4 },
  subtitulo: { fontSize: 13, color: "var(--text-secondary)" },
  statsBar: {
    display: "flex", alignItems: "center", backgroundColor: "var(--bg-primary)",
    border: "1px solid var(--border-default)", borderRadius: "var(--radius-lg)",
    padding: "16px 24px", marginBottom: 20, flexWrap: "wrap",
  },
  statItem: { display: "flex", alignItems: "center" },
  stat: { display: "flex", flexDirection: "column", alignItems: "center", padding: "0 20px", gap: 2 },
  statVal: { fontSize: 20, fontWeight: 600 },
  statLabel: { fontSize: 11, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" },
  statDiv: { width: 1, height: 36, backgroundColor: "var(--border-default)" },
  grid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, alignItems: "start" },
  instruccionesBox: {
    backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)", padding: "20px 24px",
  },
  instrTitulo: { fontSize: 14, fontWeight: 600, marginBottom: 8 },
  instrDesc: { fontSize: 13, color: "var(--text-secondary)", marginBottom: 10, lineHeight: 1.6 },
  codeBlock: {
    fontFamily: "var(--font-mono)", fontSize: 12, backgroundColor: "var(--bg-secondary)",
    padding: "10px 14px", borderRadius: "var(--radius-md)",
  },
  code: { fontFamily: "var(--font-mono)", fontSize: 12, backgroundColor: "var(--bg-secondary)", padding: "1px 5px", borderRadius: 3 },
};
