# Framework Ferzion de Construção de Perguntas

> **Documento vivo.** Atualizado continuamente conforme aprendizado real. Quando refinar uma redação ou criar um padrão novo de mapeamento, registre aqui.

---

## Índice

1. [Por que este documento existe](#por-que-este-documento-existe)
2. [Anatomia de uma pergunta excelente](#1-anatomia-de-uma-pergunta-excelente)
3. [Os 4 arquétipos de pergunta](#2-os-4-arquétipos-de-pergunta)
4. [Os 7 vícios que matam perguntas](#3-os-7-vícios-que-matam-perguntas)
5. [Linguagem para o espectro completo](#4-linguagem-para-o-espectro-completo)
6. [Anatomia das opções](#5-anatomia-das-opções)
7. [Mapeamento Resposta → Sinal](#6-mapeamento-resposta--sinal)
8. [Pensando a devolutiva enquanto cria a pergunta](#7-pensando-a-devolutiva-enquanto-cria-a-pergunta)
9. [Ritual de criação de pergunta](#ritual-de-criação-de-pergunta)
10. [Checklist final antes de salvar uma pergunta](#checklist-final-antes-de-salvar-uma-pergunta)

- [Apêndice A — Vocabulário Ferzion para microcopy](#apêndice-a--vocabulário-ferzion-para-microcopy)
- [Apêndice B — Taxonomia e Espinha Dorsal](#apêndice-b--taxonomia-e-espinha-dorsal)

---

## Por que este documento existe

A metodologia da Ferzion é o ativo intelectual mais valioso do produto. Cada pergunta cadastrada no admin não é apenas um item de formulário — é uma decisão consultiva que vai produzir sinais, que vão alimentar diagnósticos, que vão formar a devolutiva que o cliente recebe.

Sem framework, perguntas viram acúmulo. Com framework, viram sistema.

Este documento é o **manual operacional** que orienta a criação de qualquer pergunta dentro do CMS do app `methodology`.

---

## 1. Anatomia de uma pergunta excelente

Toda pergunta da Ferzion tem **5 camadas internas**. Quatro são invisíveis ao cliente, uma é o que ele vê. Se você não consegue verbalizar todas as cinco, a pergunta ainda não está pronta.

| Camada                  | Onde vive                                     | O que é                                           |
| ----------------------- | --------------------------------------------- | ------------------------------------------------- |
| 1. Hipótese diagnóstica | `objetivo_interno`                            | O que você suspeita encontrar com esta pergunta   |
| 2. Sinal-alvo           | `MapeamentoDeSinal`                           | Que sinal estruturado a resposta deve produzir    |
| 3. Caminho de captura   | `condicao` do mapeamento                      | Direto (escolha → sinal) ou inferido (combinação) |
| 4. Uso na devolutiva    | (mental, mas registrar em `objetivo_interno`) | Como o sinal aparece no Ato 6                     |
| 5. Texto público        | `texto_publico`                               | A pergunta que o cliente lê                       |

**Checagem prática:** antes de salvar, verbalize as 5 camadas mentalmente. Se uma falta, ainda não está pronta — ou não vale a pena.

---

## 2. Os 4 arquétipos de pergunta

Não confunda com os tipos técnicos (`escolha_unica`, `escala`, etc. — esses são _forma_). Arquétipos são _função_.

### Calibradora

- **Função:** classificação rápida que produz UM sinal.
- **Padrão de redação:** "Como você descreveria...?" / "Em qual destes contextos você se encaixa?"
- **Tipo técnico ideal:** `escolha_unica` com 3-5 opções.
- **Uso no diagnóstico:** alimenta `perfis_minimos` de outras perguntas.
- **Exemplo:** _1.5 — "Como você descreveria o porte da sua operação hoje?"_

### Reveladora

- **Função:** o cliente revela algo concreto que ele não verbalizaria com sim/não.
- **Padrão de redação:** "Que tarefa, na sua operação, alguém faz mais de uma vez?" / "O que aconteceu nas últimas semanas que te trouxe aqui?"
- **Tipo técnico ideal:** `texto_longo`.
- **Uso no diagnóstico:** sinais por análise de palavras-chave OU preservada como contexto.
- **Exemplo:** _1.7 — "O que aconteceu nas últimas semanas que te trouxe até aqui?"_

### Mapeadora

- **Função:** o cliente identifica múltiplos elementos de uma realidade. Captura amplitude.
- **Padrão de redação:** "Onde mora..." / "Quais destes você usa..."
- **Tipo técnico ideal:** `escolha_multipla`.
- **Uso no diagnóstico:** a _contagem_ de marcações é sinal por si só.
- **Exemplo:** _3.1 — "Onde mora a informação importante da sua empresa hoje?"_

### Confrontadora

- **Função:** força o cliente a tomar consciência de um trade-off ou tensão. Cria momento "uau".
- **Padrão de redação:** "O que tira seu sono...?" / "Se [pessoa] sai amanhã, o que para?"
- **Tipo técnico ideal:** `texto_longo` ou `escolha_unica` desconfortável.
- **Uso no diagnóstico:** alimenta insights de severidade alta.
- **Exemplo:** _3.6 — "O que tira seu sono em relação à operação?"_

**Proporção saudável de briefing:**

| Arquétipo      | % do total |
| -------------- | ---------- |
| Calibradoras   | ~50%       |
| Mapeadoras     | ~25%       |
| Reveladoras    | ~15%       |
| Confrontadoras | ~10%       |

Confrontadoras em excesso queimam o cliente.

---

## 3. Os 7 vícios que matam perguntas

| Vício                          | Sintoma                                                | Antídoto                                            |
| ------------------------------ | ------------------------------------------------------ | --------------------------------------------------- |
| **Composta**                   | Cliente responde uma e esquece a outra                 | Uma pergunta = uma resposta                         |
| **Corporativês estéril**       | Cliente leigo trava, experiente responde mecanicamente | Linguagem de conversa real                          |
| **Resposta desejada embutida** | "Você sente que poderia automatizar mais?"             | Pergunta neutra que mostra realidade, não aspiração |
| **Categoria vazia**            | Opções "Pequena/Média/Grande" sem referência           | Ancorar com números ou exemplos concretos           |
| **Pergunta-cego**              | Cliente que não mede vira mudo                         | Sempre incluir opção de escape diagnóstica          |
| **Especificidade falsa**       | Campo data de fundação                                 | Faixas que correspondem ao que vai usar             |
| **Pergunta sem sinal**         | Ocupa tempo, não alimenta diagnóstico                  | Toda pergunta tem ≥1 mapeamento OU é Reveladora     |

**Checagem prática:** leia em voz alta para alguém fora do projeto. Se a pessoa franze a testa, tem vício.

---

## 4. Linguagem para o espectro completo

**Regra de ouro:** escreva para o leigo, satisfaça o experiente.

### Os dois testes

**Teste do MEI:** imagine um microempresário com pouca familiaridade tecnológica lendo. Entende sem glossário?

**Teste do CTO:** imagine um CTO de empresa estabelecida lendo a mesma pergunta. Acha simplista demais?

Se as duas respostas são "sim", você acertou — sofisticação invisível.

### Glossário Ferzion

Sempre traduzir os termos da esquerda para os da direita no `texto_publico`:

| Não use           | Use                                             |
| ----------------- | ----------------------------------------------- |
| Stakeholder       | Quem participa, quem decide                     |
| Workflow          | Como o trabalho acontece                        |
| Operação          | Como vocês fazem o que fazem                    |
| Stack tecnológico | Os sistemas que vocês usam                      |
| Processo          | Rotina, tarefa                                  |
| Insumos / outputs | "O que precisa para começar / o que sai pronto" |
| Compliance        | "Regras que vocês precisam seguir"              |
| Estratégia        | "Plano", "direção" (ou cortar)                  |
| Implementação     | Botar pra rodar                                 |
| Otimização        | Deixar mais rápido / mais simples               |
| Métricas          | Os números que vocês acompanham                 |

### Decisão importante

`texto_publico` é radicalmente humano. `objetivo_interno` é tecnicamente preciso. Eles **não precisam usar a mesma linguagem**. Aproveite a separação.

---

## 5. Anatomia das opções

### Princípios

**MECE.** As opções não se sobrepõem, e juntas cobrem o universo possível.

**Ordem narrativa.** Ordene por intensidade ou progressão lógica, não alfabeticamente.

**Texto humano, código técnico.** O `codigo_interno` é preciso (`porte_3`, `modelo_recorrente`). O `texto_publico` é conversa.

**Cada opção é um sinal mappeável.** Para cada opção, pergunte: "se alguém marcar isso, que sinal extraímos?"

**A "opção de honestidade".** Para perguntas confrontadoras ou de medição, sempre inclua: _"Não sei / Não tenho certeza / Prefiro não responder agora"_. Essa resposta é o sinal mais valioso possível.

### Padrão de quantidade

| Tipo             | Quantidade ideal      | Por quê                         |
| ---------------- | --------------------- | ------------------------------- |
| Escolha única    | 3-6 opções            | Mais que isso vira matriz       |
| Escolha múltipla | 4-8 opções            | Mais que isso o cliente desiste |
| Escala           | 5 ou 7 pontos (ímpar) | Forçar tomada de posição        |

---

## 6. Mapeamento Resposta → Sinal

### Padrão A — Direto (1 opção → 1 valor)

1 `MapeamentoDeSinal` por opção, cada um produzindo um valor distinto do sinal.
**Quando:** Calibradoras com escala ordinal clara.

### Padrão B — Agregado (combinação → 1 valor)

Múltiplas marcações somam para definir um valor (ex: 3+ marcações = `alto`).
**Quando:** Mapeadoras (`escolha_multipla`).
**Implementação atual:** múltiplos mapeamentos parciais com `peso`. O motor agregador (futura Frente C) calcula. Por enquanto, documente intenção em `notas`.

### Padrão C — Múltiplo (1 resposta → N sinais)

Mesma resposta alimenta vários sinais simultaneamente.
**Quando:** respostas ricas que iluminam múltiplas dimensões.
**Implementação:** múltiplos `MapeamentoDeSinal` para a mesma combinação de pergunta + opção.

### Padrão D — Preservado (texto livre → sinal de texto)

Sinal tipo `TEXTO`, valor é a resposta inteira preservada.
**Quando:** Reveladoras. Valor está no contexto, não na classificação.
**Implementação:** `condicao={"operador": "always"}` + `valor_extraido` é o texto.

### Pesos

| Peso    | Significado                                |
| ------- | ------------------------------------------ |
| 1.0     | Sinal primário, mapeamento canônico        |
| 0.5-0.8 | Sinal secundário, contribui mas não define |
| 0.1-0.3 | Sinal indicativo, agregado com outros      |

---

## 7. Pensando a devolutiva enquanto cria a pergunta

### Teste das 3 frases

Para cada pergunta, escreva 3 frases curtas que vão aparecer no relatório final, conforme as respostas:

```
Se sinal = ALTO  → "[texto da devolutiva versão crítica]"
Se sinal = MÉDIO → "[texto da devolutiva versão neutra]"
Se sinal = BAIXO → "[texto da devolutiva versão positiva]"
```

Se você consegue escrever as 3 frases, a pergunta está pronta. Se não consegue, o sinal não tem profundidade suficiente.

### Princípio Ferzion da devolutiva

Toda devolutiva fala sobre **força**, **risco**, e **oportunidade** — nunca só sobre falha.

- ❌ "Vocês estão um caos."
- ✅ "Vocês cresceram organicamente, e isso é mérito — agora chegou o momento de estruturar."

---

## Ritual de criação de pergunta

Para cada pergunta nova, antes de tocar no admin:

1. Definir o **arquétipo** (Calibradora / Reveladora / Mapeadora / Confrontadora)
2. Escrever a **hipótese diagnóstica** em uma frase
3. Listar o(s) **sinal(is)-alvo** que você quer extrair
4. Esboçar o **texto público** (rodar testes do MEI e do CTO)
5. Listar as **opções** (se aplicável), com `codigo_interno` + `texto_publico`
6. Esboçar as **3 frases da devolutiva** (Padrão A/B/C)
7. _Só agora_ abrir o admin e popular

Parece muito. Da quinta pergunta em diante, leva 4 minutos.

---

## Checklist final antes de salvar uma pergunta

- [ ] As 5 camadas estão verbalizadas (mental ou em rascunho)
- [ ] Arquétipo identificado
- [ ] Sem nenhum dos 7 vícios
- [ ] Passa nos testes do MEI e do CTO
- [ ] Opções (se houver) são MECE com escape diagnóstico
- [ ] Pelo menos 1 mapeamento de sinal — OU é Reveladora preservada
- [ ] As 3 frases da devolutiva foram esboçadas mentalmente

Se todos os itens ✓, salvar com confiança.

---

# Apêndice A — Vocabulário Ferzion para microcopy

Frases que aparecem com frequência em ajuda contextual (`helper_text`, `placeholder`):

- "Pode ser uma frase só. A gente puxa o resto na conversa."
- "Quanto mais sincero, mais útil para o seu próprio diagnóstico."
- "Não tem resposta certa aqui — é sobre entender o seu momento."
- "Pode pular se não fizer sentido para vocês agora."
- "A gente sabe que isso muda. Responde pensando em hoje."

Esse tom é parte da identidade — usá-lo consistentemente cria sensação de coerência.

---

# Apêndice B — Taxonomia e Espinha Dorsal

## B1. Taxonomia mental: `categoria.dominio.dimensao`

Padrão conceitual em 3 níveis. Não codificada nas chaves — vive na cabeça e em filtros.

| Nível     | O que é           | Onde vive                      |
| --------- | ----------------- | ------------------------------ |
| Categoria | Família semântica | Atributo `categoria` no modelo |
| Domínio   | Área de negócio   | Convenção da `chave`           |
| Dimensão  | Atributo medido   | Convenção da `chave`           |

**Regra de chave:** `{dominio}_{dimensão}` quando categoria sozinha não diferencia.

- ✅ `dispersao_informacao`, `volume_comercial`, `historico_perda_operacional`
- ❌ `dispersao` (vago), `comercial` (vago)

**Por que não renomear para 3-níveis literais:** quebra mapeamentos, polui legibilidade. Categoria já cumpre o nível superior.

## B2. Domínios canônicos

| Domínio                    | Cobre                            |
| -------------------------- | -------------------------------- |
| `comercial`                | Vendas, prospecção, ticket       |
| `operacao` / `operacional` | Entrega, execução, processo core |
| `tecnologia`               | Sistemas, integrações, dados     |
| `governanca`               | Decisão, hierarquia, estrutura   |
| `pessoas`                  | Equipe, dependências humanas     |
| `financeiro`               | Caixa, faturamento, custos       |
| `cliente`                  | Relacionamento, retenção, NPS    |

Sinais novos devem caber em um destes 7. Criar 8º exige justificativa explícita.

## B3. Princípios anti-bagunça

1. Antes de criar sinal novo → buscar no catálogo.
2. Sinal só existe se for reutilizável. Específico de pergunta única → texto preservado.
3. Sinal sem dono mental → não devia existir.
4. Chave editável só em correção imediata. Após uso, imutável.

## B4. Classificação tri-circular dos sinais

### Círculo 1 — CORE INDISPENSÁVEL (briefing não funciona sem)

```
porte_operacional
papel_decisor
modelo_comercial
complexidade_operacional
faixa_investimento
perfil_profundidade_calculado
```

### Círculo 2 — CORE DIAGNÓSTICO (eleva qualidade)

```
dispersao_informacao
dependencia_humana_critica
ferramenta_comercial
fragmentacao_tecnologica
historico_perda_operacional
```

### Círculo 3 — CORE CONTEXTUAL (enriquece)

```
maturidade_temporal
volume_comercial
nivel_integracao
tempo_perdido_operacional
referencia_inspiracional
urgencia_implicita
```

### Círculo 4 — TEXTO PRESERVADO

```
disponibilidade_tempo  (categórico — calibração leve do fluxo)
evento_gatilho         (texto)
proposta_valor         (texto)
visao_futura           (texto)
```

**Ordem de povoamento:** Círculo 1 → 2 → 3+4.

## B5. Espinha dorsal — 8 perguntas universais

| Ato         | Código | Nome interno         | Sinal-alvo              | Arquétipo   |
| ----------- | ------ | -------------------- | ----------------------- | ----------- |
| Acolhimento | 0.1    | `tempo_disponivel`   | `disponibilidade_tempo` | Calibradora |
| Calibração  | 1.5    | `porte`              | `porte_operacional`     | Calibradora |
| Calibração  | 1.7    | `evento_gatilho`     | `evento_gatilho`        | Reveladora  |
| Compreensão | 2A.1   | `proposta_valor`     | `proposta_valor`        | Reveladora  |
| Compreensão | 2B.1   | `modelo_comercial`   | `modelo_comercial`      | Calibradora |
| Diagnóstico | 3.1    | `mora_informacao`    | `dispersao_informacao`  | Mapeadora   |
| Aspirações  | 4.1    | `visao_12_meses`     | `visao_futura`          | Reveladora  |
| Restrições  | 5.1    | `faixa_investimento` | `faixa_investimento`    | Calibradora |

**Decisão alimentada por cada pergunta:**

| Pergunta             | Decisão                     |
| -------------------- | --------------------------- |
| `tempo_disponivel`   | Densidade do fluxo          |
| `porte`              | Perfil de profundidade      |
| `evento_gatilho`     | Captura dor real e urgência |
| `proposta_valor`     | Linguagem da devolutiva     |
| `modelo_comercial`   | Módulos sugeridos           |
| `mora_informacao`    | Score de maturidade digital |
| `visao_12_meses`     | Frase final emocional       |
| `faixa_investimento` | Escopo da proposta          |

**Verticalizações HERDAM as 8.** Adicionam atos/perguntas especializadas, espinha permanece. Permite comparação longitudinal entre nichos.

## B6. Workflow de povoamento

| Fase | Foco                                          | Prazo     |
| ---- | --------------------------------------------- | --------- |
| 1    | 8 perguntas-âncora + Círculo 1 completo       | semana 1  |
| 2    | Diagnóstico operacional + Círculo 2           | semana 2  |
| 3    | Círculo 3, ramificações por perfil, microcopy | semana 3+ |

Camada por camada. Não tentar fechar atos em paralelo.
