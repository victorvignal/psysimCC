from pathlib import Path

import chainlit as cl

from src.ficha_loader import load_ficha
from src.patient_agent import PatientAgent
from src.voice import PatientVoice, voice_for_ficha, _clean_text

_PROJECT_ROOT = Path(__file__).parent.parent
_VALIDATED_DIR = _PROJECT_ROOT / "fichas" / "validated"


@cl.set_chat_profiles
async def chat_profiles() -> list[cl.ChatProfile]:
    return [
        cl.ChatProfile(
            name=p.stem,
            markdown_description=p.stem.replace("_", " ").title(),
        )
        for p in sorted(_VALIDATED_DIR.glob("*.yaml"))
    ]


@cl.on_chat_start
async def on_start() -> None:
    profile = cl.user_session.get("chat_profile") or "maria_01"
    ficha = load_ficha(_VALIDATED_DIR / f"{profile}.yaml")

    agent = PatientAgent(ficha)
    tts = voice_for_ficha(ficha.apresentacao.genero)

    cl.user_session.set("agent", agent)
    cl.user_session.set("tts", tts)
    cl.user_session.set("nome", ficha.apresentacao.nome_ficticio)

    await cl.Message(
        content=(
            f"**Patient:** {ficha.apresentacao.nome_ficticio} &nbsp;|&nbsp; "
            f"**Level:** {ficha.nivel_dificuldade}\n\n"
            "*Session started. Greet the patient to begin.*"
        ),
    ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    agent: PatientAgent | None = cl.user_session.get("agent")
    if not agent:
        await cl.Message(content="No patient loaded. Please start a new chat.").send()
        return

    tts: PatientVoice = cl.user_session.get("tts")
    nome: str = cl.user_session.get("nome", "Patient")

    # Stream patient response token by token
    msg = cl.Message(content="", author=nome)
    await msg.send()

    full_reply = ""
    async for token in agent.respond_stream(message.content):
        await msg.stream_token(token)
        full_reply += token

    await msg.update()

    # Attach TTS audio below the text response
    if tts and full_reply.strip():
        try:
            wav = tts.synthesize(full_reply)
            if wav:
                await cl.Message(
                    content="",
                    author=nome,
                    elements=[cl.Audio(content=wav, mime="audio/wav", name="voice", display="inline")],
                ).send()
        except Exception:
            pass
