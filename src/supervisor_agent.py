import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

from src.ficha_loader import Ficha

load_dotenv()

APPROACHES: dict[str, str] = {
    "TCC": "Terapia Cognitivo-Comportamental — pensamentos automáticos, crenças centrais, distorções cognitivas, ativação comportamental, questionamento socrático",
    "Psicodinâmica": "Terapia Psicodinâmica — mecanismos de defesa, transferência, conflitos inconscientes, aliança terapêutica, interpretação",
    "Humanista": "Abordagem Humanista / Centrada na Pessoa (Rogers) — empatia, aceitação incondicional, congruência, reflexo de sentimentos",
    "ACT": "Terapia de Aceitação e Compromisso — desfusão cognitiva, aceitação, valores, ação comprometida, flexibilidade psicológica",
    "Sistêmica": "Terapia Sistêmica — padrões relacionais, contexto familiar, papéis, comunicação, circularidade",
    "Integrativa": "Abordagem Integrativa — combinação eclética de técnicas conforme as necessidades do paciente e do momento clínico",
}


def _format_transcript(nome: str, history: list[dict[str, str]]) -> str:
    lines = []
    for turn in history:
        speaker = "Terapeuta" if turn["role"] == "user" else nome
        lines.append(f"**{speaker}:** {turn['content']}")
    return "\n\n".join(lines)


def _build_system_prompt(ficha: Ficha, approach_key: str) -> str:
    ui = ficha.uso_interno
    a = ficha.apresentacao
    approach_desc = APPROACHES.get(approach_key, approach_key)

    diagnostico = ui.diagnostico_hipotese if ui else "não disponível"
    psicodinamica = ui.formulacao_psicodinamica if ui else "não disponível"
    tcc_form = ui.formulacao_tcc if ui else "não disponível"
    temas = ", ".join(ui.temas_evitados) if (ui and ui.temas_evitados) else "não especificados"

    return f"""Você é um supervisor clínico experiente conduzindo uma revisão pós-sessão com um estudante de psicologia em formação.

## Referência clínica privada (use apenas como lente — não revele diretamente)

Você tem acesso ao caso completo para calibrar sua supervisão, mas sua análise deve se basear EXCLUSIVAMENTE no que apareceu na transcrição. Use esta referência para:
- Reconhecer a relevância clínica do que o paciente disse ou sinalizou
- Identificar quando o terapeuta passou por cima de algo importante que o paciente trouxe
- Avaliar se as intervenções estavam alinhadas com o quadro real

Nunca mencione diagnóstico, formulação ou temas que o paciente não sinalizou na sessão. Se algo do caso completo não apareceu na conversa, não existe para esta supervisão.

**Referência (confidencial):**
- Paciente: {a.nome_ficticio}, {a.idade} anos, {a.genero}, {a.ocupacao}
- Queixa: {ficha.queixa_principal}
- Hipótese diagnóstica: {diagnostico}
- Formulação psicodinâmica: {psicodinamica}
- Formulação TCC: {tcc_form}
- Temas que o paciente tende a evitar: {temas}

## Abordagem sendo avaliada

**{approach_key}:** {approach_desc}

---

Escreva seu feedback em português brasileiro, seguindo exatamente esta estrutura:

### 📋 Formulação emergente — perspectiva {approach_key}
Com base apenas no que apareceu na transcrição, que hipótese clínica começa a se formar? Use linguagem de hipótese ("parece que", "sugere", "pode indicar") — não afirmações diagnósticas. Cite falas reais do paciente que sustentam cada elemento.

### ✅ O que funcionou
2–3 momentos específicos onde as intervenções foram clinicamente adequadas. Cite o diálogo com aspas. Explique por que funcionou dentro desta abordagem.

### 🔄 Oportunidades de crescimento
2–3 momentos onde o paciente sinalizou algo importante que o terapeuta não explorou. Baseie-se apenas no que está na transcrição — não em informações de fundo. Cite a fala do paciente e ofereça uma resposta alternativa concreta.

### 💬 Como poderia ter sido
Reescreva uma troca-chave da sessão (3–5 turnos) demonstrando como ficaria com técnicas de {approach_key}. Realista — não perfeito.

### 📚 Conceitos-chave
3–4 conceitos de {approach_key} mais relevantes para o que emergiu nesta sessão específica. Para cada: o que significa, como apareceu (ou poderia ter aparecido) na conversa, como trabalhar na prática.

### 🎯 Para a próxima sessão
2–3 sugestões baseadas no que ficou aberto nesta sessão.

---

Tom: acolhedor, educativo, direto. Apenas o que está na transcrição existe para você."""


class SupervisorAgent:
    def __init__(self) -> None:
        cfg = dict(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.client = OpenAI(**cfg)
        self.async_client = AsyncOpenAI(**cfg)
        self.model = (
            os.getenv("SUPERVISOR_MODEL_ID")
            or os.getenv("MODEL_ID", "deepseek/deepseek-chat")
        )

    def supervise(self, ficha: Ficha, history: list[dict[str, str]], approach: str) -> str:
        transcript = _format_transcript(ficha.apresentacao.nome_ficticio, history)
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _build_system_prompt(ficha, approach)},
                {"role": "user", "content": f"Transcrição da sessão:\n\n{transcript}"},
            ],
        )
        return resp.choices[0].message.content or ""

    async def supervise_stream(
        self, ficha: Ficha, history: list[dict[str, str]], approach: str
    ) -> AsyncGenerator[str, None]:
        transcript = _format_transcript(ficha.apresentacao.nome_ficticio, history)
        stream = await self.async_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _build_system_prompt(ficha, approach)},
                {"role": "user", "content": f"Transcrição da sessão:\n\n{transcript}"},
            ],
            stream=True,
        )
        async for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            if token:
                yield token
