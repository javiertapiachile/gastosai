/**
 * Raíz de la aplicación React con rutas principales.
 */

import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import DashboardPage from "./pages/Dashboard";
import ImportarPage from "./pages/Importar";
import TransaccionesPage from "./pages/Transacciones";
import { ConfiguracionPage } from "./pages/index";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="importar" element={<ImportarPage />} />
          <Route path="transacciones" element={<TransaccionesPage />} />
          <Route path="configuracion" element={<ConfiguracionPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
