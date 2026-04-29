# Ferzion Discovery

> Plataforma de discovery e briefing estratégico — o primeiro produto que o cliente experimenta da Ferzion.

A promessa-âncora: **transformar caos operacional em clareza.**

---

## Status do projeto

**Fase atual:** Backend — fundação completa. Iniciando camada de execução (sessões + API).

| Camada                                  | Status      | Detalhe                                                                |
| --------------------------------------- | ----------- | ---------------------------------------------------------------------- |
| **Backend — domínio metodologia**       | ✅ Completo | 10 entidades, append-only, snapshots imutáveis                         |
| **Backend — admin (CMS)**               | ✅ Completo | 7 admins customizados, bloqueio de versão imutável, ações de transição |
| **Backend — seed declarativo**          | 🟡 Parcial  | Loader idempotente + Ato 1 (6/~50 perguntas)                           |
| **Backend — domínio briefing**          | ✅ Completo | BriefingSessao, RespostaPergunta, SinalCapturado, EventoBriefing       |
| **Backend — API REST pública**          | 🔴 Pendente | DRF endpoints (iniciar/responder/concluir)                             |
| **Backend — engine de discovery**       | 🔴 Pendente | Fluxo + filtragem por perfil                                           |
| **Backend — engine de sinais**          | 🔴 Pendente | Extração resposta → sinal                                              |
| **Backend — engine de profiling (SCA)** | 🔴 Pendente | Score Composto de Aprofundamento                                       |
| **Backend — engine de síntese**         | 🔴 Pendente | Devolutiva determinística                                              |
| **Backend — auth (link mágico)**        | 🔴 Pendente | Identidade do respondente                                              |
| **Backend — notificações**              | 🔴 Pendente | Email + Celery                                                         |
| **Frontend — Next.js público**          | 🟡 Scaffold | Estrutura inicial, sem implementação                                   |
| **Frontend — painel cliente**           | 🔴 Pendente | Dashboard pós-briefing                                                 |
| **Frontend — console Ferzion**          | 🔴 Pendente | Vista interna de sessões                                               |

**Conteúdo metodológico cadastrado:** 1 roteiro · 8 atos · 22 sinais · 6 perguntas · 28 opções · 29 mapeamentos · 18 frases de devolutiva.

---

## Stack

### Backend

- Python 3.12 · Django 5 · DRF · PostgreSQL · Redis · Celery · uv

### Frontend público

- Next.js 15 · React 19 · TypeScript · Tailwind · Framer Motion

### Painéis internos

- Django Templates · HTMX · Alpine.js · Tailwind

### Infraestrutura

- Docker · Docker Compose · GitHub Actions · Cloudflare (futuro)

---

## Setup

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

| Serviço            | URL local                   | Porta       |
| ------------------ | --------------------------- | ----------- |
| Backend (Django)   | http://localhost:8001       | 8001 → 8000 |
| Frontend (Next.js) | http://localhost:3001       | 3001 → 3000 |
| Admin              | http://localhost:8001/admin | —           |
| Postgres           | `postgres://localhost:5433` | 5433 → 5432 |
| Redis              | `redis://localhost:6380`    | 6380 → 6379 |

### Popular metodologia inicial

```bash
docker compose exec backend uv run python manage.py seed_methodology
```

Idempotente. Cria identidade, v1 em rascunho, 8 atos canônicos, 22 sinais, perguntas declarativas dos atos populados.

Modo destrutivo: `seed_methodology --force` (apaga tudo e recria).

---

## Estrutura

```
backend/apps/
├── methodology/      # ✅ Conteúdo versionado (roteiros, atos, perguntas, sinais, insights, regras)
├── briefing/         # ✅ Sessões dos clientes (modelos)
├── discovery_engine/ # 🔴 Motor de fluxo
├── signals_engine/   # 🔴 Resposta → Sinal
├── profiling/        # 🔴 Score de Aprofundamento (SCA)
├── insights/         # 🔴 Insights condicionais
├── synthesis/        # 🔴 Geração da devolutiva
├── project_brief/    # 🔴 Output técnico (JSON/MD/PDF)
├── client_panel/     # 🔴 Painel do cliente
├── ferzion_console/  # 🔴 Console interno
├── identity/         # 🔴 Auth (link mágico)
├── notifications/    # 🔴 Email + Celery
└── audit/            # ✅ LGPD + auditoria (django-auditlog)
```

```
backend/apps/methodology/
├── models.py                    # 10 entidades de domínio
├── admin/                       # CMS customizado
│   ├── _helpers.py
│   ├── catalogo_sinal.py
│   ├── roteiro.py
│   ├── ato.py
│   ├── pergunta.py
│   ├── insight.py
│   └── regra.py
├── seeds/                       # Conteúdo declarativo
│   ├── _spec.py                 # Dataclasses (PerguntaSpec, OpcaoSpec, MapeamentoSpec)
│   ├── _loader.py               # Carregador idempotente
│   └── ato_1_calibracao.py      # 6 perguntas
└── management/commands/
    └── seed_methodology.py      # Comando de seed
```

```
backend/apps/briefing/
├── models.py                    # BriefingSessao + Resposta + Sinal + Evento
├── admin.py                     # Admin de QA (read-only)
├── api/                         # 🔴 Pendente (DRF)
└── tests/
```

---

## Roadmap até MVP

Cada item é uma entrega testável e commit limpo.

### Frente C — Engines (backend)

- [ ] **API REST pública** — `iniciar`, `obter_estado`, `responder`, `concluir` (DRF)
- [ ] **Engine de discovery** — fluxo + filtragem por perfil + próxima pergunta
- [ ] **Engine de sinais** — extrai sinais de respostas via mapeamentos
- [ ] **Engine de profiling (SCA)** — calcula `perfil_profundidade_calculado`
- [ ] **Engine de síntese** — gera devolutiva determinística aplicando regras

### Frente B — Frontend

- [ ] **Design tokens** — primitives → semantic → components (substituível)
- [ ] **Atos 0-1** — Acolhimento + Calibração com transições suaves
- [ ] **Atos 2-5** — fluxo principal com insights ao vivo
- [ ] **Ato 6** — devolutiva (cards, score, frase-síntese, oportunidades)
- [ ] **Ato 7** — Ponte (link mágico para painel)

### Frente D — Identidade e painéis

- [ ] **Auth link mágico** — token único por email, sem senha
- [ ] **Painel cliente** — dashboard pós-briefing, devolutiva expandida
- [ ] **Console Ferzion** — visão interna de todas as sessões + analytics
- [ ] **Notificações** — email transacional via Celery

### Conteúdo metodológico (paralelo)

- [ ] Ato 2 — Compreensão do Negócio (~6 perguntas)
- [ ] Ato 3 — Diagnóstico Operacional (~10 perguntas — coração da metodologia)
- [ ] Ato 4 — Aspirações e Visão (~4 perguntas)
- [ ] Ato 5 — Restrições (~4 perguntas)
- [ ] Insights condicionais (Ato 3 ao vivo + Ato 6)
- [ ] Regras de síntese (frase-síntese, oportunidades, módulos sugeridos)

### Onda 2 — Validações automáticas (gatilho: 5+ perguntas reais)

Ver `docs/methodology/invariantes-onda-2.md`.

---

## Princípios não-negociáveis

1. **Engine genérica + conteúdo como ativo intelectual** — código não pode embedar metodologia.
2. **Determinístico antes de IA** — IA potencializa, não sustenta.
3. **Append-only** — metodologia versionada, snapshots imutáveis, sessões nunca editadas.
4. **Sofisticação invisível** — escrever para o leigo, satisfazer o experiente.
5. **Branding substituível** — design tokens em 3 camadas.
6. **Pinning de versão** — sessão antiga reflete metodologia da época.

---

## Documentação técnica

- `docs/architecture/decisions/` — ADRs (6 decisões registradas)
- `docs/methodology/framework-de-perguntas.md` — manual de construção de perguntas + taxonomia + espinha dorsal
- `docs/methodology/invariantes-onda-2.md` — mapa de validações futuras

---

## Convenções de commit

```
feat(<app>): descrição
refactor(<app>): descrição
fix(<app>): descrição
docs: descrição
chore: descrição
```

Exemplos reais do histórico:

```
feat(methodology): seed declarativo do Ato 1 (6 perguntas + segmento_operacional)
feat(methodology): FraseDevolutiva, Arquetipo da pergunta, constraint de mapeamento
feat(methodology): infraestrutura de seed declarativo (PerguntaSpec + loader idempotente)
docs: framework Ferzion de construção de perguntas
```

---

## Estado do banco (após seed)

```
Identidade: Roteiro Universal Ferzion
Versão atual: v1 (Rascunho)
Atos: 8
Sinais: 22
Perguntas: 6
Sessões: 0
```
