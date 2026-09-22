# Reny Shaders — P0 Capability Probe Screenshot Manifest

- **Suite tested tree SHA:** `30d6451fcbf4e9717cae3c5d8369fcbfb2e75461`
- **Report/documentation tree SHA:** `93fae1b832a1d63656398f93a766540d127ccbd2`
- **Generated:** `2026-09-22T17:48:45.037500+00:00`
- **Policy:** Binaries are excluded from Git per `AGENTS.md` asset hygiene rules.
- **Screenshot dir (configurable via P0_SCREENSHOT_DIR):** `/tmp/opencode/p0_probe_artifacts`

## Gate Results

| Gate | Status | Evidence | Error |
|---|---|---|---|
| `client_window_present` | **PASS** | Minecraft window active (ID: 100663298) |  |
| `player_in_game_fixture` | **FAIL** | Player not verifiably in-game at suite start; aborting | no fresh server confirmation for `Seed:` after four attempts |

The suite intentionally stopped before screenshot, dimension, reload, resize, movement, and history gates. No visual PASS is claimed from this run.

## Capture Records

| Scenario | Resolution | SHA-256 Digest | Observation / Gate |
|---|---|---|---|

## Semantic MCP Preflight

- `tools/list`: **PASS**; the project-local `minecraft-dev` MCP launcher exposed the generic tools.
- `minecraft_ping`: **INCONCLUSIVE / BRIDGE_UNAVAILABLE** — `ECONNREFUSED 127.0.0.1:18731`.
- `minecraft_get_client_state`: **INCONCLUSIVE / BRIDGE_UNAVAILABLE** — `ECONNREFUSED 127.0.0.1:18731`.
- The MCP bridge was not loaded in the Forge instance; this is not semantic runtime evidence.

## Reproduction Instruction

```bash
# 1. Launch dedicated probe instance
./tools/harness/launch_probe_client.sh

# 2. Run semantic preflight when the shared bridge is available
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"minecraft_ping","arguments":{}}}' \
  | node ../minecraft-dev-toolkit/mcp/src/index.js

# 3. Run the P0 validation suite (records tested_tree_sha, fail-closed)
python3 tools/harness/run_p0_suite.py --commit-sha 30d6451fcbf4e9717cae3c5d8369fcbfb2e75461

# 4. Evaluate capabilities from evidence (explicit exit code)
python3 tools/harness/probe_runner.py --tested-sha 93fae1b832a1d63656398f93a766540d127ccbd2
```
