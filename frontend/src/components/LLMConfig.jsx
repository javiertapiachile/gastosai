/**
 * Panel de configuración LLM con actualización en caliente.
 * Los cambios se aplican inmediatamente sin reiniciar Docker.
 * Para que sean permanentes hay que actualizar el .env.
 */

import { useState } from "react";
import client from "../api/client";

const PROVEEDORES = [
  {
    id: "anthropic",
    nombre: "Anthropic Claude",
    modelo: "claude-3-5-haiku-latest",
    descripcion: "Rápido y preciso. Recomendado para clasificación.",
    campoKey: "anthropic_api_key",
    placeholder: "sk-ant-api03-...",
  },
  {
    id: "openai",
    nombre: "OpenAI",
    modelo: "gpt-4o-mini",
    descripcion: "Excelente calidad, costo muy bajo.",
    campoKey: "openai_api_key",
    placeholder: "sk-proj-...",
  },
  {
    id: "ollama",
    nombre: "Ollama (local)",
    modelo: "gemma4, llama3, mistral...",
    descripcion: "100% local, sin costo. Requiere Ollama instalado.",
    campoKey: null,
  },
];

export default function LLMConfig({ configActual, onActualizado }) {
  const [proveedorSeleccionado, setProveedorSeleccionado] = useState(
    configActual?.llm_provider || "anthropic"
  );
  const [apiKey, setApiKey] = useState("");
  const [ollamaModel, setOllamaModel] = useState(configActual?.ollama_model || "");
  const [ollamaUrl, setOllamaUrl] = useState(configActual?.ollama_base_url || "");
  const [guardando, setGuardando] = useState(false);
  const [probando, setProbando] = useState(false);
  const [resultadoTest, setResultadoTest] = useState(null);
  const [error, setError] = useState(null);
  const [exito, setExito] = useState(null);

  async function guardarConfig() {
    setGuardando(true);
    setError(null);
    setExito(null);

    const payload = { llm_provider: proveedorSeleccionado };

    if (proveedorSeleccionado === "anthropic" && apiKey) {
      payload.anthropic_api_key = apiKey;
    }
    if (proveedorSeleccionado === "openai" && apiKey) {
      payload.openai_api_key = apiKey;
    }
    if (proveedorSeleccionado === "ollama") {
      if (ollamaModel) payload.ollama_model = ollamaModel;
      if (ollamaUrl) payload.ollama_base_url = ollamaUrl;
    }

    try {
      const { data } = await client.patch("/config/", payload);
      setExito(`✅ ${data.mensaje}`);
      setApiKey(""); // Limpiar key por seguridad
      onActualizado?.();
    } catch (err) {
      setError(err.response?.data?.detail || "Error al guardar configuración");
    } finally {
      setGuardando(false);
    }
  }

  async function probarConexion() {
    setProbando(true);
    setResultadoTest(null);
    try {
      const { data } = await client.get("/config/llm/test");
      setResultadoTest(data);
    } catch (err) {
      setResultadoTest({ ok: false, error: err.message });
    } finally {
      setProbando(false);
    }
  }

  const proveedor = PROVEEDORES.find(p => p.id === proveedorSeleccionado);
  const proveedorActualEnServidor = configActual?.llm_provider;

  return (
    <div style={styles.seccion}>
      <h2 style={styles.titulo}>Proveedor LLM</h2>

      {/* Selector de proveedor */}
      <div style={styles.grid}>
        {PROVEEDORES.map((p) => {
          const activo = p.id === proveedorActualEnServidor;
          const seleccionado = p.id === proveedorSeleccionado;
          return (
            <div
              key={p.id}
              onClick={() => { setProveedorSeleccionado(p.id); setResultadoTest(null); setExito(null); }}
              style={{
                ...styles.card,
                ...(seleccionado ? styles.cardSeleccionado : {}),
                cursor: "pointer",
              }}
            >
              <div style={styles.cardHeader}>
                <span style={styles.cardNombre}>{p.nombre}</span>
                {activo && <span style={styles.badgeActivo}>activo</span>}
              </div>
              <div style={styles.cardModelo}>{p.modelo}</div>
              <div style={styles.cardDesc}>{p.descripcion}</div>
            </div>
          );
        })}
      </div>

      {/* Campos específicos del proveedor */}
      <div style={styles.campos}>
        {(proveedorSeleccionado === "anthropic" || proveedorSeleccionado === "openai") && (
          <div style={styles.campo}>
            <label style={styles.label}>
              API Key
              {configActual?.[proveedorSeleccionado === "anthropic" ? "anthropic_configurado" : "openai_configurado"] && (
                <span style={styles.yaConfigurado}> ✓ ya configurada</span>
              )}
            </label>
            <input
              type="password"
              placeholder={proveedor?.placeholder || "Ingresa tu API key"}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              style={styles.input}
            />
            <span style={styles.hint}>
              Deja vacío para mantener la key actual.
            </span>
          </div>
        )}

        {proveedorSeleccionado === "ollama" && (
          <>
            <div style={styles.campo}>
              <label style={styles.label}>Modelo</label>
              <input
                type="text"
                placeholder={configActual?.ollama_model || "gemma4:latest"}
                value={ollamaModel}
                onChange={(e) => setOllamaModel(e.target.value)}
                style={styles.input}
              />
            </div>
            <div style={styles.campo}>
              <label style={styles.label}>URL de Ollama</label>
              <input
                type="text"
                placeholder={configActual?.ollama_base_url || "http://host.docker.internal:11434"}
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
                style={styles.input}
              />
            </div>
          </>
        )}
      </div>

      {error && <div style={styles.errorBox}>{error}</div>}
      {exito && <div style={styles.exitoBox}>{exito}</div>}

      {/* Acciones */}
      <div style={styles.acciones}>
        <button
          style={{ ...styles.btnGuardar, opacity: guardando ? 0.7 : 1 }}
          onClick={guardarConfig}
          disabled={guardando}
        >
          {guardando ? "Guardando..." : "Aplicar configuración"}
        </button>

        <button
          style={{ ...styles.btnTest, opacity: probando ? 0.7 : 1 }}
          onClick={probarConexion}
          disabled={probando}
        >
          {probando ? "Probando..." : "🔌 Probar conexión"}
        </button>

        {resultadoTest && (
          <span style={{
            fontSize: 13, fontWeight: 500, padding: "6px 12px",
            borderRadius: "var(--radius-md)",
            color: resultadoTest.ok ? "var(--success)" : "var(--danger)",
            backgroundColor: resultadoTest.ok ? "var(--success-light)" : "var(--danger-light)",
          }}>
            {resultadoTest.ok
              ? `✅ ${resultadoTest.proveedor}`
              : `❌ ${resultadoTest.error?.slice(0, 60)}`}
          </span>
        )}
      </div>

      <p style={styles.nota}>
        Los cambios se aplican inmediatamente. Para que sean permanentes entre reinicios,
        actualiza también el archivo <code style={styles.code}>.env</code>.
      </p>
    </div>
  );
}

const styles = {
  seccion: {
    backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-lg)", padding: "24px", marginBottom: 16,
  },
  titulo: { fontSize: 15, fontWeight: 600, marginBottom: 16 },
  grid: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 16 },
  card: {
    border: "1px solid var(--border-default)", borderRadius: "var(--radius-md)",
    padding: "12px 14px", transition: "all 0.15s",
  },
  cardSeleccionado: { borderColor: "var(--accent)", backgroundColor: "var(--accent-light)" },
  cardHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 },
  cardNombre: { fontSize: 13, fontWeight: 600 },
  badgeActivo: {
    fontSize: 10, fontWeight: 600, backgroundColor: "var(--success-light)",
    color: "var(--success)", padding: "1px 6px", borderRadius: 99,
  },
  cardModelo: { fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--text-secondary)", marginBottom: 4 },
  cardDesc: { fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.4 },
  campos: { marginBottom: 14 },
  campo: { marginBottom: 10 },
  label: { display: "block", fontSize: 12, fontWeight: 500, color: "var(--text-secondary)", marginBottom: 5 },
  yaConfigurado: { fontWeight: 400, color: "var(--success)" },
  input: {
    width: "100%", padding: "8px 12px", fontSize: 13,
    border: "1px solid var(--border-default)", borderRadius: "var(--radius-md)",
    backgroundColor: "var(--bg-secondary)", color: "var(--text-primary)",
    outline: "none", boxSizing: "border-box",
  },
  hint: { fontSize: 11, color: "var(--text-tertiary)", marginTop: 3, display: "block" },
  errorBox: {
    backgroundColor: "var(--danger-light)", color: "var(--danger)",
    borderRadius: "var(--radius-md)", padding: "10px 14px", fontSize: 13, marginBottom: 12,
  },
  exitoBox: {
    backgroundColor: "var(--success-light)", color: "var(--success)",
    borderRadius: "var(--radius-md)", padding: "10px 14px", fontSize: 13, marginBottom: 12,
  },
  acciones: { display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginBottom: 12 },
  btnGuardar: {
    fontSize: 13, fontWeight: 500, backgroundColor: "var(--accent)", color: "white",
    border: "none", borderRadius: "var(--radius-md)", padding: "8px 16px", cursor: "pointer",
  },
  btnTest: {
    fontSize: 13, border: "1px solid var(--border-default)", borderRadius: "var(--radius-md)",
    padding: "8px 14px", cursor: "pointer", backgroundColor: "var(--bg-secondary)",
    color: "var(--text-primary)",
  },
  nota: { fontSize: 11, color: "var(--text-tertiary)", lineHeight: 1.6 },
  code: {
    fontFamily: "var(--font-mono)", fontSize: 11, backgroundColor: "var(--bg-secondary)",
    padding: "1px 4px", borderRadius: 3,
  },
};
