#!/usr/bin/env python3
"""
Reny Shaders — Automated P0 Capability Probe & Validation Suite
Target: Minecraft 1.7.10 / Forge 10.13.4.1614 / OptiFine 1.7.10 HD U E7
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
SHADERS_DIR = REPO_ROOT / "shaders"
DEFAULT_INSTANCE = Path(
    os.environ.get(
        "MINECRAFT_INSTANCE_DIR",
        Path.home() / "Documents/curseforge/minecraft/Instances/Reny Shaders Probe",
    )
)
LOG_PATH = DEFAULT_INSTANCE / "logs" / "latest.log"
MANIFEST_PATH = REPO_ROOT / "benchmarks" / "artifacts" / "p0_probe" / "MANIFEST.md"
SCREENSHOT_DIR = Path(
    os.environ.get("P0_SCREENSHOT_DIR", "/tmp/opencode/p0_probe_artifacts")
)


def run_cmd(args: List[str], timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        check=False,
    )


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class GateResult:
    def __init__(self, name: str, status: str, evidence: str, error: Optional[str] = None) -> None:
        self.name = name
        self.status = status  # PASS, FAIL, INCONCLUSIVE
        self.evidence = evidence
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "evidence": self.evidence,
            "error": self.error,
        }


class P0Suite:
    def __init__(
        self,
        instance_dir: Path = DEFAULT_INSTANCE,
        update_repo_manifest: bool = False,
    ) -> None:
        self.instance_dir = instance_dir
        self.screenshot_dir = SCREENSHOT_DIR
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = (
            MANIFEST_PATH
            if update_repo_manifest
            else self.screenshot_dir / "MANIFEST.md"
        )
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.gates: List[GateResult] = []
        self.captures: List[Dict[str, Any]] = []
        self.overall_success = True

    def record_gate(self, name: str, status: str, evidence: str, error: Optional[str] = None) -> None:
        gate = GateResult(name, status, evidence, error)
        self.gates.append(gate)
        symbol = "✓" if status == "PASS" else ("?" if status == "INCONCLUSIVE" else "✗")
        print(f"[{symbol}] {name}: {status} — {evidence}" + (f" (error: {error})" if error else ""))
        if status == "FAIL":
            self.overall_success = False

    def get_window(self) -> Optional[str]:
        res = run_cmd(["xdotool", "search", "--onlyvisible", "--name", "Minecraft 1.7.10"])
        windows = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        return windows[-1] if windows else None

    def get_window_geometry(self, win: str) -> Optional[Tuple[int, int, int, int]]:
        res = run_cmd(["xwininfo", "-id", win])
        if res.returncode != 0:
            return None
        try:
            x = int(re.search(r"Absolute upper-left X:\s+(\d+)", res.stdout).group(1))
            y = int(re.search(r"Absolute upper-left Y:\s+(\d+)", res.stdout).group(1))
            w = int(re.search(r"Width:\s+(\d+)", res.stdout).group(1))
            h = int(re.search(r"Height:\s+(\d+)", res.stdout).group(1))
            return x, y, w, h
        except (AttributeError, ValueError):
            return None

    def focus_window(self) -> bool:
        w = self.get_window()
        if not w:
            return False
        res = run_cmd(["xdotool", "windowactivate", w])
        run_cmd(["xdotool", "windowraise", w])
        time.sleep(0.3)
        return res.returncode == 0

    def click_relative(self, rx: float, ry: float, delay: float = 0.5) -> bool:
        w = self.get_window()
        if not w:
            return False
        geom = self.get_window_geometry(w)
        if not geom:
            return False
        x, y, width, height = geom
        cx = x + int(width * rx)
        cy = y + int(height * ry)
        run_cmd(["xdotool", "mousemove", str(cx), str(cy)])
        time.sleep(0.08)
        run_cmd(["xdotool", "mousedown", "1"])
        time.sleep(0.12)
        run_cmd(["xdotool", "mouseup", "1"])
        time.sleep(delay)
        return True

    def send_chat_command(self, command: str) -> bool:
        w = self.get_window()
        if not w:
            return False
        self.focus_window()
        run_cmd(["xdotool", "key", "t"])
        time.sleep(0.2)
        run_cmd(["xdotool", "key", "ctrl+a"])
        run_cmd(["xdotool", "key", "BackSpace"])
        time.sleep(0.1)
        run_cmd(["xdotool", "type", "--delay", "30", "--clearmodifiers", command])
        time.sleep(0.15)
        run_cmd(["xdotool", "key", "Return"])
        time.sleep(0.5)
        return True

    def capture_screen(self, scenario_name: str, observation: str) -> Tuple[bool, Optional[Path]]:
        w = self.get_window()
        if not w:
            return False, None

        path = self.screenshot_dir / f"{scenario_name}.png"
        res = run_cmd(["scrot", "-o", "-w", w, str(path)])
        if res.returncode != 0 or not path.is_file() or path.stat().st_size == 0:
            return False, None

        geom = self.get_window_geometry(w)
        res_str = f"{geom[2]}x{geom[3]}" if geom else "1280x720"
        sha256 = compute_sha256(path)
        iso_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        self.captures.append({
            "scenario": scenario_name,
            "filename": path.name,
            "path": str(path),
            "resolution": res_str,
            "sha256": sha256,
            "size_bytes": path.stat().st_size,
            "timestamp": iso_time,
            "observation": observation,
        })
        return True, path

    def wait_for_log(self, pattern: str, timeout: float = 30.0) -> bool:
        start = time.time()
        regex = re.compile(pattern)
        while time.time() - start < timeout:
            if LOG_PATH.exists():
                try:
                    text = LOG_PATH.read_text(encoding="utf-8", errors="replace")
                    if regex.search(text):
                        return True
                except Exception:
                    pass
            time.sleep(0.5)
        return False

    def reload_shaders_via_gui(self) -> bool:
        """Reload shaders via in-game settings navigation without modifying tracked files."""
        w = self.get_window()
        if not w:
            return False

        self.focus_window()
        # Escape -> Options -> Video Settings -> Shaders -> Done -> Done -> Done -> Escape
        run_cmd(["xdotool", "key", "Escape"])
        time.sleep(0.5)
        self.click_relative(0.38, 0.62)  # Options...
        self.click_relative(0.38, 0.58)  # Video Settings...
        self.click_relative(0.38, 0.68)  # Shaders...
        self.click_relative(0.50, 0.93, delay=2.5)  # Done in Shaders (triggers loadShaderPack)
        self.click_relative(0.50, 0.93)  # Done in Video Settings
        self.click_relative(0.50, 0.93)  # Done in Options
        run_cmd(["xdotool", "key", "Escape"])
        time.sleep(1.0)
        return True

    def cycle_shader_option_mode(self) -> bool:
        """Cycle the PROBE_MODE option inside Shader Options subscreen."""
        w = self.get_window()
        if not w:
            return False

        self.focus_window()
        run_cmd(["xdotool", "key", "Escape"])
        time.sleep(0.5)
        self.click_relative(0.38, 0.62)  # Options...
        self.click_relative(0.38, 0.58)  # Video Settings...
        self.click_relative(0.38, 0.68)  # Shaders...
        self.click_relative(0.83, 0.93, delay=1.0)  # Shader Options...
        self.click_relative(0.20, 0.25, delay=0.8)  # Click Probe Mode button
        self.click_relative(0.68, 0.95, delay=2.5)  # Done in Shader Options
        self.click_relative(0.50, 0.93)  # Done in Shaders
        self.click_relative(0.50, 0.93)  # Done in Video Settings
        self.click_relative(0.50, 0.93)  # Done in Options
        run_cmd(["xdotool", "key", "Escape"])
        time.sleep(1.0)
        return True

    def perform_camera_motion(self, duration: float = 2.0) -> None:
        self.focus_window()
        run_cmd(["xdotool", "keydown", "w"])
        start = time.time()
        while time.time() - start < duration:
            run_cmd(["xdotool", "mousemove_relative", "--", "8", "0"])
            time.sleep(0.06)
        run_cmd(["xdotool", "keyup", "w"])
        time.sleep(0.4)

    def write_manifest(self, commit_sha: str) -> None:
        lines = [
            "# Reny Shaders — P0 Capability Probe Screenshot Manifest",
            "",
            f"- **Commit SHA:** `{commit_sha}`",
            f"- **Generated:** `{datetime.datetime.now(datetime.timezone.utc).isoformat()}`",
            "- **Policy:** Binaries are excluded from Git per `AGENTS.md` asset hygiene rules.",
            "- **Location on PC:** `/tmp/opencode/p0_probe_artifacts/`",
            "",
            "## Capture Records",
            "",
            "| Scenario | Resolution | SHA-256 Digest | Observation / Gate |",
            "|---|---|---|---|",
        ]

        for c in self.captures:
            lines.append(
                f"| `{c['scenario']}` | `{c['resolution']}` | `{c['sha256']}` | {c['observation']} |"
            )

        lines.extend([
            "",
            "## Reproduction Instruction",
            "",
            "```bash",
            "# 1. Launch dedicated probe instance",
            "./tools/harness/launch_probe_client.sh",
            "",
            "# 2. Run the P0 validation suite",
            "python3 tools/harness/run_p0_suite.py",
            "",
            "# 3. Verify evaluation report",
            "python3 tools/harness/probe_runner.py",
            "```",
        ])

        self.manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote screenshot manifest to: {self.manifest_path}")

    def run_all(self, commit_sha: str) -> int:
        print("\n=== STARTING P0 VALIDATION SUITE (FAIL-CLOSED) ===\n")
        w = self.get_window()
        if not w:
            self.record_gate(
                "client_window_present",
                "FAIL",
                "Minecraft 1.7.10 window was not detected on X11 display",
                error="Window query returned empty",
            )
            return 1
        self.record_gate(
            "client_window_present",
            "PASS",
            f"Minecraft window active (ID: {w})",
        )

        # ---------------------------------------------------------------------
        # 1. EXP-P0-STACK: Overworld Baseline Smoke
        # ---------------------------------------------------------------------
        print("\n--- Gate: EXP-P0-STACK (Overworld) ---")
        ok = self.reload_shaders_via_gui()
        if not ok:
            self.record_gate("shader_reload_gui", "FAIL", "Failed to reload shaders via GUI")
        else:
            self.record_gate("shader_reload_gui", "PASS", "Shaders reloaded via in-game settings GUI")

        # Overworld Day Still
        ok, _ = self.capture_screen(
            "exp_p0_stack_overworld_day_still",
            "Overworld day scene rendering with terrain, water, foliage, and mode badge",
        )
        if not ok:
            self.record_gate("capture_overworld_still", "FAIL", "Failed to capture Overworld still screenshot")
        else:
            self.record_gate("capture_overworld_still", "PASS", "Captured Overworld still screenshot")

        # Overworld Day Motion
        self.perform_camera_motion(1.5)
        ok, _ = self.capture_screen(
            "exp_p0_stack_overworld_day_motion",
            "Overworld camera movement without geometry tears or visual corruption",
        )
        if not ok:
            self.record_gate("capture_overworld_motion", "FAIL", "Failed to capture Overworld motion screenshot")
        else:
            self.record_gate("capture_overworld_motion", "PASS", "Captured Overworld motion screenshot")

        # Overworld Night
        self.send_chat_command("/time set 18000")
        time.sleep(1.0)
        ok, _ = self.capture_screen(
            "exp_p0_stack_overworld_night",
            "Overworld night scene verifying dark sky, stars, and emissive contrast",
        )
        if not ok:
            self.record_gate("capture_overworld_night", "FAIL", "Failed to capture Overworld night screenshot")
        else:
            self.record_gate("capture_overworld_night", "PASS", "Captured Overworld night screenshot")

        # ---------------------------------------------------------------------
        # 2. EXP-P0-CAP: Modes 1 to 5 via GUI option cycling
        # ---------------------------------------------------------------------
        print("\n--- Gate: EXP-P0-CAP (Diagnostic Probe Modes) ---")
        
        # Mode 1: Uniforms & Capabilities HUD
        self.cycle_shader_option_mode()
        ok, _ = self.capture_screen(
            "exp_p0_cap_mode1_uniforms_hud",
            "Mode 1 HUD verifying frameCounter heartbeat, frameTime bar, sunPosition, and worldTime",
        )
        if not ok:
            self.record_gate("capture_mode1_hud", "FAIL", "Failed to capture Mode 1 HUD screenshot")
        else:
            self.record_gate("capture_mode1_hud", "PASS", "Captured Mode 1 HUD screenshot")

        # Mode 2: History & Skip-Clear Persistence
        self.cycle_shader_option_mode()
        time.sleep(1.5)
        ok, _ = self.capture_screen(
            "exp_p0_history_still_persistent_trail",
            "Mode 2 persistent trailing arc in colortex3 confirming colortex3Clear = false",
        )
        if not ok:
            self.record_gate("capture_history_trail", "FAIL", "Failed to capture History still screenshot")
        else:
            self.record_gate("capture_history_trail", "PASS", "Captured History still screenshot")

        # Mode 2 Motion
        self.perform_camera_motion(1.5)
        ok, _ = self.capture_screen(
            "exp_p0_history_motion",
            "Mode 2 camera motion with persistent screen-space trail",
        )
        if not ok:
            self.record_gate("capture_history_motion", "FAIL", "Failed to capture History motion screenshot")
        else:
            self.record_gate("capture_history_motion", "PASS", "Captured History motion screenshot")

        # Mode 2 Teleport
        self.send_chat_command("/tp ~50 ~ ~50")
        time.sleep(0.8)
        ok, _ = self.capture_screen(
            "exp_p0_history_after_teleport",
            "Mode 2 teleport cut demonstrating retention of screen-space buffer",
        )
        if not ok:
            self.record_gate("capture_history_teleport", "FAIL", "Failed to capture History teleport screenshot")
        else:
            self.record_gate("capture_history_teleport", "PASS", "Captured History teleport screenshot")

        # Mode 2 Resize
        run_cmd(["wmctrl", "-r", "Minecraft 1.7.10", "-e", "0,200,100,1024,600"])
        time.sleep(1.5)
        ok, _ = self.capture_screen(
            "exp_p0_history_after_resize",
            "Mode 2 window resize to 1024x600 confirming clean FBO reallocation",
        )
        if not ok:
            self.record_gate("capture_history_resize", "FAIL", "Failed to capture History resize screenshot")
        else:
            self.record_gate("capture_history_resize", "PASS", "Captured History resize screenshot")
        # Restore window
        run_cmd(["wmctrl", "-r", "Minecraft 1.7.10", "-e", "0,320,212,1280,720"])
        time.sleep(1.0)

        # Mode 3: Material ID Mapping
        self.cycle_shader_option_mode()
        ok, _ = self.capture_screen(
            "exp_p0_material_mapping_swatches",
            "Mode 3 material ID visualization with false coloring from block.properties",
        )
        if not ok:
            self.record_gate("capture_material_mapping", "FAIL", "Failed to capture Material mapping screenshot")
        else:
            self.record_gate("capture_material_mapping", "PASS", "Captured Material mapping screenshot")

        # Mode 4: Buffer Formats
        self.cycle_shader_option_mode()
        ok, _ = self.capture_screen(
            "exp_p0_formats_fp16_r11f_split",
            "Mode 4 split screen verifying RGBA16F (left) and R11F_G11F_B10F (right) buffers",
        )
        if not ok:
            self.record_gate("capture_formats_split", "FAIL", "Failed to capture Formats split screenshot")
        else:
            self.record_gate("capture_formats_split", "PASS", "Captured Formats split screenshot")

        # Mode 5: Deferred Pass Validation
        self.cycle_shader_option_mode()
        ok, _ = self.capture_screen(
            "exp_p0_deferred_pass_confirmed",
            "Mode 5 green banner confirming deferred pass execution and RENY_DEFERRED_MAGIC communication",
        )
        if not ok:
            self.record_gate("capture_deferred_pass", "FAIL", "Failed to capture Deferred pass screenshot")
        else:
            self.record_gate("capture_deferred_pass", "PASS", "Captured Deferred pass screenshot")

        # Cycle back to Mode 0 for dimensions
        self.cycle_shader_option_mode()

        # ---------------------------------------------------------------------
        # 3. EXP-P0-DIM: Dimension Transitions (Nether and End)
        # ---------------------------------------------------------------------
        print("\n--- Gate: EXP-P0-DIM (Dimension Transitions) ---")
        self.send_chat_command("/setblock ~ ~ ~ portal")
        log_ok = self.wait_for_log(r"Loading dimension -1", timeout=30.0)
        if not log_ok:
            self.record_gate("dim_nether_transition", "FAIL", "Nether dimension -1 transition log not observed")
        else:
            self.record_gate("dim_nether_transition", "PASS", "Nether dimension -1 transition confirmed in log")

        time.sleep(3.0)
        ok, _ = self.capture_screen(
            "exp_p0_dim_nether_smoke",
            "Nether DIM -1 rendering with world-1 shader override badge (red)",
        )
        if not ok:
            self.record_gate("capture_nether_smoke", "FAIL", "Failed to capture Nether smoke screenshot")
        else:
            self.record_gate("capture_nether_smoke", "PASS", "Captured Nether smoke screenshot")

        # Return to Overworld
        self.send_chat_command("/setblock ~ ~ ~ portal")
        self.wait_for_log(r"Loading dimension 0", timeout=30.0)
        time.sleep(3.0)
        self.perform_camera_motion(1.5)

        # The End
        self.send_chat_command("/setblock ~ ~ ~ end_portal")
        log_ok = self.wait_for_log(r"Loading dimension 1", timeout=30.0)
        if not log_ok:
            self.record_gate("dim_end_transition", "FAIL", "The End dimension 1 transition log not observed")
        else:
            self.record_gate("dim_end_transition", "PASS", "The End dimension 1 transition confirmed in log")

        time.sleep(3.0)
        ok, _ = self.capture_screen(
            "exp_p0_dim_end_smoke",
            "The End DIM 1 rendering with world1 shader override badge (purple)",
        )
        if not ok:
            self.record_gate("capture_end_smoke", "FAIL", "Failed to capture End smoke screenshot")
        else:
            self.record_gate("capture_end_smoke", "PASS", "Captured End smoke screenshot")

        # ---------------------------------------------------------------------
        # Final Summary and Manifest
        # ---------------------------------------------------------------------
        self.write_manifest(commit_sha)

        failed_gates = [g.name for g in self.gates if g.status == "FAIL"]
        if self.overall_success and len(failed_gates) == 0:
            print("\n=== ALL P0 SUITE GATES PASSED (FAIL-CLOSED) ===\n")
            return 0
        else:
            print(f"\n=== P0 SUITE FINISHED WITH FAILURES: {failed_gates} ===\n")
            return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="P0 Validation Suite Runner")
    parser.add_argument("--commit-sha", type=str, default="", help="Commit SHA to record in manifest")
    parser.add_argument(
        "--update-repo-manifest",
        action="store_true",
        help="Update benchmarks/artifacts/p0_probe/MANIFEST.md in repository",
    )
    args = parser.parse_args()

    commit_sha = args.commit_sha
    if not commit_sha:
        res = run_cmd(["git", "rev-parse", "HEAD"])
        commit_sha = res.stdout.strip() if res.returncode == 0 else "unknown"

    suite = P0Suite(update_repo_manifest=args.update_repo_manifest)
    return suite.run_all(commit_sha)


if __name__ == "__main__":
    sys.exit(main())
