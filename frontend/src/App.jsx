/**
 * App con rutas protegidas. RutaProtegida se suscribe reactivamente
 * al store para redirigir inmediatamente tras login/logout.
 */

import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import Layout from "./components/Layout";
import LoginPage from "./pages/Login";
import DashboardPage from "./pages/Dashboard";
import ImportarPage from "./pages/Importar";
import TransaccionesPage from "./pages/Transacciones";
import ConfiguracionPage from "./pages/Settings";

function RutaProtegida({ children }) {
  const token = useAuthStore((state) => state.token);
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function LoginGuard() {
  const token = useAuthStore((state) => state.token);
  // Si ya está autenticado y va a /login, redirigir al dashboard
  if (token) return <Navigate to="/" replace />;
  return <LoginPage />;
}

export default function App() {
  const inicializar = useAuthStore((state) => state.inicializar);

  useEffect(() => {
    inicializar();
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginGuard />} />
        <Route
          path="/"
          element={
            <RutaProtegida>
              <Layout />
            </RutaProtegida>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="importar" element={<ImportarPage />} />
          <Route path="transacciones" element={<TransaccionesPage />} />
          <Route path="configuracion" element={<ConfiguracionPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
