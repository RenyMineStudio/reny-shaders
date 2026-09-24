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


## Estudo comparativo: showcase de múltiplos shaders

**Status: VISUAL RESEARCH / PRIOR ART — NON-NORMATIVE.**

Esta seção registra um segundo material visual discutido em 2026-09-24: um showcase que apresenta vários shaderpacks em composição semelhante. Os nomes abaixo são os rótulos exibidos no próprio vídeo; versão, preset, configuração, resolução, hardware, pipeline interno e custo real não foram verificados.

O material-fonte não é versionado no repositório e não constitui licença, dependência, benchmark, especificação técnica ou autorização para reutilizar código/assets. Ele serve apenas como **prior art perceptivo**: uma forma de decompor soluções visuais e identificar relações que podem ser reimplementadas de modo próprio, barato e compatível com o stack alvo.

### Limites da comparação

O showcase favorece especialmente:

- sunset/golden hour;
- céu e nuvens;
- fog/haze;
- foliage;
- silhuetas arquitetônicas grandes;
- contraste entre foreground e horizonte.

Ele não prova qualidade nem compatibilidade em:

- interiores;
- meio-dia;
- noite prolongada;
- água em diferentes ângulos/profundidades;
- chuva intensa;
- transparência e partículas;
- entidades e TESRs;
- glints/overlays;
- portais;
- dimensões modded;
- mão/itens em primeira pessoa;
- combate;
- movimento rápido de câmera;
- estabilidade temporal;
- frame time, bandwidth, VRAM compartilhada ou custo por pass.

Portanto:

> aparência observada = evidência visual da imagem final; técnica interna e custo = desconhecidos.

Nenhuma conclusão de eficiência deve ser derivada do showcase isoladamente.

### Eclipse

**Leitura visual:**

- céu com forte sensação de volume;
- boa separação quente/frio entre luz, ambiente e sombra;
- silhuetas arquitetônicas claras;
- foreground ainda preserva vegetação e informação local;
- sensação de escala forte sem depender apenas de blur/fog.

**Valor para Reny:**

- referência útil para separar céu claro/quente de ambiente mais frio;
- demonstra que silhueta + distribuição de luminância podem vender escala antes de efeitos complexos;
- reforça a importância de preservar cor local no foreground.

**Guardrails:**

- não assumir que nuvens volumosas exigem ou justificam volumetria pesada;
- não perseguir reflexos ou aparência de renderer moderno apenas porque aparecem convincentes;
- reproduzir a relação perceptiva, não a técnica presumida.

**Classificação Reny:** referência visual alta para céu, contraste e escala; implementação desconhecida.

### Reverie

**Leitura visual:**

- luz solar quente atravessa a cena com grande autoridade;
- foliage responde fortemente ao golden hour;
- composição muito coerente em torno da direção da luz;
- atmosfera integra céu, vegetação e arquitetura.

**Risco observado:**

- dominante amarela/laranja invade grande parte dos materiais;
- cor local pode ser subordinada demais ao estado do céu;
- o resultado pode ficar dependente de um horário específico para parecer correto.

**Valor para Reny:**

- estudar a hierarquia da luz e a forma como ela organiza foliage;
- preservar luz solar quente sem permitir que o renderer inteiro vire uma única temperatura.

**Classificação Reny:** referência moderada; útil para iluminação direcional, não para grading global.

### Bliss

**Leitura visual:**

- atmospheric perspective extremamente forte;
- objetos distantes perdem contraste e parecem inseridos em uma massa de ar;
- estruturas grandes adquirem escala por absorção atmosférica;
- paleta fria cria profundidade e separa bem planos distantes.

**Risco observado:**

- fog começa a dominar a cena relativamente cedo;
- midground pode perder informação útil;
- contraste médio reduzido pode prejudicar navegação e combate;
- dominante lavanda/roxa pode sobrepor identidade de materiais/biomas.

**Valor para Reny:**

Bliss é uma das referências mais importantes do showcase para o princípio:

> foreground limpo → midground progressivamente integrado → background fortemente absorvido → horizonte fundido com sky/fog.

O objetivo não é copiar sua densidade de fog, mas preservar a sensação de que **o ar possui espessura**.

**Classificação Reny:** referência muito alta para profundidade atmosférica, com fortes restrições de gameplay.

### Kappa

**Leitura visual:**

- silhueta monumental muito forte;
- céu e sol dominam a composição;
- alto contraste transforma arquitetura em massa legível.

**Risco observado:**

- foreground próximo de black crush em partes da cena;
- dominante quente muito agressiva;
- composição favorece captura cinematográfica mais do que leitura contínua de gameplay.

**Valor para Reny:**

- estudar silhueta contra céu;
- usar exposição e contraste para dar peso a arquitetura distante;
- evitar elevar esse comportamento a regra geral do Default.

**Classificação Reny:** referência moderada para composição; baixa como grading-base do Overworld.

### Voyager

**Leitura visual:**

- equilíbrio muito forte entre haze, foreground legível, céu, silhueta e cor local;
- separação de planos ocorre sem apagar prematuramente o midground;
- objetos próximos permanecem detalhados;
- background perde detalhe de forma progressiva e natural;
- horizonte participa da composição sem virar parede de fog.

**Valor para Reny:**

É a referência estrutural mais útil deste showcase para distribuição de informação:

> foreground detalhado/escuro → midground reconhecível → background progressivamente absorvido → sky suficientemente luminoso para sustentar silhueta.

Essa estrutura conversa diretamente com a política Reny:

> qualidade próxima → simplificação/fade → atmosfera distante.

O objetivo não é fazer “Reny = Voyager”, mas estudar o equilíbrio de profundidade e legibilidade.

**Classificação Reny:** referência visual muito alta para estrutura espacial do Default.

### Hysteria

**Leitura visual:**

- sobriedade cromática forte;
- atmosfera mais suja, antiga e pesada;
- arquitetura ganha presença dark fantasy sem precisar de saturação;
- haze e contraste carregam boa parte do mood.

**Risco observado:**

- desaturação/sepia excessivos podem apagar identidade de biomas;
- materiais diferentes podem convergir visualmente demais;
- uso constante reduziria o espaço para variação climática e temporal.

**Valor para Reny:**

Reforça o princípio:

> cor é recurso de hierarquia, não obrigação de preencher toda a imagem.

É especialmente relevante para preservar autoridade visual de magia, lava, portais, Tensura e emissivos.

**Classificação Reny:** referência alta para contenção cromática e peso dark fantasy.

### Amethyst Shaders

**Leitura visual:**

- personalidade cromática muito forte;
- céu fantástico e saturado;
- magenta/rosa e amarelo dominam a cena;
- luz e nuvens funcionam como espetáculo visual explícito.

**Risco observado no Overworld Default:**

- céu e grading podem competir com gameplay e materiais;
- pouca reserva visual para conteúdo sobrenatural posterior;
- identidade do mundo natural passa a depender demais da paleta fantástica.

**Valor para Reny:**

Baixo como referência do mundo ordinário, mas alto para momentos em que queremos quebrar deliberadamente a sobriedade:

- magia;
- skills Tensura;
- portais;
- rituais;
- eventos sobrenaturais;
- dimensões especiais;
- estados temporários de grande autoridade visual.

**Classificação Reny:** baixa para Default; alta como prior art de sobrenatural.

### Solas

**Leitura visual:**

- fog/atmosfera funcionam como grande massa cromática;
- profundidade é imediatamente perceptível;
- poucas relações visuais dominantes produzem identidade forte;
- sky, fog e exposure parecem suficientes para transformar radicalmente a cena.

**Risco observado no Overworld Default:**

- wash rosa/vermelho reduz informação material;
- uso contínuo pode cansar e tornar biomas pouco distintos;
- atmosfera de estado especial pode parecer permanente.

**Valor para Reny:**

Serve como referência para a hipótese de que uma dimensão ou estado extraordinário pode ganhar identidade com mudanças relativamente concentradas em:

- sky;
- fog color;
- fog density;
- exposure;
- light temperature;
- emissive hierarchy.

Isso é conceitualmente atraente porque pode permitir identidades dimensionais diferentes sem exigir renderers totalmente distintos, **se o stack alvo provar que essa parametrização é segura e barata**.

**Classificação Reny:** moderada para Default; alta como referência para dimensões/estados especiais.

### Síntese transversal

Nenhum shader do showcase deve ser tratado como modelo completo do Reny.

A combinação perceptiva mais útil é:

- **Voyager** → estrutura de profundidade e legibilidade;
- **Eclipse** → separação céu/luz/sombra e sensação de escala;
- **Bliss** → absorção atmosférica distante;
- **Hysteria** → contenção cromática e peso dark fantasy;
- **Amethyst / Solas** → referência de ruptura cromática para sobrenatural e dimensões especiais.

Essa síntese é conceitual. Ela não autoriza copiar shaders, curvas, assets, código ou presets.

O primeiro estudo visual registrado neste documento continua mais útil como referência **holística de mood dark fantasy**. Este segundo showcase é mais útil como **biblioteca comparativa de relações visuais**.

Em termos práticos:

> primeiro estudo = como o mundo deve fazer o jogador se sentir  
> segundo estudo = quais relações visuais merecem ser investigadas para chegar lá

### Hipóteses Reny derivadas do showcase

As seguintes hipóteses merecem experimentação futura, sem virar requisito agora.

#### H1 — Atmosfera como multiplicador de escala

Uma solução barata de sky + fog/haze + exposição pode aumentar percepção de escala mais do que adicionar vários efeitos locais.

**A provar:**

- custo no stack alvo;
- estabilidade durante movimento;
- comportamento em render distances diferentes;
- leitura de gameplay em chuva/noite;
- impacto em iGPU.

#### H2 — Preservar informação por distância

Distribuir detalhe de forma não uniforme pode entregar melhor qualidade percebida:

- near field: contraste, materiais e sombras úteis;
- mid field: redução controlada de contraste/detalhe;
- far field: silhueta, fog e atmosfera dominam.

Essa hipótese combina visualmente com a política de sombras já canônica, mas ainda precisa ser validada em cenas reais.

#### H3 — Temperatura separada vale mais que tint global

Luz solar quente + ambiente/sombra mais frios pode produzir riqueza visual sem recolorir todos os materiais com um único grade.

**Guardrail:** materiais e biomas próximos precisam manter identidade suficiente.

#### H4 — Sobriedade aumenta autoridade do sobrenatural

Se o mundo ordinário permanecer cromaticamente contido, eventos/objetos mágicos podem usar:

- mais saturação;
- maior contraste local;
- emissive strength;
- mudanças temporárias de fog/sky quando justificadas;

e parecer muito mais poderosos sem exigir efeitos caros permanentes.

#### H5 — Identidade dimensional por parâmetros compartilhados

Se o pipeline 1.7.10 permitir de forma comprovada, dimensões podem reutilizar o mesmo renderer e variar principalmente parâmetros artísticos, antes de receber técnicas exclusivas.

**Isso permanece hipótese até EXP-P0-DIM e validação no stack real.**

### Ordem conceitual de retorno visual

O showcase reforça, mas não prova, a seguinte ordem de investigação:

> sky/atmosfera → fog/haze → exposição/tonemapping → iluminação direcional → sombras próximas → água → emissivos/sobrenatural → detalhes secundários

Essa lista descreve **prioridade de experimentação perceptiva**, não ordem obrigatória de passes nem arquitetura de renderer.

### O que não concluir deste material

Não concluir que:

- Voyager, Eclipse, Bliss ou qualquer outro shader é “tecnicamente melhor”;
- determinado shader é mais rápido ou mais lento;
- nuvens observadas são volumétricas ou precisam ser implementadas da mesma forma;
- fog observada usa depth, height, raymarching ou qualquer algoritmo específico;
- reflexos observados justificam SSR;
- iluminação observada implica GI;
- aparência detalhada implica PBR;
- uma captura bonita garante estabilidade temporal;
- uma cena de sunset representa meio-dia, interiores, chuva, noite ou dimensões;
- o custo visual observado cabe no budget Reny.

### Política de uso como prior art

Ao revisitar estes shaders no futuro:

1. identificar primeiro a **relação visual** que queremos entender;
2. não transportar técnica presumida automaticamente;
3. verificar licença antes de estudar/reutilizar qualquer código ou asset;
4. preferir reimplementação independente de princípios gerais;
5. construir a hipótese mais barata compatível com o efeito percebido;
6. testar em cena canônica reproduzível;
7. medir GPU/frame time e estabilidade;
8. rejeitar a solução se o ganho visual marginal não justificar custo/compatibilidade.

### Promoção para decisão canônica

Nenhuma conclusão desta seção altera o Default, Lite, Showcase ou a arquitetura atual.

Uma hipótese extraída do showcase só pode virar decisão Reny depois de:

1. capability necessária ser confirmada no stack Minecraft 1.7.10 alvo;
2. implementação mínima própria existir;
3. comparação controlada mostrar ganho visual;
4. movimento/câmera não revelar instabilidade material;
5. gameplay próximo continuar legível;
6. condições difíceis — noite, chuva, interiores e transparência — não sofrerem regressão importante;
7. benchmark reproduzível justificar o custo;
8. hardware modesto/iGPU ser testado ou a ausência dessa evidência ficar explícita;
9. compatibilidade modded relevante ser exercitada;
10. Pedro aprovar qualquer mudança material da estética canônica.

Até lá, esta seção é **mapa de investigação visual**, não backlog de implementação.

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
