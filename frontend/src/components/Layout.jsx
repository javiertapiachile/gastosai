/**
 * Layout principal con nav + info de usuario + logout.
 */

import { NavLink, Outlet } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

const NAV_ITEMS = [
  { to: "/",              label: "Dashboard" },
  { to: "/importar",      label: "Importar" },
  { to: "/transacciones", label: "Transacciones" },
  { to: "/configuracion", label: "Configuración" },
];

export default function Layout() {
  const { usuario, logout } = useAuthStore();

  return (
    <div style={styles.wrapper}>
      <header style={styles.topbar}>
        <span style={styles.logo}>💸 GastosAI</span>

        <nav style={styles.nav}>
          {NAV_ITEMS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              style={({ isActive }) => ({
                ...styles.navLink,
                ...(isActive ? styles.navLinkActive : {}),
              })}
            >
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Info de usuario */}
        <div style={styles.userArea}>
          <span style={styles.userName}>
            {usuario?.nombre}
            {usuario?.es_admin && <span style={styles.adminBadge}>admin</span>}
          </span>
          <button style={styles.btnLogout} onClick={logout}>
            Salir
          </button>
        </div>
      </header>

      <main style={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}

const styles = {
  wrapper: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    backgroundColor: "var(--bg-tertiary)",
  },
  topbar: {
    backgroundColor: "var(--bg-primary)",
    borderBottom: "1px solid var(--border-default)",
    padding: "0 24px",
    height: "52px",
    display: "flex",
    alignItems: "center",
    gap: "16px",
    position: "sticky",
    top: 0,
    zIndex: 100,
  },
  logo: {
    fontSize: "15px",
    fontWeight: "600",
    color: "var(--text-primary)",
    letterSpacing: "-0.02em",
    marginRight: "8px",
    whiteSpace: "nowrap",
  },
  nav: {
    display: "flex",
    gap: "4px",
    flex: 1,
  },
  navLink: {
    fontSize: "13px",
    fontWeight: "500",
    color: "var(--text-secondary)",
    textDecoration: "none",
    padding: "5px 10px",
    borderRadius: "var(--radius-md)",
    transition: "var(--transition-fast)",
    whiteSpace: "nowrap",
  },
  navLinkActive: {
    backgroundColor: "var(--accent-light)",
    color: "var(--accent-text)",
  },
  userArea: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    marginLeft: "auto",
  },
  userName: {
    fontSize: "13px",
    color: "var(--text-secondary)",
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  adminBadge: {
    fontSize: "10px",
    fontWeight: "600",
    backgroundColor: "var(--accent-light)",
    color: "var(--accent-text)",
    padding: "1px 6px",
    borderRadius: "99px",
  },
  btnLogout: {
    fontSize: "12px",
    fontWeight: "500",
    border: "1px solid var(--border-default)",
    borderRadius: "var(--radius-md)",
    padding: "4px 12px",
    cursor: "pointer",
    backgroundColor: "var(--bg-secondary)",
    color: "var(--text-secondary)",
  },
  main: {
    flex: 1,
    padding: "24px",
    maxWidth: "1280px",
    width: "100%",
    margin: "0 auto",
  },
};
