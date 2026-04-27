import { listFichas, type FichaInfo } from "@/lib/api";
import PatientGrid from "@/components/PatientGrid";
import DashboardClient from "@/components/DashboardClient";
import LogoutButton from "@/components/LogoutButton";

export default async function Home() {
  let fichas: FichaInfo[] = [];
  let error: string | null = null;

  try {
    fichas = await listFichas();
  } catch {
    error = "Não foi possível conectar ao servidor.";
  }

  return (
    <main className="min-h-screen" style={{ background: "var(--bg)" }}>
      <nav className="h-11 px-6 flex items-center gap-4 shrink-0"
        style={{ background: "var(--nav-bg)", color: "var(--nav-text)" }}>
        <span className="font-bold text-base tracking-tight">psysim</span>
        <span className="w-px h-4 opacity-20" style={{ background: "var(--nav-text)" }} />
        <span className="text-sm" style={{ color: "rgba(250,250,247,0.6)" }}>
          Simulador clínico de psicologia
        </span>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs font-mono" style={{ color: "rgba(250,250,247,0.3)" }}>
            {new Date().toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}
          </span>
          <LogoutButton />
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-10">

        {/* Dashboard + trajetória (client-side, com auth token) */}
        <DashboardClient />

        {/* Pacientes */}
        <div>
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
