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
    estilo_comunicacao: str          # descrição livre do estilo
    estilo_sessao: str               # plain | upset | verbose | reserved | tangent | pleasing
    como_responde_abertas: str     # como responde a perguntas abertas
    como_responde_pressao: str     # como reage quando se sente pressionada
    reacao_silencio: str             # como reage a silêncio do terapeuta
    defesas_tipicas: list[str] = []
    resistencias: list[str] = []
    alianca_inicial: str
    red_flags: list[str] = []
    arco_possivel: str | None = None


class ConscienciaPaciente(BaseModel):
    tem_consciencia_de: list[str] = []    # o paciente sabe e pode falar
    nao_tem_consciencia_de: list[str] = []  # abaixo da superfície, emerge com vínculo
    nunca_revela_spontaneamente: list[str] = []  # só se perguntado com confiança estabelecida


class GatilhosSessao(BaseModel):
    intensificam: list[str] = []    # temas que elevam emoção visivelmente
    fecham: list[str] = []          # temas que fazem o paciente se fechar
    invasivos_inicio: list[str] = []  # perguntas que parecem invasivas cedo


class UsoInterno(BaseModel):
    diagnostico_hipotese: str
    formulacao_psicodinamica: str
    formulacao_tcc: str | None = None
    crencas_centrais: str | None = None   # crenças principais do paciente (TCC)
    padrao_relacional: str | None = None  # padrão relacional central (psicodinâmica)
    recursos_genuinos: list[str] = []     # forças reais do paciente
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
    motivo_declarado: str | None = None          # o que o paciente diz que o trouxe
    motivo_subjacente: str | None = None          # o que realmente está por trás (não revela)
    sintomas_ativos: list[str]
    historia_pregressa: str
    historia_familiar: str
    gatilho_atual: str
    comportamento: Comportamento
    consciencia: ConscienciaPaciente | None = None  # conhecimento do paciente sobre si
    gatilhos: GatilhosSessao | None = None          # gatilhos na sessão
    metadata: Metadata
    uso_interno: UsoInterno | None = None            # stripped from patient prompt


def load_ficha(path: str | Path) -> Ficha:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    # Handle _uso_interno (legacy underscore prefix)
    for key in ["_uso_interno", "consciencia", "gatilhos"]:
        val = raw.pop(f"_{key}" if key == "_uso_interno" else key, None)
        if val is not None:
            raw[key] = val
    return Ficha.model_validate(raw)
