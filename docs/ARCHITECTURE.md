# Arquitetura de Rendering

## Status de decisão

Este documento distingue:

- **FREEZE** — direção segura o suficiente para virar contrato;
- **PROVISIONAL** — melhor baseline atual, ainda depende de execução;
- **EXPERIMENTAL** — só entra depois de um probe/benchmark específico;
- **REJECT DEFAULT** — fora do Default inicial.

## Baseline provisório

**PROVISIONAL**

- Minecraft 1.7.10;
- Forge 10.13.4.1614;
- OptiFine 1.7.10 HD U E7;
- vertex + fragment shaders;
- GLSL conservador;
- renderer independente de Reny Optimization.

O baseline só congela depois do P0 stack smoke.

## Dois contratos históricos

### ShadersMod standalone 2.3.x

O path clássico é substancialmente mais limitado:

- gbuffers clássicos, shadow, composite0..7 e final;
- color/depth/shadow buffers legados;
- mc_Entity, mc_midTexCoord e at_tangent;
- câmera/matrizes anteriores;
- sem block.properties por nome;
- sem profiles/options comparáveis ao E7;
- sem world<id>;
- sem ping-pong automático/skip-clear equivalente ao E7.

### OptiFine 1.7.10 D7 → E7

O stack tardio adiciona capabilities importantes:

- shader options/profiles;
- includes;
- world<id>;
- custom textures;
- frameCounter/frameTime;
- block-ID mapping;
- entity/block-entity IDs;
- skip framebuffer clear;
- formatos compactos/half-float;
- block.properties fixes;
- Forge mod block mapping;
- custom uniforms;
- deferred e restore de ping-pong em E7.

Isso não torna E7 equivalente ao OptiFine/Iris moderno.

## Hard limits

Não projetar baseline dependente de:

- compute shader;
- geometry shader no loader do pack;
- SSBO/image load-store;
- motion vectors gerais;
- at_velocity;
- arbitrary relative size.buffer;
- cascades nativas;
- history buffer dedicado;
- velocity-aware full-scene TAA.

Capacidade máxima de attachments/passes não é orçamento de performance.

## Data contract mínimo

Começar com o menor conjunto possível:

- color/albedo/light result necessário;
- depth já fornecido pelo host;
- shadow depth quando shadows estiverem habilitadas;
- normal/material flags somente se houver consumidor real.

Meta inicial: **1–2 color outputs úteis**, não “usar oito porque existem”.

Cada novo attachment precisa responder:

1. quem escreve;
2. quem lê;
3. em qual resolução/formato;
4. qual problema visual resolve;
5. qual custo medido adiciona.

## Frame candidate — Default

~~~text
Shadow pass curta, inicialmente uma vez por frame
        ↓
GBuffers essenciais
  - preserve vanilla lightmap/AO
  - material class
  - cheap directional basis
  - vertex motion apenas onde seguro
        ↓
Deferred/composite principal
  - apply shadow
  - ambient/directional balance
  - atmosphere/fog/horizon
  - emissive hierarchy
        ↓
Translucent/water conforme ordering do host
  - Fresnel
  - fake sky/sun reflection
  - absorption/depth quando válido
        ↓
Final
  - tonemap / grading
  - dither
  - cheap AA somente se necessário
~~~

## Pass policy

Primeiro milestone:

- sem bloom pass;
- sem SSAO pass;
- sem temporal history;
- sem SSR.

Novo pass só é permitido quando uma cena canônica revelar problema perceptual concreto que não possa ser resolvido no pass existente.

Pass full-resolution exige benchmark antes/depois.

## Lighting e AO

Ordem de investimento:

1. vanilla lightmap;
2. vanilla smooth lighting/AO;
3. directional diffuse;
4. wrapped/hemispherical ambient simples;
5. fog/depth cue;
6. contact darkening mínimo, se ainda necessário;
7. SSAO amplo somente se todo o restante falhar visualmente.

**REJECT DEFAULT:** SSAO full-res.

## Sombras

**FREEZE:** near quality → fade → fog.

Candidate:

- single directional shadow map;
- distância curta/moderada;
- resolução pequena/moderada;
- bias estável;
- nearest ou poucos PCF taps por preset;
- fade explícito antes do cutoff.

**EXPERIMENTAL:** distorted mapping.

**REJECT DEFAULT:**

- cascades completas;
- 16/32-tap PCF;
- long-distance high-resolution shadow;
- pass extra full-res de contact shadows.

Shadow rerender deve ser benchmarkado antes de micro-otimizações de água/fog.

## Água

Candidate ladder:

1. tint/depth;
2. + Fresnel;
3. + normal barata;
4. + sun specular;
5. + fake sky/fog reflection.

**REJECT DEFAULT:** SSR raymarched, cubemap dinâmico, refração multipass.

## Emissivos e sobrenatural

**FREEZE:** hierarquia semântica de emissivos.

Primeiro resolver com:

- emissive strength por material;
- contraste/saturação seletivos;
- integrated/fake halo quando possível.

Bloom dedicado é **EXPERIMENTAL** e depende de capability/custo. Não assumir quarter-res path.

## Material awareness

**PROVISIONAL/HIGH ROI**

Preferir um catálogo versionado que gere classes pequenas para o shader.

Exemplo conceitual:

- DEFAULT_OPAQUE;
- FOLIAGE;
- WATER;
- LAVA;
- METAL;
- EMISSIVE_COMMON;
- MAGIC;
- TENSURA_SPECIAL;
- PORTAL;
- TRANSLUCENT_SPECIAL.

Regras:

- usar namespaced mapping quando o baseline permitir;
- evitar ID numérico cru como contrato;
- unknown → neutral fallback;
- TESRs/entities/custom renderers são paths separados;
- cobertura deve ser provada em galeria material.

## Dimensões

O mecanismo world<id> é **CONFIRMED CAPABILITY** no stack tardio.

Design candidato:

- engine comum em shaders/lib;
- wrappers de programa por dimensão;
- parâmetros artísticos por dimensão;
- Overworld primeiro;
- outras dimensões depois do baseline.

A semântica de tempo, custom sky, fog e renderer modded é **PROVISIONAL** até EXP-P0-DIM.

## Temporalidade

Separar quatro técnicas:

1. true temporal accumulation;
2. frame-alternating work;
3. spatial interleaving;
4. deterministic sample rotation.

E7 fornece primitivas úteis: frame counter/time, previous matrices/camera, skip-clear e ping-pong semantics.

Faltam motion vectors gerais e reset semantics robustos.

Decisão:

- full-scene TAA: **REJECT DEFAULT**;
- spatial dither/sample rotation: **HIGH ROI**;
- camera-only history: **EXPERIMENTAL**;
- persistent local history: **BLOCKED** até EXP-P0-HISTORY.

## Reduced-resolution work

Não assumir size.buffer relativo.

Qualquer solução de bloom/AO “half/quarter-res” precisa provar qual mecanismo real usa no E7.

Um commit histórico de composite scaling não é suficiente para transformar a feature em contrato do build E7.

## Presets

### Lite

Deve cortar trabalho estrutural:

- shadows off/minimal conforme benchmark;
- zero bloom;
- zero AO extra;
- fewer taps;
- simpler water;
- mínimo de outputs.

### Default

Baseline visual canônico:

- atmosphere completa;
- near shadow estável;
- material classes;
- fake water;
- emissivos;
- pass count mínimo.

### Showcase

Escala dentro da mesma arquitetura:

- shadows melhores;
- water detail;
- contact darkening;
- bloom se provado;
- formatos/precisão maiores quando necessários.

## Fronteira com Reny Optimization

Reny Shaders funciona sozinho.

Reny Optimization pode futuramente fornecer:

- GPU/frame timing;
- P95/P99;
- FBO lifecycle/reuse;
- redundant clear/state reduction;
- shadow culling;
- capability/driver detection;
- material registry compartilhado;
- update-frequency control.

Nenhuma dessas integrações pode ser requisito para a aparência Default sem decisão explícita.

## Ordem de implementação

A ordem vinculante está em docs/EXPERIMENTS.md.

Resumo:

1. capability probe + benchmark harness;
2. pass-through correto;
3. tonemap/grade/dither;
4. sky/fog;
5. directional/lightmap;
6. material mapping;
7. shadows;
8. water;
9. emissive hierarchy;
10. presets;
11. dimensions;
12. compatibility torture suite;
13. somente então bloom/AO/temporal local.
