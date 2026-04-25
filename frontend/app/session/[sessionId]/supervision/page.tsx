import SupervisionView from "@/components/SupervisionView";

export default async function SupervisionPage({
  params,
  searchParams,
}: {
  params: Promise<{ sessionId: string }>;
  searchParams: Promise<{ nome?: string; approach?: string }>;
}) {
  const { sessionId } = await params;
  const { nome = "Paciente", approach = "TCC" } = await searchParams;
  return (
    <SupervisionView
      sessionId={sessionId}
      nome={nome}
      initialApproach={approach}
    />
  );
}
