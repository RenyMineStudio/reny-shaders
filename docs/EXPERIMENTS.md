# Experimentos e Benchmarks

Este documento define a ordem de prova antes de ampliar o renderer.

## Regra geral

Não escolher números por tradição de shaderpack.

Toda comparação deve manter constantes:

- mundo/seed;
- posição;
- yaw/pitch;
- resolução;
- render distance;
- preset;
- weather/time;
- duração;
- stack/mods;
- hardware/driver.

Registrar capturas comparáveis e frame time.

## P0 — Architecture blockers

### EXP-P0-STACK — E7 no stack real

**Hipótese:** Forge 1614 + OptiFine E7 carrega com o workload real e expõe as capabilities necessárias.

Procedimento:

- shader probe mínimo;
- Overworld;
- Nether;
- End quando aplicável;
- ao menos uma dimensão modded representativa;
- reload de shader;
- troca de dimensão;
- movimento de câmera;
- logs verificados.

Sucesso:

- compila e carrega;
- troca dimensão;
- reload funciona;
- sem corrupção visual/crash material.

Falha bloqueia a baseline atual.

**Registro histórico (2026-09-18, pré-hardening): PENDING REVALIDATION**
- Este resultado antecede os gates fail-closed de cursor, rotação, semântica MCP e evidência target-specific de dimensões.
- Não é prova atual de 19 programas, dimensões, resize ou estabilidade visual; o novo relatório só promove claims após suite completa com provenance.

### EXP-P0-CAP — capability probe versionado

Testar isoladamente:

- deferred;
- includes;
- profiles/options;
- block.properties;
- Forge mapping;
- world folders;
- custom texture/noise;
- frameCounter/frameTime;
- colortex clear skip;
- compact/half-float formats;
- qualquer scale.<program> realmente aceito.

Saída versionada:

~~~text
capability: [nome da capability]
stack/version: Minecraft 1.7.10 / Forge 10.13.4.1614 / OptiFine HD U E7
hardware: Mesa Intel(R) Iris(R) Xe Graphics (ADL GT2)
driver: 4.6 (Compatibility Profile) Mesa 25.2.8
pass|fail: PASS | REJECTED
observations: [detalhes observados no cliente real]
~~~

Relatório gerado em `benchmarks/reports/p0_probe_report.md` e JSON estruturado em `benchmarks/reports/p0_probe_report.json`.
Evidências visuais capturadas em `benchmarks/artifacts/p0_probe/`.

### EXP-P0-MATERIAL — cobertura modded

Criar galeria com vanilla + materiais modded representativos.

Verificar:

- opaque;
- foliage;
- water;
- lava;
- metal;
- emissive;
- magic;
- portal;
- translucent special;
- TESR equivalente quando existir.

Gate: material crítico não deve depender de heurística de cor se mapping confiável estiver disponível.

### EXP-P0-DIM — dimension semantics

Verificar:

- world<id> selecionado corretamente;
- includes comuns;
- time/sky/fog data;
- custom sky behavior;
- troca de dimensão sem estado sujo.

Não assumir que seleção correta implica atmosfera correta.

### EXP-P0-HISTORY — skip-clear semantics

Pattern/counter de teste em buffer persistente.

Eventos obrigatórios:

- câmera parada/movimento;
- resize;
- shader reload;
- FOV change;
- teleporte;
- dimension switch;
- alteração de preset.

Saída: tabela de validade/reset.

**Tabela de validade e reset observada no stack real (2026-09-18):**

| Evento | Comportamento Observado | Classificação | Implicação de Arquitetura |
|---|---|---|---|
| Câmera parada | Rastro suave e contínuo de 25–30 frames decaindo via `prev * 0.96` | Persistência válida | Primitiva funcional para acumulação estável |
| Movimento de câmera | O rastro persiste no espaço de tela sem corrupção ou rasgos | Persistência válida | Acumulação em coordenadas de tela requer reprojeção para dados mundiais |
| Window resize | FBO e buffers são recriados na nova resolução; histórico reinicia | Reset limpo | Sem vazamento de memória ou distorção de aspecto |
| Shader reload (GUI / F3+R) | Shaders recompilam e o framebuffer é limpo | Reset limpo | Sem estado residual |
| FOV change | Projeção altera; buffer em screen-space permanece estável | Persistência válida | Mudança de FOV preserva integridade do buffer |
| Teleporte | O histórico em tela NÃO é limpo automaticamente pelo host | Conteúdo antigo reutilizado | Shader MUST detectar corte de câmera (`distance(camPos, prevCamPos) > threshold`) para resetar histórico |
| Troca de dimensão | `checkWorldChanged` chama `Shaders.uninit()`, reinicializando buffers | Reset limpo | Sem contaminação entre Overworld, Nether e End |
| Alteração de opção/preset | Shaders recompilam e o framebuffer é reinicializado | Reset limpo | Transição segura |

Se reset seguro não puder ser garantido, history local continua bloqueado. Com o descarte explícito em descontinuidade de câmera, primitivas temporais pontuais são desbloqueadas para investigação.

### EXP-P0-SHADOW-COST — custo bruto

Mesma cena:

1. shadows off;
2. shadow mínima on.

Medir:

- frame time;
- P95/P99;
- movimento;
- comportamento com foliage/entities/TESR.

Objetivo: saber o custo do rerender antes de discutir filtering.

## P1 — High ROI

### EXP-P1-ATMOSPHERE

A/B incremental:

1. vanilla/pass-through;
2. + sky;
3. + fog/horizon;
4. + grade;
5. + directional/ambient relation.

Critério: ganho perceptual incremental versus custo.

### EXP-P1-SHADOW-SWEEP

Sweep sem número ideal pré-fixado:

- resolution;
- distance;
- nearest/1/4 taps;
- linear versus distorted;
- fade range.

Cenas: DAY-OPEN, FOREST, MOTION.

Capturar shimmer e peter-panning em movimento.

### EXP-P1-WATER

Ladder:

A. tint/depth;
B. + Fresnel;
C. + normal;
D. + sun specular;
E. + fake reflection extra.

Parar onde o ganho marginal cair.

### EXP-P1-AO-LADDER

1. lightmap/AO vanilla;
2. + directional;
3. + ambient gradient;
4. + 2/4-tap contact darkening;
5. SSAO mais amplo somente se déficit perceptual permanecer.

### EXP-P1-EMISSIVE

1. semantic emissive;
2. integrated boost/fake halo;
3. bloom somente se houver rota comprovadamente barata.

Cena MAGIC é obrigatória.

### EXP-P1-FORMAT

Comparar onde aplicável:

- RGBA8;
- packed/compact format;
- half float.

Verificar:

- banding;
- filtering;
- blending;
- driver errors;
- frame time;
- memória/bandwidth.

## P2 — Optimization

Depois do Default estável:

- MRT count sweep;
- noisetex versus procedural hash;
- LUT versus polynomial grading;
- branch versus branchless material dispatch;
- shadow sampling microbench;
- include/profile variants;
- sample rotation stability;
- camera-only temporal;
- OptiFine versus Angelica apenas como pesquisa de backend alternativo.

## Cenas canônicas

### SCENE-DAY-OPEN

Campo/planície, sol alto, foliage moderado.

Mede shadow distance/resolution e color balance.

### SCENE-SUNSET

Horizonte longo, sol baixo.

Mede fog, grading, banding e shadow transition.

### SCENE-NIGHT

Baixa luz ambiente + fontes emissivas.

Mede legibilidade, black crush e autoridade de emissivos.

### SCENE-MAGIC

Partículas, magia, portal/emissivos representativos.

Mede overdraw e hierarquia sobrenatural.

### SCENE-WATER

Margem de lago/rio, ângulos rasantes e movimento.

Mede Fresnel, aliasing, depth tint e shoreline.

### SCENE-FOREST

Foliage alpha-tested densa.

Mede shadow shimmer, overdraw e vertex waving.

### SCENE-MODDED-BASE

TESRs, máquinas/cabos/líquidos/entidades representativas do workload real.

Mede split CPU/GPU, state bugs e material mapping.

### SCENE-MOTION

Trajeto reproduzível andando/correndo e girando câmera.

Mede P95/P99, hitching, shimmer e qualquer ghosting.

## Métricas mínimas

Quando disponíveis:

- GPU frame time;
- CPU frame time;
- median;
- P95;
- P99;
- 1% low;
- hitch count;
- FPS como métrica auxiliar;
- memória/VRAM/shared-memory pressure;
- compile/runtime errors;
- regressão visual;
- compatibilidade.

## Ordem de implementação

1. capability probe E7 + benchmark harness;
2. pass-through shader fiel;
3. final tonemap/grade + dither;
4. analytic sky + fog;
5. directional/ambient preservando lightmap/AO;
6. material mapping generated;
7. near shadows;
8. cheap water;
9. supernatural emissive hierarchy;
10. Lite/Default/Showcase com cortes reais;
11. dimension wrappers;
12. compatibility torture suite;
13. bloom/contact darkening/temporal local somente depois;
14. backend alternativo/Reny Optimization apenas após Default maduro.

## Gate de decisão

Uma técnica passa de experimento para arquitetura quando:

- capability está provada;
- ganho visual aparece em cena canônica;
- movimento não revela artefato material;
- custo é aceitável no preset alvo;
- compatibilidade relevante passa;
- resultado é reproduzível.
