from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel


class Apresentacao(BaseModel):
    nome_ficticio: str
    idade: int
    genero: str
    ocupacao: str
    escolaridade: str
    contexto_social: str
    religiosidade: str | None = None


class Comportamento(BaseModel):
    estilo_comunicacao: str
    defesas_tipicas: list[str] = []
    resistencias: list[str] = []
    alianca_inicial: str
    red_flags: list[str] = []
    arco_possivel: str | None = None


class UsoInterno(BaseModel):
    diagnostico_hipotese: str
    formulacao_psicodinamica: str
    formulacao_tcc: str | None = None
    temas_evitados: list[str] = []


class Metadata(BaseModel):
    origem: str
    criada_em: date | str
    revisada_por: list[str] | str | None = None
    versao_schema: str | float


class Ficha(BaseModel):
    id: str
    nivel_dificuldade: str
    apresentacao: Apresentacao
    queixa_principal: str
    sintomas_ativos: list[str]
    historia_pregressa: str
    historia_familiar: str
    gatilho_atual: str
    comportamento: Comportamento
    metadata: Metadata
    uso_interno: UsoInterno | None = None  # stripped from patient prompt


def load_ficha(path: str | Path) -> Ficha:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    uso_interno = raw.pop("_uso_interno", None)
    if uso_interno:
        raw["uso_interno"] = uso_interno
    return Ficha.model_validate(raw)
