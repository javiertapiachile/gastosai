/**
 * Página de autenticación: login y registro en una sola pantalla.
 * El primer usuario registrado se convierte automáticamente en admin.
 */

import { useState } from "react";
import { useAuthStore } from "../store/authStore";

export default function LoginPage() {
  const [modo, setModo] = useState("login"); // "login" | "registro"
  const [form, setForm] = useState({ email: "", nombre: "", password: "" });
  const { login, registro, cargando, error } = useAuthStore();

  async function handleSubmit(e) {
    e.preventDefault();
    if (modo === "login") {
      await login(form.email, form.password);
    } else {
      await registro(form.email, form.nombre, form.password);
    }
  }

  function campo(key, placeholder, type = "text") {
    return (
      <input
        type={type}
        placeholder={placeholder}
        value={form[key]}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        style={styles.input}
        required
        autoComplete={type === "password" ? "current-password" : "email"}
      />
    );
  }

  return (
    <div style={styles.wrapper}>
      <div style={styles.card}>
        {/* Logo */}
        <div style={styles.logo}>💸 GastosAI</div>
        <p style={styles.tagline}>Dashboard local de gastos personales con IA</p>

        {/* Tabs */}
        <div style={styles.tabs}>
          <button
            style={{ ...styles.tab, ...(modo === "login" ? styles.tabActivo : {}) }}
            onClick={() => setModo("login")}
            type="button"
          >
            Iniciar sesión
          </button>
          <button
            style={{ ...styles.tab, ...(modo === "registro" ? styles.tabActivo : {}) }}
            onClick={() => setModo("registro")}
            type="button"
          >
            Crear cuenta
          </button>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} style={styles.form}>
          {campo("email", "Email", "email")}
          {modo === "registro" && campo("nombre", "Tu nombre")}
          {campo("password", "Contraseña", "password")}

          {error && <div style={styles.errorBox}>{error}</div>}

          <button
            type="submit"
            style={{ ...styles.btnSubmit, opacity: cargando ? 0.7 : 1 }}
            disabled={cargando}
          >
            {cargando
              ? "Cargando..."
              : modo === "login" ? "Ingresar" : "Crear cuenta"}
          </button>
        </form>

        {/* Info registro */}
        {modo === "registro" && (
          <p style={styles.infoRegistro}>
            El primer usuario registrado será administrador del sistema.
            Los datos de cada usuario son completamente independientes.
          </p>
        )}

        {modo === "login" && (
          <p style={styles.infoRegistro}>
            ¿Primera vez? Crea una cuenta para empezar.
          </p>
        )}
      </div>
    </div>
  );
}

const styles = {
  wrapper: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "var(--bg-tertiary)",
    padding: 20,
  },
  card: {
    backgroundColor: "var(--bg-primary)",
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-xl)",
    padding: "36px 40px",
    width: "100%",
    maxWidth: 400,
  },
  logo: {
    fontSize: 24,
    fontWeight: 600,
    marginBottom: 6,
    textAlign: "center",
    color: "var(--text-primary)",
  },
  tagline: {
    fontSize: 13,
    color: "var(--text-tertiary)",
    textAlign: "center",
    marginBottom: 28,
  },
  tabs: {
    display: "flex",
    backgroundColor: "var(--bg-secondary)",
    borderRadius: "var(--radius-md)",
    padding: 3,
    marginBottom: 24,
  },
  tab: {
    flex: 1,
    padding: "7px 0",
    fontSize: 13,
    fontWeight: 500,
    border: "none",
    borderRadius: "var(--radius-sm)",
    cursor: "pointer",
    backgroundColor: "transparent",
    color: "var(--text-secondary)",
    transition: "all 0.15s ease",
  },
  tabActivo: {
    backgroundColor: "var(--bg-primary)",
    color: "var(--text-primary)",
    boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  input: {
    width: "100%",
    padding: "10px 14px",
    fontSize: 14,
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)",
    backgroundColor: "var(--bg-secondary)",
    color: "var(--text-primary)",
    outline: "none",
    boxSizing: "border-box",
  },
  errorBox: {
    backgroundColor: "var(--danger-light)",
    color: "var(--danger)",
    borderRadius: "var(--radius-md)",
    padding: "10px 14px",
    fontSize: 13,
  },
  btnSubmit: {
    width: "100%",
    padding: "11px 0",
    fontSize: 14,
    fontWeight: 600,
    backgroundColor: "var(--accent)",
    color: "white",
    border: "none",
    borderRadius: "var(--radius-md)",
    cursor: "pointer",
    marginTop: 4,
  },
  infoRegistro: {
    fontSize: 12,
    color: "var(--text-tertiary)",
    textAlign: "center",
    marginTop: 16,
    lineHeight: 1.6,
  },
};
