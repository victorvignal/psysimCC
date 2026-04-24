# Simulador Clínico — Contexto do Projeto

## Objetivo

Construir um simulador de pacientes para treino clínico de estudantes de psicologia. Agentes de IA encenam pacientes com diferentes quadros, permitindo praticar entrevista, formulação de caso e condução de intervenções antes de atendimentos reais. Um segundo agente atua como supervisor, lendo a transcrição da sessão e devolvendo feedback estruturado.

Projeto iniciado em conversa com Claude (web). Este arquivo consolida o contexto para continuar o desenvolvimento no Claude Code.

## Arquitetura (4 componentes)

1. **Ficha do paciente** — YAML estruturado em `fichas/validated/`, serve como contrato do sistema
2. **Agente-paciente** — LLM com system prompt gerado a partir da ficha
3. **Agente-supervisor** — segundo LLM que analisa transcrição e devolve feedback estruturado
4. **Interface + persistência** — onde o usuário conversa; sessões salvas em `sessions/`

## Stack

- **Linguagem**: Python 3.11+
- **Modelo LLM**: [DECIDIR — opções avaliadas: Claude Sonnet 4.6 (recomendação inicial), GPT-4o, Llama 3.3 70B via Ollama]
- **Interface**: [DECIDIR — opções: terminal (rich), Chainlit, Streamlit]
- **Persistência**: JSON em disco pro MVP; SQLite + SQLAlchemy se escalar
- **Gerenciador de pacotes**: [DECIDIR — uv recomendado, alternativas: poetry, pip]
- **Formato de ficha**: YAML

## Fases de desenvolvimento

- [ ] **Fase 0** — Setup: estrutura de pastas, pyproject.toml, .env, .gitignore
- [ ] **Fase 1** — MVP terminal: loop de chat com uma ficha, transcrição em JSON
- [ ] **Fase 2** — Agente supervisor: análise estruturada da transcrição pós-sessão
- [ ] **Fase 3** — Múltiplas fichas + interface web (Chainlit)
- [ ] **Fase 4** — Avaliação: rubrica de habilidades clínicas (baseada em MITI ou Helpful Responses)
- [ ] **Fase 5** (opcional) — Voz (Whisper + TTS), multi-usuário, deploy, gerador de fichas

## Estrutura de pastas alvo

```
simulador-clinico/
├── CLAUDE.md                 # este arquivo
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── fichas/
│   ├── validated/            # fichas revisadas, prontas pra usar
│   │   └── maria_01.yaml
│   └── draft/                # rascunhos em revisão
├── src/
│   ├── __init__.py
│   ├── ficha_loader.py       # carrega YAML e valida schema
│   ├── patient_agent.py      # gera system prompt + chama LLM
│   ├── supervisor_agent.py   # análise pós-sessão
│   └── session.py            # loop de conversa + persistência
├── prompts/
│   ├── patient_template.md   # template do system prompt do paciente
│   └── supervisor_template.md
└── sessions/                 # transcrições salvas (JSON)
```

## Convenções

- **Código**: type hints em tudo, docstrings curtas, formatação com `ruff`
- **Ficha YAML**: formato definido em `fichas/validated/maria_01.yaml` (referência canônica); mudanças de schema requerem atualização dessa ficha primeiro
- **Metadados obrigatórios** em toda ficha: `origem`, `criada_em`, `revisada_por`
- **Campos "uso interno"** (diagnóstico, formulação psicodinâmica) NÃO entram no system prompt do agente-paciente — só no do supervisor. Isso simula o paciente real, que não entrega o diagnóstico pronto.
- **Commits**: conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`)

## Princípios de design

- **Ficha como contrato**: o formato da ficha é o ponto mais importante do projeto; o código deriva dela. Evitar mudanças de schema depois que tiver várias fichas salvas.
- **Modular desde o dia 1**: trocar de modelo (Claude → GPT → local) ou de interface (terminal → web) não deve exigir refazer o resto.
- **Curadoria humana**: fichas geradas por IA passam por `draft/` e só migram pra `validated/` após revisão manual.
- **Separação de responsabilidades**: simulador (usar) e gerador de fichas (criar fichas novas) são ferramentas distintas que compartilham o formato YAML.

## Considerações éticas

- Deixar explícito na interface que o paciente é simulado, não real
- Não usar o simulador como terapia para o próprio usuário
- Para casos com risco simulado (ideação suicida, autolesão), prever supervisor humano na revisão
- Se um dia virar pesquisa com participantes reais (estudantes sendo avaliados), precisa passar por comitê de ética
- Não treinar/ajustar modelos com dados de pacientes reais sem consentimento e anonimização rigorosa

## Estado atual

**Fase 0, passo 1 concluído**: estrutura pensada, primeira ficha (`maria_01.yaml`) pronta. Próximo: criar `pyproject.toml`, `.gitignore`, `.env.example` e inicializar repositório git.

## Decisões pendentes (pedir ao usuário antes de implementar)

1. Modelo LLM pro MVP: Claude Sonnet 4.6 / GPT-4o / Ollama local / outro
2. Interface inicial: terminal puro (rich) / Chainlit / Streamlit
3. Gerenciador de pacotes: uv / poetry / pip+venv

## Histórico de decisões tomadas

- **2026-04-24**: formato da ficha definido como YAML (vs JSON) pela legibilidade ao escrever manualmente
- **2026-04-24**: separação entre `fichas/draft/` e `fichas/validated/` pra forçar curadoria
- **2026-04-24**: primeira ficha (`maria_01`) construída manualmente como referência canônica do schema

## Como trabalhar neste projeto

Quando o usuário pedir pra avançar:

1. Confirmar em qual fase estamos e o próximo passo concreto
2. Se houver decisão pendente relevante pra esse passo, perguntar antes de codar
3. Código pequeno e testável por vez; rodar antes de prosseguir
4. Atualizar a seção "Estado atual" deste CLAUDE.md ao concluir cada etapa
5. Commits frequentes com mensagens descritivas
