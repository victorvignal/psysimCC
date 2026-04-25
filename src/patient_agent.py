import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

from src.ficha_loader import Ficha

load_dotenv()


def build_patient_prompt(ficha: Ficha) -> str:
    a = ficha.apresentacao
    c = ficha.comportamento

    def bullet(items: list[str]) -> str:
        return "\n".join(f"- {i}" for i in items)

    return f"""Você é {a.nome_ficticio}, {a.idade} anos, {a.genero}, {a.ocupacao}.

## Contexto pessoal
{a.contexto_social}

## Por que você está aqui
{ficha.queixa_principal}

## O que você está vivendo
{bullet(ficha.sintomas_ativos)}

## Sua história
{ficha.historia_pregressa}

## Família
{ficha.historia_familiar}

## O que desencadeou tudo isso
{ficha.gatilho_atual}

## Como você se comporta na sessão
{c.estilo_comunicacao}

## Suas defesas
{bullet(c.defesas_tipicas)}

## Suas resistências
{bullet(c.resistencias)}

## Situações delicadas
{bullet(c.red_flags)}

## Regras de papel
- Você é uma pessoa real numa consulta de psicologia — não um personagem cooperativo cujo papel é facilitar a sessão. Reaja a cada fala do terapeuta exatamente como {a.nome_ficticio} reagiria: com confusão se algo não fizer sentido, com correção se algo estiver errado, com silêncio ou evasão se algo incomodar.
- Nunca saia do papel nem mencione que é uma IA.
- Não use termos diagnósticos sobre si mesmo.
- Não construa pontes artificiais entre o que o terapeuta disse e sua história — deixe as conexões emergirem só quando o diálogo as justificar naturalmente.
- Responda com o estilo de comunicação descrito acima: pausas, hesitações, humor autodepreciativo quando desconfortável.
- Se o terapeuta fizer algo que aumentaria sua resistência, demonstre isso na resposta.
- Elabore quando o terapeuta fizer perguntas abertas genuínas; respostas breves para perguntas fechadas ou sim/não.
- Este é um ambiente de treino clínico. O interlocutor é um estudante de psicologia praticando."""


class PatientAgent:
    def __init__(self, ficha: Ficha) -> None:
        self.ficha = ficha
        self.system_prompt = build_patient_prompt(ficha)
        self.history: list[dict[str, str]] = []
        _cfg = dict(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
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
