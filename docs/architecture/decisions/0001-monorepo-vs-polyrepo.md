# ADR 0001 — Monorepo (backend + frontend + infra no mesmo repositório)

**Status:** Aceito

## Contexto
O projeto contém múltiplas faces que evoluem juntas: backend Django, frontend Next.js, painéis em Django Templates, infraestrutura.

## Decisão
Monorepo único.

## Justificativa
- Sincronia de evolução: mudança de contrato de API exige PR atômico.
- CI/CD simplificado.
- Onboarding mais simples.
- Documentação centralizada.

## Consequências
**Positivas:** refatorações cross-cutting em PR único; reuso de tipos viável.
**Negativas:** repositório cresce; CI precisa de path filters.
