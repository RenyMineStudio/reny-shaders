# AGENTS.md

Este arquivo define o contrato operacional para agentes que trabalham no Reny Shaders.

## Missão

Reny Shaders é o shaderpack performance-first do The Reawakening para Minecraft 1.7.10.

Objetivo central:

> maximizar qualidade visual percebida por milissegundo de GPU.

O projeto deve parecer mais caro do que realmente é. Priorize identidade, compatibilidade, frame time, estabilidade e simplicidade.

## Autoridade

Pedro mantém autoridade sobre visão, escopo, direção artística e mudanças normativas.

O mantenedor pode investigar main, revisar mudanças, bloquear regressões, selecionar a próxima tarefa e integrar trabalho correto. Mudanças destrutivas, alteração material de escopo ou mudança da estética canônica dependem de Pedro.

Executor implementa. Mantenedor decide.

## Hierarquia de evidência

Quando houver conflito, use esta ordem:

1. código + execução real + benchmark/captura reproduzível;
2. AGENTS.md e decisões atuais do repositório;
3. documentação canônica deste repositório;
4. evidência primária da versão correta do stack;
5. pesquisa técnica versionada;
6. documentação moderna usada apenas como referência;
7. prior art;
8. inferência.

Nunca assuma que documentação moderna do OptiFine/Iris vale para Minecraft 1.7.10.

Classifique claims relevantes como:

- CONFIRMED IN TARGET STACK;
- EXTERNAL EVIDENCE;
- RENY DECISION;
- HYPOTHESIS / EXPERIMENT REQUIRED;
- REJECTED / FAILED.

## Baseline técnico

Baseline provisório, não contrato final:

- Minecraft 1.7.10;
- Forge 10.13.4.1614;
- OptiFine 1.7.10 HD U E7;
- vertex + fragment shaders;
- GLSL conservador;
- sem dependência obrigatória de Reny Optimization.

Até o P0 smoke fechar, qualquer capability do E7 deve ser tratada conforme docs/EVIDENCE.md.

## Invariantes visuais

Reny deve manter identidade própria:

- dark fantasy atmosférico, legível e eficiente;
- mundo natural relativamente sóbrio;
- luz, fog e atmosfera fornecem profundidade;
- noite realmente escura, sem destruir silhuetas;
- sobrenatural, magia, lava, portais, Tensura e emissivos têm maior autoridade visual;
- Default é a aparência oficial;
- Lite preserva identidade com cortes de custo reais;
- Showcase aumenta qualidade sem virar outro renderer.

Não copiar a estética de BSL, Complementary, SEUS, Sildur, Chocapic ou qualquer outro pack. Eles são prior art.

## Princípios de rendering

Se duas técnicas parecem equivalentes em gameplay, prefira a mais barata.

São válidos quando medidos e visualmente aceitáveis:

- fake lighting/reflections;
- aproximações analíticas;
- LUTs pequenas;
- dithering;
- sample rotation;
- packing;
- reuse de buffers/dados;
- vertex tricks;
- efeitos limitados por distância;
- interleaving;
- atualização menos frequente quando o host permitir;
- fog para mascarar simplificações.

Nenhum efeito ganha pass full-resolution dedicado sem justificar o custo.

Não introduza um G-buffer “por tradição”. Cada attachment deve possuir consumidor e benefício mensurável.

## Prioridade visual

Alta prioridade:

- tonemapping/color grading;
- sky/fog/atmosfera;
- iluminação direcional;
- sombras próximas;
- água convincente barata;
- emissivos seletivos;
- vegetação barata no vertex quando segura.

Não trate como requisito:

- SSR;
- GI pesada;
- volumétricos raymarched;
- PBR generalizado;
- parallax;
- DoF permanente;
- motion blur;
- chromatic aberration;
- cascaded shadow maps completas;
- TAA full-scene.

## Sombras

Política canônica:

> qualidade próxima → simplificação/fade → atmosfera distante.

Resolução, distância, filtering, distortion e taps são decisões de benchmark.

Não aceite equivalência numérica de shadow maps sem captura em movimento e medição.

## Material awareness

Prefira classificação em build/configuração a inferência runtime.

No baseline E7, block mapping e block.properties são mecanismos candidatos. O GLSL deve receber classes semânticas pequenas quando possível.

Não assumir que TESRs, entidades, líquidos customizados ou renderers de mods seguem o mesmo path.

Unknown material deve cair em fallback neutro.

## Dimensões

O mecanismo world<id> é evidência de capability do E7, não prova de semântica correta para toda dimensão modded.

Use renderer comum + wrappers/parâmetros artísticos por dimensão apenas depois do EXP-P0-DIM.

## Temporalidade

Separe:

- true temporal accumulation;
- frame-alternating tricks;
- spatial interleaving;
- deterministic sample rotation.

Sem motion vectors gerais, full-scene TAA não é baseline.

Skip-clear/history, camera-only reprojection e qualquer reuse temporal permanecem experimentais até gates de persistência/reset.

## Performance

Hardware modesto, Intel integrada e GPUs antigas são alvo real.

Trate como suspeitos até benchmark:

- shadow rerender;
- passes full-res extras;
- MRTs numerosos;
- formatos largos;
- overdraw;
- transparência/partículas;
- clears/cópias/FBO churn;
- blur com muitos fetches;
- branches ou trigonometria em hot path;
- qualquer efeito caro com ganho marginal.

Meça quando possível:

- GPU frame time;
- CPU frame time;
- median;
- P95/P99;
- 1% low/hitches;
- estabilidade durante movimento;
- pressão de memória compartilhada quando observável.

FPS médio sozinho não fecha performance.

## Compatibilidade

O alvo é Forge 1.7.10 fortemente modded.

Smokes obrigatórios quando afetados:

- terrain opaque/cutout;
- foliage;
- entities;
- TESRs;
- líquidos/translúcidos;
- partículas;
- glints/overlays;
- custom skies;
- portais;
- dimensões modded;
- hand/items em primeira pessoa;
- câmera/movimento rápido.

Não declarar suporte a mod ou dimensão sem execução relevante.

## Licenças

Shader/code de terceiros é prior art.

Antes de reutilizar código ou asset:

1. localizar licença/termos primários;
2. confirmar que a versão estudada está coberta;
3. registrar atribuição/restrições;
4. só então importar.

Ausência de licença = não assumir permissão.

Prefira reimplementar princípios gerais de forma própria.

## Minecraft Dev Toolkit e clientes agentivos

Quando uma tarefa depender do shared `minecraft-dev`, trate OpenCode V2 e OMP como clientes independentes. O repo deve versionar ambos os formatos project-local no mesmo slice de integração: `opencode.json` com `mcp.servers.minecraft-dev` e `.omp/mcp.json` com `mcpServers.minecraft-dev`.

Nunca assuma que OMP autodiscovery do arquivo OpenCode substitui a configuração OMP-native. Ambos devem apontar para o mesmo servidor/launcher lógico e nenhum deles pode exigir configuração global ou path absoluto versionado.

O guard `.opencode/plugins/minecraft-mcp-guard.js` é OpenCode-specific. Uma sessão OMP com o mesmo MCP deve seguir semantic-first por contrato, mas não pode alegar paridade fail-closed até existir enforcement OMP-native provado.

## Gates de entrega

Quando aplicável, uma mudança só pode ser considerada concluída depois de:

1. shader compilar/carregar sem erro no stack real;
2. client smoke em Minecraft 1.7.10;
3. cenas comparáveis antes/depois;
4. benchmark reproduzível;
5. perfis afetados validados;
6. movimento/câmera exercitados;
7. hardware-alvo testado ou ausência explicitamente declarada;
8. nenhuma regressão visual/material importante;
9. compatibilidade modded relevante preservada;
10. documentação coerente.

CI ou screenshot isolado não substituem execução real.

## Higiene

- shaders, código e comentários técnicos em inglês;
- documentação pode ser em português;
- não commitar builds, logs, dumps ou assets sem permissão;
- não introduzir segredo/path absoluto;
- não engolir erro;
- não usar TODO como entrega;
- não remover teste/gate para obter verde;
- números mágicos precisam de contexto.

## Protocolo de tarefa

Toda tarefa de implementação deve declarar:

- objetivo;
- estado atual;
- evidência relevante;
- stack/dependências;
- escopo e fora de escopo;
- invariantes visuais/performance;
- critérios de aceite;
- cenas/benchmark/smokes;
- branch sugerida;
- título da PR.

A primeira ordem de implementação está em docs/EXPERIMENTS.md.

## Definição de concluído

Branch, commit local, relatório, shader que apenas compila ou screenshot bonito não significam conclusão.

A regra é:

> evidência do stack → hipótese barata → protótipo mínimo → cena reproduzível → benchmark → validação visual → compatibilidade → revisão → decisão → integração.
