# ADR 0004 — Stack dual: Next.js público + Django Templates internos

**Status:** Aceito

## Decisão
- Face 1 (briefing público): Next.js 15+ + React 19 + TypeScript + Tailwind + Framer Motion.
- Faces 2 e 3 (painéis): Django Templates + HTMX + Alpine.js + Tailwind.

## Justificativa
Next.js + Framer Motion para experiência narrativa cinematográfica do briefing.
HTMX para CRUD denso dos painéis (5x mais rápido que React).

Princípio: ferramenta certa para o contexto, não uniformização por dogma.

## Consequências
**Positivas:** máxima velocidade nos painéis, máxima qualidade na face pública.
**Negativas:** dois conjuntos de habilidades (mitigado por design tokens compartilhados).
