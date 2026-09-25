# Reny Shaders — P0 Capability Probe Report

- **Date:** `2026-09-22T18:44:12.306383+00:00`
- **Tested tree SHA (actually executed):** `cb02cce`
- **Report HEAD SHA:** `cb02cced113ef3ce6fd3b54aa69a7ed0278b63d3`
- **Working Tree Clean at report:** `Yes`
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

## Capability Matrix Results

| Capability | Status | Evidence | Notes |
|---|---|---|---|
| `EXP-P0-STACK` | **INCONCLUSIVE** | Insufficient log evidence for full stack execution | Overworld/Nether/End execution is evidenced by the P0 suite gates, not by this predicate alone |
| `deferred` | **INCONCLUSIVE** | Program 'deferred' absent from runtime log | Inter-pass data flow is a separate visual-manifest observation, not proven by load lines |
| `composite` | **INCONCLUSIVE** | Program 'composite' absent from runtime log | Runs at display resolution in E7; no scaling is claimed |
| `final` | **INCONCLUSIVE** | Program 'final' absent from runtime log | HUD content is evidenced by captures listed in the manifest |
| `shadow` | **INCONCLUSIVE** | Program 'shadow' absent from runtime log | Minimal shadow pass compiled without observed error |
| `world<id>` | **INCONCLUSIVE** | No target-specific world<id> runtime evidence | Generic renderer reset/reload lines do not prove dimension routing |
| `includes` | **INCONCLUSIVE** | No compile evidence confirming include resolution | Depth-10 nesting is parser documentation, not measured here |
| `profiles/options` | **INCONCLUSIVE** | profiles/options unproven: requires registration, at least two observed mode values, and persisted value; registration=False, transitions=[], persisted=optionsshaders.txt persists PROBE_MODE:0 | Mode-cycle persistence is additionally evidenced by suite mode_change gates |
| `block.properties (vanilla)` | **INCONCLUSIVE** | Vanilla mapping unproven: parser acceptance for expected IDs missing (['block.100', 'block.101', 'block.102', 'block.103', 'block.104', 'block.105', 'block.106', 'block.107', 'block.108', 'block.109']); source_error=None | mc_Entity.x transport is shader-source fact, verified visually in Mode 3 captures |
| `Forge mod block mapping` | **INCONCLUSIVE / UNPROVEN** | Modded block coverage not exercised in clean baseline environment | Requires modded workload; not claimed here |
| `custom textures / noise` | **INCONCLUSIVE / UNPROVEN** | Custom texture/noise assets not loaded or not logged in this probe run | Mechanism documented in E7 parser docs; assets unexercised in P0 minimal probe |
| `buffer_formats (FP16 / R11F)` | **INCONCLUSIVE** | No buffer format lines observed in log | FBO completeness is inferred from absence of errors plus rendered captures |
| `colortex_skip_clear` | **INCONCLUSIVE** | No 'clear disabled' line observed in log | Temporal persistence across frames is evidenced by Mode 2 captures in the manifest |
| `frameCounter / frameTime` | **INCONCLUSIVE** | Uniform exercise unproven: pack load unobserved; Mode 1 uniform exercise not observed | Heartbeat/bar motion is a visual-manifest observation, not a log predicate |
| `scale.<program>` | **REJECTED IN E7** | Inspected Shaders.class and ShaderPackParser.class in OptiFine E7 jar: scale.<program> symbols absent (composite-scale commit 5b0151b4 is 2018, post-E7) | Scaling added upstream in 2018, post-E7; E7 packs must not rely on it |

## Programs Compiled and Loaded in Target Runtime


## Runtime Errors Observed

**None observed in parsed log.** Absence of parsed errors is not a proof of zero driver warnings.

## Mandatory Gate Policy

- Mandatory FAIL capabilities: `(none)`
- Any entry above forces a non-zero evaluator exit code.
- `INCONCLUSIVE / UNPROVEN` is reported separately and is never promoted to PASS.


## Anecdotal Performance Observations (NOT a benchmark)

- F3 FPS values, when recorded during manual observation, are host anecdotes only.
- They must not be cited as GPU frame-time conclusions.

