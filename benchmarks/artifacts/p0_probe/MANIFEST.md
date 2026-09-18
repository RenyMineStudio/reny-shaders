# Reny Shaders — P0 Capability Probe Artifact Manifest

## Policy & Hygiene

Per `AGENTS.md` asset hygiene rules, binary image files (`.png`) are excluded from Git tracking to avoid repository bloat and unauthorized binary commits.

Screen captures generated during P0 testing are stored in `/tmp/opencode/p0_probe_artifacts/` (or locally via `P0_SCREENSHOT_DIR`) and verified via SHA-256 checksums and runtime logs.

---

## Verified Scenarios & Capture Manifest

All captures taken at **1280x720** resolution on the target stack:
- Minecraft 1.7.10 / Forge 10.13.4.1614 / OptiFine 1.7.10 HD U E7 / Java 8 (Temurin 1.8.0_312)
- GPU: Mesa Intel(R) Iris(R) Xe Graphics (ADL GT2) / OpenGL 4.6 Mesa 25.2.8
- Tested Commit: `2606f53099566b621ec3c6be2a84805109ee574b` (and final verified HEAD)

| Scenario ID | Artifact File | Probe Mode / Context | SHA-256 Digest | Gate & Observations |
|---|---|---|---|---|
| `STACK-OVERWORLD-DAY-STILL` | `exp_p0_stack_overworld_day_still.png` | Mode 0 (Baseline) | `378079ba925697d7dfc9245ef4c09d57a22839958784d12eb0da4563a623e1dc` | **PASS** — Overworld daytime rendering with terrain, water pool, sand dunes, acacia, tallgrass, and Mode 0 green badge |
| `STACK-OVERWORLD-DAY-MOTION` | `exp_p0_stack_overworld_day_motion.png` | Mode 0 (Baseline) | `bc9a27c00f6828551a37cce14686948adfc93b6e82a9394fa996c567e7c99558` | **PASS** — Camera translation (walking forward) and yaw rotation; stable rendering without tearing or geometry corruption |
| `STACK-OVERWORLD-NIGHT` | `exp_p0_stack_overworld_night.png` | Mode 0 (Baseline) | `2ba663673caeef81b83d810243e8bb4ba0ffcbbfa3cfc1d35ae672462e249451` | **PASS** — Overworld night rendering (/time set 18000), dark sky, stars, moon phase, and silhouette contrast |
| `STACK-RELOAD-GUI` | `exp_p0_stack_overworld_after_reload.png` | Mode 0 (Baseline) | `cb1f801e02ef63b469904d9c4de423c8e41eb521191060934cf5e1eec5b9487c` | **PASS** — In-game shader reload through settings menu; full FBO and resource reinitialization without crash |
| `CAP-UNIFORMS-HUD` | `exp_p0_cap_mode1_uniforms_hud.png` | Mode 1 (Capability) | `45ec92f33c373516624da6701bbcf75cb984ca3b1c6d7a46973ae071720857b2` | **PASS** — Diagnostic HUD verifying frameCounter heartbeat pulse, frameTime bar, sunPosition indicator, worldTime |
| `HISTORY-STILL-TRAIL` | `exp_p0_history_still_persistent_trail.png` | Mode 2 (History) | `491f0340b064c126d4ca9d1d6a666e5f917dfa74d22be3f50800b65104d49826` | **PASS** — colortex3Clear = false confirmed; orbiting cometary marker leaves smooth 25–30 frame decaying trail (prev * 0.96) |
| `HISTORY-MOTION` | `exp_p0_history_motion.png` | Mode 2 (History) | `e2a76f2bc886754ba1f80373ab1a3f6561cfcb7ef7156c70172e2cf3eefaece5` | **PASS** — Camera rotation and movement in Mode 2; persistent screen-space trail remains intact without corruption |
| `HISTORY-TELEPORT` | `exp_p0_history_after_teleport.png` | Mode 2 (History) | `fc4bbf6bc3eb8b2f901a1c322d76d4aaef1b701bc44c9b32c66cffea8d9dca4a` | **PASS (EVIDENCE)** — Teleport (/tp ~50 ~ ~50); demonstrates host does NOT clear history; camera delta check required in shader |
| `HISTORY-RESIZE` | `exp_p0_history_after_resize.png` | Mode 2 (History) | `c50f9076bc932fb2c262e316a7ce0397ee4daef12f45ec8f67e527f09c73082a` | **PASS** — Window resized to 1024x600; FBO and history buffer reallocated cleanly without stretching or leak |
| `HISTORY-FOV-CHANGE` | `exp_p0_history_after_fov_change.png` | Mode 2 (History) | `8fbc8d317075cbe838421c97a82c6fb586a1114b7e51c89feea30c00b70d4c9f` | **PASS** — FOV altered in options; projection matrix updated while screen-space history buffer remains valid |
| `CAP-MATERIAL-MAPPING` | `exp_p0_material_mapping_swatches.png` | Mode 3 (Material) | `1bf6bb3b9fa7298642a25b3061ce20f8623544eb4b5006b53a07dc57b427b235` | **PASS (VANILLA)** — mc_Entity.x attribute and block.properties false-coloring verified on stone, dirt, wood, water |
| `CAP-FORMATS-SPLIT` | `exp_p0_formats_fp16_r11f_split.png` | Mode 4 (Formats) | `7be3fe244a04d9c904724a4968df7eeb98638b9d8804683526549a1506bf4141` | **PASS** — Split screen rendering: colortex2 (RGBA16F, left) and colortex4 (R11F_G11F_B10F, right); no driver FBO errors |
| `CAP-DEFERRED-PASS` | `exp_p0_deferred_pass_confirmed.png` | Mode 5 (Deferred) | `a274a480dc3d4841913fe1c1a93e8276f7c8ec17fa42d76f874558231c6a6e8e` | **PASS** — Green top banner confirming deferred.fsh execution, RENY_DEFERRED_MAGIC write, and ping-pong buffer restore |
| `DIM-NETHER-SMOKE` | `exp_p0_dim_nether_smoke.png` | Nether (world-1) | `6c1032df4c50303da5744cb446d3e387c142c16f21ceb5f13459c55bdf9b9db2` | **PASS** — Nether transition via portal; world-1/ program selection active with red badge; netherrack, fire, lava |
| `DIM-NETHER-MOTION` | `exp_p0_dim_nether_motion.png` | Nether (world-1) | `f00c73200ffbb4459f42da9f9ad72d3eeb142b781b0a8767fa32c3f811568285` | **PASS** — Camera movement in Nether dimension with continuous rendering |
| `DIM-END-SMOKE` | `exp_p0_dim_end_smoke.png` | The End (world1) | `8f8b8a53e414c9c102c916ec0c5ecf052528c11e74167e411b438ea2d1c67623` | **PASS** — The End transition via end_portal; world1/ program selection active with purple badge; endstone, Enderman |
| `DIM-END-MOTION` | `exp_p0_dim_end_motion.png` | The End (world1) | `4c73ba3a58e0a75f0a0d9da9f38f903a4cf13bc20d778d9fa3ecae2617f69a53` | **PASS** — Camera motion in The End; void sky and lighting stable |
| `STACK-RETURN-OVERWORLD`| `exp_p0_stack_returned_overworld.png` | Overworld (return) | `7ad6a7989fa713919e8cfbeea3ba1608930a0d2fb89a42be486aee831b83d1e6` | **PASS** — Clean return to Overworld; FBO uninit and reinit confirmed, no cross-dimension state leakage |

---

## Reproduction Protocol

To reproduce the exact suite in a local environment:

```bash
# 1. Deploy shaderpack to the dedicated instance
python3 tools/harness/probe_runner.py --deploy-only

# 2. Launch the Minecraft client
./tools/harness/launch_probe_client.sh

# 3. Execute the automated validation suite
python3 tools/harness/run_p0_suite.py

# 4. Generate structured evaluation reports
python3 tools/harness/probe_runner.py
```
