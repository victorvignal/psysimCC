import json
import os
from collections.abc import AsyncGenerator
from dataclasses import dataclass

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


RUBRICA_DIMENSOES = [
    "Empatia e validação",
    "Formulação de caso",
    "Técnica de entrevista",
    "Manejo de resistência",
    "Aliança terapêutica",
    "Planejamento terapêutico",
]


@dataclass
class DimensaoRubrica:
    nome: str
    score: int        # 1–5
    justificativa: str


def _build_rubrica_prompt(ficha: Ficha, approach_key: str) -> str:
    a = ficha.apresentacao
    approach_desc = APPROACHES.get(approach_key, approach_key)
    dims = "\n".join(f"- {d}" for d in RUBRICA_DIMENSOES)
    return f"""Você é um supervisor clínico avaliando uma sessão de treino.

Contexto do caso:
- Paciente: {a.nome_ficticio}, {a.idade} anos, {a.genero}, {a.ocupacao}
- Queixa: {ficha.queixa_principal}
- Abordagem avaliada: {approach_key} — {approach_desc}

Avalie a sessão nas dimensões abaixo com nota de 1 a 5 e justificativa de 1–2 frases baseada EXCLUSIVAMENTE no que apareceu na transcrição.

Escala: 1 = ausente/inadequado · 2 = insuficiente · 3 = adequado · 4 = bom · 5 = excelente

Dimensões:
{dims}

Retorne APENAS JSON válido, sem texto fora do JSON:
{{
  "dimensoes": [
    {{"nome": "...", "score": N, "justificativa": "..."}},
    ...
  ]
}}"""


def _format_transcript(nome: str, history: list[dict[str, str]]) -> str:
    lines = []
    for turn in history:
        speaker = "Terapeuta" if turn["role"] == "user" else nome
        lines.append(f"**{speaker}:** {turn['content']}")
    return "\n\n".join(lines)


def _build_system_prompt(ficha: Ficha, approach_key: str) -> str:
    a = ficha.apresentacao
    approach_desc = APPROACHES.get(approach_key, approach_key)

    return f"""Você é um supervisor clínico experiente conduzindo uma revisão pós-sessão com um estudante de psicologia em formação.

## Contexto do caso

Você sabe apenas o que qualquer supervisor saberia antes de ver a sessão: os dados de apresentação do paciente e a queixa que o trouxe até aqui. Sua análise deve se basear EXCLUSIVAMENTE no que apareceu na transcrição — não faça inferências a partir de informações que o paciente não trouxe na sessão.

**Apresentação:**
- Paciente: {a.nome_ficticio}, {a.idade} anos, {a.genero}, {a.ocupacao}
- Queixa principal: {ficha.queixa_principal}

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

Tom: acolhedor, educativo, direto. Tudo o que você sabe sobre o paciente além dos dados de apresentação acima vem da transcrição — nada mais."""


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

    def get_rubrica(
        self, ficha: Ficha, history: list[dict[str, str]], approach: str
    ) -> list[DimensaoRubrica]:
        transcript = _format_transcript(ficha.apresentacao.nome_ficticio, history)
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _build_rubrica_prompt(ficha, approach)},
                {"role": "user", "content": f"Transcrição:\n\n{transcript}"},
            ],
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        return [
            DimensaoRubrica(
                nome=d["nome"],
                score=max(1, min(5, int(d["score"]))),
                justificativa=d.get("justificativa", ""),
            )
            for d in data.get("dimensoes", [])
        ]

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
