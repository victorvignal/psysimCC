import { listFichas, type FichaInfo } from "@/lib/api";
import PatientGrid from "@/components/PatientGrid";

export default async function Home() {
  let fichas: FichaInfo[] = [];
  let error: string | null = null;

  try {
    fichas = await listFichas();
  } catch {
    error = "Não foi possível conectar ao servidor. Verifique se o backend está rodando.";
  }

  return (
    <main className="min-h-screen" style={{ background: "var(--bg)" }}>
      <nav style={{ background: "var(--nav-bg)", color: "var(--nav-text)" }}
        className="px-6 h-11 flex items-center">
        <span className="font-bold text-base tracking-tight">psysim</span>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-bold mb-0.5" style={{ color: "var(--text)" }}>
          Escolha um paciente
        </h1>
        <p className="text-sm mb-8 font-mono" style={{ color: "var(--text-faint)" }}>
          {error ? "" : `${fichas.length} ${fichas.length === 1 ? "ficha disponível" : "fichas disponíveis"}`}
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
    </main>
  );
}
