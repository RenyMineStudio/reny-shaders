#!/usr/bin/env python3
"""
Reny Shaders — P0 harness fail-closed verification (static, no Minecraft needed).

Demonstrates controlled failures:
 1. X11 command failure  -> click_relative returns (False, error)
 2. Screenshot failure   -> capture_screen returns failure on scrot error
 3. Log read failure     -> fresh-log read reports error, wait does not match
 4. Stale-log match      -> old 'Loading dimension -1' never satisfies a new wait
 5. Mandatory FAIL       -> probe_runner evaluator exits non-zero

Exit code: 0 only if ALL negative controls behave as specified.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_p0_suite import (  # noqa: E402
    LogCursor,
    P0Suite,
    read_fresh_log,
    wait_for_fresh_log,
)
from probe_runner import (  # noqa: E402
    evaluate_capabilities,
    mandatory_failures,
    verify_scale_bytecode,
)

PASS_COUNT = 0
FAILURES: List[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS_COUNT
    if cond:
        PASS_COUNT += 1
        print(f"[✓] {name} — {detail}")
    else:
        FAILURES.append(name)
        print(f"[✗] {name} — FAILED: {detail}")


def test_x11_command_failure() -> None:
    """xdotool binary shadowed by a failing stub must fail the click."""
    import run_p0_suite as suite_mod
    orig = suite_mod.run_checked
    from run_p0_suite import CheckedResult

    def fake_fail(args, timeout=30.0):
        return CheckedResult(ok=False, returncode=1, stdout="", stderr="stub failure", error="exit=1: stub failure")

    suite_mod.run_checked = fake_fail
    try:
        suite = P0Suite.__new__(P0Suite)
        ok, err = suite.click_relative(0.5, 0.5)
        check("x11_command_failure", ok is False and err is not None,
              f"click_relative -> ok={ok}, err={err}")
    finally:
        suite_mod.run_checked = orig


def test_screenshot_failure() -> None:
    """scrot failure must yield capture failure, never a phantom screenshot."""
    import run_p0_suite as suite_mod
    orig = suite_mod.run_checked
    from run_p0_suite import CheckedResult

    calls = {"n": 0}

    def fake(args, timeout=30.0):
        calls["n"] += 1
        # Window search succeeds; scrot fails.
        if args and args[0] == "xdotool":
            return CheckedResult(ok=True, returncode=0, stdout="12345\n")
        return CheckedResult(ok=False, returncode=1, stdout="", stderr="scrot: failed", error="exit=1: scrot: failed")

    suite_mod.run_checked = fake
    try:
        with tempfile.TemporaryDirectory() as td:
            suite = P0Suite.__new__(P0Suite)
            suite.screenshot_dir = Path(td)
            suite.captures = []
            # Stub geometry to avoid xwininfo dependency.
            suite.get_window_geometry = lambda win: ((0, 0, 1280, 720), None)  # type: ignore[method-assign]
            ok, path, err = suite.capture_screen("injected_fail", "failure-injection")
            check("screenshot_failure", ok is False and path is None and err is not None,
                  f"capture_screen -> ok={ok}, err={err}")
    finally:
        suite_mod.run_checked = orig


def test_log_read_failure() -> None:
    """Unreadable/missing log must produce an explicit diagnostic, not silent pass."""
    missing = Path("/tmp/opencode/reny-p0-does-not-exist-xyz/latest.log")
    cursor = LogCursor.capture(missing)
    check("log_cursor_missing",
          cursor.error is not None,
          f"cursor.error={cursor.error}")
    fresh = read_fresh_log(cursor)
    check("log_read_failure",
          fresh.error is not None and fresh.lines == "",
          f"fresh.error={fresh.error}")
    wait = wait_for_fresh_log(cursor, r"Loading dimension -1", timeout=1.0)
    check("log_wait_on_bad_cursor",
          wait.matched is False and wait.error is not None,
          f"matched={wait.matched}, error={wait.error}")


def test_stale_log_match() -> None:
    """An old 'Loading dimension -1' line must NOT satisfy a fresh wait."""
    with tempfile.NamedTemporaryFile("w+", suffix=".log", delete=False) as f:
        f.write("[Server thread/INFO]: Loading dimension -1 (old session evidence)\n")
        f.flush()
        log_path = Path(f.name)
    try:
        cursor = LogCursor.capture(log_path)  # cursor AFTER the stale line
        check("stale_cursor_clean", cursor.error is None, f"cursor size={cursor.size}")
        # Fresh wait with no new content must time out negatively.
        wait = wait_for_fresh_log(cursor, r"Loading dimension -1", timeout=1.0)
        check("stale_log_rejected",
              wait.matched is False,
              f"matched={wait.matched}, evidence={wait.evidence}")
        # Appending a genuinely new line must satisfy the same wait.
        with log_path.open("a", encoding="utf-8") as af:
            af.write("[Server thread/INFO]: Loading dimension -1 (fresh transition)\n")
        wait2 = wait_for_fresh_log(cursor, r"Loading dimension -1", timeout=3.0)
        check("fresh_log_accepted",
              wait2.matched is True,
              f"matched={wait2.matched}, evidence={wait2.evidence}")
    finally:
        log_path.unlink(missing_ok=True)


def test_scale_tristate() -> None:
    """Missing jar / bad zip => INCONCLUSIVE, never REJECTED."""
    v = verify_scale_bytecode(Path("/tmp/opencode/reny-p0-no-such-optifine.jar"))
    check("scale_missing_jar_inconclusive",
          v.outcome == "INCONCLUSIVE" and "REJECT" not in v.outcome,
          f"outcome={v.outcome}: {v.message}")
    with tempfile.NamedTemporaryFile("wb", suffix=".jar", delete=False) as f:
        f.write(b"not a zip at all")
        bad = Path(f.name)
    try:
        v2 = verify_scale_bytecode(bad)
        check("scale_bad_zip_inconclusive",
              v2.outcome == "INCONCLUSIVE",
              f"outcome={v2.outcome}: {v2.message}")
    finally:
        bad.unlink(missing_ok=True)


def test_mandatory_fail_exit() -> None:
    """A mandatory FAIL capability must be reported by mandatory_failures()."""
    log_analysis = {
        "pack_loaded": True, "pack_name": "X", "worlds_detected": None,
        "block_mapping_parsed": False, "block_mapping_warnings": [],
        "block_mapping_invalid_ids": [], "custom_uniforms": [],
        "buffer_formats": {}, "skip_clear_buffers": [], "ping_pong_flips": [],
        "programs_loaded": [], "programs_disabled": [],
        "custom_textures_loaded": [], "custom_noise_loaded": False,
        "framebuffer_created": False, "errors": [], "warnings": [],
    }
    caps = evaluate_capabilities(
        log_analysis, {}, Path("/tmp/opencode/reny-p0-no-such-optifine.jar"),
        Path("/tmp/opencode/reny-p0-no-instance"), None,
    )
    failed = mandatory_failures(caps)
    check("mandatory_fail_detected",
          len(failed) > 0,
          f"mandatory failures={failed}")
    # Exit-code contract: non-zero iff mandatory failures exist.
    simulated_exit = 2 if failed else 0
    check("mandatory_fail_exit_nonzero", simulated_exit != 0,
          f"simulated evaluator exit={simulated_exit}")


def test_verified_command_no_window() -> None:
    """A state-changing command with no game window must FAIL verification."""
    import tempfile
    from run_p0_suite import P0Suite, SCREENSHOT_DIR
    with tempfile.TemporaryDirectory() as td:
        suite = P0Suite.__new__(P0Suite)
        suite.instance_dir = Path(td)
        suite.log_paths = [Path(td) / "logs" / "client_stdout.log", Path(td) / "logs" / "latest.log"]
        suite.options_path = Path(td) / "optionsshaders.txt"
        suite.screenshot_dir = Path(td)
        suite.captures = []
        # No MC window exists in this environment: xdotool search fails.
        ok, evidence, err = suite.send_chat_command_verified("/time set 0", r"Set the time to", timeout=2.0)
        check("verified_command_no_window",
              ok is False and not evidence and err is not None,
              f"ok={ok}, err={(err or '')[:120]}")


def main() -> int:
    print("=== P0 HARNESS FAIL-CLOSED VERIFICATION ===\n")
    test_x11_command_failure()
    test_screenshot_failure()
    test_log_read_failure()
    test_stale_log_match()
    test_scale_tristate()
    test_verified_command_no_window()
    test_mandatory_fail_exit()
    print(f"\n{PASS_COUNT} negative controls passed, {len(FAILURES)} failed: {FAILURES}")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
