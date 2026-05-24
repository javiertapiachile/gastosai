/**
 * Página de autenticación: login y registro.
 */

import { useState } from "react";
import { useAuthStore } from "../store/authStore";

export default function LoginPage() {
  const [modo, setModo] = useState("login");
  const [form, setForm] = useState({ email: "", nombre: "", password: "" });
  const { login, registro, cargando, error } = useAuthStore();

  async function handleSubmit(e) {
    e.preventDefault();

    // Validaciones en cliente antes de llamar al servidor
    if (!form.email.includes("@")) {
      useAuthStore.setState({ error: "Ingresa un email válido" });
      return;
    }
    if (form.password.length < 6) {
      useAuthStore.setState({ error: "La contraseña debe tener al menos 6 caracteres" });
      return;
    }
    if (form.password.length > 72) {
      useAuthStore.setState({ error: "La contraseña no puede superar 72 caracteres" });
      return;
    }
    if (modo === "registro" && form.nombre.trim().length < 2) {
      useAuthStore.setState({ error: "Ingresa tu nombre (mínimo 2 caracteres)" });
      return;
    }

    if (modo === "login") {
      await login(form.email, form.password);
    } else {
      await registro(form.email, form.nombre, form.password);
    }
  }

  function cambiarModo(nuevoModo) {
    setModo(nuevoModo);
    setForm({ email: "", nombre: "", password: "" });
    useAuthStore.setState({ error: null });
  }

  return (
    <div style={styles.wrapper}>
      <div style={styles.card}>
        <div style={styles.logo}>💸 GastosAI</div>
        <p style={styles.tagline}>Dashboard local de gastos personales con IA</p>

        {/* Tabs */}
        <div style={styles.tabs}>
          <button
            style={{ ...styles.tab, ...(modo === "login" ? styles.tabActivo : {}) }}
            onClick={() => cambiarModo("login")}
            type="button"
          >
            Iniciar sesión
          </button>
          <button
            style={{ ...styles.tab, ...(modo === "registro" ? styles.tabActivo : {}) }}
            onClick={() => cambiarModo("registro")}
            type="button"
          >
            Crear cuenta
          </button>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.campoWrapper}>
            <label style={styles.label}>Email</label>
            <input
              type="email"
              placeholder="tu@email.com"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              style={styles.input}
              required
              autoComplete="email"
            />
          </div>

          {modo === "registro" && (
            <div style={styles.campoWrapper}>
              <label style={styles.label}>Nombre</label>
              <input
                type="text"
                placeholder="Tu nombre"
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                style={styles.input}
                required
                autoComplete="name"
              />
            </div>
          )}

          <div style={styles.campoWrapper}>
            <label style={styles.label}>Contraseña</label>
            <input
              type="password"
              placeholder={modo === "registro" ? "Mínimo 6 caracteres" : "Tu contraseña"}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              style={styles.input}
              required
              autoComplete={modo === "login" ? "current-password" : "new-password"}
            />
          </div>

          {/* Error del servidor o validación cliente */}
          {error && (
            <div style={styles.errorBox}>
              ⚠️ {error}
            </div>
          )}

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

        {modo === "registro" && (
          <p style={styles.infoBox}>
            El primer usuario registrado será administrador.
            Los datos de cada usuario son completamente independientes.
          </p>
        )}

        {modo === "login" && (
          <p style={styles.infoBox}>
            ¿Primera vez? Haz clic en <strong>Crear cuenta</strong>.
          </p>
        )}
      </div>
    </div>
  );
}

const styles = {
  wrapper: {
    minHeight: "100vh", display: "flex", alignItems: "center",
    justifyContent: "center", backgroundColor: "var(--bg-tertiary)", padding: 20,
  },
  card: {
    backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-xl)", padding: "36px 40px", width: "100%", maxWidth: 400,
  },
  logo: { fontSize: 24, fontWeight: 600, marginBottom: 6, textAlign: "center" },
  tagline: { fontSize: 13, color: "var(--text-tertiary)", textAlign: "center", marginBottom: 28 },
  tabs: {
    display: "flex", backgroundColor: "var(--bg-secondary)",
    borderRadius: "var(--radius-md)", padding: 3, marginBottom: 24,
  },
  tab: {
    flex: 1, padding: "7px 0", fontSize: 13, fontWeight: 500, border: "none",
    borderRadius: "var(--radius-sm)", cursor: "pointer",
    backgroundColor: "transparent", color: "var(--text-secondary)",
    transition: "all 0.15s ease",
  },
  tabActivo: {
    backgroundColor: "var(--bg-primary)", color: "var(--text-primary)",
    boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
  },
  form: { display: "flex", flexDirection: "column", gap: 14 },
  campoWrapper: { display: "flex", flexDirection: "column", gap: 5 },
  label: { fontSize: 12, fontWeight: 500, color: "var(--text-secondary)" },
  input: {
    width: "100%", padding: "10px 14px", fontSize: 14,
    border: "1px solid var(--border-default)", borderRadius: "var(--radius-md)",
    backgroundColor: "var(--bg-secondary)", color: "var(--text-primary)",
    outline: "none", boxSizing: "border-box",
  },
  errorBox: {
    backgroundColor: "var(--danger-light)", color: "var(--danger)",
    borderRadius: "var(--radius-md)", padding: "10px 14px",
    fontSize: 13, lineHeight: 1.5,
  },
  btnSubmit: {
    width: "100%", padding: "11px 0", fontSize: 14, fontWeight: 600,
    backgroundColor: "var(--accent)", color: "white", border: "none",
    borderRadius: "var(--radius-md)", cursor: "pointer", marginTop: 4,
  },
  infoBox: {
    fontSize: 12, color: "var(--text-tertiary)", textAlign: "center",
    marginTop: 16, lineHeight: 1.6,
  },
};
