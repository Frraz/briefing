# ADR 0003 — Versionamento append-only da metodologia

**Status:** Aceito

## Decisão
Toda entidade da metodologia (Roteiro, Ato, Pergunta, Insight, RegraDeSintese) é imutável após publicação. Edições geram nova versão. Briefings fixam (pin) a versão ativa no momento de início.

## Justificativa
- Integridade histórica: briefing como "fotografia daquele momento operacional".
- Auditoria nativa.
- A/B testing nativo.
- Comparação longitudinal (cliente em v3 hoje, v8 daqui a 2 anos).

## Consequências
**Positivas:** confiabilidade absoluta; reprocessamento sem perder histórico; benchmarking.
**Negativas:** modelagem mais complexa; banco cresce; UX de "edição" precisa de cuidado.
