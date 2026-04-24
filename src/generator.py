import os
import re
import sys
import argparse
from datetime import date
from pathlib import Path

import yaml
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from src.ficha_loader import Ficha

load_dotenv()

console = Console()

_PROJECT_ROOT = Path(__file__).parent.parent
_VALIDATED_DIR = _PROJECT_ROOT / "fichas" / "validated"
_DRAFT_DIR = _PROJECT_ROOT / "fichas" / "draft"
_REFERENCE_FICHA = _VALIDATED_DIR / "maria_01.yaml"


def _build_system_prompt() -> str:
    reference = _REFERENCE_FICHA.read_text(encoding="utf-8")
    return f"""You are a clinical case writer for a psychology training simulator used by Brazilian psychology students.

Your job: receive a free-text description of a patient and output a complete, fictional, clinically plausible patient case in YAML format.

## Schema — follow this exactly (this is a real example from the system)

{reference}

## Output rules
- Output ONLY valid YAML. No markdown fences, no explanation, no commentary.
- Every field present in the example is required unless it has `| None` in the schema.
- `_uso_interno` must always be complete: diagnosis, both formulations (psicodinamica + tcc), and temas_evitados.
- `metadata.origem` → `gerado_por_ia`
- `metadata.criada_em` → `{date.today().isoformat()}`
- `metadata.revisada_por` → `[pendente]`
- `metadata.versao_schema` → `0.1`
- `id` → follow the pattern `firstname_01` in lowercase, no accents (e.g. `joao_01`, `ana_02`)
- Do NOT copy Maria's case. Create a genuinely different patient, different quadro, different history.
- All narrative fields in Brazilian Portuguese.
- `nivel_dificuldade` → iniciante | intermediario | avancado
- Fields marked "USO INTERNO" go only in `_uso_interno`, never in the patient-facing sections.
"""


def _strip_fences(raw: str) -> str:
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.MULTILINE)
    return re.sub(r"\n?```$", "", raw.strip(), flags=re.MULTILINE).strip()


def _unique_id(proposed: str) -> str:
    """Return proposed ID, auto-incrementing suffix if it already exists."""
    base = re.sub(r"_\d+$", "", proposed)
    existing = {p.stem for d in [_VALIDATED_DIR, _DRAFT_DIR] if d.exists() for p in d.glob("*.yaml")}
    n = 1
    candidate = f"{base}_{n:02d}"
    while candidate in existing:
        n += 1
        candidate = f"{base}_{n:02d}"
    return candidate


def _parse_and_validate(raw: str) -> tuple[Ficha, str]:
    yaml_text = _strip_fences(raw)
    data = yaml.safe_load(yaml_text)
    uso_interno = data.pop("_uso_interno", None)
    if uso_interno:
        data["uso_interno"] = uso_interno
    ficha = Ficha.model_validate(data)
    return ficha, yaml_text


def generate(description: str) -> tuple[Ficha, str]:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    model = os.getenv("GENERATOR_MODEL_ID") or os.getenv("MODEL_ID", "deepseek/deepseek-chat")

    messages: list[dict[str, str]] = [
        {"role": "system", "content": _build_system_prompt()},
        {"role": "user", "content": f"Generate a patient case:\n\n{description}"},
    ]

    for attempt in range(3):
        resp = client.chat.completions.create(model=model, messages=messages)
        raw = resp.choices[0].message.content or ""

        try:
            return _parse_and_validate(raw)
        except Exception as exc:
            if attempt < 2:
                messages += [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": f"YAML validation failed: {exc}\n\nOutput only the corrected YAML."},
                ]
            else:
                raise ValueError(f"Failed after 3 attempts. Last error: {exc}") from exc

    raise RuntimeError("unreachable")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerador de fichas de pacientes")
    parser.add_argument("descricao", help="Descrição livre do paciente a gerar")
    args = parser.parse_args()

    console.print()
    console.print(Panel(
        f"[dim]{args.descricao}[/dim]",
        title="[bold cyan]Gerando ficha[/bold cyan]",
        border_style="cyan",
    ))

    with console.status("[dim]Gerando paciente...[/dim]"):
        try:
            ficha, yaml_text = generate(args.descricao)
        except Exception as exc:
            console.print(f"[bold red]Erro:[/bold red] {exc}")
            sys.exit(1)

    # Ensure unique ID before saving
    ficha_id = _unique_id(ficha.id)
    if ficha_id != ficha.id:
        yaml_text = re.sub(r"^id:.*$", f"id: {ficha_id}", yaml_text, flags=re.MULTILINE)

    out_path = _DRAFT_DIR / f"{ficha_id}.yaml"
    _DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml_text, encoding="utf-8")

    console.print()
    console.print(Syntax(yaml_text, "yaml", theme="monokai", line_numbers=False))
    console.print()
    console.print(f"[bold green]Salvo em:[/bold green] {out_path}")
    console.print("[dim]Revise o arquivo antes de mover para fichas/validated/[/dim]")
    console.print()
