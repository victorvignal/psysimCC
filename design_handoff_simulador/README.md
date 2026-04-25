# Handoff: psysim — Interface Web

## Overview

Wireframes lo-fi para o simulador clínico de treino de estudantes de psicologia.
O sistema tem três telas principais: seleção de paciente, sessão de chat com o agente-paciente, e tela de supervisão/feedback.

## Sobre os arquivos

Os arquivos `.html` neste pacote são **referências de design em HTML** — wireframes mostrando estrutura, fluxo e comportamento pretendido. **Não são código de produção para copiar diretamente.**

A tarefa é **recriar esses designs no ambiente já existente do projeto** (`psysim` — Python + Chainlit), aplicando os padrões e componentes do Chainlit onde possível, e estendendo com CSS/JS customizado onde necessário. Se a interface for migrada para outro framework (ex: React + FastAPI), usar o wireframe como guia fiel de layout e funcionalidade.

## Fidelidade

**Low-fidelity (lofi) — wireframes estruturais.**
Mostram layout, hierarquia de informação e fluxo. Não têm cores finais, tipografia definitiva nem espaçamentos exatos. O desenvolvedor deve usar as fichas como guia de estrutura e aplicar o design system final sobre elas.

---

## Telas / Views

### Tela 1 — Seleção de Paciente

**Propósito:** estudante escolhe qual ficha/paciente quer atender antes de iniciar uma sessão.

Três variações propostas — escolher uma ou combinar elementos:

#### 1A · Cards de pacientes
- **Layout:** navbar fixa (40px) + área principal com grid de cards (3 colunas, 228px × 160px cada) + seção "Sessões recentes" abaixo
- **Card de paciente:** cabeçalho colorido por nível, avatar circular, badge de dificuldade (iniciante / intermediário / avançado), nome + idade, diagnóstico resumido, botão de ação
- **Estado bloqueado:** card com opacidade 0.5 e botão "🔒 bloqueado" — desbloqueia por progressão de nível
- **Sessões recentes:** lista de sessões anteriores com link para retomar ou ver feedback

#### 1B · Lista densa + preview lateral
- **Layout:** painel esquerdo fixo (300px) com lista de fichas + painel direito com preview da ficha selecionada
- **Lista:** linha por paciente com avatar, nome, badge de nível e diagnóstico resumido; item selecionado tem borda esquerda colorida
- **Preview:** exibe queixa principal, sintomas ativos, defesas típicas e nível de dificuldade da ficha YAML
- **Ações:** "Iniciar nova sessão" e "Continuar sessão #N" no rodapé do preview

#### 1C · Dashboard acadêmico ⭐ (recomendada para turma)
- **Layout:** sidebar vertical estreita (56px) com ícones de navegação + área principal
- **Stats row:** 4 métricas em destaque (sessões totais, horas de prática, feedbacks recebidos, pacientes atendidos)
- **Lista de pacientes:** linhas com borda esquerda colorida por nível, ações inline
- **Painel de progresso:** barras por competência (Acolhimento, Formulação, Manejo de resistência, Técnica) baseadas nas sessões supervisionadas

---

### Tela 2 — Sessão (chat com o agente-paciente)

**Propósito:** estudante conversa com o agente-paciente em tempo real; supervisor IA pode dar feedback durante a sessão.

#### 2A · Chat + painel de abas
- **Layout:** topbar (44px) + strip do supervisor (32px) + área de chat (esquerda, ~580px) + painel lateral com abas (direita, ~300px)
- **Strip do supervisor:** faixa verde no topo com a nota mais recente do supervisor IA
- **Painel lateral — abas:** Ficha | Notas | Supervisor
  - Ficha: queixa, sintomas, defesas, alertas (ex: "não pressionar sobre pai")
  - Notas: textarea livre para o estudante anotar durante a sessão
  - Supervisor: histórico de notas em tempo real
- **Input:** textarea + botão "enviar"; suporte a áudio (edge-tts já implementado)
- **Bubbles:** paciente (fundo creme, borda esquerda arredondada), terapeuta (fundo azul-claro, borda direita arredondada)

#### 2B · 3 colunas fixas ⭐ (recomendada para desktop)
- **Layout:** topbar + 3 colunas separadas por divisórias verticais
  - **Col 1 (~260px):** ficha clínica completa sempre visível (queixa, sintomas, defesas, alertas)
  - **Col 2 (~460px):** chat com o paciente
  - **Col 3 (~280px):** supervisor em tempo real + notas pessoais + seleção de abordagem (TCC / Psicodinâmica / Humanista)
- **Supervisor col 3:** cards coloridos por tipo (✓ verde, ⚠ amarelo, 💡 azul) com nota e timestamp

#### 2C · Chat wide + painéis overlay
- **Layout:** topbar com botões "📋 ficha" e "🎓 supervisor" que abrem painéis como overlay/drawer
- **Chat:** ocupa quase toda a largura; notas do supervisor aparecem **inline**, como uma bubble verde logo após a fala do paciente relevante
- **Input:** barra fixa no rodapé, largura total menos margens

---

### Tela 3 — Supervisão e Feedback

**Propósito:** revisão estruturada da sessão encerrada (ou em tempo real via drawer).

#### 3A · Transcrição anotada + rubrica
- **Layout:** painel esquerdo (~520px) com transcrição + painel direito (~340px) com rubrica
- **Transcrição:** cada turn tem label (MARIA / VOCÊ), texto da fala, e quando há avaliação: badge inline verde (✓) ou amarelo (⚠) com nota curta
- **Rubrica:** 4 dimensões com escala visual de 5 pontos (quadradinhos preenchidos) + observação textual

#### 3B · Drawer lateral em tempo real ⭐ (recomendada)
- **Layout:** sessão de chat ao fundo (com scrim semitransparente) + drawer lateral direito (480px) que desliza durante a sessão
- **Drawer:** cabeçalho com título + seleção de abordagem; cards de feedback em tempo real (✓ / ⚠ / 💡) com botões de reação do estudante ("👍 útil", "🤔 discordo", "🚩 ignorar")
- **Fechar drawer:** retorna para o chat sem perder estado

#### 3C · Relatório acadêmico completo
- **Layout:** header com metadados da sessão + 3 colunas
  - **Col 1:** rubrica MITI adaptada (6 dimensões, escala 1–5)
  - **Col 2:** análise narrativa (o que funcionou / a desenvolver / sugestões para próxima sessão)
  - **Col 3:** gráfico de barras de evolução histórica por dimensão (sparkline por sessão) + CTA para nova sessão
- **Exportar PDF:** botão no topbar

---

## Fluxo de navegação

```
Seleção de paciente
    └─→ Sessão (chat)
            ├─→ [botão "supervisão"] → Drawer supervisor (Tela 3B, em tempo real)
            └─→ [encerrar sessão] → Relatório de supervisão (Tela 3A ou 3C)
                                          └─→ Seleção de paciente (nova sessão)
```

---

## Comportamentos e Interações

- **Supervisor em tempo real:** chamado ao digitar "supervisão" (comportamento atual no `app.py`) OU de forma assíncrona a cada N turnos. O wireframe 2B/2C mostra feedback contínuo — avaliar se isso é viável com o modelo atual ou se fica pós-sessão.
- **Seleção de abordagem (TCC / Psicodinâmica / Humanista):** feita antes ou durante a sessão; muda o prompt do `SupervisorAgent`.
- **Notas pessoais:** salvas localmente por sessão (associar ao `session_id`).
- **Reações ao feedback:** botões "útil / discordo / ignorar" — dado valioso para avaliar qualidade do supervisor; salvar no banco junto com a supervisão.
- **Cards bloqueados:** lógica de desbloqueio por nível de dificuldade — definir critério (ex: N sessões de nível anterior com score mínimo).

---

## Componentes-chave a implementar

| Componente | Descrição |
|---|---|
| `PatientCard` | Card de seleção de paciente com nível e estado de bloqueio |
| `SessionHeader` | Topbar com nome do paciente, contador de tempo, botões de ação |
| `ChatBubble` | Bubble de mensagem (variantes: paciente, terapeuta, supervisor) |
| `FichaPanel` | Painel lateral com dados clínicos da ficha YAML |
| `SupervisorNote` | Card de nota do supervisor (✓ / ⚠ / 💡) com reações |
| `RubricaView` | Escala visual de 5 pontos por dimensão |
| `ProgressChart` | Sparkline de evolução histórica por competência |

---

## Estado necessário

```
session: {
  id, ficha_id, started_at, duration,
  history: [{role, content, timestamp}],
  notes: string,            // notas pessoais do estudante
  approach: 'TCC' | 'Psicodinâmica' | 'Humanista',
  supervisor_notes: [{timestamp, type, content, reaction}]
}

student: {
  name, turma,
  sessions: session[],
  progress: { [dimensao]: number[] }  // por sessão
}
```

---

## Tokens de design (sugeridos — a refinar)

| Token | Valor sugerido |
|---|---|
| Cor de fundo | `#f5f0e8` (creme) |
| Superfície | `#fafaf7` |
| Texto principal | `#1a1a1a` |
| Verde (iniciante / positivo) | `#4a7a4a` / `#d4e8d4` |
| Azul (neutro / informação) | `#4a5a7a` / `#d4dce8` |
| Amarelo (atenção) | `#8a6a2a` / `#f0e0c0` |
| Vermelho (avançado / erro) | `#7a2a2a` / `#f0d4d4` |
| Fonte título | Caveat (handwritten) — só nos wireframes; usar fonte do design system final |
| Fonte mono | Space Mono — para labels, timestamps, metadados |

---

## Arquivos neste pacote

| Arquivo | Descrição |
|---|---|
| `Wireframes Simulador Clínico.html` | Todos os 9 wireframes em canvas navegável (pan/zoom) |
| `design-canvas.jsx` | Componente de canvas usado pelo HTML acima |
| `README.md` | Este documento |

---

## Referência do codebase atual

O projeto já tem:
- `src/app.py` — Chainlit app com seleção de perfil via `@cl.set_chat_profiles`, loop de mensagens, chamada ao supervisor
- `src/patient_agent.py` — streaming de resposta do agente-paciente
- `src/supervisor_agent.py` — análise pós-sessão com seleção de abordagem
- `src/database.py` — persistência de sessões e supervisões
- `fichas/validated/maria_01.yaml` — schema canônico da ficha

A interface web atual é **Chainlit**. Os wireframes assumem uma interface mais customizada — avaliar se vale estender o tema Chainlit ou migrar para React + backend FastAPI/WebSocket.
