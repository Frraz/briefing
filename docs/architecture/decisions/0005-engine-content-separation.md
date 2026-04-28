# ADR 0005 — Engine + Content Separation

**Status:** Aceito

## Decisão
Separação radical entre motor (código) e conteúdo (dados).
Motor genérico (apps `discovery_engine`, `signals_engine`, `synthesis`) percorre grafo versionado.
Conteúdo (perguntas, insights, regras) vive no banco, gerenciado pelo app `methodology`.

## Justificativa
- Velocidade de evolução metodológica (sem deploy).
- Especialização por nicho sem multiplicar código.
- Separação saudável entre time de produto e engenharia.

> O motor é genérico. O conteúdo é o ativo intelectual.

## Consequências
**Positivas:** refinamento contínuo; A/B testing nativo; verticalização futura.
**Negativas:** complexidade inicial maior (mitigada por Admin customizado).
