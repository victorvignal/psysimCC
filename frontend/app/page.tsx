import { getDashboard, listFichas, type FichaInfo, type Dashboard } from "@/lib/api";
import PatientGrid from "@/components/PatientGrid";
import DashboardStats from "@/components/DashboardStats";

export default async function Home() {
  let fichas: FichaInfo[] = [];
  let dashboard: Dashboard | null = null;
  let error: string | null = null;

  try {
    [fichas, dashboard] = await Promise.all([listFichas(), getDashboard()]);
  } catch {
    try {
      fichas = await listFichas();
    } catch {
      error = "Não foi possível conectar ao servidor.";
    }
  }

  return (
    <main className="min-h-screen" style={{ background: "var(--bg)" }}>
      <nav style={{ background: "var(--nav-bg)", color: "var(--nav-text)" }}
        className="px-6 h-11 flex items-center">
        <span className="font-bold text-base tracking-tight">psysim</span>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-10">

        {/* Stats */}
        {dashboard && <DashboardStats dashboard={dashboard} />}

        {/* Pacientes */}
        <div className="mt-10">
          <h2 className="text-lg font-bold mb-1" style={{ color: "var(--text)" }}>
            Pacientes disponíveis
          </h2>
          <p className="text-xs font-mono mb-5" style={{ color: "var(--text-faint)" }}>
            {fichas.length} {fichas.length === 1 ? "ficha" : "fichas"}
          </p>

          {error ? (
            <div className="rounded-lg p-4 text-sm"
              style={{ background: "var(--red-bg)", color: "var(--red-fg)", border: "1px solid var(--red-fg)" }}>
              {error}
            </div>
          ) : (
            <PatientGrid fichas={fichas} />
          )}
        </div>
      </div>
    </main>
  );
}
