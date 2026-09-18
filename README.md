# Reny Shaders

**Reny Shaders** é o shaderpack performance-first do **The Reawakening** para **Minecraft 1.7.10**.

A meta não é maximizar fidelidade física nem quantidade de efeitos. A meta é:

> **maximizar qualidade visual percebida por milissegundo de GPU.**

O jogador deve perceber **dark fantasy, atmosfera, profundidade e magia**. A GPU deve fazer o mínimo de trabalho necessário.

## Estado atual

O projeto está em fase de **validação de stack e arquitetura**, antes da implementação visual ampla.

Baseline de engenharia **provisório**:

- Minecraft 1.7.10;
- Forge 10.13.4.1614;
- OptiFine 1.7.10 HD U E7;
- GLSL conservador compatível com o backend real;
- nenhuma dependência obrigatória de Reny Optimization.

Esse baseline só vira contrato depois de smoke real no modpack e nos hardwares-alvo.

## Identidade canônica

Reny deve parecer **dark fantasy atmosférico, legível e eficiente**:

- mundo natural relativamente sóbrio;
- cores controladas;
- luz, fog e céu carregando grande parte da identidade;
- noite realmente escura, mas com silhuetas legíveis;
- sobrenatural, magia, lava, portais, Tensura e emissivos com maior autoridade visual;
- sombras fortes perto e progressivamente menos relevantes à distância;
- água convincente por aproximação barata, não por reflexo fisicamente completo.

O **Default** é a aparência oficial do The Reawakening. **Lite** preserva a mesma identidade com cortes estruturais de custo. **Showcase** aumenta qualidade sem virar outro renderer.

## Princípios de engenharia

- Se duas técnicas parecem equivalentes em gameplay, prefira a mais barata.
- Nenhum efeito ganha pass full-resolution dedicado sem justificar o custo.
- Bandwidth, fill-rate, MRTs, clears, FBO switches, overdraw e shared memory são custos de primeira classe.
- Reutilize lightmap, vanilla AO, depth, buffers e classificação de material antes de reconstruir informação cara.
- Capacidade do host não equivale a orçamento: suportar oito attachments não significa que Reny deve usá-los.
- Código, execução real, capturas comparáveis e benchmark prevalecem sobre documentação ou tradição de shaderpacks.

## Direção técnica congelada

Já é seguro tratar como contrato:

- vertex + fragment como baseline; sem dependência de compute/geometry;
- atmosphere-first: sky, fog, grading e iluminação direcional são CORE;
- lightmap + vanilla AO antes de SSAO;
- sombra próxima → fade/simplificação → atmosfera distante;
- água via Fresnel + normal barata + céu/sol + absorção/depth, sem SSR no Default;
- material awareness preferencialmente pré-classificado;
- TAA full-scene, SSR full-scene, GI pesada, cascades completas, volumétricos raymarched, DoF permanente, motion blur e chromatic aberration ficam fora do Default inicial;
- Reny Shaders deve continuar funcional sem Reny Optimization.

## O que ainda é provisório

Precisamos provar no stack real:

- OptiFine E7 dentro do The Reawakening;
- comportamento de `block.properties` e Forge block mapping no workload real;
- seleção e semântica de `world<id>` em dimensões modded;
- estabilidade e reset de skip-clear/history;
- existência prática de qualquer rota de composite scaling útil;
- formatos e quantidade de MRTs realmente baratos em Intel/GPUs antigas;
- custo bruto da shadow pass e sua interação com foliage, entidades e TESRs.

Não assumir `size.buffer` relativo, motion vectors gerais ou qualquer capability moderna de Iris/OptiFine sem evidência específica para 1.7.10.

## Arquitetura mínima candidata

```text
Shadow pass curta, quando habilitada
        ↓
GBuffers essenciais
  - preservar lightmap/AO vanilla
  - classificar material
  - mínimo de outputs úteis
        ↓
Deferred/composite principal
  - sombra
  - iluminação ambiente/direcional
  - sky/fog/horizon
  - hierarquia emissiva
        ↓
Translucent/water
  - Fresnel
  - fake sky/sun reflection
  - absorção/depth quando válida
        ↓
Final
  - tonemap / grade
  - dither
  - AA barato somente se necessário
```

Primeiro milestone: **sem bloom dedicado, sem SSAO dedicado, sem temporal history e sem SSR**.

## Documentação

- [AGENTS.md](AGENTS.md) — contrato de manutenção e execução.
- [docs/ART_DIRECTION.md](docs/ART_DIRECTION.md) — identidade visual e invariantes dos presets.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — arquitetura candidata e políticas de rendering.
- [docs/EVIDENCE.md](docs/EVIDENCE.md) — capability matrix, claims confirmados e armadilhas históricas.
- [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) — P0/P1/P2, cenas e métricas de benchmark.
- [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md) — riscos e smoke classes para o ecossistema 1.7.10 modded.

## Prioridade imediata

A próxima etapa não é “deixar bonito”. É construir um **capability/smoke probe versionado para E7** e um harness de benchmark reproduzível. Só depois entram atmosfera, sombras, água e emissivos em ordem de ROI.

## Relações de projeto

- **Reny Shaders:** aparência e rendering layer.
- **Reny Optimization:** infraestrutura/performance; pode cooperar futuramente, mas não é dependência.
- **The Reawakening:** workload, integração de conteúdo e direção artística canônica.

