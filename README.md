---
title: Clinical Simulator
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Simulador Clínico

Simulador de pacientes para treino clínico de estudantes de psicologia. Agentes de IA encenam pacientes com diferentes quadros, permitindo praticar entrevista, formulação de caso e condução de intervenções antes de atendimentos reais. Um agente supervisor devolve feedback estruturado após cada sessão.

## Status

🚧 Em desenvolvimento — Fase 0 (setup).

## Motivação

Estudantes de psicologia têm oportunidades limitadas de praticar habilidades clínicas antes de atender pacientes reais. Role-play com colegas é útil mas tem limites: os colegas cansam, os casos tendem a ser simplificados, e é difícil simular resistências, transferências ou riscos de forma consistente.

Este projeto usa LLMs para gerar pacientes simulados com comportamento clinicamente plausível: defesas ativas, resistências, ambivalência, respostas que variam conforme a condução do terapeuta. O objetivo não é substituir supervisão humana, mas oferecer um ambiente de treino complementar, seguro e disponível.

## Arquitetura

Quatro componentes:

1. **Ficha do paciente** — YAML com quadro clínico, dinâmica, defesas e como responder a diferentes condutas
2. **Agente-paciente** — LLM que recebe a ficha como system prompt e conduz a sessão no papel
3. **Agente-supervisor** — LLM que analisa a transcrição pós-sessão e devolve feedback estruturado
4. **Interface + persistência** — chat (terminal ou web) e armazenamento das sessões

## Roadmap

- **Fase 0** — Setup do projeto
- **Fase 1** — MVP: chat de terminal com uma ficha, transcrição salva em JSON
- **Fase 2** — Agente supervisor com rubrica estruturada
- **Fase 3** — Múltiplas fichas + interface web
- **Fase 4** — Avaliação: medir evolução de habilidades clínicas com rubrica validada
- **Fase 5** — Voz, multi-usuário, gerador de fichas assistido por IA

## Princípios

- **A ficha é o contrato**: o formato YAML é estável; o código deriva dele
- **Curadoria humana**: fichas geradas por IA só entram no sistema após revisão
- **Modular desde o início**: trocar modelo ou interface sem refazer o resto
- **Ética em primeiro lugar**: simulação explícita, não substitui terapia real nem supervisão

## Considerações éticas

Este simulador **não é** e **não deve ser usado como** terapia para o próprio usuário. Casos que envolvam risco simulado (ideação suicida, autolesão) devem ser discutidos com supervisor humano qualificado. Se o projeto for usado em pesquisa envolvendo estudantes, precisa passar por comitê de ética.

## Referência do schema de ficha

Ver `fichas/validated/maria_01.yaml` — é a ficha de referência e define a estrutura canônica.

## Tecnologia

Python 3.11+. Modelo LLM e interface a definir (ver `CLAUDE.md` para decisões pendentes).

## Licença

A definir.
