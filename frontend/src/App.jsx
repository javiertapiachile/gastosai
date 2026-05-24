/**
 * App con rutas protegidas por autenticación.
 * Si no hay token, muestra LoginPage.
 */

import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import Layout from "./components/Layout";
import LoginPage from "./pages/Login";
import DashboardPage from "./pages/Dashboard";
import ImportarPage from "./pages/Importar";
import TransaccionesPage from "./pages/Transacciones";
import ConfiguracionPage from "./pages/Settings";

function RutaProtegida({ children }) {
  const { token } = useAuthStore();
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  const { inicializar } = useAuthStore();

  useEffect(() => {
    // Restaurar token del localStorage al arrancar
    inicializar();
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        {/* Ruta pública */}
        <Route path="/login" element={<LoginPage />} />

        {/* Rutas protegidas */}
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

        {/* Cualquier ruta desconocida → home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
