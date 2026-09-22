#!/usr/bin/env python3
"""
Reny Shaders — Automated P0 Capability Probe & Validation Suite
Target: Minecraft 1.7.10 / Forge 10.13.4.1614 / OptiFine 1.7.10 HD U E7

Fail-closed contract:
- Every X11 subprocess return code is inspected; any unexpected failure
  propagates as an explicit gate FAIL (never silent success).
- Log waits only accept evidence produced AFTER a captured cursor
  (stale matches from earlier in the session never satisfy a gate).
- Log read failures produce diagnostics + coherent FAIL/INCONCLUSIVE,
  never `except Exception: pass`.
- Overall exit code is non-zero when any FAIL gate exists.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
SHADERS_DIR = REPO_ROOT / "shaders"
DEFAULT_INSTANCE = Path(
    os.environ.get(
        "MINECRAFT_INSTANCE_DIR",
        str(Path.home() / "Documents/curseforge/minecraft/Instances/Reny Shaders Probe"),
    )
)
LOG_PATH = DEFAULT_INSTANCE / "logs" / "latest.log"
OPTIONS_SHADERS_PATH = DEFAULT_INSTANCE / "optionsshaders.txt"
MANIFEST_PATH = REPO_ROOT / "benchmarks" / "artifacts" / "p0_probe" / "MANIFEST.md"
SCREENSHOT_DIR = Path(
    os.environ.get("P0_SCREENSHOT_DIR", "/tmp/opencode/p0_probe_artifacts")
)


# ---------------------------------------------------------------------------
# Checked subprocess execution (fail-closed)
# ---------------------------------------------------------------------------

@dataclass
class CheckedResult:
    ok: bool
    returncode: Optional[int]
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None


def run_checked(args: List[str], timeout: float = 30.0) -> CheckedResult:
    """Run a subprocess and never hide transport failures."""
    try:
        proc = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        return CheckedResult(
            ok=proc.returncode == 0,
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            error=None if proc.returncode == 0 else f"exit={proc.returncode}: {(proc.stderr or proc.stdout or '')[:300]}",
        )
    except FileNotFoundError as exc:
        return CheckedResult(ok=False, returncode=None, error=f"binary-not-found: {exc}")
    except subprocess.TimeoutExpired as exc:
        return CheckedResult(ok=False, returncode=None, error=f"timeout after {timeout}s: {exc}")
    except OSError as exc:
        return CheckedResult(ok=False, returncode=None, error=f"os-error: {exc}")


# Verified menu geometry (content fractions on the 1280x720 MC window,
# measured against real screenshots of each OptiFine E7 screen; the
# content origin comes from `xdotool getwindowgeometry`, which already
# accounts for WM decorations).
MENU_PAUSE_OPTIONS = (0.392, 0.642)
MENU_OPTIONS_VIDEO = (0.313, 0.568)
MENU_VIDEO_SHADERS = (0.313, 0.668)
MENU_SHADERS_DONE = (0.500, 0.929)
MENU_SHADERS_OPTIONS = (0.820, 0.930)
MENU_SHADEROPTS_PROBE = (0.290, 0.250)
MENU_SHADEROPTS_DONE = (0.710, 0.920)
MENU_VIDEO_DONE = (0.500, 0.940)
MENU_OPTIONS_DONE = (0.500, 0.890)

CONFIRM_TIME_SET = r"Set the time to"
CONFIRM_TELEPORTED = r"Teleported RenyTester"
CONFIRM_BLOCK_PLACED = r"Block placed"
CONFIRM_SEED = r"Seed:"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Fresh-log cursor: only evidence produced AFTER capture counts
# ---------------------------------------------------------------------------

@dataclass
class LogCursor:
    path: Path
    inode: Optional[int] = None
    size: int = 0
    prefix_sha256: Optional[str] = None
    captured_at: float = 0.0
    error: Optional[str] = None

    @classmethod
    def capture(cls, path: Path) -> "LogCursor":
        cur = cls(path=path, captured_at=time.time())
        try:
            st = path.stat()
            cur.inode = st.st_ino
            cur.size = st.st_size
            with path.open("rb") as f:
                cur.prefix_sha256 = hashlib.sha256(f.read(min(st.st_size, 4096))).hexdigest()
        except FileNotFoundError:
            cur.error = f"log file not found at capture: {path}"
        except OSError as exc:
            cur.error = f"log stat failed at capture: {exc}"
        return cur



@dataclass
class FreshLogRead:
    lines: str = ""
    truncated_or_rotated: bool = False
    error: Optional[str] = None

def read_fresh_log(cursor: LogCursor) -> FreshLogRead:

    """Read only bytes appended after cursor; handle rotation/truncation explicitly."""
    try:
        st = cursor.path.stat()
    except FileNotFoundError as exc:
        return FreshLogRead(error=f"log file missing on read: {exc}")
    except OSError as exc:
        return FreshLogRead(error=f"log stat failed on read: {exc}")

    truncated_or_rotated = False
    start_offset = cursor.size
    if cursor.inode is not None and st.st_ino != cursor.inode:
        # File rotated/recreated: the cursor is invalid, never trust its bytes.
        truncated_or_rotated = True
        start_offset = 0
    elif st.st_size < cursor.size:
        # Truncated in place: the cursor is invalid, never trust its bytes.
        truncated_or_rotated = True
        start_offset = 0

    try:
        with cursor.path.open("rb") as f:
            raw_all = f.read()
        current_prefix = hashlib.sha256(raw_all[: min(cursor.size, 4096)]).hexdigest()
        if cursor.prefix_sha256 is not None and current_prefix != cursor.prefix_sha256:
            truncated_or_rotated = True
            start_offset = 0
        raw = raw_all[start_offset:]
        text = raw.decode("utf-8", errors="replace")
        return FreshLogRead(lines=text, truncated_or_rotated=truncated_or_rotated)
    except OSError as exc:
        return FreshLogRead(error=f"log read failed at offset {start_offset}: {exc}")


@dataclass
class LogWaitResult:
    matched: bool
    evidence: str = ""
    error: Optional[str] = None
    truncated_or_rotated: bool = False


def wait_for_fresh_log(
    cursor: LogCursor,
    pattern: str,
    timeout: float = 30.0,
    poll_interval: float = 0.5,
) -> LogWaitResult:
    """Wait only for trustworthy bytes appended after the cursor."""
    if cursor.error is not None:
        return LogWaitResult(False, error=f"cursor capture failed, cannot trust wait: {cursor.error}")
    try:
        regex = re.compile(pattern)
    except re.error as exc:
        return LogWaitResult(False, error=f"invalid regex {pattern!r}: {exc}")
    deadline = time.time() + timeout
    last_error: Optional[str] = None
    while time.time() < deadline:
        fresh = read_fresh_log(cursor)
        if fresh.error is not None:
            last_error = fresh.error
        elif fresh.truncated_or_rotated:
            return LogWaitResult(
                False,
                evidence="log rotated or truncated after cursor; fresh evidence is not trustworthy",
                error="log rotation/truncation invalidated the evidence cursor",
                truncated_or_rotated=True,
            )
        else:
            match = regex.search(fresh.lines)
            if match:
                return LogWaitResult(True, evidence=f"fresh match after cursor: {match.group(0)[:220]!r}")
        time.sleep(poll_interval)
    return LogWaitResult(
        False,
        evidence=f"no fresh match for {pattern!r} within {timeout}s",
        error=last_error or f"timeout waiting for fresh log pattern {pattern!r}",
    )


def capture_all(paths: List[Path]) -> List[LogCursor]:
    return [LogCursor.capture(p) for p in paths]


def read_fresh_combined(cursors: List[LogCursor]) -> FreshLogRead:
    """Concatenate fresh bytes from every evidence log (rotation-aware per file)."""
    parts: List[str] = []
    rotated = False
    errors: List[str] = []
    for c in cursors:
        if c.error is not None:
            errors.append(f"{c.path.name}: cursor failed: {c.error}")
            continue
        fresh = read_fresh_log(c)
        if fresh.error is not None:
            errors.append(f"{c.path.name}: {fresh.error}")
            continue
        if fresh.truncated_or_rotated:
            rotated = True
        if fresh.lines:
            parts.append(fresh.lines)
    combined = "\n".join(parts)
    err = "; ".join(errors) if errors and not combined else None
    return FreshLogRead(lines=combined, truncated_or_rotated=rotated, error=err)


def wait_for_fresh_combined(
    cursors: List[LogCursor],
    pattern: str,
    timeout: float = 30.0,
    poll_interval: float = 0.5,
) -> LogWaitResult:
    """
    Wait for `pattern` in bytes appended AFTER all cursors, across every
    evidence log. Stale occurrences from earlier in the session never satisfy
    the wait, no matter which file carried them.
    """
    bad = [c for c in cursors if c.error is not None]
    if bad:
        return LogWaitResult(
            matched=False, evidence="",
            error="cursor capture failed, cannot trust wait: "
                  + "; ".join(f"{c.path.name}: {c.error}" for c in bad),
        )
    try:
        regex = re.compile(pattern)
    except re.error as exc:
        return LogWaitResult(matched=False, evidence="", error=f"invalid regex {pattern!r}: {exc}")

    deadline = time.time() + timeout
    last_error: Optional[str] = None
    while time.time() < deadline:
        fresh = read_fresh_combined(cursors)
        if fresh.error is not None:
            last_error = fresh.error
        elif fresh.truncated_or_rotated:
            return LogWaitResult(
                False,
                evidence="one or more logs rotated or truncated after cursor; evidence is not trustworthy",
                error="log rotation/truncation invalidated the evidence cursors",
                truncated_or_rotated=True,
            )
        else:
            match = regex.search(fresh.lines)
            if match:
                return LogWaitResult(True, evidence=f"fresh match after cursor: {match.group(0)[:220]!r}")
        time.sleep(poll_interval)
    return LogWaitResult(
        False,
        evidence=f"no fresh match for {pattern!r} within {timeout}s",
        error=last_error or f"timeout waiting for fresh log pattern {pattern!r}",
    )


# Fresh re-init signature of a real dimension switch on this stack.
# NOTE: "Loading dimension <id>" lines are emitted only at integrated-server
# startup, so they can NEVER satisfy a fresh post-action wait on their own;
# they are kept in the alternation only as a harmless extra. The operative
# evidence is the shader re-init block (Reset world renderers / per-dimension
# program loads) that a portal transition triggers.
DIM_SWITCH_FRESH_PATTERN = (
    r"Reset world renderers"
    r"|\[Shaders\] Uninit"
    r"|Program loaded: world-1/"
    r"|Program loaded: world1/"
    r"|Loading dimension -1"
    r"|Loading dimension 1"
    r"|Loading dimension 0"
)


def read_probe_mode_option(options_path: Path = OPTIONS_SHADERS_PATH) -> Tuple[Optional[int], Optional[str]]:
    """Read persisted PROBE_MODE from optionsshaders.txt (runtime file, not tracked)."""
    try:
        text = options_path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None, f"optionsshaders.txt not found: {options_path}"
    except OSError as exc:
        return None, f"optionsshaders.txt read failed: {exc}"
    m = re.search(r"^PROBE_MODE\s*[:=]\s*(\d+)\s*$", text, re.MULTILINE)
    if not m:
        return None, "PROBE_MODE key absent in optionsshaders.txt"
    try:
        return int(m.group(1)), None
    except ValueError as exc:
        return None, f"PROBE_MODE value not an int: {exc}"


class GateResult:
    def __init__(self, name: str, status: str, evidence: str, error: Optional[str] = None) -> None:
        assert status in ("PASS", "FAIL", "INCONCLUSIVE")
        self.name = name
        self.status = status
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
        # Evidence logs: JVM stdout carries the [Shaders] loader lines while
        # latest.log carries server lines; parse both so evidence routing
        # never depends on which launch flags were used.
        self.log_paths = [
            instance_dir / "logs" / "client_stdout.log",
            instance_dir / "logs" / "latest.log",
        ]
        self.options_path = instance_dir / "optionsshaders.txt"
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

    # -- gate bookkeeping ----------------------------------------------------
    def record_gate(self, name: str, status: str, evidence: str, error: Optional[str] = None) -> None:
        gate = GateResult(name, status, evidence, error)
        self.gates.append(gate)
        symbol = "✓" if status == "PASS" else ("?" if status == "INCONCLUSIVE" else "✗")
        print(f"[{symbol}] {name}: {status} — {evidence}" + (f" (error: {error})" if error else ""))
        if status == "FAIL":
            self.overall_success = False

    # -- X11 primitives (all fail-closed) ------------------------------------
    def get_window(self) -> Tuple[Optional[str], Optional[str]]:
        res = run_checked(["xdotool", "search", "--onlyvisible", "--name", "Minecraft 1.7.10"])
        if not res.ok:
            return None, f"xdotool search failed: {res.error}"
        windows = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        if not windows:
            return None, "xdotool search returned zero windows"
        return windows[-1], None

    def get_window_geometry(self, win: str) -> Tuple[Optional[Tuple[int, int, int, int]], Optional[str]]:
        # Content origin + size via xdotool (accounts for WM decorations;
        # xwininfo absolute coords alone miss by the decoration offset).
        res = run_checked(["xdotool", "getwindowgeometry", win])
        if not res.ok:
            return None, f"getwindowgeometry failed: {res.error}"
        try:
            pos = re.search(r"Position:\s+(-?\d+),(-?\d+)", res.stdout)
            geo = re.search(r"Geometry:\s+(\d+)x(\d+)", res.stdout)
            if not pos or not geo:
                raise ValueError(f"unparseable geometry output: {res.stdout[:200]!r}")
            x, y = int(pos.group(1)), int(pos.group(2))
            w, h = int(geo.group(1)), int(geo.group(2))
            return (x, y, w, h), None
        except (AttributeError, ValueError) as exc:
            return None, f"window geometry parse failed: {exc}"

    def focus_window(self) -> Tuple[bool, Optional[str]]:
        w, err = self.get_window()
        if not w:
            return False, err or "no window to focus"
        r1 = run_checked(["xdotool", "windowactivate", w])
        r2 = run_checked(["xdotool", "windowraise", w])
        time.sleep(1.0)  # let the WM grant focus before any pointer action
        if not r1.ok:
            return False, f"windowactivate failed: {r1.error}"
        if not r2.ok:
            return False, f"windowraise failed: {r2.error}"
        r3 = run_checked(["xdotool", "getwindowfocus"])
        if r3.ok and r3.stdout.strip() != w:
            return False, f"focus not granted (focused={r3.stdout.strip()!r}, want={w!r})"
        if not r3.ok:
            return False, f"getwindowfocus check failed: {r3.error}"
        return True, None

    def click_relative(self, rx: float, ry: float, delay: float = 0.5) -> Tuple[bool, Optional[str]]:
        w, err = self.get_window()
        if not w:
            return False, err or "click aborted: no window"
        geom, gerr = self.get_window_geometry(w)
        if not geom:
            return False, gerr or "click aborted: no geometry"
        x, y, width, height = geom
        cx = x + int(width * rx)
        cy = y + int(height * ry)
        # Proven delivery on this stack needs a real press hold (~0.3s);
        # 0.1s taps are silently swallowed by the LWJGL window.
        res = run_checked(["xdotool", "mousemove", str(cx), str(cy)])
        if not res.ok:
            return False, f"click mousemove failed at ({cx},{cy}): {res.error}"
        time.sleep(0.2)
        res = run_checked(["xdotool", "mousedown", "1"])
        if not res.ok:
            return False, f"click mousedown failed at ({cx},{cy}): {res.error}"
        time.sleep(0.3)
        res = run_checked(["xdotool", "mouseup", "1"])
        if not res.ok:
            return False, f"click mouseup failed at ({cx},{cy}): {res.error}"
        time.sleep(delay)
        return True, None

    def send_chat_command(self, command: str) -> Tuple[bool, Optional[str]]:
        w, err = self.get_window()
        if not w:
            return False, err or "chat command aborted: no window"
        ok, ferr = self.focus_window()
        if not ok:
            return False, f"chat command aborted, focus failed: {ferr}"
        steps = [
            ["xdotool", "key", "t"],
            ["xdotool", "key", "ctrl+a"],
            ["xdotool", "key", "BackSpace"],
            ["xdotool", "type", "--delay", "30", "--clearmodifiers", command],
            ["xdotool", "key", "Return"],
        ]
        for cmd in steps:
            res = run_checked(cmd)
            if not res.ok:
                return False, f"chat step {' '.join(cmd)} failed: {res.error}"
            time.sleep(0.15)
        time.sleep(0.5)
        return True, None

    def send_chat_command_verified(
        self,
        command: str,
        confirm_pattern: str,
        timeout: float = 15.0,
    ) -> Tuple[bool, str, Optional[str]]:
        """Send a chat command and prove the SERVER acted on it.

        xdotool success alone never counts as execution: after sending the
        keys, a fresh-log wait must observe the server's confirmation line.
        One retry is allowed; persistent absence is an explicit failure.
        """
        for attempt in (1, 2):
            cursors = capture_all(self.log_paths)
            ok, send_err = self.send_chat_command(command)
            if not ok:
                last_err = f"attempt {attempt}: key delivery failed: {send_err}"
                time.sleep(1.0)
                continue
            wait = wait_for_fresh_combined(cursors, confirm_pattern, timeout=timeout)
            if wait.matched:
                return True, f"server confirmed (attempt {attempt}): {wait.evidence}", None
            last_err = (f"attempt {attempt}: no server confirmation: {wait.evidence} "
                        f"(error: {wait.error})")
            time.sleep(1.0)
        return False, "", f"command {command!r} unverified after 2 attempts: {last_err}"

    def ensure_in_game(self, tries: int = 4) -> Tuple[bool, Optional[str]]:
        """Prove the player is in-game (not in a menu/title/death screen).

        Uses the harmless `/seed` probe: only an in-game chat accepts and
        answers it. Between attempts a single Escape collapses any open
        menu/chat toward the game. GUI flows must call this first so they
        never start navigating from an unknown screen (which previously
        cascaded onto the title screen and clicked Realms).
        """
        last_err: Optional[str] = None
        for attempt in range(1, tries + 1):
            ok, _, err = self.send_chat_command_verified("/seed", CONFIRM_SEED, timeout=10.0)
            if ok:
                return True, None
            last_err = err
            res = run_checked(["xdotool", "key", "Escape"])
            if not res.ok:
                return False, f"ensure_in_game: Escape failed: {res.error}"
            time.sleep(1.5)
        return False, f"not verifiably in-game after {tries} attempts: {last_err}"

    def resize_window(self, geometry: str) -> Tuple[bool, Optional[str]]:
        res = run_checked(["wmctrl", "-r", "Minecraft 1.7.10", "-e", geometry])
        if not res.ok:
            return False, f"wmctrl resize {geometry!r} failed: {res.error}"
        return True, None

    def capture_screen(self, scenario_name: str, observation: str) -> Tuple[bool, Optional[Path], Optional[str]]:
        w, err = self.get_window()
        if not w:
            return False, None, err or "screenshot aborted: no window"

        path = self.screenshot_dir / f"{scenario_name}.png"
        res = run_checked(["scrot", "-o", "-w", w, str(path)])
        if not res.ok:
            return False, None, f"scrot failed: {res.error}"
        try:
            if not path.is_file():
                return False, None, f"scrot exit 0 but file missing: {path}"
            size = path.stat().st_size
        except OSError as exc:
            return False, None, f"screenshot stat failed: {exc}"
        if size == 0:
            return False, None, f"screenshot is zero bytes: {path}"

        geom, _ = self.get_window_geometry(w)
        res_str = f"{geom[2]}x{geom[3]}" if geom else "unknown"
        try:
            sha256 = compute_sha256(path)
        except OSError as exc:
            return False, None, f"sha256 failed: {exc}"
        iso_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        self.captures.append({
            "scenario": scenario_name,
            "filename": path.name,
            "path": str(path),
            "resolution": res_str,
            "sha256": sha256,
            "size_bytes": size,
            "timestamp": iso_time,
            "observation": observation,
        })
        return True, path, None

    # -- composite GUI flows (propagate every internal failure) --------------
    def reload_shaders_via_gui(self) -> Tuple[bool, str, Optional[str]]:
        """Reload shaders via in-game settings; prove with fresh framebuffer evidence."""
        w, err = self.get_window()
        if not w:
            return False, "", err or "reload aborted: no window"

        cursors = capture_all(self.log_paths)
        bad = [c for c in cursors if c.error is not None]
        if bad:
            return False, "", "reload aborted, log cursor failed: " + "; ".join(
                f"{c.path.name}: {c.error}" for c in bad)

        ok, gerr = self.ensure_in_game()
        if not ok:
            return False, "", f"reload aborted, not in-game: {gerr}"

        failures: List[str] = []

        def step(cmd: List[str], sleep_after: float = 0.0) -> None:
            res = run_checked(cmd)
            if not res.ok:
                failures.append(f"{' '.join(cmd)} -> {res.error}")
            if sleep_after:
                time.sleep(sleep_after)

        step(["xdotool", "key", "Escape"], 1.5)
        nav = [
            (MENU_PAUSE_OPTIONS, 0.8, "Options..."),
            (MENU_OPTIONS_VIDEO, 0.8, "Video Settings..."),
            (MENU_VIDEO_SHADERS, 1.0, "Shaders..."),
        ]
        for (rx, ry), d, label in nav:
            ok_c, cerr = self.click_relative(rx, ry, delay=d)
            if not ok_c:
                failures.append(f"click {label} ({rx},{ry}) -> {cerr}")
        for (rx, ry), d, label in [
            (MENU_SHADERS_DONE, 2.5, "Done/Shaders"),
            (MENU_VIDEO_DONE, 0.8, "Done/Video"),
            (MENU_OPTIONS_DONE, 0.8, "Done/Options"),
        ]:
            ok_c, cerr = self.click_relative(rx, ry, delay=d)
            if not ok_c:
                failures.append(f"click {label} ({rx},{ry}) -> {cerr}")
        step(["xdotool", "key", "Escape"], 1.0)

        if failures:
            return False, "", f"reload GUI steps failed: {'; '.join(failures)}"

        wait = wait_for_fresh_combined(cursors, r"Framebuffer created\.|Program loaded: final", timeout=30.0)
        if not wait.matched:
            return False, "", f"reload not evidenced in fresh log: {wait.evidence} (error: {wait.error})"
        return True, wait.evidence, None

    def cycle_shader_option_mode(self) -> Tuple[bool, Optional[int], Optional[int], Optional[str]]:
        """Cycle PROBE_MODE via Shader Options; verify persistence in optionsshaders.txt."""
        w, err = self.get_window()
        if not w:
            return False, None, None, err or "mode cycle aborted: no window"

        before, rerr = read_probe_mode_option(self.options_path)
        if rerr is not None:
            # Missing key before the cycle is a hard diagnostic, not silent.
            return False, before, None, f"pre-cycle PROBE_MODE unreadable: {rerr}"

        ok, gerr = self.ensure_in_game()
        if not ok:
            return False, before, None, f"mode cycle aborted, not in-game: {gerr}"

        failures: List[str] = []
        res = run_checked(["xdotool", "key", "Escape"])
        if not res.ok:
            failures.append(f"Escape -> {res.error}")
        time.sleep(1.5)
        nav = [
            (MENU_PAUSE_OPTIONS, 0.8, "Options..."),
            (MENU_OPTIONS_VIDEO, 0.8, "Video Settings..."),
            (MENU_VIDEO_SHADERS, 1.0, "Shaders..."),
            (MENU_SHADERS_OPTIONS, 1.2, "Shader Options..."),
            (MENU_SHADEROPTS_PROBE, 1.0, "Probe Mode button"),
            (MENU_SHADEROPTS_DONE, 2.5, "Done/ShaderOpts"),
            (MENU_SHADERS_DONE, 0.8, "Done/Shaders"),
            (MENU_VIDEO_DONE, 0.8, "Done/Video"),
            (MENU_OPTIONS_DONE, 0.8, "Done/Options"),
        ]
        for (rx, ry), d, label in nav:
            ok_c, cerr = self.click_relative(rx, ry, delay=d)
            if not ok_c:
                failures.append(f"click {label} ({rx},{ry}) -> {cerr}")
        res = run_checked(["xdotool", "key", "Escape"])
        if not res.ok:
            failures.append(f"final Escape -> {res.error}")
        time.sleep(1.0)

        if failures:
            return False, before, None, f"mode cycle GUI steps failed: {'; '.join(failures)}"

        # Poll runtime options file: OptiFine persists asynchronously after Done.
        after: Optional[int] = None
        last_err: Optional[str] = None
        for _ in range(10):
            after, last_err = read_probe_mode_option(self.options_path)
            if last_err is None and after is not None and after != before:
                break
            time.sleep(0.5)
        if last_err is not None or after is None:
            return False, before, after, f"post-cycle PROBE_MODE unreadable: {last_err}"
        if after == before:
            return False, before, after, f"PROBE_MODE did not advance (before={before}, after={after})"
        if not (0 <= after <= 5):
            return False, before, after, f"PROBE_MODE out of range after cycle: {after}"
        return True, before, after, None

    def cycle_to_mode(self, target: int) -> Tuple[bool, Optional[int], Optional[int], Optional[str]]:
        """Advance PROBE_MODE via repeated GUI cycles until it equals target (max 6 steps)."""
        if not (0 <= target <= 5):
            return False, None, None, f"target out of range: {target}"
        start_val, rerr = read_probe_mode_option(self.options_path)
        if rerr is not None:
            return False, start_val, None, f"initial PROBE_MODE unreadable: {rerr}"
        if start_val == target:
            return True, start_val, target, None
        current = start_val
        for _ in range(6):
            ok, _, after, err = self.cycle_shader_option_mode()
            if not ok:
                return False, start_val, after, err
            current = after  # type: ignore[assignment]
            if current == target:
                return True, start_val, current, None
        return False, start_val, current, f"did not reach mode {target} within 6 cycles (ended at {current})"

    def perform_camera_motion(self, duration: float = 2.0) -> Tuple[bool, Optional[str]]:
        ok, ferr = self.focus_window()
        if not ok:
            return False, f"motion aborted, focus failed: {ferr}"
        failures: List[str] = []
        res = run_checked(["xdotool", "keydown", "w"])
        if not res.ok:
            return False, f"keydown w failed: {res.error}"
        start = time.time()
        while time.time() - start < duration:
            res = run_checked(["xdotool", "mousemove_relative", "--", "8", "0"])
            if not res.ok:
                failures.append(f"mousemove_relative -> {res.error}")
            time.sleep(0.06)
        res = run_checked(["xdotool", "keyup", "w"])
        if not res.ok:
            failures.append(f"keyup w -> {res.error}")
        time.sleep(0.4)
        if failures:
            return False, "; ".join(failures)
        return True, None

    # -- manifest ------------------------------------------------------------
    def write_manifest(self, tested_tree_sha: str) -> Tuple[bool, Optional[str]]:
        try:
            res_head = run_checked(["git", "rev-parse", "HEAD"])
            head_now = res_head.stdout.strip() if res_head.ok else "unknown"
            lines = [
                "# Reny Shaders — P0 Capability Probe Screenshot Manifest",
                "",
                f"- **Tested tree SHA:** `{tested_tree_sha}`",
                f"- **HEAD at report time:** `{head_now}`",
                f"- **Generated:** `{datetime.datetime.now(datetime.timezone.utc).isoformat()}`",
                "- **Policy:** Binaries are excluded from Git per `AGENTS.md` asset hygiene rules.",
                f"- **Screenshot dir (configurable via P0_SCREENSHOT_DIR):** `{self.screenshot_dir}`",
                "",
                "## Gate Results",
                "",
                "| Gate | Status | Evidence | Error |",
                "|---|---|---|---|",
            ]
            for g in self.gates:
                lines.append(f"| `{g.name}` | **{g.status}** | {g.evidence} | {g.error or ''} |")
            lines += [
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
                "# 2. Run the P0 validation suite (records tested_tree_sha, fail-closed)",
                "python3 tools/harness/run_p0_suite.py",
                "",
                "# 3. Evaluate capabilities from fresh evidence (explicit exit code)",
                "python3 tools/harness/probe_runner.py",
                "```",
            ])
            self.manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"Wrote screenshot manifest to: {self.manifest_path}")
            return True, None
        except OSError as exc:
            return False, f"manifest write failed: {exc}"

    # -- main flow -----------------------------------------------------------
    def run_all(self, tested_tree_sha: str) -> int:
        print("\n=== STARTING P0 VALIDATION SUITE (FAIL-CLOSED) ===\n")
        print(f"Tested tree SHA: {tested_tree_sha}")
        w, werr = self.get_window()
        if not w:
            self.record_gate(
                "client_window_present",
                "FAIL",
                "Minecraft 1.7.10 window was not detected on X11 display",
                error=werr or "Window query returned empty",
            )
            self.write_manifest(tested_tree_sha)
            return 1
        self.record_gate("client_window_present", "PASS", f"Minecraft window active (ID: {w})")
        ok_g, gerr = self.ensure_in_game()
        if not ok_g:
            self.record_gate("player_in_game_fixture", "FAIL",
                              "Player not verifiably in-game at suite start; aborting",
                              error=gerr)
            self.write_manifest(tested_tree_sha)
            return 1
        self.record_gate("player_in_game_fixture", "PASS", "Player in-game (/seed answered)")

        # -----------------------------------------------------------------
        # 1. EXP-P0-STACK: Overworld baseline
        # -----------------------------------------------------------------
        print("\n--- Gate: EXP-P0-STACK (Overworld) ---")
        ok, evidence, err = self.reload_shaders_via_gui()
        if not ok:
            self.record_gate("shader_reload_gui", "FAIL", "Shader reload via GUI not evidenced", error=err)
        else:
            self.record_gate("shader_reload_gui", "PASS", f"Reload evidenced: {evidence}")

        ok, _, err = self.capture_screen(
            "exp_p0_stack_overworld_day_still",
            "Overworld day scene rendering with terrain, water, foliage, and mode badge",
        )
        if not ok:
            self.record_gate("capture_overworld_still", "FAIL", "Overworld still capture failed", error=err)
        else:
            self.record_gate("capture_overworld_still", "PASS", "Captured Overworld still screenshot")

        ok_m, merr = self.perform_camera_motion(1.5)
        if not ok_m:
            self.record_gate("camera_motion_overworld", "FAIL", "Camera motion failed", error=merr)
        else:
            self.record_gate("camera_motion_overworld", "PASS", "Camera motion executed (W + yaw)")
        ok, _, err = self.capture_screen(
            "exp_p0_stack_overworld_day_motion",
            "Overworld camera movement without geometry tears or visual corruption",
        )
        if not ok:
            self.record_gate("capture_overworld_motion", "FAIL", "Overworld motion capture failed", error=err)
        else:
            self.record_gate("capture_overworld_motion", "PASS", "Captured Overworld motion screenshot")

        ok_c, evidence, cerr = self.send_chat_command_verified("/time set 18000", CONFIRM_TIME_SET)
        if not ok_c:
            self.record_gate("time_set_night", "FAIL", "Server did not confirm '/time set 18000'", error=cerr)
        else:
            time.sleep(1.0)
            self.record_gate("time_set_night", "PASS", f"Night time server-confirmed: {evidence}")
        ok, _, err = self.capture_screen(
            "exp_p0_stack_overworld_night",
            "Overworld night scene verifying dark sky, stars, and emissive contrast",
        )
        if not ok:
            self.record_gate("capture_overworld_night", "FAIL", "Overworld night capture failed", error=err)
        else:
            self.record_gate("capture_overworld_night", "PASS", "Captured Overworld night screenshot")

        # -----------------------------------------------------------------
        # 2. EXP-P0-CAP: Modes 1..5 via verified GUI option cycling
        # -----------------------------------------------------------------
        print("\n--- Gate: EXP-P0-CAP (Diagnostic Probe Modes) ---")

        def goto_and_capture(
            gate_base: str,
            target_mode: int,
            scenario: str,
            observation: str,
            settle: float = 0.8,
        ) -> None:
            ok_cy, before, after, cyerr = self.cycle_to_mode(target_mode)
            if not ok_cy or after != target_mode:
                self.record_gate(
                    f"{gate_base}_mode_change",
                    "FAIL",
                    f"PROBE_MODE did not reach {target_mode} (before={before}, after={after})",
                    error=cyerr,
                )
                return
            self.record_gate(
                f"{gate_base}_mode_change",
                "PASS",
                f"PROBE_MODE reached {target_mode} (from {before}), persisted in optionsshaders.txt",
            )
            time.sleep(settle)
            ok_s, _, serr = self.capture_screen(scenario, observation)
            if not ok_s:
                self.record_gate(f"{gate_base}_capture", "FAIL", f"{scenario} capture failed", error=serr)
            else:
                self.record_gate(f"{gate_base}_capture", "PASS", f"Captured {scenario} at PROBE_MODE={after}")

        goto_and_capture(
            "mode1_hud", 1, "exp_p0_cap_mode1_uniforms_hud",
            "Mode 1 HUD verifying frameCounter heartbeat, frameTime bar, sunPosition, and worldTime",
        )

        ok_cy, before, after, cyerr = self.cycle_to_mode(2)
        if not ok_cy or after != 2:
            self.record_gate("history_mode_change", "FAIL",
                              f"PROBE_MODE did not reach 2 (before={before}, after={after})", error=cyerr)
        else:
            self.record_gate("history_mode_change", "PASS",
                              f"PROBE_MODE reached 2 (from {before}), persisted in optionsshaders.txt")

        # Mode 2 still: reuse the mode-2 state just reached, no extra cycle needed
        # for the still itself, but the cycle gate above already proved entry.
        time.sleep(1.5)
        ok, _, err = self.capture_screen(
            "exp_p0_history_still_persistent_trail",
            "Mode 2 persistent trailing arc in colortex3 confirming colortex3Clear = false",
        )
        if not ok:
            self.record_gate("capture_history_trail", "FAIL", "History still capture failed", error=err)
        else:
            self.record_gate("capture_history_trail", "PASS", "Captured History still screenshot")

        ok_m, merr = self.perform_camera_motion(1.5)
        if not ok_m:
            self.record_gate("camera_motion_history", "FAIL", "History camera motion failed", error=merr)
        else:
            self.record_gate("camera_motion_history", "PASS", "History camera motion executed")
        ok, _, err = self.capture_screen(
            "exp_p0_history_motion", "Mode 2 camera motion with persistent screen-space trail",
        )
        if not ok:
            self.record_gate("capture_history_motion", "FAIL", "History motion capture failed", error=err)
        else:
            self.record_gate("capture_history_motion", "PASS", "Captured History motion screenshot")

        ok_c, evidence, cerr = self.send_chat_command_verified("/tp ~50 ~ ~50", CONFIRM_TELEPORTED)
        if not ok_c:
            self.record_gate("teleport_command", "FAIL", "Server did not confirm teleport", error=cerr)
        else:
            time.sleep(0.8)
            self.record_gate("teleport_command", "PASS", f"Teleport server-confirmed: {evidence}")
        ok, _, err = self.capture_screen(
            "exp_p0_history_after_teleport",
            "Mode 2 teleport cut demonstrating retention of screen-space buffer",
        )
        if not ok:
            self.record_gate("capture_history_teleport", "FAIL", "History teleport capture failed", error=err)
        else:
            self.record_gate("capture_history_teleport", "PASS", "Captured History teleport screenshot")

        ok_r, rerr = self.resize_window("0,200,100,1024,600")
        if not ok_r:
            self.record_gate("resize_to_1024x600", "FAIL", "Resize to 1024x600 failed", error=rerr)
        else:
            time.sleep(1.5)
            self.record_gate("resize_to_1024x600", "PASS", "Resize to 1024x600 executed")
        ok, _, err = self.capture_screen(
            "exp_p0_history_after_resize",
            "Mode 2 window resize to 1024x600 confirming clean FBO reallocation",
        )
        if not ok:
            self.record_gate("capture_history_resize", "FAIL", "History resize capture failed", error=err)
        else:
            self.record_gate("capture_history_resize", "PASS", "Captured History resize screenshot")
        ok_r, rerr = self.resize_window("0,320,212,1280,720")
        if not ok_r:
            self.record_gate("resize_restore_1280x720", "FAIL", "Restore to 1280x720 failed", error=rerr)
        else:
            time.sleep(1.0)
            self.record_gate("resize_restore_1280x720", "PASS", "Restore to 1280x720 executed")

        goto_and_capture(
            "material_mapping", 3, "exp_p0_material_mapping_swatches",
            "Mode 3 material ID visualization with false coloring from block.properties",
        )
        goto_and_capture(
            "formats_split", 4, "exp_p0_formats_fp16_r11f_split",
            "Mode 4 split screen verifying RGBA16F (left) and R11F_G11F_B10F (right) buffers",
        )
        goto_and_capture(
            "deferred_pass", 5, "exp_p0_deferred_pass_confirmed",
            "Mode 5 green banner confirming deferred pass execution and RENY_DEFERRED_MAGIC communication",
        )
        # Return to Mode 0 for dimensions (verified as well).
        ok_cy, before, after, cyerr = self.cycle_to_mode(0)
        if not ok_cy or after != 0:
            self.record_gate("return_mode_cycle", "FAIL",
                              f"Return to mode 0 not evidenced (before={before}, after={after})", error=cyerr)
        else:
            self.record_gate("return_mode_cycle", "PASS", f"Returned to PROBE_MODE 0 (from {before})")

        # -----------------------------------------------------------------
        # 3. EXP-P0-DIM: fresh-log dimension transitions
        # -----------------------------------------------------------------
        print("\n--- Gate: EXP-P0-DIM (Dimension Transitions) ---")
        cursors = capture_all(self.log_paths)
        bad = [c for c in cursors if c.error is not None]
        if bad:
            self.record_gate("dim_nether_transition", "FAIL",
                              "Nether wait aborted: log cursor failed",
                              error="; ".join(f"{c.path.name}: {c.error}" for c in bad))
        else:
            ok_c, evidence, cerr = self.send_chat_command_verified(
                "/setblock ~ ~ ~ portal", CONFIRM_BLOCK_PLACED)
            if not ok_c:
                self.record_gate("dim_nether_command", "FAIL", "Server did not confirm Nether portal setblock", error=cerr)
            else:
                self.record_gate("dim_nether_command", "PASS", f"Nether portal server-confirmed: {evidence}")
                wait = wait_for_fresh_combined(cursors, DIM_SWITCH_FRESH_PATTERN, timeout=45.0)
                if not wait.matched:
                    self.record_gate("dim_nether_transition", "FAIL",
                                      f"Fresh Nether transition not observed: {wait.evidence}", error=wait.error)
                else:
                    extra = f" (rotation seen: {wait.truncated_or_rotated})" if wait.truncated_or_rotated else ""
                    self.record_gate("dim_nether_transition", "PASS",
                                      f"Fresh Nether transition confirmed: {wait.evidence}{extra}")

        time.sleep(3.0)
        ok, _, err = self.capture_screen(
            "exp_p0_dim_nether_smoke", "Nether DIM -1 rendering with world-1 shader override badge (red)",
        )
        if not ok:
            self.record_gate("capture_nether_smoke", "FAIL", "Nether smoke capture failed", error=err)
        else:
            self.record_gate("capture_nether_smoke", "PASS", "Captured Nether smoke screenshot")

        cursors = capture_all(self.log_paths)
        bad = [c for c in cursors if c.error is not None]
        if bad:
            self.record_gate("dim_return_transition", "FAIL",
                              "Return wait aborted: log cursor failed",
                              error="; ".join(f"{c.path.name}: {c.error}" for c in bad))
        else:
            ok_c, evidence, cerr = self.send_chat_command_verified(
                "/setblock ~ ~ ~ portal", CONFIRM_BLOCK_PLACED)
            if not ok_c:
                self.record_gate("dim_return_command", "FAIL", "Server did not confirm return portal setblock", error=cerr)
            else:
                wait = wait_for_fresh_combined(cursors, DIM_SWITCH_FRESH_PATTERN, timeout=45.0)
                if not wait.matched:
                    self.record_gate("dim_return_transition", "FAIL",
                                      f"Fresh Overworld return not observed: {wait.evidence}", error=wait.error)
                else:
                    self.record_gate("dim_return_transition", "PASS",
                                      f"Fresh Overworld return confirmed: {wait.evidence}")
        time.sleep(3.0)
        ok_m, merr = self.perform_camera_motion(1.5)
        if not ok_m:
            self.record_gate("camera_motion_return", "FAIL", "Return camera motion failed", error=merr)
        else:
            self.record_gate("camera_motion_return", "PASS", "Return camera motion executed")

        cursors = capture_all(self.log_paths)
        bad = [c for c in cursors if c.error is not None]
        if bad:
            self.record_gate("dim_end_transition", "FAIL",
                              "End wait aborted: log cursor failed",
                              error="; ".join(f"{c.path.name}: {c.error}" for c in bad))
        else:
            ok_c, evidence, cerr = self.send_chat_command_verified(
                "/setblock ~ ~ ~ end_portal", CONFIRM_BLOCK_PLACED)
            if not ok_c:
                self.record_gate("dim_end_command", "FAIL", "Server did not confirm end portal setblock", error=cerr)
            else:
                self.record_gate("dim_end_command", "PASS", f"End portal server-confirmed: {evidence}")
                wait = wait_for_fresh_combined(cursors, DIM_SWITCH_FRESH_PATTERN, timeout=45.0)
                if not wait.matched:
                    self.record_gate("dim_end_transition", "FAIL",
                                      f"Fresh End transition not observed: {wait.evidence}", error=wait.error)
                else:
                    extra = f" (rotation seen: {wait.truncated_or_rotated})" if wait.truncated_or_rotated else ""
                    self.record_gate("dim_end_transition", "PASS",
                                      f"Fresh End transition confirmed: {wait.evidence}{extra}")

        time.sleep(3.0)
        ok, _, err = self.capture_screen(
            "exp_p0_dim_end_smoke", "The End DIM 1 rendering with world1 shader override badge (purple)",
        )
        if not ok:
            self.record_gate("capture_end_smoke", "FAIL", "End smoke capture failed", error=err)
        else:
            self.record_gate("capture_end_smoke", "PASS", "Captured End smoke screenshot")

        # -----------------------------------------------------------------
        # Final summary and manifest
        # -----------------------------------------------------------------
        ok_w, werr = self.write_manifest(tested_tree_sha)
        if not ok_w:
            self.record_gate("manifest_write", "FAIL", "Manifest write failed", error=werr)
        else:
            self.record_gate("manifest_write", "PASS", f"Manifest written to {self.manifest_path}")

        failed_gates = [g.name for g in self.gates if g.status == "FAIL"]
        if self.overall_success and len(failed_gates) == 0:
            print("\n=== ALL P0 SUITE GATES PASSED (FAIL-CLOSED) ===\n")
            return 0
        print(f"\n=== P0 SUITE FINISHED WITH FAILURES: {failed_gates} ===\n")
        return 1


def _git_rev_parse_head() -> str:
    res = run_checked(["git", "rev-parse", "HEAD"])
    return res.stdout.strip() if res.ok and res.stdout.strip() else "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="P0 Validation Suite Runner (fail-closed)")
    parser.add_argument("--commit-sha", type=str, default="",
                        help="Tested tree SHA to record (defaults to current HEAD)")
    parser.add_argument("--update-repo-manifest", action="store_true",
                        help="Update benchmarks/artifacts/p0_probe/MANIFEST.md in repository")
    args = parser.parse_args()

    tested_sha = args.commit_sha.strip() or _git_rev_parse_head()
    suite = P0Suite(update_repo_manifest=args.update_repo_manifest)
    return suite.run_all(tested_sha)


if __name__ == "__main__":
    sys.exit(main())
