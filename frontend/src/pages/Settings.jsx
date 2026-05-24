/**
 * Página de configuración — LLM, categorías, estadísticas del sistema.
 */

import { useState } from "react";
import { useFetch } from "../hooks/useFetch";
import LLMConfig from "../components/LLMConfig";
import CategoryManager from "../components/CategoryManager";

export default function ConfiguracionPage() {
  const [recargarCats, setRecargarCats] = useState(0);

  const { data: config, loading: configLoading } = useFetch("/config/");
  const { data: stats } = useFetch("/config/stats");
  const { data: categorias, refetch: refetchCats } = useFetch(
    "/categories/",
    { _r: recargarCats }
  );

  function handleCatActualizada() {
    setRecargarCats((r) => r + 1);
    refetchCats();
  }

  return (
    <div style={styles.wrapper}>
      <div style={styles.header}>
        <h1 style={styles.titulo}>Configuración</h1>
        <p style={styles.subtitulo}>Gestiona el proveedor LLM y las categorías del sistema</p>
      </div>

      {/* Estado del sistema */}
      <div style={styles.statsBar}>
        <div style={styles.stat}>
          <span style={styles.statVal}>{stats?.total_transacciones ?? "—"}</span>
          <span style={styles.statLabel}>Transacciones</span>
        </div>
        <div style={styles.statDivider} />
        <div style={styles.stat}>
          <span style={styles.statVal}>{stats?.total_importaciones ?? "—"}</span>
          <span style={styles.statLabel}>Importaciones</span>
        </div>
        <div style={styles.statDivider} />
        <div style={styles.stat}>
          <span style={styles.statVal}>{stats?.entradas_cache_llm ?? "—"}</span>
          <span style={styles.statLabel}>Entradas en caché LLM</span>
        </div>
        <div style={styles.statDivider} />
        <div style={styles.stat}>
          <span style={styles.statVal}>{stats?.proveedor_llm ?? "—"}</span>
          <span style={styles.statLabel}>Proveedor activo</span>
        </div>
      </div>

      <div style={styles.grid}>
        {/* Columna izquierda: LLM */}
        <div>
          {configLoading ? (
            <div style={styles.skeleton} />
          ) : (
            <LLMConfig configActual={config} />
          )}

          {/* Instrucciones de cambio de proveedor */}
          <div style={styles.instruccionesBox}>
            <h3 style={styles.instruccionesTitulo}>¿Cómo cambiar el proveedor?</h3>
            <ol style={styles.pasos}>
              <li style={styles.paso}>
                Edita el archivo <code style={styles.code}>.env</code> en la raíz del proyecto
              </li>
              <li style={styles.paso}>
                Cambia <code style={styles.code}>LLM_PROVIDER=anthropic</code> por el proveedor deseado
              </li>
              <li style={styles.paso}>
                Agrega la API key correspondiente
              </li>
              <li style={styles.paso}>
                Ejecuta <code style={styles.code}>docker compose down && docker compose up</code>
              </li>
            </ol>
          </div>
        </div>

        {/* Columna derecha: categorías */}
        <div>
          <CategoryManager
            categorias={categorias}
            onActualizado={handleCatActualizada}
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
    display: "flex",
    alignItems: "center",
    gap: 0,
    backgroundColor: "var(--bg-primary)",
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)",
    padding: "16px 24px",
    marginBottom: 20,
    flexWrap: "wrap",
  },
  stat: { display: "flex", flexDirection: "column", alignItems: "center", padding: "0 24px", gap: 2 },
  statVal: { fontSize: 20, fontWeight: 600, color: "var(--text-primary)" },
  statLabel: { fontSize: 11, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" },
  statDivider: { width: 1, height: 36, backgroundColor: "var(--border-default)" },

  grid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 16,
    alignItems: "start",
  },

  skeleton: {
    height: 300,
    backgroundColor: "var(--bg-secondary)",
    borderRadius: "var(--radius-lg)",
    marginBottom: 16,
  },

  instruccionesBox: {
    backgroundColor: "var(--bg-primary)",
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)",
    padding: "20px 24px",
  },
  instruccionesTitulo: { fontSize: 14, fontWeight: 600, marginBottom: 12 },
  pasos: { paddingLeft: 20 },
  paso: { fontSize: 13, color: "var(--text-secondary)", marginBottom: 8, lineHeight: 1.6 },
  code: {
    fontFamily: "var(--font-mono)",
    fontSize: 12,
    backgroundColor: "var(--bg-secondary)",
    padding: "1px 5px",
    borderRadius: 3,
    color: "var(--text-primary)",
  },
};
