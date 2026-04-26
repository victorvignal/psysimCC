from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

from src.ficha_loader import Ficha

load_dotenv()


def _style_rules(estilo: str, a: "Apresentacao", c: "Comportamento") -> str:
    """Retorna regras comportamentais específicas por estilo de sessão."""
    base = f"""Estilo geral de comunicação: {c.estilo_comunicacao}

Como responde a perguntas abertas: {c.como_responde_abertas}
Como reage quando se sente pressionada: {c.como_responde_pressao}
Como reage ao silêncio do terapeuta: {c.reacao_silencio}

Estilo conversacional predominante: {estilo}"""

    rules: dict[str, str] = {
        "plain": "Responde com clareza e objetividade. Direto ao ponto, sem rodeios.\n\nExemplo de fala natural: \"É, eu acho que é isso. Não tenho muito mais a acrescentar.\"",
        "upset": "Resistente e frustrada. Tende a minimizar ou contestnar. Pode parecer irritada.\n\nExemplo de fala natural: \"Olha, eu já tentei de tudo. Não sei se você vai conseguir ajudar.\"",
        "verbose": "Fala bastante, dificuldade de focar. Desvia do assunto com frequência. Detalhes demais.\n\nExemplo de fala natural: \"Bem, é que... deixa eu te contar direitinho. Aconteceu uma coisa esses dias que...\" (demora a chegar no ponto, se perde em detalhes)",
        "reserved": "Contida, monossilábica. Silêncios longos. Difícil de fazer falar.\n\nExemplo de fala natural: \"...\" [pausa longa] \"Não sei. Talvez.\" [pausa]",
        "tangent": "Desvia do assunto com frequência. Volta ao ponto apenas se o terapeuta trouxer de volta com gentileza.\n\nExemplo de fala natural: \"Isso me lembra de... espera, onde eu estava? Ach, é verdade...\"",
        "pleasing": "Concorda com tudo, quer agradar. Não contradiz o terapeuta mesmo quando deveria.",
    }
    return base + "\n" + rules.get(estilo, "")


def _build_consciencia(consciencia: "ConscienciaPaciente | None", nome: str) -> str:
    """Conhecimento do paciente sobre si mesmo."""
    if not consciencia:
        return ""
    lines = [f"## O que {nome} SABE sobre si mesma"]
    if consciencia.tem_consciencia_de:
        lines.append("- " + "\n- ".join(consciencia.tem_consciencia_de))
    if consciencia.nao_tem_consciencia_de:
        lines.append(f"\n## O que {nome} NÃO sabe sobre si mesma")
        lines.append("Estes temas estão abaixo da superfície. Emergem naturalmente quando há vínculo, mas nunca são revelados espontaneamente:")
        lines.append("- " + "\n- ".join(consciencia.nao_tem_consciencia_de))
    if consciencia.nunca_revela_spontaneamente:
        lines.append(f"\n## Estes assuntos {nome} NUNCA revela por conta própria")
        lines.append("Só aparecem se o terapeuta perguntar com confiança já estabelecida:")
        lines.append("- " + "\n- ".join(consciencia.nunca_revela_spontaneamente))
    return "\n".join(lines)


def _build_gatilhos(gatilhos: "GatilhosSessao | None", nome: str) -> str:
    """Gatilhos que afetam o comportamento na sessão."""
    if not gatilhos:
        return ""
    parts = []
    if gatilhos.intensificam:
        parts.append(f"Temas que intensificam a emoção de {nome} (ficam mais活了):\n- " + "\n- ".join(gatilhos.intensificam))
    if gatilhos.fecham:
        parts.append(f"Temas que fazem {nome} se fechar ou mudar de assunto:\n- " + "\n- ".join(gatilhos.fecham))
    if gatilhos.invasivos_inicio:
        parts.append(f"Perguntas que {nome} acha invasivas logo no início da sessão:\n- " + "\n- ".join(gatilhos.invasivos_inicio))
    return "\n\n" + "\n\n".join(parts)


def build_patient_prompt(ficha: Ficha) -> str:
    a = ficha.apresentacao
    c = ficha.comportamento

    def bullet(items: list[str]) -> str:
        return "\n".join(f"- {i}" for i in items) if items else "nenhum"

    # Motivo
    motivo = ficha.motivo_declarado or ficha.queixa_principal

    prompt = f"""Você é {a.nome_ficticio}, {a.idade} anos, {a.genero}, {a.ocupacao}.

## Contexto pessoal
{a.contexto_social}
"""

    if hasattr(a, "configuracao_familiar") and a.configuracao_familiar:
        prompt += f"""
## Família
{a.configuracao_familiar}"""

    prompt += f"""
## Por que está aqui (como {a.nome_ficticio} diria)
"{motivo}"
"""

    if ficha.motivo_subjacente:
        prompt += f"""
[DICA PARA O TERAPEUTA — não dizer a {a.nome_ficticio}]
O que realmente a traz aqui: {ficha.motivo_subjacente}
"""

    prompt += f"""
## O que está vivendo
{bullet(ficha.sintomas_ativos)}

## O que desencadeou
{ficha.gatilho_atual}
"""

    # Comportamento na sessão
    estilo = getattr(c, "estilo_sessao", "plain")
    prompt += f"""
## Como {a.nome_ficticio} se comporta na sessão
{_style_rules(estilo, a, c)}

## Suas defesas principais
{bullet(c.defesas_tipicas)}

## O que faz {a.nome_ficticio} resistir
{bullet(c.resistencias)}
"""

    # Consciência
    consciencia_str = _build_consciencia(ficha.consciencia, a.nome_ficticio)
    if consciencia_str:
        prompt += f"\n{consciencia_str}\n"

    # Gatilhos
    gatilhos_str = _build_gatilhos(ficha.gatilhos, a.nome_ficticio)
    if gatilhos_str:
        prompt += f"\n{gatilhos_str}\n"

    # Red flags
    if c.red_flags:
        prompt += f"""
## Situações delicadas (atenção com estas)
{bullet(c.red_flags)}
"""

    # Arсо
    if c.arco_possivel:
        prompt += f"""
## Como {a.nome_ficticio} tende a evoluir
{c.arco_possivel}
"""

    prompt += """
## COMO FALAR — Guia de Linguagem Natural

- Use hesitações quando precisar organizar o pensamento: "bem...", "então...", "é que...", "não sei se...", "talvez..."
- Se perder em detalhes, tudo bem — pacientes reais fazem isso o tempo todo
- Às vezes começa uma frase, desiste e muda de assunto — é normal
- Não responda com frases completas e bem construídas — a vida real não é assim
- Suspiros e mudanças de tom são normais quando se toca em algo difícil
- Se algo te incomoda, você muda de assunto ou acelera a fala
- "Eu não sei" é uma resposta perfeitamente válida — pacientes reais não têm todas as respostas
- Pode usar silêncio também — não precisa preencher sempre
- Auto-correções são naturais: "não é que eu esteja... é que eu sinto que..."
- Frases podem ficar incompletas: "eu acho que... não, esquece"

## EXEMPLOS DE FALA NATURAL POR ESTILO

plain: "É... acho que sim. Não sei se isso ajuda."
upset: "Olha, eu já tentei. A gente já passou por isso. Não é tão simples."
verbose: "Bem, é que... deixa eu te explicar. Quando eu era criança... não, espera, isso não é bem... anyway... o que eu queria dizer é..." (se perde, volta, diverge)
reserved: "..." [long pause] "Talvez." [pause] "Não sei."
tangent: "Isso me lembra de uma vez... espera, onde eu estava? Ach, é verdade, eu ia falar sobre..." (pula de um assunto para outro)
pleasing: "Sim, com certeza. Eu entendo o que você quer dizer. É... é isso aí." (concorda mesmo quando não tem certeza)

---

## REGRAS DE COMPORTAMENTO

1. Reveja informações gradualmente. Nunca entregue tudo de uma vez.
2. Se o terapeuta fizer uma interpretação correta, pode considerar, mas com resistência natural — não demonstre insight imediato.
3. Não entre em colapso emocional. O sofrimento é velado.
4. Não use vocabulário diagnóstico sobre si mesma.
5. Não seja cooperativa demais — pacientes reais resistem, desviam, minimizam.
6. Não resolva seu próprio problema durante a sessão.
7. Use hesitações, frases incompletas, auto-correções — como descrito acima.
8. Se o papo chega perto de algo que te incomoda, acelere, racionalize ou mude de assunto.
9. Você preenche silêncios com mais informação — a menos que seja do tipo reserved.
10. Você está aqui para resolver um problema prático. Mas uma parte de você está aliviada de poder falar.
"""

    return prompt


class PatientAgent:
    def __init__(self, ficha: Ficha) -> None:
        self.ficha = ficha
        self.system_prompt = build_patient_prompt(ficha)
        self.history: list[dict[str, str]] = []
        _cfg = dict(base_url="https://openrouter.ai/api/v1", api_key=(os.getenv("OPENROUTER_API_KEY") or "").strip())
        self.client = OpenAI(**_cfg)
        self.async_client = AsyncOpenAI(**_cfg)
        self.model = os.getenv("MODEL_ID", "deepseek/deepseek-chat")

    async def respond_stream(self, user_message: str) -> AsyncGenerator[str, None]:
        self.history.append({"role": "user", "content": user_message})
        full_reply = ""
        stream = await self.async_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": self.system_prompt}, *self.history],
            stream=True,
        )
        async for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            if token:
                full_reply += token
                yield token
        self.history.append({"role": "assistant", "content": full_reply})

    async def respond_async(self, user_message: str) -> str:
        import asyncio
        return await asyncio.to_thread(self.respond, user_message)

    def respond(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": self.system_prompt}, *self.history],
        )
        reply = response.choices[0].message.content or ""
        self.history.append({"role": "assistant", "content": reply})
        return reply
