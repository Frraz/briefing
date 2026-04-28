# ADR 0002 — Django (com DRF) como backend principal

**Status:** Aceito

## Decisão
Django 5 + Django REST Framework.

## Justificativa
1. Painéis administrativos densos — Django Admin é insubstituível.
2. SSR nas faces 2 e 3 — Django Templates + HTMX.
3. Migrations e modelagem rica de domínio — Django ORM líder.

FastAPI seria correto se fôssemos API-only com SPA pura. Não somos.

## Consequências
**Positivas:** velocidade nos painéis, ORM maduro.
**Negativas:** DRF mais verboso que FastAPI; async não first-class (mitigamos com Celery).
