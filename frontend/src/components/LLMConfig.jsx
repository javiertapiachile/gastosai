/**
 * Panel de configuración del proveedor LLM.
 * Muestra el proveedor activo y permite probar la conexión.
 * La API key se configura en el .env — no se expone en la UI por seguridad.
 */

import { useState } from "react";
import client from "../api/client";

const PROVEEDORES = [
  {
    id: "anthropic",
    nombre: "Anthropic Claude",
    modelo: "claude-3-5-haiku-latest",
    descripcion: "Rápido, preciso y económico. Recomendado.",
    url: "https://console.anthropic.com",
  },
  {
    id: "openai",
    nombre: "OpenAI",
    modelo: "gpt-4o-mini",
    descripcion: "Excelente calidad de clasificación.",
    url: "https://platform.openai.com/api-keys",
  },
  {
    id: "ollama",
    nombre: "Ollama (local)",
    modelo: "llama3, mistral, etc.",
    descripcion: "100% local, sin costo de API. Requiere Ollama instalado.",
    url: "https://ollama.ai",
  },
];

export default function LLMConfig({ configActual }) {
  const [probando, setProbando] = useState(false);
  const [resultado, setResultado] = useState(null);

  async function probarConexion() {
    setProbando(true);
    setResultado(null);
    try {
      const { data } = await client.get("/config/llm/test");
      setResultado(data);
    } catch (err) {
      setResultado({ ok: false, error: err.message });
    } finally {
      setProbando(false);
    }
  }

  const proveedorActivo = PROVEEDORES.find(
    (p) => p.id === configActual?.llm_provider
  );

  return (
    <div style={styles.seccion}>
      <h2 style={styles.titulo}>Proveedor LLM</h2>
      <p style={styles.desc}>
        El proveedor activo se configura en el archivo <code style={styles.code}>.env</code>.
        Para cambiarlo, edita <code style={styles.code}>LLM_PROVIDER</code> y reinicia Docker.
      </p>

      {/* Tarjetas de proveedores */}
      <div style={styles.grid}>
        {PROVEEDORES.map((p) => {
          const activo = p.id === configActual?.llm_provider;
          const configurado =
            (p.id === "anthropic" && configActual?.anthropic_configurado) ||
            (p.id === "openai" && configActual?.openai_configurado) ||
            p.id === "ollama";

          return (
            <div
              key={p.id}
              style={{
                ...styles.card,
                ...(activo ? styles.cardActivo : {}),
              }}
            >
              <div style={styles.cardHeader}>
                <span style={styles.cardNombre}>{p.nombre}</span>
                {activo && <span style={styles.badgeActivo}>Activo</span>}
                {!activo && configurado && (
                  <span style={styles.badgeConfig}>Configurado</span>
                )}
              </div>
              <div style={styles.cardModelo}>{p.modelo}</div>
              <div style={styles.cardDesc}>{p.descripcion}</div>
              <a
                href={p.url}
                target="_blank"
                rel="noopener noreferrer"
                style={styles.cardLink}
              >
                {p.id === "ollama" ? "Descargar Ollama →" : "Obtener API Key →"}
              </a>
            </div>
          );
        })}
      </div>

      {/* Proveedor actual */}
      <div style={styles.infoBox}>
        <div style={styles.infoRow}>
          <span style={styles.infoLabel}>Proveedor activo</span>
          <span style={styles.infoValor}>
            {proveedorActivo?.nombre ?? configActual?.llm_provider ?? "—"}
          </span>
        </div>
        <div style={styles.infoRow}>
          <span style={styles.infoLabel}>Anthropic API Key</span>
          <span style={styles.infoValor}>
            {configActual?.anthropic_configurado ? "✅ Configurada" : "❌ No configurada"}
          </span>
        </div>
        <div style={styles.infoRow}>
          <span style={styles.infoLabel}>OpenAI API Key</span>
          <span style={styles.infoValor}>
            {configActual?.openai_configurado ? "✅ Configurada" : "❌ No configurada"}
          </span>
        </div>
        {configActual?.llm_provider === "ollama" && (
          <div style={styles.infoRow}>
            <span style={styles.infoLabel}>Modelo Ollama</span>
            <span style={styles.infoValor}>{configActual?.ollama_model}</span>
          </div>
        )}
      </div>

      {/* Botón de prueba */}
      <div style={styles.testRow}>
        <button
          style={{ ...styles.btnTest, opacity: probando ? 0.7 : 1 }}
          onClick={probarConexion}
          disabled={probando}
        >
          {probando ? "Probando conexión..." : "🔌 Probar conexión LLM"}
        </button>

        {resultado && (
          <div style={{
            ...styles.resultadoBox,
            backgroundColor: resultado.ok ? "var(--success-light)" : "var(--danger-light)",
            color: resultado.ok ? "var(--success)" : "var(--danger)",
          }}>
            {resultado.ok
              ? `✅ Conectado — ${resultado.proveedor}`
              : `❌ Error — ${resultado.error}`}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  seccion: {
    backgroundColor: "var(--bg-primary)",
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)",
    padding: "24px",
    marginBottom: 16,
  },
  titulo: { fontSize: 15, fontWeight: 600, marginBottom: 8 },
  desc: { fontSize: 13, color: "var(--text-secondary)", marginBottom: 20, lineHeight: 1.6 },
  code: {
    fontFamily: "var(--font-mono)",
    fontSize: 12,
    backgroundColor: "var(--bg-secondary)",
    padding: "1px 5px",
    borderRadius: 3,
  },

  grid: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 20 },
  card: {
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)",
    padding: "14px 16px",
    cursor: "default",
  },
  cardActivo: {
    borderColor: "var(--accent)",
    backgroundColor: "var(--accent-light)",
  },
  cardHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 },
  cardNombre: { fontSize: 13, fontWeight: 600, color: "var(--text-primary)" },
  badgeActivo: {
    fontSize: 10,
    fontWeight: 600,
    backgroundColor: "var(--accent)",
    color: "white",
    padding: "2px 7px",
    borderRadius: 99,
  },
  badgeConfig: {
    fontSize: 10,
    fontWeight: 600,
    backgroundColor: "var(--success-light)",
    color: "var(--success)",
    padding: "2px 7px",
    borderRadius: 99,
  },
  cardModelo: { fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--text-secondary)", marginBottom: 6 },
  cardDesc: { fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: 10 },
  cardLink: { fontSize: 12, color: "var(--accent)", textDecoration: "none" },

  infoBox: {
    backgroundColor: "var(--bg-secondary)",
    borderRadius: "var(--radius-md)",
    padding: "12px 16px",
    marginBottom: 16,
  },
  infoRow: {
    display: "flex",
    justifyContent: "space-between",
    padding: "5px 0",
    fontSize: 13,
    borderBottom: "1px solid var(--border-default)",
  },
  infoLabel: { color: "var(--text-secondary)" },
  infoValor: { fontWeight: 500, color: "var(--text-primary)" },

  testRow: { display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" },
  btnTest: {
    fontSize: 13,
    fontWeight: 500,
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)",
    padding: "8px 16px",
    backgroundColor: "var(--bg-primary)",
    color: "var(--text-primary)",
    cursor: "pointer",
  },
  resultadoBox: {
    fontSize: 13,
    fontWeight: 500,
    padding: "8px 14px",
    borderRadius: "var(--radius-md)",
  },
};
