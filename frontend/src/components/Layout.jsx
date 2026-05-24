/**
 * Layout principal: topbar con navegación + área de contenido.
 * Todas las páginas se renderizan dentro de este componente.
 */

import { NavLink, Outlet } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/",              label: "Dashboard" },
  { to: "/importar",      label: "Importar" },
  { to: "/transacciones", label: "Transacciones" },
  { to: "/configuracion", label: "Configuración" },
];

export default function Layout() {
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
    gap: "24px",
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
  },
  nav: {
    display: "flex",
    gap: "4px",
  },
  navLink: {
    fontSize: "13px",
    fontWeight: "500",
    color: "var(--text-secondary)",
    textDecoration: "none",
    padding: "5px 10px",
    borderRadius: "var(--radius-md)",
    transition: "var(--transition-fast)",
  },
  navLinkActive: {
    backgroundColor: "var(--accent-light)",
    color: "var(--accent-text)",
  },
  main: {
    flex: 1,
    padding: "24px",
    maxWidth: "1280px",
    width: "100%",
    margin: "0 auto",
  },
};
