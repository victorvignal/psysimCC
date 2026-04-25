import os
from pathlib import Path

import chainlit as cl

from src.database import save_session, save_supervision
from src.ficha_loader import load_ficha
from src.patient_agent import PatientAgent
from src.supervisor_agent import APPROACHES, SupervisorAgent
from src.timer import SessionTimer
from src.voice import PatientVoice, voice_for_ficha

_SESSION_DURATION = int(os.getenv("SESSION_DURATION_MINUTES", "0"))

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

    timer = SessionTimer(_SESSION_DURATION) if _SESSION_DURATION > 0 else None

    cl.user_session.set("agent", PatientAgent(ficha))
    cl.user_session.set("tts", voice_for_ficha(ficha.apresentacao.genero))
    cl.user_session.set("ficha", ficha)
    cl.user_session.set("nome", ficha.apresentacao.nome_ficticio)
    cl.user_session.set("timer", timer)

    timer_hint = f" &nbsp;|&nbsp; **⏱ {_SESSION_DURATION} min**" if timer else ""
    await cl.Message(
        content=(
            f"**Paciente:** {ficha.apresentacao.nome_ficticio} &nbsp;|&nbsp; "
            f"**Nível:** {ficha.nivel_dificuldade}{timer_hint}\n\n"
            "*Sessão iniciada. Cumprimente o paciente para começar.*\n\n"
            "_Quando quiser supervisão, envie_ **supervisão**_._"
        ),
    ).send()

    if timer:
        timer_msg = await cl.Message(
            content="⏱ Timer de sessão",
            actions=[
                cl.Action(name="timer_show", label="🕐 Ver tempo", payload={}),
                cl.Action(name="timer_toggle", label="⏸ Pausar", payload={}),
            ],
        ).send()
        cl.user_session.set("timer_msg", timer_msg)


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

    timer: SessionTimer | None = cl.user_session.get("timer")
    if timer:
        if timer.expired:
            await cl.Message(content=f"⏱ **Tempo encerrado.** Duração total: {timer.elapsed_str}").send()
            return
        if timer.check_threshold(10):
            await cl.Message(content="⏱ Restam **10 minutos** de sessão.").send()
        elif timer.check_threshold(5):
            await cl.Message(content="⏱ Restam **5 minutos** de sessão.").send()
        elif timer.check_threshold(1):
            await cl.Message(content="⏱ **Último minuto!**").send()

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


@cl.action_callback("timer_show")
async def on_timer_show(action: cl.Action) -> None:
    timer: SessionTimer | None = cl.user_session.get("timer")
    if not timer:
        return
    await cl.Message(content=timer.status_line()).send()


@cl.action_callback("timer_toggle")
async def on_timer_toggle(action: cl.Action) -> None:
    timer: SessionTimer | None = cl.user_session.get("timer")
    timer_msg = cl.user_session.get("timer_msg")
    if not timer:
        return

    paused = timer.toggle()
    toggle_label = "▶ Retomar" if paused else "⏸ Pausar"
    status_text = "⏸ Timer pausado." if paused else "▶ Timer retomado."

    if timer_msg:
        timer_msg.actions = [
            cl.Action(name="timer_show", label="🕐 Ver tempo", payload={}),
            cl.Action(name="timer_toggle", label=toggle_label, payload={}),
        ]
        await timer_msg.update()

    await cl.Message(content=status_text).send()
