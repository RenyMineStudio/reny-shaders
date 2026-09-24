# Direção Artística

## Tese

Reny Shaders deve entregar **dark fantasy atmosférico, legível e eficiente**.

A identidade não nasce de uma lista grande de efeitos. Ela nasce de relações coerentes entre luz, sombra, atmosfera, cor, distância e hierarquia visual.

> mundo ordinário relativamente contido → sobrenatural visualmente poderoso

## Mundo natural

O Overworld e materiais comuns devem permanecer relativamente sóbrios:

- saturação controlada;
- contraste suficiente para leitura de formas;
- luz solar com direção clara;
- sombra e ambiente sem aparência “plástica”;
- fog e horizonte integrando a cena;
- foliage vivo, mas sem waving exagerado;
- ausência de bloom generalizado.

O objetivo não é “cinza”. O objetivo é preservar espaço visual para que magia e emissivos realmente tenham autoridade.

## Luz e temperatura

Direção preferida:

- luz solar mais quente;
- ambiente/sombra mais fria e desaturada;
- relação variável com hora, chuva e dimensão;
- wrapped diffuse/ambient gradients podem ser usados para preservar volume se não lavarem o contraste.

A noite não deve ser uma versão azul do dia.

## Noite

A noite canônica é realmente escura.

Requisitos:

- céu e ambiente caem materialmente em luminância;
- formas importantes continuam legíveis por silhueta;
- fontes emissivas ganham importância;
- black crush não deve esconder geometria próxima necessária ao gameplay;
- night vision e estados especiais precisam de comportamento compatível.

A leitura deve vir de contraste e composição, não de elevar toda a exposição.

## Sky, fog e atmosfera

Atmosfera é uma das maiores fontes de identidade por custo.

CORE:

- analytic/gradient sky;
- horizon haze;
- fog de distância;
- height component simples quando legível;
- resposta a chuva;
- integração com sol/lua;
- dither estável para evitar banding.

Fog também é ferramenta de performance: pode esconder transições de shadow/detail à distância. Ela nunca deve virar uma cortina constante para mascarar problemas próximos.

## Sombras

Direção:

> sombra de alta qualidade perto → fade/simplificação → atmosfera longe

Sombras distantes têm menor prioridade que estabilidade durante movimento.

Critérios visuais:

- evitar shimmer agressivo;
- evitar peter-panning evidente;
- preservar contato e direção próxima;
- fade deve ocorrer antes do limite perceptível;
- fog/haze devem tornar a perda distante natural.

Distorted shadow mapping é experimento, não estética obrigatória.

## Água

A água oficial deve parecer convincente sem “provar” que existe um sistema físico completo.

Elementos preferidos:

- Fresnel;
- normal simples/procedural ou textura barata;
- highlight solar;
- fake reflection derivada de sky/fog;
- absorption/depth tint quando os dados forem confiáveis;
- underwater fog coerente.

SSR não é requisito do Default.

## Sobrenatural

Magia, Tensura, lava, portais, rituais, entidades especiais e emissivos podem quebrar deliberadamente a sobriedade do mundo natural.

Ferramentas preferidas:

- semantic emissive strength;
- contraste local;
- saturação seletiva;
- cor de fog/atmosfera quando a dimensão/efeito justificar;
- pulsos temporais simples;
- fake halo antes de bloom dedicado.

O jogador precisa perceber energia sobrenatural; não precisa perceber um blur gaussiano.

## Materiais

Classes semânticas devem alterar comportamento visual apenas quando houver benefício claro.

Categorias iniciais candidatas:

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

A lista é arquitetura candidata, não compromisso com IDs finais.

## Presets

### Lite

Preserva:

- sky/fog/grade;
- relação warm/cool;
- hierarquia emissiva;
- água com Fresnel simplificado;
- dither estável.

Pode cortar:

- shadows ou reduzir agressivamente;
- bloom;
- AO extra;
- taps;
- detalhe de normal da água;
- outputs/buffers não essenciais.

### Default

É a aparência oficial.

Deve concentrar orçamento em:

- atmosfera completa;
- uma solução de sombra próxima estável;
- água barata convincente;
- classes materiais;
- emissivos seletivos.

Efeito sem ganho claro no hardware modesto não entra.

### Showcase

Aumenta qualidade dentro da mesma arquitetura:

- shadow resolution/filter/distance maiores;
- water detail;
- contact darkening;
- bloom opcional, se provado;
- precisão extra quando realmente necessária.

Showcase não pode virar outro shaderpack.


## Estudo visual: atmosfera dark fantasy por profundidade

**Status: VISUAL RESEARCH — NON-NORMATIVE.**

Esta seção registra uma referência visual discutida em 2026-09-24. O material-fonte não é versionado no repositório e não constitui licença, dependência, especificação técnica ou alvo de cópia. O objetivo é preservar os princípios perceptivos observados antes que decisões de implementação sejam tomadas.

### Observações úteis

A referência reforça uma direção compatível com a identidade Reny:

- a sensação de escala vem principalmente da separação entre foreground, midground e background;
- atmospheric perspective forte pode carregar mais identidade que efeitos screen-space caros;
- sky, fog, exposição e color grading formam a maior parte do mood percebido;
- foreground deve preservar contraste e leitura local enquanto a distância perde contraste e detalhe progressivamente;
- mundo natural frio/desaturado pode reservar saturação e luminância para magia, lava, portais, Tensura e outros emissivos;
- água escura e integrada ao ambiente pode funcionar melhor que reflexos ostensivos;
- arquitetura distante ganha presença por silhueta e absorção atmosférica, sem exigir iluminação local complexa;
- noite pode ser muito escura desde que geometria e navegação próximas continuem legíveis.

### Guardrails extraídos da referência

Não promover a estética observada literalmente para o Default.

Em particular:

- não comprimir o mundo natural até uma paleta quase monocromática;
- não permitir que fog vire uma parede uniforme próxima da câmera;
- não aceitar black crush que destrua informação necessária ao gameplay;
- não confundir aparência volumétrica com requisito de volumetria raymarched;
- não inferir necessidade de SSR, GI, PBR completo ou passes dedicados apenas porque a referência parece visualmente rica.

A hipótese preferida é obter sensação equivalente com uma cadeia barata:

> sky/atmosfera → fog por distância/altura quando viável → exposição/tonemapping → iluminação direcional → água simples → sombras próximas → detalhe secundário

Essa ordem é uma **hipótese de retorno visual por custo**, não um contrato de pipeline.

### Promoção para decisão canônica

Qualquer princípio desta seção só deve virar requisito, parâmetro ou implementação depois de:

1. capability relevante ser confirmada no stack Minecraft 1.7.10 alvo;
2. existir protótipo mínimo reproduzível;
3. cenas comparáveis demonstrarem ganho visual;
4. benchmark mostrar custo aceitável em hardware modesto/iGPU;
5. movimento, noite e condições de baixa visibilidade preservarem gameplay;
6. a solução manter espaço visual para sobrenatural/emissivos dominarem quando necessário.

Até esses gates, esta seção deve orientar exploração visual, não arquitetura.

## Anti-objetivos

Não perseguir por padrão:

- “look BSL/Complementary/SEUS”;
- PBR generalizado;
- reflexos screen-space como demonstração técnica;
- volumetria pesada;
- lens flare/chromatic aberration;
- DoF ou motion blur permanentes;
- efeitos que prejudicam combate, navegação ou leitura de UI.

## Critério final

Uma técnica visual entra quando:

1. melhora uma cena canônica de gameplay;
2. preserva identidade Reny;
3. não cria artefatos materiais em movimento;
4. justifica custo e compatibilidade;
5. escala coerentemente entre Lite, Default e Showcase.
