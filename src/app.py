from pathlib import Path

import chainlit as cl

from src.database import save_session, save_supervision
from src.ficha_loader import load_ficha
from src.patient_agent import PatientAgent
from src.supervisor_agent import APPROACHES, SupervisorAgent
from src.voice import PatientVoice, voice_for_ficha

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

    cl.user_session.set("agent", PatientAgent(ficha))
    cl.user_session.set("tts", voice_for_ficha(ficha.apresentacao.genero))
    cl.user_session.set("ficha", ficha)
    cl.user_session.set("nome", ficha.apresentacao.nome_ficticio)

    await cl.Message(
        content=(
            f"**Paciente:** {ficha.apresentacao.nome_ficticio} &nbsp;|&nbsp; "
            f"**Nível:** {ficha.nivel_dificuldade}\n\n"
            "*Sessão iniciada. Cumprimente o paciente para começar.*\n\n"
            "_Quando quiser supervisão, envie_ **supervisão**_._"
        ),
    ).send()


@cl.on_chat_end
async def on_end() -> None:
    agent: PatientAgent | None = cl.user_session.get("agent")
    ficha = cl.user_session.get("ficha")
    if agent and agent.history and ficha:
        session_id = save_session(ficha.id, agent.history)
        cl.user_session.set("session_id", session_id)


@cl.on_message
async def on_message(message: cl.Message) -> None:
    if "supervis" in message.content.lower():
        await _run_supervision()
        return

    agent: PatientAgent | None = cl.user_session.get("agent")
    if not agent:
        await cl.Message(content="Nenhum paciente carregado. Inicie um novo chat.").send()
        return

    tts: PatientVoice = cl.user_session.get("tts")
    nome: str = cl.user_session.get("nome", "Paciente")

    msg = cl.Message(content="", author=nome)
    await msg.send()

    full_reply = ""
    async for token in agent.respond_stream(message.content):
        await msg.stream_token(token)
        full_reply += token

    await msg.update()

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


async def _run_supervision() -> None:
    agent: PatientAgent | None = cl.user_session.get("agent")
    ficha = cl.user_session.get("ficha")

    if not agent or not agent.history:
        await cl.Message(content="Nenhuma sessão para supervisionar ainda. Converse com o paciente primeiro.").send()
        return

    # Approach selection
    res = await cl.AskActionMessage(
        content="## 🎓 Supervisão\n\nEscolha a abordagem terapêutica:",
        actions=[
            cl.Action(name=key, payload={"approach": key}, label=key)
            for key in APPROACHES
        ],
        timeout=120,
    ).send()

    if not res:
        return

    approach = res.get("approach", "TCC")
    supervisor = SupervisorAgent()

    await cl.Message(content=f"Analisando a sessão pela perspectiva **{approach}**...").send()

    msg = cl.Message(content="", author="Supervisor")
    await msg.send()

    full_feedback = ""
    async for token in supervisor.supervise_stream(ficha, agent.history, approach):
        await msg.stream_token(token)
        full_feedback += token

    await msg.update()

    session_id = cl.user_session.get("session_id")
    if not session_id:
        session_id = save_session(ficha.id, agent.history)
        cl.user_session.set("session_id", session_id)
    save_supervision(session_id, approach, full_feedback)
