# Compatibilidade 1.7.10 Modded

Reny Shaders não é um shader para um cliente vanilla idealizado. O alvo é Forge 1.7.10 fortemente modded.

## Princípio

Compatibilidade é parte da arquitetura, não cleanup depois da estética.

Um shader visualmente correto que quebra TESRs, líquidos, partículas, céu customizado ou dimensões não está concluído.

## Classes de risco

### Estado OpenGL não convencional

Risco:

- mod altera blend/depth/cull/fog/lighting e não restaura exatamente;
- shader assume estado anterior incorreto.

Testar:

- antes/depois de TESRs;
- overlays;
- partículas;
- hand/items;
- reload.

### TESRs e renderers customizados

Risco:

- path não usa o mesmo material mapping;
- dados esperados de terrain não existem;
- CPU cost domina;
- estado ou matrizes diferem.

Política: não forçar classificação global. Tratar somente quando um smoke real revelar problema.

### Transparência e líquidos

Risco:

- sorting;
- depth semantics;
- tanques/fluidos customizados;
- side leakage;
- alpha/blend inconsistente.

Testar água vanilla e pelo menos um líquido/tanque modded representativo antes de congelar water path.

### Partículas e magia

Risco:

- overdraw;
- blend modes especiais;
- emissive threshold incorreto;
- TAA/history ghosting.

Cena MAGIC deve usar densidade realista, não uma partícula isolada.

### Custom sky e dimensões

Risco:

- sky renderer próprio;
- time/fog semantics inesperadas;
- world folder correto, mas conteúdo visual errado;
- transição deixando state/history inválido.

Dimension support exige smoke próprio.

### Glint, beacon e overlays

Risco:

- fallback de programa;
- additive blending;
- first-person artifacts;
- HUD/world overlays.

### Material misclassification

Risco:

- bloco modded recebe classe errada;
- unknown recebe waving/emission indevida;
- mapping muda entre versões do pack.

Unknown deve ser neutro.

## Smoke matrix mínima

| Classe | O que validar |
|---|---|
| terrain opaque | cor, lightmap, shadow |
| cutout/foliage | alpha, waving, shadow |
| entities | lighting, shadow, emissive |
| TESRs | estado, material, transparência |
| water/liquids | depth, Fresnel, sorting |
| translucent blocks | blending/depth |
| particles | blend, overdraw, emissive |
| glint/overlay | programa e blend |
| custom sky | sky/fog ordering |
| portal | emissive/transparency |
| dimension | world selection + semantics |
| hand/item | primeira pessoa opaca/translúcida |
| camera motion | shimmer/hitches/state |
| shader reload | resources/history reset |

## Mudanças de estado obrigatórias

Testes que quebram muitas soluções “funciona na screenshot”:

- shader reload;
- resize;
- fullscreen/windowed quando aplicável;
- FOV change;
- teleporte;
- dimension switch;
- weather transition;
- day/night transition;
- preset switch;
- entrar/sair da água;
- abrir inventário/GUI e retornar.

## Stack combinations

A baseline OptiFine E7 é provisória.

Combinações de mods de otimização/rendering devem ser testadas no workload real. Compatibilidade binária não implica compatibilidade visual ou frame pacing.

Não documentar “compatível com FastCraft”, Angelica ou qualquer outro renderer sem smoke/benchmark específico.

## Angelica

Angelica é uma rota futura relevante, mas muda o contrato:

- backend Iris-like;
- GL mais moderno;
- incompatibilidades próprias;
- shader backend ainda tratado como Beta na pesquisa consolidada;
- incompatível com OptiFine.

Não construir o Default inicial como dual-backend antes de existir uma baseline madura.

## Reny Optimization

Pode ajudar futuramente com:

- profiling;
- FBO lifecycle;
- state-change reduction;
- culling;
- capability detection;
- material registry;
- shadow scheduling.

Nunca usar isso para esconder dependência não documentada.

## Bug handling

Quando uma incompatibilidade aparecer:

1. reduzir para uma smoke scene;
2. classificar CPU/GPU/state/material/order;
3. capturar log e comparação;
4. identificar programa/path afetado;
5. criar correção mínima;
6. repetir smoke geral;
7. benchmarkar se a correção adiciona custo.

Não adicionar “compat hacks” globais sem reproduzir o problema.

## O que ainda não afirmamos

Este repositório atualmente **não afirma suporte validado** para:

- conjunto completo de mods do The Reawakening;
- custom dimensions específicas;
- FastCraft + E7;
- Angelica;
- qualquer hardware/driver individual.

Esses contratos surgem dos experimentos, não da intenção.
