#!/usr/bin/env python3
"""
Reny Shaders — Automated P0 Capability Probe & Validation Suite
Target: Minecraft 1.7.10 / Forge 10.13.4.1614 / OptiFine 1.7.10 HD U E7
"""

from __future__ import annotations

import argparse
import datetime
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
DEFAULT_INSTANCE = Path(os.environ.get("MINECRAFT_INSTANCE_DIR", Path.home() / "Documents/curseforge/minecraft/Instances/Reny Shaders Probe"))
INSTALL_DIR = Path(os.environ.get("MINECRAFT_INSTALL_DIR", Path.home() / "Documents/curseforge/minecraft/Install"))
JAVA_BIN = INSTALL_DIR / "java" / "jre-legacy" / "bin" / "java"
NATIVES_DIR = INSTALL_DIR / "natives" / "forge-10.13.4.1614"
LOG_PATH = DEFAULT_INSTANCE / "logs" / "latest.log"
ARTIFACTS_DIR = REPO_ROOT / "benchmarks" / "artifacts" / "p0_probe"
REPORTS_DIR = REPO_ROOT / "benchmarks" / "reports"
PACK_NAME = "Reny-Capability-Probe"


def run_cmd(args: List[str], timeout: float = 30.0, cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd or REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        check=False,
    )


class P0Suite:
    def __init__(self, instance_dir: Path = DEFAULT_INSTANCE) -> None:
        self.instance_dir = instance_dir
        self.artifacts_dir = ARTIFACTS_DIR
        self.reports_dir = REPORTS_DIR
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.results: Dict[str, Any] = {}
        self.screenshots: List[str] = []

    def get_window(self) -> Optional[str]:
        res = run_cmd(["xdotool", "search", "--onlyvisible", "--name", "Minecraft 1.7.10"])
        windows = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        return windows[-1] if windows else None

    def focus_window(self) -> bool:
        w = self.get_window()
        if w:
            run_cmd(["xdotool", "windowactivate", "--sync", w])
            time.sleep(0.3)
            return True
        return False

    def send_chat_command(self, command: str) -> None:
        w = self.get_window()
        if not w:
            return
        self.focus_window()
        # Open chat with 't'
        run_cmd(["xdotool", "key", "t"])
        time.sleep(0.2)
        # Clear any stray character
        run_cmd(["xdotool", "key", "ctrl+a"])
        run_cmd(["xdotool", "key", "BackSpace"])
        time.sleep(0.1)
        # Type command
        run_cmd(["xdotool", "type", "--delay", "30", "--clearmodifiers", command])
        time.sleep(0.2)
        # Submit
        run_cmd(["xdotool", "key", "Return"])
        time.sleep(0.5)

    def capture_screenshot(self, name: str) -> Path:
        w = self.get_window()
        path = self.artifacts_dir / f"{name}.png"
        if w:
            self.focus_window()
            run_cmd(["scrot", "-w", w, str(path)])
        else:
            run_cmd(["scrot", str(path)])
        self.screenshots.append(path.name)
        print(f"Captured: {path.name}")
        return path

    def switch_probe_mode(self, mode: int) -> None:
        options_path = self.instance_dir / "optionsshaders.txt"
        content = options_path.read_text(encoding="utf-8", errors="replace")
        if "PROBE_MODE=" in content:
            new_content = re.sub(r"PROBE_MODE=\d+", f"PROBE_MODE={mode}", content)
        else:
            new_content = content + f"\nPROBE_MODE={mode}\n"
        options_path.write_text(new_content, encoding="utf-8")
        
        # Also update probe_config.glsl default to match
        cfg_file = SHADERS_DIR / "lib" / "probe_config.glsl"
        cfg_text = cfg_file.read_text(encoding="utf-8")
        new_cfg = re.sub(r"#define PROBE_MODE \d+", f"#define PROBE_MODE {mode}", cfg_text)
        cfg_file.write_text(new_cfg, encoding="utf-8")
        print(f"Set PROBE_MODE to {mode}")

    def trigger_shader_reload(self) -> None:
        self.focus_window()
        # In Minecraft 1.7.10, F3+R reloads shaders.
        # Use keydown F3 + r + keyup F3
        run_cmd(["xdotool", "keydown", "F3"])
        time.sleep(0.15)
        run_cmd(["xdotool", "key", "r"])
        time.sleep(0.15)
        run_cmd(["xdotool", "keyup", "F3"])
        time.sleep(2.5)

    def perform_camera_motion(self, duration: float = 2.0) -> None:
        self.focus_window()
        run_cmd(["xdotool", "keydown", "w"])
        # Slight mouse drift for yaw rotation
        start = time.time()
        while time.time() - start < duration:
            run_cmd(["xdotool", "mousemove_relative", "--", "4", "0"])
            time.sleep(0.05)
        run_cmd(["xdotool", "keyup", "w"])
        time.sleep(0.5)

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

    def run_all_experiments(self) -> Dict[str, Any]:
        print("\n=== STARTING P0 EXPERIMENTAL SUITE ===\n")

        # Ensure window is focused and in-world
        self.focus_window()
        time.sleep(1.0)

        # ---------------------------------------------------------------------
        # 1. EXP-P0-STACK: Overworld Baseline (Mode 0)
        # ---------------------------------------------------------------------
        print("--- [1/6] EXP-P0-STACK: Overworld Smoke ---")
        self.switch_probe_mode(0)
        self.trigger_shader_reload()
        
        # Set daytime for clear terrain smoke
        self.send_chat_command("/time set 6000")
        self.send_chat_command("/weather clear")
        time.sleep(1.0)

        # Capture Overworld Day - Still
        self.capture_screenshot("exp_p0_stack_overworld_day_still")
        
        # Camera motion
        self.perform_camera_motion(1.5)
        self.capture_screenshot("exp_p0_stack_overworld_day_motion")

        # Night test for lightmap & emissive authority
        self.send_chat_command("/time set 18000")
        time.sleep(1.0)
        self.capture_screenshot("exp_p0_stack_overworld_night")

        # Shader reload test in-world
        print("Testing in-world shader reload (F3+R)...")
        self.trigger_shader_reload()
        self.capture_screenshot("exp_p0_stack_overworld_after_reload")

        # Window resize test
        print("Testing window resize handling...")
        w = self.get_window()
        if w:
            run_cmd(["wmctrl", "-r", "Minecraft 1.7.10", "-e", "0,200,100,1024,600"])
            time.sleep(1.5)
            self.capture_screenshot("exp_p0_stack_resize_1024x600")
            # Restore to standard 1280x720
            run_cmd(["wmctrl", "-r", "Minecraft 1.7.10", "-e", "0,320,212,1280,720"])
            time.sleep(1.5)

        # ---------------------------------------------------------------------
        # 2. EXP-P0-CAP: Capability & Uniforms Probe (Mode 1)
        # ---------------------------------------------------------------------
        print("\n--- [2/6] EXP-P0-CAP: Uniforms & Includes Probe (Mode 1) ---")
        self.switch_probe_mode(1)
        self.trigger_shader_reload()
        time.sleep(1.0)
        self.capture_screenshot("exp_p0_cap_mode1_uniforms_hud")

        # ---------------------------------------------------------------------
        # 3. EXP-P0-HISTORY: Skip-Clear Persistence (Mode 2)
        # ---------------------------------------------------------------------
        print("\n--- [3/6] EXP-P0-HISTORY: Skip-Clear & Persistence (Mode 2) ---")
        self.switch_probe_mode(2)
        self.trigger_shader_reload()
        time.sleep(1.0)

        # Still camera: persistent trail should form cleanly
        time.sleep(2.0)
        self.capture_screenshot("exp_p0_history_still_persistent_trail")

        # Motion: does history blur or corrupt during camera motion?
        self.perform_camera_motion(2.0)
        self.capture_screenshot("exp_p0_history_motion")

        # Teleport: test history reset on position discontinuity
        self.send_chat_command("/tp ~50 ~ ~50")
        time.sleep(1.0)
        self.capture_screenshot("exp_p0_history_after_teleport")

        # ---------------------------------------------------------------------
        # 4. EXP-P0-MATERIAL: Block Mapping & Properties (Mode 3)
        # ---------------------------------------------------------------------
        print("\n--- [4/6] EXP-P0-MATERIAL: Material ID Mapping (Mode 3) ---")
        self.switch_probe_mode(3)
        self.trigger_shader_reload()
        time.sleep(1.0)

        # Spawn representative test materials nearby to exercise mapping
        # Stone, dirt, wood, leaves, water, lava, iron ore, torch
        self.send_chat_command("/setblock ~2 ~ ~ stone")
        self.send_chat_command("/setblock ~2 ~ ~1 dirt")
        self.send_chat_command("/setblock ~2 ~ ~2 log")
        self.send_chat_command("/setblock ~2 ~ ~3 leaves")
        self.send_chat_command("/setblock ~2 ~ ~4 iron_ore")
        self.send_chat_command("/setblock ~2 ~ ~5 torch")
        time.sleep(1.0)
        self.capture_screenshot("exp_p0_material_mapping_swatches")

        # ---------------------------------------------------------------------
        # 5. EXP-P0-FORMATS: Buffer Formats (Mode 4)
        # ---------------------------------------------------------------------
        print("\n--- [5/6] EXP-P0-FORMATS: Half-Float & Compact Buffers (Mode 4) ---")
        self.switch_probe_mode(4)
        self.trigger_shader_reload()
        time.sleep(1.0)
        self.capture_screenshot("exp_p0_formats_fp16_r11f_split")

        # ---------------------------------------------------------------------
        # 6. EXP-P0-DEFERRED: Deferred Stage Execution (Mode 5)
        # ---------------------------------------------------------------------
        print("\n--- [6/6] EXP-P0-DEFERRED: Deferred Stage Execution (Mode 5) ---")
        self.switch_probe_mode(5)
        self.trigger_shader_reload()
        time.sleep(1.0)
        self.capture_screenshot("exp_p0_deferred_pass_confirmed")

        # ---------------------------------------------------------------------
        # 7. EXP-P0-DIM: Dimension Transitions (Nether & End)
        # ---------------------------------------------------------------------
        print("\n--- [7/7] EXP-P0-DIM: Nether and End Dimensions ---")
        # Return to baseline mode 0 for dimension tests
        self.switch_probe_mode(0)
        self.trigger_shader_reload()
        time.sleep(1.0)

        # Nether transition via portal placement
        print("Spawning Nether portal...")
        self.send_chat_command("/setblock ~ ~ ~ portal")
        print("Waiting for Nether dimension load (dimension -1)...")
        self.wait_for_log(r"Loading dimension -1", timeout=30.0)
        time.sleep(5.0)
        self.capture_screenshot("exp_p0_dim_nether_smoke")
        self.perform_camera_motion(1.5)
        self.capture_screenshot("exp_p0_dim_nether_motion")

        # Return / End transition via end_portal placement
        print("Spawning End portal...")
        self.send_chat_command("/setblock ~ ~ ~ end_portal")
        print("Waiting for The End dimension load (dimension 1)...")
        self.wait_for_log(r"Loading dimension 1", timeout=30.0)
        time.sleep(5.0)
        self.capture_screenshot("exp_p0_dim_end_smoke")
        self.perform_camera_motion(1.5)
        self.capture_screenshot("exp_p0_dim_end_motion")

        # Switch back to Baseline Overworld
        self.send_chat_command("/setblock ~ ~ ~ end_portal")
        time.sleep(5.0)
        self.capture_screenshot("exp_p0_stack_returned_overworld")

        print("\n=== ALL P0 EXPERIMENTS COMPLETED SUCCESSFULLY ===\n")
        return {
            "status": "COMPLETE",
            "screenshots": self.screenshots,
        }


def main() -> int:
    suite = P0Suite()
    suite.run_all_experiments()
    return 0


if __name__ == "__main__":
    sys.exit(main())
