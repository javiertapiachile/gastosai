/**
 * Páginas placeholder — se implementan en fases posteriores.
 * Fase 1 solo necesita que las rutas existan y rendericen algo.
 */

export function DashboardPage() {
  return (
    <div>
      <h1 style={{ fontSize: "22px", fontWeight: "600", marginBottom: "8px" }}>Dashboard</h1>
      <p style={{ color: "var(--text-secondary)" }}>Los KPIs y gráficos se implementan en Fase 4.</p>
    </div>
  );
}

export function ImportarPage() {
  return (
    <div>
      <h1 style={{ fontSize: "22px", fontWeight: "600", marginBottom: "8px" }}>Importar extracto</h1>
      <p style={{ color: "var(--text-secondary)" }}>El parser de archivos se implementa en Fase 2.</p>
    </div>
  );
}

export function TransaccionesPage() {
  return (
    <div>
      <h1 style={{ fontSize: "22px", fontWeight: "600", marginBottom: "8px" }}>Transacciones</h1>
      <p style={{ color: "var(--text-secondary)" }}>La tabla interactiva se implementa en Fase 4.</p>
    </div>
  );
}

export function ConfiguracionPage() {
  return (
    <div>
      <h1 style={{ fontSize: "22px", fontWeight: "600", marginBottom: "8px" }}>Configuración</h1>
      <p style={{ color: "var(--text-secondary)" }}>La configuración LLM se implementa en Fase 5.</p>
    </div>
  );
}
