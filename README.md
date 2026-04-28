# Ferzion Discovery

> Plataforma de discovery e briefing estratégico — o primeiro produto que o cliente experimenta da Ferzion.

A promessa-âncora: **transformar caos operacional em clareza.**

## Stack
- Backend: Python 3.12 · Django 5 · DRF · PostgreSQL · Redis · Celery · uv
- Frontend público: Next.js 15 · React 19 · TypeScript · Tailwind · Framer Motion
- Painéis internos: Django Templates · HTMX · Alpine.js · Tailwind

## Setup

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- Backend → http://localhost:8000
- Frontend → http://localhost:3000
- Admin → http://localhost:8000/admin

## Estrutura

```
backend/apps/
├── methodology/      # Conteúdo versionado
├── briefing/         # Sessões dos clientes
├── discovery_engine/ # Motor de fluxo
├── signals_engine/   # Resposta → Sinal
├── profiling/        # Score de Aprofundamento
├── insights/         # Insights condicionais
├── synthesis/        # Geração da devolutiva
├── project_brief/    # Output técnico (JSON/MD/PDF)
├── client_panel/     # Painel do cliente
├── ferzion_console/  # Console interno
├── identity/         # Auth
├── notifications/    # Email + Celery
└── audit/            # LGPD + auditoria
```

## Princípios não-negociáveis
1. Engine genérica + conteúdo como ativo intelectual
2. Determinístico antes de IA
3. Append-only (metodologia versionada)
4. Sofisticação invisível
5. Branding substituível via design tokens
