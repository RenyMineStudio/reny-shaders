# Reny Shaders — P0 Capability Probe Report

- **Date:** `2026-09-22T17:50:47.374613+00:00`
- **Tested tree SHA (actually executed):** `93fae1b832a1d63656398f93a766540d127ccbd2`
- **Report HEAD SHA:** `93fae1b832a1d63656398f93a766540d127ccbd2`
- **Working Tree Clean at report:** `No`
- **Evidence delta allowlisted-only:** `Yes`
- **Evidence delta files:** `(none — reports generated on tested tree)`
- **Evidence delta error:** `(none)`
- **PROBE_MODE persisted at evaluation:** `0`
- **Minecraft:** `1.7.10`
- **Forge:** `10.13.4.1614`
- **OptiFine:** `1.7.10 HD U E7`
- **Java Runtime:** `openjdk version "1.8.0_312"`
- **GPU:** `Mesa Intel(R) Iris(R) Xe Graphics (ADL GT2)`
- **Driver / GL:** `4.6 (Compatibility Profile) Mesa 25.2.8-0ubuntu0.24.04.2`
- **GLSL Version:** `4.60`

## Provenance

Tested tree SHA is the tree the suite executed. If the report HEAD is ahead, the `tested_tree_sha..report_head_sha` delta must contain only allowlisted evidence files (`benchmarks/artifacts/p0_probe/MANIFEST.md, benchmarks/reports/p0_probe_report.json, benchmarks/reports/p0_probe_report.md`). A wider delta invalidates the provenance claim.

## Suite Execution Gate

- **Status:** **FAIL**
- **Suite tested tree SHA:** `30d6451fcbf4e9717cae3c5d8369fcbfb2e75461`
- **Failed gate:** `player_in_game_fixture`
- **Exit code:** `1`
- **Evidence:** Minecraft window existed, but fresh `Seed:` server confirmation was absent after four attempts.
- **Visual gates executed:** `No`; no screenshot, dimension, reload, resize, movement, or history PASS is claimed from this run.
- **Report tree relation:** `93fae1b832a1d63656398f93a766540d127ccbd2` is a subsequent documentation-only amendment before report generation.
- **MCP preflight:** `tools/list` PASS; `minecraft_ping` and `minecraft_get_client_state` returned `ECONNREFUSED 127.0.0.1:18731` and remain `INCONCLUSIVE / BRIDGE_UNAVAILABLE`.

## Capability Matrix Results

| Capability | Status | Evidence | Notes |
|---|---|---|---|
| `EXP-P0-STACK` | **PASS** | Pack 'Reny-Capability-Probe' loaded; framebuffer created; 54 distinct program entries with 0 observed errors | Overworld/Nether/End execution is evidenced by the P0 suite gates, not by this predicate alone |
| `deferred` | **PASS** | Log shows 'Program loaded: deferred' and 'deferred_last' restore entry | Inter-pass data flow is a separate visual-manifest observation, not proven by load lines |
| `composite` | **PASS** | Log shows 'Program loaded: composite' (22 flip lines observed) | Runs at display resolution in E7; no scaling is claimed |
| `final` | **PASS** | Log shows 'Program loaded: final' | HUD content is evidenced by captures listed in the manifest |
| `shadow` | **PASS** | Log shows 'Program loaded: shadow' | Minimal shadow pass compiled without observed error |
| `includes` | **PASS** | Repo shaders contain #include lines and compiled with 0 observed errors | Depth-10 nesting is parser documentation, not measured here |
| `profiles/options` | **INCONCLUSIVE** | profiles/options unproven: requires registration, at least two observed mode values, and persisted value; registration=False, transitions=[], persisted=optionsshaders.txt persists PROBE_MODE:0 | Mode-cycle persistence is additionally evidenced by suite mode_change gates |
| `block.properties (vanilla)` | **INCONCLUSIVE** | Vanilla mapping unproven: parser acceptance for expected IDs missing (['block.100', 'block.101', 'block.102', 'block.103', 'block.104', 'block.105', 'block.106', 'block.107', 'block.108', 'block.109']); source_error=None | mc_Entity.x transport is shader-source fact, verified visually in Mode 3 captures |
| `Forge mod block mapping` | **INCONCLUSIVE / UNPROVEN** | Parser tolerated namespaced keys but emitted 27 'Block not found' warnings; modded mapping not exercised | Requires modded workload; not claimed here |
| `custom textures / noise` | **INCONCLUSIVE / UNPROVEN** | Custom texture/noise assets not loaded or not logged in this probe run | Mechanism documented in E7 parser docs; assets unexercised in P0 minimal probe |
| `buffer_formats (FP16 / R11F)` | **PASS** | Log shows colortex2 format: RGBA16F and colortex4 format: R11F_G11F_B10F with no observed FBO error | FBO completeness is inferred from absence of errors plus rendered captures |
| `colortex_skip_clear` | **PASS** | Log shows 'colortex3 clear disabled' | Temporal persistence across frames is evidenced by Mode 2 captures in the manifest |
| `frameCounter / frameTime` | **INCONCLUSIVE** | Uniform exercise unproven: Mode 1 uniform exercise not observed | Heartbeat/bar motion is a visual-manifest observation, not a log predicate |
| `scale.<program>` | **REJECTED IN E7** | Inspected Shaders.class and ShaderPackParser.class in OptiFine E7 jar: scale.<program> symbols absent (composite-scale commit 5b0151b4 is 2018, post-E7) | Scaling added upstream in 2018, post-E7; E7 packs must not rely on it |

## Programs Compiled and Loaded in Target Runtime

- `composite`
- `composite`
- `composite`
- `composite`
- `composite]]></log4j:Message>`
- `composite]]></log4j:Message>`
- `composite]]></log4j:Message>`
- `composite]]></log4j:Message>`
- `composite]]></log4j:Message>`
- `composite]]></log4j:Message>`
- `composite]]></log4j:Message>`
- `composite_last`
- `composite_last`
- `composite_last`
- `composite_last`
- `composite_last]]></log4j:Message>`
- `composite_last]]></log4j:Message>`
- `composite_last]]></log4j:Message>`
- `composite_last]]></log4j:Message>`
- `composite_last]]></log4j:Message>`
- `composite_last]]></log4j:Message>`
- `composite_last]]></log4j:Message>`
- `deferred`
- `deferred`
- `deferred`
- `deferred`
- `deferred]]></log4j:Message>`
- `deferred]]></log4j:Message>`
- `deferred]]></log4j:Message>`
- `deferred]]></log4j:Message>`
- `deferred]]></log4j:Message>`
- `deferred]]></log4j:Message>`
- `deferred]]></log4j:Message>`
- `deferred_last`
- `deferred_last`
- `deferred_last`
- `deferred_last`
- `deferred_last]]></log4j:Message>`
- `deferred_last]]></log4j:Message>`
- `deferred_last]]></log4j:Message>`
- `deferred_last]]></log4j:Message>`
- `deferred_last]]></log4j:Message>`
- `deferred_last]]></log4j:Message>`
- `deferred_last]]></log4j:Message>`
- `final`
- `final`
- `final`
- `final`
- `final]]></log4j:Message>`
- `final]]></log4j:Message>`
- `final]]></log4j:Message>`
- `final]]></log4j:Message>`
- `final]]></log4j:Message>`
- `final]]></log4j:Message>`
- `final]]></log4j:Message>`
- `gbuffers_basic`
- `gbuffers_basic`
- `gbuffers_basic`
- `gbuffers_basic`
- `gbuffers_basic]]></log4j:Message>`
- `gbuffers_basic]]></log4j:Message>`
- `gbuffers_basic]]></log4j:Message>`
- `gbuffers_basic]]></log4j:Message>`
- `gbuffers_basic]]></log4j:Message>`
- `gbuffers_basic]]></log4j:Message>`
- `gbuffers_basic]]></log4j:Message>`
- `gbuffers_block`
- `gbuffers_block`
- `gbuffers_block`
- `gbuffers_block`
- `gbuffers_block]]></log4j:Message>`
- `gbuffers_block]]></log4j:Message>`
- `gbuffers_block]]></log4j:Message>`
- `gbuffers_block]]></log4j:Message>`
- `gbuffers_block]]></log4j:Message>`
- `gbuffers_block]]></log4j:Message>`
- `gbuffers_block]]></log4j:Message>`
- `gbuffers_clouds`
- `gbuffers_clouds`
- `gbuffers_clouds`
- `gbuffers_clouds`
- `gbuffers_clouds]]></log4j:Message>`
- `gbuffers_clouds]]></log4j:Message>`
- `gbuffers_clouds]]></log4j:Message>`
- `gbuffers_clouds]]></log4j:Message>`
- `gbuffers_clouds]]></log4j:Message>`
- `gbuffers_clouds]]></log4j:Message>`
- `gbuffers_clouds]]></log4j:Message>`
- `gbuffers_damagedblock`
- `gbuffers_damagedblock`
- `gbuffers_damagedblock`
- `gbuffers_damagedblock`
- `gbuffers_damagedblock]]></log4j:Message>`
- `gbuffers_damagedblock]]></log4j:Message>`
- `gbuffers_damagedblock]]></log4j:Message>`
- `gbuffers_damagedblock]]></log4j:Message>`
- `gbuffers_damagedblock]]></log4j:Message>`
- `gbuffers_damagedblock]]></log4j:Message>`
- `gbuffers_damagedblock]]></log4j:Message>`
- `gbuffers_entities`
- `gbuffers_entities`
- `gbuffers_entities`
- `gbuffers_entities`
- `gbuffers_entities]]></log4j:Message>`
- `gbuffers_entities]]></log4j:Message>`
- `gbuffers_entities]]></log4j:Message>`
- `gbuffers_entities]]></log4j:Message>`
- `gbuffers_entities]]></log4j:Message>`
- `gbuffers_entities]]></log4j:Message>`
- `gbuffers_entities]]></log4j:Message>`
- `gbuffers_hand`
- `gbuffers_hand`
- `gbuffers_hand`
- `gbuffers_hand`
- `gbuffers_hand]]></log4j:Message>`
- `gbuffers_hand]]></log4j:Message>`
- `gbuffers_hand]]></log4j:Message>`
- `gbuffers_hand]]></log4j:Message>`
- `gbuffers_hand]]></log4j:Message>`
- `gbuffers_hand]]></log4j:Message>`
- `gbuffers_hand]]></log4j:Message>`
- `gbuffers_skybasic`
- `gbuffers_skybasic`
- `gbuffers_skybasic`
- `gbuffers_skybasic`
- `gbuffers_skybasic]]></log4j:Message>`
- `gbuffers_skybasic]]></log4j:Message>`
- `gbuffers_skybasic]]></log4j:Message>`
- `gbuffers_skybasic]]></log4j:Message>`
- `gbuffers_skybasic]]></log4j:Message>`
- `gbuffers_skybasic]]></log4j:Message>`
- `gbuffers_skybasic]]></log4j:Message>`
- `gbuffers_skytextured`
- `gbuffers_skytextured`
- `gbuffers_skytextured`
- `gbuffers_skytextured`
- `gbuffers_skytextured]]></log4j:Message>`
- `gbuffers_skytextured]]></log4j:Message>`
- `gbuffers_skytextured]]></log4j:Message>`
- `gbuffers_skytextured]]></log4j:Message>`
- `gbuffers_skytextured]]></log4j:Message>`
- `gbuffers_skytextured]]></log4j:Message>`
- `gbuffers_skytextured]]></log4j:Message>`
- `gbuffers_terrain`
- `gbuffers_terrain`
- `gbuffers_terrain`
- `gbuffers_terrain`
- `gbuffers_terrain]]></log4j:Message>`
- `gbuffers_terrain]]></log4j:Message>`
- `gbuffers_terrain]]></log4j:Message>`
- `gbuffers_terrain]]></log4j:Message>`
- `gbuffers_terrain]]></log4j:Message>`
- `gbuffers_terrain]]></log4j:Message>`
- `gbuffers_terrain]]></log4j:Message>`
- `gbuffers_textured`
- `gbuffers_textured`
- `gbuffers_textured`
- `gbuffers_textured`
- `gbuffers_textured]]></log4j:Message>`
- `gbuffers_textured]]></log4j:Message>`
- `gbuffers_textured]]></log4j:Message>`
- `gbuffers_textured]]></log4j:Message>`
- `gbuffers_textured]]></log4j:Message>`
- `gbuffers_textured]]></log4j:Message>`
- `gbuffers_textured]]></log4j:Message>`
- `gbuffers_textured_lit`
- `gbuffers_textured_lit`
- `gbuffers_textured_lit`
- `gbuffers_textured_lit`
- `gbuffers_textured_lit]]></log4j:Message>`
- `gbuffers_textured_lit]]></log4j:Message>`
- `gbuffers_textured_lit]]></log4j:Message>`
- `gbuffers_textured_lit]]></log4j:Message>`
- `gbuffers_textured_lit]]></log4j:Message>`
- `gbuffers_textured_lit]]></log4j:Message>`
- `gbuffers_textured_lit]]></log4j:Message>`
- `gbuffers_water`
- `gbuffers_water`
- `gbuffers_water`
- `gbuffers_water`
- `gbuffers_water]]></log4j:Message>`
- `gbuffers_water]]></log4j:Message>`
- `gbuffers_water]]></log4j:Message>`
- `gbuffers_water]]></log4j:Message>`
- `gbuffers_water]]></log4j:Message>`
- `gbuffers_water]]></log4j:Message>`
- `gbuffers_water]]></log4j:Message>`
- `gbuffers_weather`
- `gbuffers_weather`
- `gbuffers_weather`
- `gbuffers_weather`
- `gbuffers_weather]]></log4j:Message>`
- `gbuffers_weather]]></log4j:Message>`
- `gbuffers_weather]]></log4j:Message>`
- `gbuffers_weather]]></log4j:Message>`
- `gbuffers_weather]]></log4j:Message>`
- `gbuffers_weather]]></log4j:Message>`
- `gbuffers_weather]]></log4j:Message>`
- `shadow`
- `shadow`
- `shadow`
- `shadow`
- `shadow]]></log4j:Message>`
- `shadow]]></log4j:Message>`
- `shadow]]></log4j:Message>`
- `shadow]]></log4j:Message>`
- `shadow]]></log4j:Message>`
- `shadow]]></log4j:Message>`
- `shadow]]></log4j:Message>`
- `world-1/composite`
- `world-1/composite`
- `world-1/composite]]></log4j:Message>`
- `world-1/final`
- `world-1/final`
- `world-1/final]]></log4j:Message>`
- `world-1/gbuffers_basic`
- `world-1/gbuffers_basic`
- `world-1/gbuffers_basic]]></log4j:Message>`
- `world-1/gbuffers_textured`
- `world-1/gbuffers_textured`
- `world-1/gbuffers_textured]]></log4j:Message>`
- `world1/composite`
- `world1/composite]]></log4j:Message>`
- `world1/final`
- `world1/final]]></log4j:Message>`
- `world1/gbuffers_basic`
- `world1/gbuffers_basic]]></log4j:Message>`
- `world1/gbuffers_textured`
- `world1/gbuffers_textured]]></log4j:Message>`

## Runtime Errors Observed

**None observed in parsed log.** Absence of parsed errors is not a proof of zero driver warnings.

## Mandatory Gate Policy

- Mandatory FAIL capabilities: `world<id> (missing)`
- Any entry above forces a non-zero evaluator exit code.
- `INCONCLUSIVE / UNPROVEN` is reported separately and is never promoted to PASS.


## Anecdotal Performance Observations (NOT a benchmark)

- F3 FPS values, when recorded during manual observation, are host anecdotes only.
- They must not be cited as GPU frame-time conclusions.
