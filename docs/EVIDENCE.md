# Evidência e Capabilities

Este documento registra o que a pesquisa consolidada permite afirmar sobre o stack 1.7.10 sem contaminar o projeto com documentação moderna.

## Regra

Uma capability pode existir e ainda ser ruim para o orçamento Reny.

Sempre separar:

- existência;
- versão;
- estabilidade;
- custo;
- compatibilidade.

## Capability matrix

| Capability | ShadersMod 2.3.x | OptiFine 1.7.10 E7 | Status Reny |
|---|---|---|---|
| Vertex + fragment | sim | sim | CONFIRMED |
| Compute | não | não | REJECT |
| Geometry stage no pack | não encontrado | não documentado/carregado | REJECT |
| 8 color buffers legados | sim | sim | CONFIRMED capability |
| depthtex0..2 | sim/forte | sim | CONFIRMED/STRONG |
| shadow depth | sim | sim | CONFIRMED |
| previous camera/matrices | sim | sim | CONFIRMED |
| frameCounter/frameTime | não clássico | D7+ | CONFIRMED E7 |
| skip framebuffer clear | não | D7+, fix E7 | CONFIRMED E7 |
| ping-pong/restore automático | não | E7 | CONFIRMED E7 mechanism |
| deferred passes | não | E7 | CONFIRMED E7 |
| profiles/options | não | D7+ | CONFIRMED E7 |
| include | não | D7+ | CONFIRMED E7 |
| block.properties | não | D7/D8+, fixes E3/E7 | CONFIRMED E7 (vanilla) |
| Forge mod block mapping | não | parser aceito; cobertura modded não exercitada no P0 | UNPROVEN / INCONCLUSIVE |
| world<id> folders | não | D7+ | CONFIRMED E7 |
| custom textures | não | parser D7+; assets não carregados no probe P0 | UNPROVEN / INCONCLUSIVE |
| custom noise | não | parser E6+; texture.noise não carregado no probe P0 | UNPROVEN / INCONCLUSIVE |
| custom uniforms | não | E7 | CONFIRMED E7 |
| half-float formats | limitado | E3+ | CONFIRMED E7 |
| R11F_G11F_B10F | não clássico | D7+ | CONFIRMED E7 |
| relative size.buffer | não | não provado; histórico moderno | DO NOT ASSUME |
| scale.<program> | não | ausente no bytecode E7; commit 2018 é posterior | REJECTED E7 |
| object motion vectors | não | não | FAILED |
| camera-only reprojection | matemática possível | possível | PLAUSIBLE |
| full-scene TAA | inadequado | inadequado sem velocity | REJECT DEFAULT |
| configurable low-frequency shadow | não exposto no path clássico | não documentado | UNPROVEN |

## Claims confirmados

### E7 não é o ShadersMod clássico

OptiFine 1.7.10 D7 trouxe o engine de shaders da linha 1.8.8 para 1.7.10. Releases posteriores adicionaram/corrigiram features relevantes até E7.

Implicação: dizer apenas “Minecraft 1.7.10 shaders” é tecnicamente insuficiente.

### Validação empírica no stack-alvo (Forge 1614 + OptiFine E7 + Mesa Intel Iris Xe)

Executado no cliente Minecraft 1.7.10 real através do probe P0 versionado.
Proveniência exata (tested tree SHA, gates e delta allowlisted) em
`benchmarks/reports/p0_probe_report.json` / `.md` e
`benchmarks/artifacts/p0_probe/MANIFEST.md`.

- **Pipeline base:** 19 programas GLSL 1.20 compilaram e executaram sem erros OpenGL ou GLSL (`gbuffers_*`, `deferred`, `composite`, `final`, `shadow`).
- **Deferred stage:** confirmado funcional entre terrain e water. `deferred.fsh` comunica com `composite` via `colortex4` com flip automático de ping-pong (`flipped buffers after deferred: 0, 4`) e restauração por `deferred_last`.
- **Skip-clear & history (`colortex3Clear = false`):** confirmado. OptiFine registrou `colortex3 clear disabled` e o probe demonstrou persistência temporal visual estável de 25–30 frames.
- **Reset de history:**
  - *Resize:* FBO e buffers são recriados na nova resolução sem crash ou distorção.
  - *Reload:* pipeline é reinicializado do zero e o buffer é zerado.
  - *Teleporte:* o buffer de histórico NÃO é limpo automaticamente pelo host; reprojeção temporal deve checar descontinuidade de câmera (`distance(cameraPosition, previousCameraPosition) > threshold`) para evitar ghosting.
  - *Troca de dimensão:* `checkWorldChanged` chama `Shaders.uninit()`, reinicializando buffers e isolando dimensões.
- **Formatos de buffer:** `RGBA16F` (`colortex2`), `R11F_G11F_B10F` (`colortex4`) e `RGBA32F` (`colortex1`) foram aceitos pelo driver Mesa Intel sem `GL_FRAMEBUFFER_INCOMPLETE`.
- **World folders (`world<id>`):** `world-1` (Nether) e `world1` (The End) foram detectados e carregados dinamicamente na troca de dimensão. Se uma pasta `world<id>` existe, OptiFine busca shaders exclusivamente nela (usando fallback interno para programas não definidos), sem herdar arquivos do diretório raiz `/shaders`.
- **Profiles & Options:** `shaders.properties` e opções declaradas em comentários (`#define PROBE_MODE ... // [0 1 2 3 4 5]`) geram telas de menu interativas com nomes e tooltips de `en_US.lang`, e persistem em `optionsshaders.txt`.
- **Reload path (observado):** F3+T recarrega texturas/recursos mas NÃO recria o framebuffer de shaders no E7; o reload de shaderpack acontece via Done na tela Shaders (recriação de framebuffer + `Reset world renderers` observados no log).
- **Option write semantics (observado):** editar `optionsshaders.txt` (arquivo runtime, fora do Git) e em seguida confirmar Done na tela Shaders NÃO aplica o valor — o OptiFine descarrega o estado in-memory da GUI sobre o arquivo. Mudanças de `PROBE_MODE` precisam passar pelo botão da tela Shader Options; o arquivo serve para leitura/verificação de persistência, não como via de escrita pré-reload.
- **Uniforms dinâmicos:** `frameCounter`, `frameTime`, `frameTimeCounter`, `worldTime` e `sunPosition` validados em tempo real via HUD de diagnóstico.
- **GLSL 1.20 legacy:** operador de módulo inteiro `%` é reservado em 1.20 e deve usar `mod(float, float)`. Formatos em `composite.fsh` devem ser declarados dentro de comentários para leitura pelo `ShaderPackParser` sem violar a gramática do compilador GLSL.

### Material mapping existe no E7

Block-ID mapping, block.properties e Forge mod block mapping estão presentes no stack tardio.

Isso prova o mecanismo. Não prova cobertura perfeita do The Reawakening.

### Per-dimension folders existem

world<id> existe no stack tardio.

Isso prova seleção de programas; não prova semântica correta de custom sky/time/fog de cada dimensão modded.

### Previous matrices/camera existem no path legado

Camera-only reprojection é matematicamente possível.

Isso não fornece motion vectors de mobs, partículas, foliage, água ou TESRs.

### Relative buffer sizing não deve ser retroprojetado

O modelo moderno de fixed/relative shader buffer sizing aparece no histórico muito depois da era 1.7.10.

Quarter-res bloom/AO não pode ser requisito arquitetural até um path real ser demonstrado.

## Claims incertos

Continuam abertos:

- cobertura de material mapping em mods reais do The Reawakening (parser comprovado no E7, mas cobertura modded não exercitada no probe P0);
- custom textures e custom noise no workload real (mecanismo previsto no parser, mas não carregado no probe P0);
- custo do ping-pong em Intel antiga;
- melhor formato por attachment;
- número prático de MRTs;
- semântica de custom dimensions modded;
- frequência reduzida de shadow sem suporte mod-side;
- bloom barato sem relative-size attachment;
- FastCraft + E7 + stack final;
- valor de Angelica como backend de produção.

## Claims rejeitados/corrigidos

- “scale.<program> existe no OptiFine 1.7.10 E7” — falso. Inspecionado no bytecode de `Shaders.class` e `ShaderPackParser.class` do JAR E7 oficial; a funcionalidade de composite scale foi adicionada apenas em 2018 (commit `5b0151b4`), portanto é posterior à era 1.7.10.
- “OptiFine 1.7.10 não tem block.properties/world folders/skip-clear” — falso para D7–E7.
- “Quarter-res buffers são nativos no E7” — não sustentado.
- “shadowPassInterval é knob de shaderpack clássico” — símbolo interno existe, mas o path inspecionado fixa o intervalo.
- “512² warped equivale a 2048² com qualidade garantida” — hipótese, não conclusão.
- “skip-clear viola OpenGL por definição” — incompatível com a própria capability documentada do E7.
- “biome/category uniform moderno e at_midBlock são garantidos no E7” — contaminação de documentação moderna.
- “full-scene TAA é fundação segura” — rejeitado para Default.
- “Operador `%` é válido em GLSL 1.20” — falso. Módulo inteiro é reservado e causa erro de compilação; requer `mod(float, float)`.
- “Diretivas de formato `colortex<n>Format` podem ficar como declarações GLSL executáveis” — falso. `RGBA16F`, `R11F_G11F_B10F`, etc. não são identificadores válidos em GLSL 1.20; devem ser declarados dentro de comentários para leitura pelo parser do OptiFine sem falhar na compilação.

## Fontes primárias/decisivas

### OptiFine 1.7.10 E7

- Changelog oficial: https://optifine.net/changelog?f=OptiFine_1.7.10_HD_U_E7.jar
- Downloads oficiais: https://optifine.net/downloads

Usos: timeline D7→E7, Forge #1614, deferred, mapping, skip-clear e features históricas.

### ShadersMod 1.7.10 source reconstruction

- https://github.com/basdxz/ShadersMod

Usos: programas, buffers, previous matrices/camera e comportamento do path standalone.

### OptiFine history

Commits relevantes identificados durante a síntese:

- 5b0151b4eb9490f685aad420600ee75ab14133e4 — “Added composite scale and buffer flip”, 2018-01-18;
- 689c8944aa467fa7651fb35d7f5a4c357a9de936 — “Added fixed size buffers”, 2021-02-01;
- 3c16cdc9ee5df36de8c0fbdad01c040f0527376c — “Added relative buffer size”, 2021-03-10.

O commit de 2018 é pista histórica, não prova automática de que a feature está no JAR E7 de 1.7.10.

## Prior art

Packs como Sildur, Chocapic13, SEUS, BSL, Complementary e MakeUp podem ensinar padrões:

- shadow distance/resolution agressivas;
- atmosphere-first;
- simple water;
- preset scaling;
- dithering;
- distorted shadows;
- selective post.

Eles não são fonte de contrato 1.7.10 e não definem a estética Reny.

## Licenciamento

Política do projeto:

> observar resultado → identificar princípio geral → verificar capability 1.7.10 → reimplementar de forma própria → benchmarkar.

Antes de copiar qualquer trecho/asset, registrar fonte primária e permissão.

Ausência de licença permissiva = não reutilizar.

## Armadilhas recorrentes

1. projetar com features modernas que E7 não tinha;
2. limitar o projeto ao standalone quando E7 já resolve parte do problema;
3. confundir maximum attachment count com orçamento;
4. congelar bloom/SSAO/temporal antes de medir atmosfera/shadow;
5. otimizar screenshot e ignorar movimento;
6. promover benchmark anedótico a fato;
7. usar prior art sem licença;
8. declarar compatibilidade modded sem smoke.

## Atualização deste documento

Promova PROVISIONAL/UNPROVEN para CONFIRMED somente quando houver:

- evidência primária versionada; ou
- probe reproduzível no stack-alvo.

Se código/execução contradizer este arquivo, código/execução vence e este arquivo deve ser corrigido.
