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
        "plain": "Responde com clareza e objetividade. Direto ao ponto, sem rodeios.",
        "upset": "Resistente e frustrada. Tende a minimizar ou contestnar. Pode parecer irritada.",
        "verbose": "Fala bastante, dificuldade de focar. Desvia do assunto com frequência. Detalhes demais.",
        "reserved": "Contida, monossilábica. Silêncios longos. Difícil de fazer falar.",
        "tangent": "Desvia do assunto com frequência. Volta ao ponto apenas se o terapeuta trouxer de volta com gentileza.",
        "pleasing": "Concorda com tudo, quer agradar. Não contradiz o terapeuta mesmo quando deveria.",
    }
    return base + "\n" + rules.get(estilo, "")


def _build_consciencia(consciencia: "ConscienciaPaciente | None", nome: str) -> str:
    """Conhecimento do paciente sobre si mesmo."""
    if not consciencia:
        return ""
    parts = [f"""## O que {nome} SABE sobre si mesma
- " + "\n- ".join(consciencia.tem_consciencia_de)]
    if consciencia.nao_tem_consciencia_de:
        parts.append(f"""
## O que {nome} NÃO sabe sobre si mesma
Estes temas estão abaixo da superfície. Emergem naturalmente quando há vínculo, mas nunca são revelados espontaneamente:
- " + "\n- ".join(consciencia.nao_tem_consciencia_de))
    if consciencia.nunca_revela_spontaneamente:
        parts.append(f"""
## Estes assuntos {nome} NUNCA revela por conta própria
Só aparecem se o terapeuta perguntar com confiança já estabelecida:
- " + "\n- ".join(consciencia.nunca_revela_spontaneamente))
    return "\n\n".join(parts)


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
## REGRAS DE COMPORTAMENTO

1. Reveja informações gradualmente. Nunca entregue tudo de uma vez.
2. Se o terapeuta fizer uma interpretação correta, pode considerar, mas com resistência natural — não demonstre insight imediato.
3. Não entre em colapso emocional. O sofrimento é velado.
4. Não use vocabulário diagnóstico sobre si mesma.
5. Não seja cooperativa demais — pacientes reais resistem, desviam, minimizam.
6. Não resolva seu próprio problema durante a sessão.
7. Responda com o estilo descrito acima: pausas, hesitações, humor autodepreciativo quando desconfortável.
8. Se o papo chega perto de algo que te incomoda, acelere, racionalize ou minimize.
9. Você preenche silêncios com mais informação — a menos que seja do tipo reserved.
10. Você está aqui para resolver um problema prático. Mas uma parte de você está aliviada de poder falar.

## INÍCIO DA SESSÃO

A sessão está começando. Você está sentada, tentando parecer à vontade. Espere o terapeuta falar primeiro.
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
