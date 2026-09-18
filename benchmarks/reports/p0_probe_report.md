# Reny Shaders — P0 Capability Probe Report

- **Date:** `2026-09-18T17:15:04.654911+00:00`
- **Commit SHA:** `2606f53099566b621ec3c6be2a84805109ee574b`
- **Working Tree Clean:** `Yes`
- **Minecraft:** `1.7.10`
- **Forge:** `10.13.4.1614`
- **OptiFine:** `1.7.10 HD U E7`
- **Java Runtime:** `openjdk version "1.8.0_312"`
- **GPU:** `Mesa Intel(R) Iris(R) Xe Graphics (ADL GT2)`
- **Driver / GL:** `4.6 (Compatibility Profile) Mesa 25.2.8-0ubuntu0.24.04.2`
- **GLSL Version:** `4.60`

## Capability Matrix Results

| Capability | Status | Evidence | Notes |
|---|---|---|---|
| `EXP-P0-STACK` | **PASS** | Pack 'Reny-Capability-Probe' loaded; framebuffer created; 19 programs compiled cleanly with 0 errors | Verified in Overworld, Nether, and End with real client execution |
| `deferred` | **PASS** | Log confirms 'Program loaded: deferred', buffer flip (0, 4), and 'deferred_last' restore | Verified visually via green diagnostic banner in Mode 5 |
| `composite` | **PASS** | Log confirms 'Program loaded: composite' (flips: 2) | Runs at full display resolution in E7 |
| `final` | **PASS** | Log confirms 'Program loaded: final' | Displays probe HUD, mode badges, and composite buffer outputs |
| `shadow` | **PASS** | Log confirms 'Program loaded: shadow' | Minimal shadow pass compiled cleanly without error |
| `includes` | **PASS** | Shaders using root-based (#include '/lib/...') and relative includes compiled with 0 errors | Nested includes up to depth 10 supported by OptiFine preprocessor |
| `world<id>` | **PASS** | OptiFine scanned and registered: Worlds: -1, 1 | World folder completely replaces root folder for programs in that dimension |
| `profiles/options` | **PASS** | shaders.properties parsed without error; PROBE_MODE option registered and GUI screens rendered | Verified in-game with localized labels from en_US.lang |
| `block.properties (vanilla)` | **PASS** | Log confirms 'Parsing block mappings: /shaders/block.properties'; vanilla IDs 100-109 parsed cleanly | Mapped IDs (100-109) passed to vertex stage via mc_Entity.x attribute |
| `Forge mod block mapping` | **INCONCLUSIVE / UNPROVEN** | Parser mechanism accepted, but target mods absent in baseline (9 'Block not found' warnings); modded mapping not exercised | Parser functions without crashing; full modded coverage requires modded workload |
| `custom textures / noise` | **INCONCLUSIVE / UNPROVEN** | Custom texture/noise assets not loaded or not logged in this probe run | Mechanism documented in E7 doc/shaders.properties; assets unexercised in P0 minimal probe |
| `buffer_formats (FP16 / R11F)` | **PASS** | Log confirms colortex2 format: RGBA16F (RGBA16F) and colortex4 format: R11F_G11F_B10F (R11F_G11F_B10F) without FBO error | Accepted by Mesa Intel Iris Xe driver without GL_FRAMEBUFFER_INCOMPLETE |
| `colortex_skip_clear` | **PASS** | Log confirms 'colortex3 clear disabled'; visual persistence confirmed across frames | Enables persistent temporal history buffer in E7 |
| `frameCounter / frameTime` | **PASS** | Built-in uniforms frameCounter and frameTime referenced and rendered live on HUD without error | Visual heartbeat and frame time bar responsive in Mode 1 |
| `scale.<program>` | **REJECTED IN E7** | Inspected Shaders.class and ShaderPackParser.class in OptiFine E7 jar: scale.<program> symbols absent (commit 5b0151b4 was in 2018, post-E7) | OptiFine 1.7.10 E7 does not support program scaling; feature added in 2018 post-E7 |

## Programs Compiled and Loaded in Target Runtime

- `composite`
- `composite_last`
- `deferred`
- `deferred_last`
- `final`
- `gbuffers_basic`
- `gbuffers_block`
- `gbuffers_clouds`
- `gbuffers_damagedblock`
- `gbuffers_entities`
- `gbuffers_hand`
- `gbuffers_skybasic`
- `gbuffers_skytextured`
- `gbuffers_terrain`
- `gbuffers_textured`
- `gbuffers_textured_lit`
- `gbuffers_water`
- `gbuffers_weather`
- `shadow`

## Runtime Errors Observed

**None.** All shader programs compiled and initialized cleanly.

## Anecdotal Performance Observations

- Overworld (Baseline Mode 0): ~160–191 FPS (observed via F3 screen)
- Overworld (Diagnostic HUD Mode 1): ~120–136 FPS (observed via F3 screen)
- Nether (DIM -1): ~140–165 FPS (observed via F3 screen)
- The End (DIM 1): ~170–195 FPS (observed via F3 screen)
- *Notice:* FPS values are informational host observations and must not be treated as isolated GPU timer benchmarks.
