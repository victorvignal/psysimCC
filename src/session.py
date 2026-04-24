import argparse
import json
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from src.ficha_loader import load_ficha
from src.patient_agent import PatientAgent

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


def run_session(ficha_path: str) -> None:
    ficha = load_ficha(ficha_path)
    agent = PatientAgent(ficha)
    nome = ficha.apresentacao.nome_ficticio

    console.print(Panel(
        f"[bold]Paciente:[/bold] {nome}  |  [bold]Nível:[/bold] {ficha.nivel_dificuldade}\n"
        "[dim]Digite 'sair' para encerrar a sessão[/dim]",
        title="[bold cyan]Simulador Clínico[/bold cyan]",
        border_style="cyan",
    ))
    console.print()

    while True:
        try:
            entrada = Prompt.ask("[bold green]Terapeuta[/bold green]")
        except (KeyboardInterrupt, EOFError):
            break

        if entrada.strip().lower() in {"sair", "quit", "exit"}:
            break
        if not entrada.strip():
            continue

        with console.status(f"[dim]{nome} está pensando...[/dim]"):
            reply = agent.respond(entrada)

        console.print()
        console.print(Panel(reply, title=f"[bold yellow]{nome}[/bold yellow]", border_style="yellow"))
        console.print()

    if agent.history:
        path = save_session(ficha.id, agent.history)
        console.print(f"[dim]Sessão salva em: {path}[/dim]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulador Clínico")
    parser.add_argument("ficha", nargs="?", default="fichas/validated/maria_01.yaml")
    args = parser.parse_args()
    run_session(args.ficha)


if __name__ == "__main__":
    main()
