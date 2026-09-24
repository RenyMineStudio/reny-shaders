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
| deferred passes | não | E7 | HISTORICAL / PENDING REVALIDATION |
| profiles/options | não | D7+ | HISTORICAL / PENDING REVALIDATION |
| include | não | D7+ | HISTORICAL / PENDING REVALIDATION |
| block.properties | não | D7/D8+, fixes E3/E7 | HISTORICAL / PENDING REVALIDATION |
| Forge mod block mapping | não | parser aceito; cobertura modded não exercitada no P0 | UNPROVEN / INCONCLUSIVE |
| world<id> folders | não | D7+ | HISTORICAL / PENDING REVALIDATION |
| custom textures | não | parser D7+; assets não carregados no probe P0 | UNPROVEN / INCONCLUSIVE |
| custom noise | não | parser E6+; texture.noise não carregado no probe P0 | UNPROVEN / INCONCLUSIVE |
| custom uniforms | não | E7 | HISTORICAL / PENDING REVALIDATION |
| half-float formats | limitado | E3+ | HISTORICAL / PENDING REVALIDATION |
| R11F_G11F_B10F | não clássico | D7+ | HISTORICAL / PENDING REVALIDATION |
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

### Preflight e integração semântica MCP

As evidências MCP são limitadas às fronteiras abaixo; não substituem os gates
do Forge nem do shaderpack.

- **MCP discovery:** OpenCode V2 usa `opencode.json` e seu plugin
  project-local; OMP 18.3.0 usa `.omp/mcp.json` project-local e a extensão
  project-local `.omp/extensions/minecraft-mcp-guard.js`. São configurações
  independentes para o mesmo servidor `minecraft-dev`. O bootstrap canônico
  `node ../minecraft-dev-toolkit/bootstrap/src/cli.js --consumer . --clients both`
  foi repetido e retornou `updated: false` para os alvos OpenCode e OMP.
  `opencode mcp list` mostrou `minecraft-dev connected`.
- **MCP transport:** discovery/conectividade prova somente que o processo MCP
  está configurado/conectável. Não prova que o bridge Forge, um mundo ou uma
  capability visual estejam disponíveis. `minecraft_get_capabilities` lista
  capabilities e não cria evidência semântica.
- **OMP native guard enforcement:** a extensão OMP gerada no Reny delega ao
  entrypoint canônico do MDT; o plugin OpenCode project-local também referencia
  a política compartilhada. No MDT
  `9cc91c0233eca8fdb656cc07bc74ff01457be52c`, o comando
  `node --test integrations/omp/minecraft-mcp-guard/test/extension.test.js bootstrap/test/omp-smoke.test.js`
  passou 7/7 em OMP 18.3.0. Esse smoke canônico prova o enforcement OMP no
  harness de teste do MDT, incluindo fail-closed antes de evidência, resultado
  MCP real elegível, fallback elegível e isolamento por sessão. A extensão
  wrapper project-local do Reny está instalada; não se declara um smoke de
  enforcement executado dentro de uma sessão OMP do consumidor Reny.
  Ações de pixel permanecem bloqueadas até sucesso MCP semântico atribuído na
  sessão atual ou fallback de erro de bridge elegível. `computer.run` continua
  protegido mesmo com `read_only: true`; essa flag não é sandbox. O estado de
  autorização é isolado por sessão.
- **Forge runtime availability:** MCP discovery/transport não atesta que o
  Forge bridge está carregado nem que há cliente/mundo disponível. O preflight
  semântico anterior registrou `minecraft_ping`, estado do cliente e estado do
  jogador em 2026-09-22; esses dados não promovem capabilities atuais nem
  substituem a execução relevante para um gate.
- **Shader/render evidence:** esta integração não prova compilação GLSL,
  capability do OptiFine, `world<id>`, formatos de buffer, frame time,
  performance de GPU ou correção visual. Esses claims dependem do harness,
  logs, screenshots e benchmark do Reny Shaders; permanecem sujeitos à
  proveniência e aos gates P0 correspondentes.

A política OMP compartilhada é originária do MDT canônico
`9cc91c0233eca8fdb656cc07bc74ff01457be52c`; nenhuma capability específica de
shader foi adicionada ao core ou inferida a partir do MCP.

> **Proveniência:** os itens de execução abaixo são registro histórico pré-hardening e permanecem **PENDING REVALIDATION** até um relatório gerado pela suite completa com tree SHA, bridge MCP e gates target-specific. Não promovê-los a CONFIRMED no PR atual.

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
- **Option write semantics, direção GUI→arquivo (provado 2026-09-24 no stack alvo):** o inverso também NÃO persiste — cliques no botão Probe Mode avançam o estado in-memory (comprovado por screenshots: `5→0→1→2`, perfil derivado acompanha), o Done-chain reexecuta o recompile que aplica o valor in-memory ao render (badge laranja `RGB(204,102,0)` do mode 2 medido no framebuffer com arquivo ainda em `PROBE_MODE=0`), mas `optionsshaders.txt` mantém o valor de boot para sempre (mtime atualiza, conteúdo não). Consequência: evidência de modes via arquivo é impossível; a suite prova modes pela cor do badge no render (`identify_badge`) com captures de hash vinculado (`mode_attestations.json`), e o evaluator só promove `profiles/options` com attestations de modes 0–5 hash-verificadas.
- **Reload via Done simples é no-op (provado 2026-09-24):** confirmar Done na tela Shaders sem dirty options não gera nenhuma linha de reinit. O recompile (`Uninit` + `Program loaded:` + `Framebuffer created.`) dispara quando há dirty options (ex.: cliques no Probe Mode) ou troca de pack/dimensão. O gate `shader_reload_gui` avança `0→1→2` antes do Done para tornar o reload real.
  - **Profiles & Options:** a execução visual histórica mostrou telas e persistência de `PROBE_MODE`; o evaluator atual só marca PASS quando registra transições específicas e confirmação em `optionsshaders.txt`.
- **GLSL 1.20 legacy:** operador de módulo inteiro `%` é reservado em 1.20 e deve usar `mod(float, float)`. Formatos em `composite.fsh` devem ser declarados dentro de comentários para leitura pelo `ShaderPackParser` sem violar a gramática do compilador GLSL.

  - **Uniforms dinâmicos:** a execução visual histórica mostrou HUD; o evaluator atual só marca PASS com marcador runtime explícito de exercício de `frameCounter`/`frameTime`.

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
