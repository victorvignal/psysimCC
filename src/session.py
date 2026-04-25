import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from src.ficha_loader import load_ficha
from src.patient_agent import PatientAgent
from src.supervisor_agent import APPROACHES, SupervisorAgent
from src.timer import SessionTimer
from src.voice import PatientVoice, voice_for_ficha

console = Console()


def save_session(ficha_id: str, history: list[dict[str, str]]) -> Path:
    out = Path("sessions")
    out.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out / f"{ficha_id}_{ts}.json"
    path.write_text(
        json.dumps({"ficha_id": ficha_id, "timestamp": ts, "turns": history}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def run_session(ficha_path: str, voice: bool = False, timer_minutes: int = 0) -> None:
    ficha = load_ficha(ficha_path)
    agent = PatientAgent(ficha)
    nome = ficha.apresentacao.nome_ficticio
    tts: Optional[PatientVoice] = voice_for_ficha(ficha.apresentacao.genero) if voice else None
    timer: Optional[SessionTimer] = SessionTimer(timer_minutes) if timer_minutes > 0 else None

    mode_hint = "  [bold magenta]🔊 voz ativa[/bold magenta]" if voice else ""
    timer_hint = f"  [bold blue]⏱ {timer_minutes} min[/bold blue]" if timer else ""
    timer_cmds = "\n[dim]'t' = ver timer  |  'p' = pausar/retomar[/dim]" if timer else ""
    console.print(Panel(
        f"[bold]Paciente:[/bold] {nome}  |  [bold]Nível:[/bold] {ficha.nivel_dificuldade}{mode_hint}{timer_hint}\n"
        f"[dim]Digite 'sair' para encerrar a sessão[/dim]{timer_cmds}",
        title="[bold cyan]Simulador Clínico[/bold cyan]",
        border_style="cyan",
    ))
    console.print()

    while True:
        if timer:
            if timer.check_threshold(10):
                console.print("[bold yellow]⏱ Restam 10 minutos.[/bold yellow]\n")
            elif timer.check_threshold(5):
                console.print("[bold yellow]⏱ Restam 5 minutos.[/bold yellow]\n")
            elif timer.check_threshold(1):
                console.print("[bold red]⏱ Último minuto![/bold red]\n")

            if timer.expired:
                console.print(Panel(
                    f"[bold]Tempo encerrado.[/bold] Duração: {timer.elapsed_str}",
                    border_style="red",
                ))
                break

        try:
            entrada = Prompt.ask("[bold green]Terapeuta[/bold green]")
        except (KeyboardInterrupt, EOFError):
            break

        cmd = entrada.strip().lower()

        if cmd in {"sair", "quit", "exit"}:
            break
        if not cmd:
            continue

        if timer and cmd == "t":
            console.print(f"[dim]{timer.status_line()}[/dim]\n")
            continue

        if timer and cmd == "p":
            paused = timer.toggle()
            console.print(f"[dim]{'⏸ Timer pausado.' if paused else '▶ Timer retomado.'}[/dim]\n")
            continue

        with console.status(f"[dim]{nome} está pensando...[/dim]"):
            reply = agent.respond(entrada)

        console.print()
        console.print(Panel(reply, title=f"[bold yellow]{nome}[/bold yellow]", border_style="yellow"))
        console.print()

        if tts:
            try:
                with console.status(f"[dim]{nome} está falando...[/dim]"):
                    tts.speak(reply)
            except Exception as exc:
                console.print(f"[dim red]TTS falhou: {exc}[/dim red]")

    if agent.history:
        path = save_session(ficha.id, agent.history)
        console.print(f"[dim]Sessão salva em: {path}[/dim]")
        _offer_supervision(ficha, agent.history)


def _offer_supervision(ficha, history: list[dict[str, str]]) -> None:
    console.print()
    if not Confirm.ask("[bold]Deseja supervisão desta sessão?[/bold]", default=True):
        return

    approach_keys = list(APPROACHES.keys())
    console.print("\n[bold]Abordagens disponíveis:[/bold]")
    for i, key in enumerate(approach_keys, 1):
        console.print(f"  [cyan]{i}.[/cyan] {key}")

    raw = Prompt.ask("\nEscolha (número ou nome)", default="1")
    try:
        approach = approach_keys[int(raw) - 1]
    except (ValueError, IndexError):
        approach = raw if raw in APPROACHES else approach_keys[0]

    console.print(f"\n[bold cyan]Supervisão — {approach}[/bold cyan]\n")
    supervisor = SupervisorAgent()
    with console.status("[dim]Analisando sessão...[/dim]"):
        feedback = supervisor.supervise(ficha, history, approach)
    console.print(Markdown(feedback))
    console.print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulador Clínico")
    parser.add_argument("ficha", nargs="?", default="fichas/validated/maria_01.yaml")
    parser.add_argument("--voice", action="store_true", help="Ativa TTS via Minimax")
    parser.add_argument("--timer", type=int, default=0, metavar="MIN", help="Duração da sessão em minutos (0 = sem limite)")
    args = parser.parse_args()
    run_session(args.ficha, voice=args.voice, timer_minutes=args.timer)


if __name__ == "__main__":
    main()
