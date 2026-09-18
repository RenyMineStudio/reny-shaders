# Reny Shaders — P0 Capability Probe Report

- **Date:** `2026-09-18T08:46:08.655705+00:00`
- **Commit SHA:** `fe4e8a2d061b544db71770be063a8a48a8377b8d`
- **Minecraft:** `1.7.10`
- **Forge:** `10.13.4.1614`
- **OptiFine:** `1.7.10 HD U E7`
- **Java Runtime:** `openjdk version "1.8.0_312"`
- **GPU:** `Mesa Intel(R) Iris(R) Xe Graphics (ADL GT2)`
- **Driver / GL:** `4.6 (Compatibility Profile) Mesa 25.2.8-0ubuntu0.24.04.2`
- **GLSL Version:** `4.60`

## Capability Matrix Results

| Capability | Status | Evidence / Notes |
|---|---|---|
| `EXP-P0-STACK` | **PASS** | Pack 'Reny-Capability-Probe' loaded successfully; 19 programs compiled without error |
| `deferred` | **PASS** | Program loaded: deferred confirmed in E7 runtime log |
| `composite` | **PASS** | Program loaded: composite confirmed in E7 runtime log |
| `final` | **PASS** | Program loaded: final confirmed in E7 runtime log |
| `shadow` | **PASS** | Program loaded: shadow confirmed in E7 runtime log |
| `includes` | **PASS** | Shaders using relative and root-based #include directives compiled without error |
| `world<id>` | **PASS** | OptiFine scanned and logged: Worlds: -1, 1 |
| `profiles/options` | **PASS** | shaders.properties parsed without error; PROBE_MODE option registered |
| `block.properties` | **PASS** | block.properties parsed; mapped IDs (100-122) active on mc_Entity.x attribute |
| `buffer_formats` | **PASS** | FBO formats accepted by driver without GL_FRAMEBUFFER_INCOMPLETE or format failure |
| `colortex_skip_clear` | **PASS** | colortex3Clear = false recognized; buffer persistence active in composite stage |
| `scale.<program>` | **REJECTED** | Bytecode analysis of OptiFine E7 Shaders.class confirms scale.<program> is absent in 1.7.10 E7 (historical commit 5b0151b4 in 2018 is post-E7) |

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
