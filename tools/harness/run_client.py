#!/usr/bin/env python3
"""
Reny Shaders — Direct Minecraft 1.7.10 Client Runner & Test Automation
Target Stack: Forge 10.13.4.1614 / OptiFine 1.7.10 HD U E7 / Java 8
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


INSTALL_DIR = Path(os.environ.get("MINECRAFT_INSTALL_DIR", Path.home() / "Documents/curseforge/minecraft/Install"))
JAVA_BIN = INSTALL_DIR / "java" / "jre-legacy" / "bin" / "java"
NATIVES_DIR = INSTALL_DIR / "natives" / "forge-10.13.4.1614"
INSTANCE_DIR = Path(os.environ.get("MINECRAFT_INSTANCE_DIR", Path.home() / "Documents/curseforge/minecraft/Instances/Reny Shaders Probe"))
LOG_PATH = INSTANCE_DIR / "logs" / "latest.log"


def build_classpath() -> str:
    forge_json = INSTALL_DIR / "versions" / "forge-10.13.4.1614" / "forge-10.13.4.1614.json"
    mc_json = INSTALL_DIR / "versions" / "1.7.10" / "1.7.10.json"
    
    with forge_json.open(encoding="utf-8") as f:
        forge_data = json.load(f)
    with mc_json.open(encoding="utf-8") as f:
        mc_data = json.load(f)

    cp_entries = []
    for lib in forge_data.get("libraries", []) + mc_data.get("libraries", []):
        name = lib.get("name")
        parts = name.split(":")
        group, artifact, version = parts[0], parts[1], parts[2]
        classifier = parts[3] if len(parts) > 3 else None
        jar_name = f"{artifact}-{version}" + (f"-{classifier}" if classifier else "") + ".jar"
        rel_path = Path(*group.split(".")) / artifact / version / jar_name
        full_path = INSTALL_DIR / "libraries" / rel_path
        if full_path.exists():
            cp_entries.append(str(full_path))

    cp_entries.append(str(INSTALL_DIR / "versions" / "forge-10.13.4.1614" / "forge-10.13.4.1614.jar"))
    cp_entries.append(str(INSTALL_DIR / "versions" / "1.7.10" / "1.7.10.jar"))
    return ":".join(cp_entries)


class MinecraftClient:
    def __init__(self, instance_dir: Path = INSTANCE_DIR) -> None:
        self.instance_dir = instance_dir
        self.process: Optional[subprocess.Popen[str]] = None
        self.launch_time: float = 0.0

    def is_running(self) -> bool:
        if self.process and self.process.poll() is None:
            return True
        res = subprocess.run(
            ["pgrep", "-f", f"[n]et.minecraft.launchwrapper.Launch.*{self.instance_dir.name}"],
            stdout=subprocess.PIPE,
            text=True,
        )
        return bool(res.stdout.strip())

    def get_window(self) -> Optional[str]:
        res = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "Minecraft 1.7.10"], stdout=subprocess.PIPE, text=True)
        windows = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        return windows[-1] if windows else None

    def focus(self) -> bool:
        w = self.get_window()
        if w:
            subprocess.run(["xdotool", "windowactivate", "--sync", w], check=False)
            return True
        return False

    def send_key(self, key: str, delay: float = 0.1) -> None:
        w = self.get_window()
        if w:
            subprocess.run(["xdotool", "key", "--window", w, key], check=False)
            time.sleep(delay)

    def capture_screen(self, output_path: Path) -> bool:
        w = self.get_window()
        if not w:
            return False
        output_path.parent.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(["scrot", "-w", w, str(output_path)], check=False)
        return res.returncode == 0

    def launch(self, extra_jvm_args: Optional[List[str]] = None) -> None:
        if self.is_running():
            print("Minecraft is already running.")
            return

        classpath = build_classpath()
        log_config = INSTALL_DIR / "assets" / "log_configs" / "client-1.7.xml"

        jvm_args = [
            str(JAVA_BIN),
            f"-Djava.library.path={NATIVES_DIR}",
            "-cp", classpath,
            "-Xmx6144m",
            "-Xms256m",
            "-Dfml.ignorePatchDiscrepancies=true",
            "-Dfml.ignoreInvalidMinecraftCertificates=true",
            f"-DlibraryDirectory={INSTALL_DIR / 'libraries'}",
            "-Duser.language=en",
        ]
        if log_config.exists():
            jvm_args.append(f"-Dlog4j.configurationFile={log_config}")
        if extra_jvm_args:
            jvm_args.extend(extra_jvm_args)

        app_args = [
            "net.minecraft.launchwrapper.Launch",
            "--username", "RenyTester",
            "--version", "forge-10.13.4.1614",
            "--gameDir", str(self.instance_dir),
            "--assetsDir", str(INSTALL_DIR / "assets"),
            "--assetIndex", "1.7.10",
            "--uuid", "00000000-0000-0000-0000-000000000000",
            "--accessToken", "0",
            "--userProperties", "{}",
            "--userType", "legacy",
            "--tweakClass", "cpw.mods.fml.common.launcher.FMLTweaker",
            "--width", "1280",
            "--height", "720",
        ]

        full_cmd = jvm_args + app_args
        self.launch_time = time.time()
        print(f"Launching Minecraft client: {JAVA_BIN}")
        log_out = self.instance_dir / "logs" / "client_stdout.log"
        log_out.parent.mkdir(parents=True, exist_ok=True)
        log_file = log_out.open("w", encoding="utf-8")
        self.process = subprocess.Popen(
            full_cmd,
            cwd=str(self.instance_dir),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    def wait_for_window(self, timeout: float = 120.0) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if self.get_window():
                return True
            time.sleep(1.0)
        return False

    def wait_log(self, pattern: str, timeout: float = 120.0) -> Optional[re.Match[str]]:
        regex = re.compile(pattern)
        start = time.time()
        while time.time() - start < timeout:
            if LOG_PATH.exists():
                try:
                    text = LOG_PATH.read_text(encoding="utf-8", errors="replace")
                    match = regex.search(text)
                    if match:
                        return match
                except Exception:
                    pass
            time.sleep(1.0)
        return None

    def terminate(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
        subprocess.run(["pkill", "-f", "[n]et.minecraft.launchwrapper.Launch"], check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--launch", action="store_true", help="Launch Minecraft client")
    parser.add_argument("--status", action="store_true", help="Check client status")
    parser.add_argument("--capture", type=Path, help="Capture screenshot to path")
    parser.add_argument("--stop", action="store_true", help="Stop Minecraft process")
    args = parser.parse_args()

    client = MinecraftClient()

    if args.status:
        running = client.is_running()
        window = client.get_window()
        print(f"Running: {running}, Window ID: {window}")
        return 0

    if args.stop:
        client.terminate()
        print("Stopped Minecraft.")
        return 0

    if args.capture:
        if client.capture_screen(args.capture):
            print(f"Captured screen to {args.capture}")
            return 0
        else:
            print("Failed to capture screen.")
            return 1

    if args.launch:
        client.launch()
        print("Waiting for Minecraft window (timeout: 180s)...")
        if client.wait_for_window(180.0):
            print(f"Minecraft window appeared: {client.get_window()}")
        else:
            print("Timed out waiting for Minecraft window.")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
