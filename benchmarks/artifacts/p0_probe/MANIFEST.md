# Reny Shaders — P0 Capability Probe Screenshot Manifest

- **Tested tree SHA:** `HEAD`
- **HEAD at report time:** `37434ae71441509645924dbc4a6101834306760c`
- **Generated:** `2026-09-22T18:21:13.913219+00:00`
- **Policy:** Binaries are excluded from Git per `AGENTS.md` asset hygiene rules.
- **Screenshot dir (configurable via P0_SCREENSHOT_DIR):** `/tmp/opencode/p0_probe_artifacts`

## Gate Results

| Gate | Status | Evidence | Error |
|---|---|---|---|
| `client_window_present` | **PASS** | Minecraft window active (ID: 100663298) |  |
| `player_in_game_fixture` | **FAIL** | Player not verifiably in-game at suite start; aborting | not verifiably in-game after 4 attempts: command '/seed' unverified after 2 attempts: attempt 2: no server confirmation: no fresh match for 'Seed:' within 10.0s (error: timeout waiting for fresh log pattern 'Seed:') |

## Capture Records

| Scenario | Resolution | SHA-256 Digest | Observation / Gate |
|---|---|---|---|

## Reproduction Instruction

```bash
# 1. Launch dedicated probe instance
./tools/harness/launch_probe_client.sh

# 2. Run the P0 validation suite (records tested_tree_sha, fail-closed)
python3 tools/harness/run_p0_suite.py

# 3. Evaluate capabilities from fresh evidence (explicit exit code)
python3 tools/harness/probe_runner.py
```
