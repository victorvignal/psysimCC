"""Dimensões de rubrica clínica por abordagem, com âncoras comportamentais por score."""

from typing import TypedDict


class Anchor(TypedDict):
    nome: str
    anchors: dict[int, str]  # score 1-5 -> descrição comportamental


RUBRICA_POR_ABORDAGEM: dict[str, list[Anchor]] = {
    "TCC": [
        {
            "nome": "Identificação de pensamentos automáticos",
            "anchors": {
                1: "Não tentou identificar pensamentos automáticos",
                2: "Mencionou pensamentos mas não os explorou",
                3: "Identificou alguns PAs com suporte do paciente",
                4: "Eliciou PAs específicos usando questionamento socrático",
                5: "Sistematicamente mapeou PAs com evidências e crenças centrais",
            },
        },
        {
            "nome": "Questionamento socrático",
            "anchors": {
                1: "Usou afirmações ou conselhos diretos em vez de perguntas",
                2: "Fez perguntas fechadas sem exploração guiada",
                3: "Usou algumas perguntas abertas de forma socrática básica",
                4: "Conduziu questionamento socrático para examinar evidências",
                5: "Usou diálogo socrático consistentemente para reestruturação cognitiva",
            },
        },
        {
            "nome": "Psicoeducação",
            "anchors": {
                1: "Não ofereceu nenhuma psicoeducação",
                2: "Psicoeducação genérica desconectada do caso",
                3: "Ofereceu psicoeducação básica ligada à queixa",
                4: "Psicoeducação clara, personalizada e bem integrada à sessão",
                5: "Psicoeducação precisa, oportunamente inserida, verificada com o paciente",
            },
        },
        {
            "nome": "Ativação comportamental",
            "anchors": {
                1: "Não abordou comportamento ou evitação",
                2: "Mencionou comportamento sem exploração ou planejamento",
                3: "Identificou padrões de evitação e discutiu alternativas básicas",
                4: "Explorou comportamento e esboçou ativação concreta",
                5: "Planejou ativação comportamental específica, graduada e colaborativa",
            },
        },
        {
            "nome": "Estruturação da sessão",
            "anchors": {
                1: "Sessão sem estrutura, objetivos ou agenda",
                2: "Esboço de agenda mas sem manutenção do foco",
                3: "Manteve alguma estrutura com desvios moderados",
                4: "Sessão bem estruturada com agenda e revisão ao final",
                5: "Estrutura TCC completa: agenda, revisão de tarefa, foco, tarefa, feedback",
            },
        },
    ],
    "Psicodinâmica": [
        {
            "nome": "Aliança terapêutica",
            "anchors": {
                1: "Postura distante ou crítica que comprometeu a aliança",
                2: "Aliança frágil, terapeuta pouco responsivo afetivamente",
                3: "Aliança básica estabelecida, empatia presente mas discreta",
                4: "Aliança sólida, terapeuta atento e responsivo emocionalmente",
                5: "Aliança profunda, reparação ativa de momentos de ruptura",
            },
        },
        {
            "nome": "Exploração histórica",
            "anchors": {
                1: "Não explorou história pessoal nem vínculos passados",
                2: "História mencionada de passagem sem aprofundamento",
                3: "Conectou queixa atual a alguns elementos históricos",
                4: "Explorou padrões históricos com ligações ao presente",
                5: "Articulou linha histórica coerente com impacto relacional claro",
            },
        },
        {
            "nome": "Interpretação e insights",
            "anchors": {
                1: "Não fez interpretações; ficou apenas no relato manifesto",
                2: "Interpretações prematuras ou sem base na transcrição",
                3: "Uma interpretação tentativa, bem fundamentada e oportuna",
                4: "Duas ou mais interpretações precisas com boa recepção do paciente",
                5: "Interpretações aprofundadas em camadas, gerou insight real",
            },
        },
        {
            "nome": "Trabalho com resistência",
            "anchors": {
                1: "Ignorou ou reforçou resistências",
                2: "Notou resistência mas não trabalhou com ela",
                3: "Nomeou resistência com alguma exploração",
                4: "Explorou resistência sem pressionar, mantendo aliança",
                5: "Trabalhou resistência habilmente, revelando função defensiva",
            },
        },
        {
            "nome": "Uso da transferência",
            "anchors": {
                1: "Não reconheceu dinâmicas transferenciais",
                2: "Dinâmica transferencial ignorada ou malmanejada",
                3: "Reconheceu transferência sem intervir diretamente",
                4: "Explorou dinâmica transferencial de forma contenida",
                5: "Usou transferência como material clínico central com precisão",
            },
        },
    ],
    "Humanista": [
        {
            "nome": "Empatia e presença",
            "anchors": {
                1: "Postura distante, respostas mecânicas ou avaliativas",
                2: "Empatia superficial ou inconsistente",
                3: "Presença empática básica, reflexos simples",
                4: "Empatia profunda, sintonizada ao mundo do paciente",
                5: "Presença plena, co-participação no mundo experiencial do paciente",
            },
        },
        {
            "nome": "Aceitação incondicional",
            "anchors": {
                1: "Julgamentos explícitos ou implícitos ao paciente",
                2: "Aceitação condicional ou seletiva perceptível",
                3: "Aceitação presente mas não comunicada com clareza",
                4: "Aceitação genuína comunicada verbal e não-verbalmente",
                5: "Aceitação incondicional clara e coerente ao longo de toda a sessão",
            },
        },
        {
            "nome": "Congruência e autenticidade",
            "anchors": {
                1: "Postura artificial, contradições entre fala e atitude",
                2: "Momentos de incongruência perceptíveis",
                3: "Razoavelmente autêntico com pequenas incongruências",
                4: "Congruente e genuíno na maior parte da sessão",
                5: "Total congruência, usou autorrevelação de forma terapêutica",
            },
        },
        {
            "nome": "Reflexo de sentimentos",
            "anchors": {
                1: "Não refletiu sentimentos, ficou nos fatos",
                2: "Reflexos imprecisos ou superficiais",
                3: "Alguns reflexos adequados de sentimentos explícitos",
                4: "Reflexos precisos de sentimentos explícitos e implícitos",
                5: "Reflexos profundos, capturou nuances emocionais e validou",
            },
        },
        {
            "nome": "Escuta ativa",
            "anchors": {
                1: "Interrompeu, desviou tópicos ou sobrepôs agenda própria",
                2: "Escuta passiva, respostas pouco ligadas ao que foi dito",
                3: "Escuta ativa básica, paráfrases simples",
                4: "Escuta ativa consistente com parafraseamento e sumarização",
                5: "Escuta profunda e responsiva, capturou implícitos e silêncios",
            },
        },
    ],
    "ACT": [
        {
            "nome": "Desfusão cognitiva",
            "anchors": {
                1: "Não trabalhou a relação do paciente com pensamentos",
                2: "Mencionou pensamentos sem promover distanciamento",
                3: "Uma tentativa básica de desfusão (nomeou o pensamento)",
                4: "Usou metáfora ou exercício de desfusão com clareza",
                5: "Paciente experienciou pensamento como evento mental (desfusão efetiva)",
            },
        },
        {
            "nome": "Aceitação e mindfulness",
            "anchors": {
                1: "Incentivou controle ou supressão de experiências internas",
                2: "Aceitação mencionada sem prática ou aprofundamento",
                3: "Convidou o paciente a observar experiências sem julgamento",
                4: "Promoveu aceitação ativa com exercício ou metáfora",
                5: "Trabalhou aceitação de forma experiencial, presente e consistente",
            },
        },
        {
            "nome": "Exploração de valores",
            "anchors": {
                1: "Não tocou em valores ou direções de vida",
                2: "Valores mencionados de forma superficial e genérica",
                3: "Explorou um valor com algum vínculo à queixa",
                4: "Clarificou valores importantes ligados ao sofrimento atual",
                5: "Mapeou valores centrais e os conectou a ações concretas",
            },
        },
        {
            "nome": "Ação comprometida",
            "anchors": {
                1: "Nenhuma orientação para ação baseada em valores",
                2: "Ação sugerida mas desconectada de valores",
                3: "Esboçou uma ação pequena ligada a um valor",
                4: "Definiu ações concretas alinhadas a valores clarificados",
                5: "Ações específicas, graduadas e comprometidas com valores do paciente",
            },
        },
        {
            "nome": "Flexibilidade psicológica",
            "anchors": {
                1: "Reforçou rigidez ou evitação experiencial",
                2: "Abordou evitação mas sem promover alternativa",
                3: "Promoveu alguma abertura a experiências difíceis",
                4: "Trabalhou hexaflex de forma integrada em momentos da sessão",
                5: "Sessão orientada consistentemente para flexibilidade psicológica",
            },
        },
    ],
    "Sistêmica": [
        {
            "nome": "Mapeamento de relações",
            "anchors": {
                1: "Não explorou contexto relacional ou familiar",
                2: "Mencionou relações sem mapeá-las",
                3: "Esboçou padrões relacionais básicos",
                4: "Mapeou relações com clareza, incluindo ciclos e papéis",
                5: "Construiu mapa relacional rico com padrões e recursos identificados",
            },
        },
        {
            "nome": "Pensamento circular",
            "anchors": {
                1: "Pensamento linear sobre causas e culpas",
                2: "Alguma circularidade mas ainda predominantemente causal",
                3: "Usou perguntas circulares básicas",
                4: "Explorou circularidade com consistência, conectou padrões",
                5: "Pensamento sistêmico claro: padrões, feedbacks e recursividade",
            },
        },
        {
            "nome": "Neutralidade sistêmica",
            "anchors": {
                1: "Tomou partido ou validou versão de um membro da família",
                2: "Neutralidade comprometida em momentos da sessão",
                3: "Manteve neutralidade básica sem explorar múltiplas perspectivas",
                4: "Neutralidade ativa, convidou múltiplos pontos de vista",
                5: "Curiosidade sistêmica genuína, neutralidade mantida consistentemente",
            },
        },
        {
            "nome": "Metáforas e recursos",
            "anchors": {
                1: "Nenhuma metáfora ou recurso do sistema utilizado",
                2: "Metáfora introduzida mas não desenvolvida",
                3: "Usou metáfora ou recurso do paciente de forma básica",
                4: "Explorou metáforas e recursos do sistema com eficácia",
                5: "Metáforas sistêmicas centrais, ampliou recursos do sistema habilmente",
            },
        },
        {
            "nome": "Tarefas sistêmicas",
            "anchors": {
                1: "Nenhuma tarefa ou diretiva prescrita",
                2: "Tarefa genérica sem ligação ao sistema",
                3: "Tarefa simples, coerente com o padrão identificado",
                4: "Tarefa sistêmica específica, colaborativa e com fundamento claro",
                5: "Tarefa criativa, paradoxal ou ritual alinhada ao sistema e objetivos",
            },
        },
    ],
    "Integrativa": [
        {
            "nome": "Flexibilidade técnica",
            "anchors": {
                1: "Aplicou técnicas de uma só abordagem rigidamente",
                2: "Tentou integrar mas de forma incoerente ou mecânica",
                3: "Transitou entre técnicas de forma básica",
                4: "Integrou técnicas de forma fluida e contextualizada",
                5: "Integração sofisticada, técnicas escolhidas conforme necessidade do momento",
            },
        },
        {
            "nome": "Formulação integrativa",
            "anchors": {
                1: "Nenhuma formulação; respondeu reativamente",
                2: "Formulação fragmentada, sem coerência entre lentes",
                3: "Formulação básica usando elementos de mais de uma abordagem",
                4: "Formulação integrativa clara ligando diferentes perspectivas",
                5: "Formulação rica e coerente, articulou múltiplas lentes elegantemente",
            },
        },
        {
            "nome": "Uso de múltiplas lentes",
            "anchors": {
                1: "Apenas uma perspectiva teórica utilizada",
                2: "Duas perspectivas justapostas mas não integradas",
                3: "Usou múltiplas lentes de forma básica e compatível",
                4: "Integrou perspectivas de forma complementar e oportuna",
                5: "Múltiplas lentes usadas fluidamente, enriquecendo a compreensão do caso",
            },
        },
        {
            "nome": "Coerência interna",
            "anchors": {
                1: "Intervenções contraditórias entre si",
                2: "Algumas incoerências entre objetivos e intervenções",
                3: "Coerência razoável com pequenos desvios",
                4: "Intervenções coerentes com a formulação e objetivo da sessão",
                5: "Coerência total: cada intervenção serve a um propósito integrado claro",
            },
        },
        {
            "nome": "Adaptação ao paciente",
            "anchors": {
                1: "Abordagem padronizada ignorando características do paciente",
                2: "Alguma adaptação mas predominantemente técnica-centrada",
                3: "Ajustes básicos ao estilo e necessidade do paciente",
                4: "Adaptação clara ao paciente, técnicas ajustadas ao caso",
                5: "Altamente personalizado, abordagem moldada pelo paciente em tempo real",
            },
        },
    ],
}


def get_dimensoes(approach: str) -> list[Anchor]:
    """Retorna dimensões da abordagem, com fallback para TCC."""
    return RUBRICA_POR_ABORDAGEM.get(approach, RUBRICA_POR_ABORDAGEM["TCC"])


def get_nomes(approach: str) -> list[str]:
    return [d["nome"] for d in get_dimensoes(approach)]


def get_anchor_text(approach: str, nome: str, score: int) -> str:
    for d in get_dimensoes(approach):
        if d["nome"] == nome:
            return d["anchors"].get(score, "")
    return ""
