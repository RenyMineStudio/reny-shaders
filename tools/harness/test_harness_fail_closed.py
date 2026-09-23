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
    evaluator_exit_code,
    evaluate_capabilities,
    mandatory_failures,
    parse_shader_logs,
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
def test_rotation_is_not_accepted_as_fresh_evidence() -> None:
    """Rotation cannot make pre-action lines trustworthy."""
    with tempfile.NamedTemporaryFile("w+", suffix=".log", delete=False) as f:
        f.write("Loading dimension -1 (old session evidence)\n")
        f.flush()
        log_path = Path(f.name)
    try:
        cursor = LogCursor.capture(log_path)
        log_path.unlink()
        log_path.write_text("Loading dimension -1 (rotated old evidence)\n", encoding="utf-8")
        wait = wait_for_fresh_log(cursor, r"Loading dimension -1", timeout=1.0)
        check("rotated_stale_log_rejected",
              wait.matched is False and wait.truncated_or_rotated,
              f"matched={wait.matched}, rotated={wait.truncated_or_rotated}, error={wait.error}")
    finally:
        log_path.unlink(missing_ok=True)


def test_capability_predicates_require_specific_evidence() -> None:
    """Parser/source presence alone must not promote runtime claims."""
    log_analysis = {
        "pack_loaded": True, "pack_name": "X", "worlds_detected": "-1, 1",
        "block_mapping_parsed": True, "block_mapping_warnings": [],
        "block_mapping_invalid_ids": [], "block_mapping_accepted_ids": [],
        "custom_uniforms": [], "buffer_formats": {}, "skip_clear_buffers": [],
        "ping_pong_flips": [], "programs_loaded": ["final"],
        "programs_disabled": [], "custom_textures_loaded": [],
        "custom_noise_loaded": False, "framebuffer_created": True,
        "errors": [], "warnings": [],
    }
    with tempfile.TemporaryDirectory() as td:
        instance = Path(td)
        (instance / "optionsshaders.txt").write_text("PROBE_MODE=1\n", encoding="utf-8")
        shots = instance / "shots"
        shots.mkdir()
        (shots / "exp_p0_cap_mode1_uniforms_hud.png").write_bytes(b"not visual evidence")
        caps = evaluate_capabilities(
            log_analysis, {}, Path(td) / "missing.jar", instance, shots,
        )
    check("profiles_require_mode_transition",
          caps["profiles/options"]["status"] == "INCONCLUSIVE",
          caps["profiles/options"]["evidence"])
    check("vanilla_mapping_requires_acceptance",
          caps["block.properties (vanilla)"]["status"] == "INCONCLUSIVE",
          caps["block.properties (vanilla)"]["evidence"])
    check("uniforms_require_exercised_evidence",
          caps["frameCounter / frameTime"]["status"] == "INCONCLUSIVE",
          caps["frameCounter / frameTime"]["evidence"])


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

def test_xml_and_plain_logs_normalize_to_same_events() -> None:
    plain = (
        "[Shaders] Program loaded: final\n"
        "[Shaders] flipped buffers after composite: 0, 3, 4\n"
        "[Shaders] Custom uniform: reny_time\n"
    )
    xml = "".join(
        f"<log4j:Message><![CDATA[{line.rstrip()}]]></log4j:Message>\n"
        for line in plain.splitlines()
    )
    plain_events = parse_shader_logs(plain)
    xml_events = parse_shader_logs(xml)
    check("xml_plain_program_events_equal",
          plain_events["programs_loaded"] == xml_events["programs_loaded"] == ["final"],
          f"plain={plain_events['programs_loaded']}, xml={xml_events['programs_loaded']}")
    check("xml_plain_flip_events_equal",
          plain_events["ping_pong_flips"] == xml_events["ping_pong_flips"],
          f"plain={plain_events['ping_pong_flips']}, xml={xml_events['ping_pong_flips']}")
    check("xml_plain_uniform_events_equal",
          plain_events["custom_uniforms"] == xml_events["custom_uniforms"] == ["reny_time"],
          f"plain={plain_events['custom_uniforms']}, xml={xml_events['custom_uniforms']}")


def test_world_capability_is_required_and_strict() -> None:
    base = {
        "pack_loaded": True, "pack_name": "X", "worlds_detected": None,
        "block_mapping_parsed": False, "block_mapping_warnings": [],
        "block_mapping_invalid_ids": [], "block_mapping_accepted_ids": [],
        "custom_uniforms": [], "buffer_formats": {}, "skip_clear_buffers": [],
        "ping_pong_flips": [], "programs_loaded": ["deferred", "composite", "final", "shadow"],
        "programs_disabled": [], "custom_textures_loaded": [],
        "custom_noise_loaded": False, "framebuffer_created": True,
        "errors": [], "warnings": [],
    }
    missing = evaluate_capabilities(base, {}, Path("/missing.jar"), Path("/missing-instance"), None)
    check("world_capability_missing_is_not_pass",
          missing["world<id>"]["status"] != "PASS" and
          missing["world<id>"]["status"] in ("FAIL", "INCONCLUSIVE"),
          f"status={missing.get('world<id>')}")


def test_mandatory_capabilities_happy_path_has_no_failures() -> None:
    analysis = {
        "pack_loaded": True, "pack_name": "X", "worlds_detected": "-1, 1",
        "block_mapping_parsed": True,
        "block_mapping_warnings": [],
        "block_mapping_invalid_ids": [],
        "block_mapping_accepted_ids": [f"block.{i}" for i in range(100, 110)],
        "probe_mode_registration": True,
        "probe_mode_transition_values": [0, 1],
        "uniforms_exercised": True,
        "custom_uniforms": [], "buffer_formats": {
            "colortex2": "RGBA16F", "colortex4": "R11F_G11F_B10F",
        },
        "skip_clear_buffers": ["colortex3"],
        "ping_pong_flips": ["flip"],
        "world_folder_loads": ["world-1/", "world1/"],
        "programs_loaded": [
            "gbuffers_terrain", "gbuffers_entities", "gbuffers_water",
            "gbuffers_hand", "gbuffers_textured", "deferred", "deferred_last",
            "composite", "final", "shadow",
        ],
        "programs_disabled": [], "custom_textures_loaded": [],
        "custom_noise_loaded": False, "framebuffer_created": True,
        "errors": [], "warnings": [],
    }
    with tempfile.TemporaryDirectory() as td:
        instance = Path(td)
        (instance / "optionsshaders.txt").write_text("PROBE_MODE=1\n", encoding="utf-8")
        caps = evaluate_capabilities(
            analysis, {}, Path("/missing.jar"), instance, None,
        )
    failed = mandatory_failures(caps)
    check("mandatory_happy_path_has_no_failures",
          not failed and evaluator_exit_code(caps) == 0 and
          all(caps[name]["status"] == "PASS"
              for name in (
                  "EXP-P0-STACK", "deferred", "composite", "final",
                  "shadow", "world<id>", "profiles/options",
                  "block.properties (vanilla)",
                  "buffer_formats (FP16 / R11F)",
                  "colortex_skip_clear", "frameCounter / frameTime",
              )),
          f"failures={failed}, exit={evaluator_exit_code(caps)}")


def test_generic_reinit_does_not_prove_dimension_target() -> None:
    from run_p0_suite import dimension_pattern_for
    check("dimension_reinit_only_not_target_evidence",
          "Reset world renderers" not in dimension_pattern_for("nether"),
          dimension_pattern_for("nether"))
    check("dimension_patterns_are_target_specific",
          all(token in dimension_pattern_for(target)
              for target, token in (("nether", "Loading dimension -1"),
                                    ("end", "Loading dimension 1"),
                                    ("overworld", "Loading dimension 0"))),
          "target patterns include explicit dimension ids")


def test_probe_mode_parser_handles_real_lines() -> None:
    """Real PROBE_MODE evidence through parse_shader_logs must not raise."""
    log = "PROBE_MODE registered\nPROBE_MODE changed: 1\n"
    try:
        events = parse_shader_logs(log)
    except Exception as exc:  # noqa: BLE001
        check("probe_mode_parser_no_keyerror", False, f"raised {type(exc).__name__}: {exc}")
        return
    check("probe_mode_parser_no_keyerror", True, "parse_shader_logs returned without exception")
    check("probe_mode_parser_registration",
          events.get("probe_mode_registration") is True,
          f"registration={events.get('probe_mode_registration')}")
    check("probe_mode_parser_transition_values",
          events.get("probe_mode_transition_values") == [1],
          f"transitions={events.get('probe_mode_transition_values')}")


def test_probe_mode_parser_bounded_transitions() -> None:
    """Bounded 0 -> 1 -> 2 transition sequence must be recorded in order."""
    log = "PROBE_MODE changed: 0\nPROBE_MODE changed: 1\nPROBE_MODE changed: 2\n"
    try:
        events = parse_shader_logs(log)
    except Exception as exc:  # noqa: BLE001
        check("probe_mode_parser_bounded_no_keyerror", False, f"raised {type(exc).__name__}: {exc}")
        return
    check("probe_mode_parser_bounded_no_keyerror", True, "parse_shader_logs returned without exception")
    check("probe_mode_parser_bounded_values",
          events.get("probe_mode_transition_values") == [0, 1, 2],
          f"transitions={events.get('probe_mode_transition_values')}")


def test_dimension_events_separated_from_world_folder_loads() -> None:
    """'Loading dimension' lines are dimension events, never shader-folder evidence."""
    log = "[Server thread/INFO]: Loading dimension -1\n[Server thread/INFO]: Loading dimension 1\n"
    events = parse_shader_logs(log)
    check("dimension_events_recorded",
          events.get("dimension_events") == [-1, 1],
          f"dimension_events={events.get('dimension_events')}")
    check("dimension_lines_not_folder_loads",
          events.get("world_folder_loads") == [],
          f"world_folder_loads={events.get('world_folder_loads')}")


def test_world_capability_negative_control() -> None:
    """Dimension lines without shader-folder evidence must never PASS world<id>."""
    log = ("[Shaders] Loaded shaderpack: Reny-Capability-Probe\n"
           "[Server thread/INFO]: Loading dimension -1\n"
           "[Server thread/INFO]: Loading dimension 1\n")
    events = parse_shader_logs(log)
    caps = evaluate_capabilities(
        events, {}, Path("/tmp/opencode/reny-p0-no-such-optifine.jar"),
        Path("/tmp/opencode/reny-p0-no-instance"), None,
    )
    status = caps["world<id>"]["status"]
    check("world_capability_negative_control",
          status != "PASS" and status in ("FAIL", "INCONCLUSIVE"),
          f"status={status}: {caps['world<id>']['evidence']}")


def test_world_capability_positive_control() -> None:
    """Shader-loader folder evidence (Program loaded: world-1/ + world1/) may PASS world<id>."""
    log = ("[Shaders] Loaded shaderpack: Reny-Capability-Probe\n"
           "[Shaders] Program loaded: world-1/gbuffers_textured\n"
           "[Shaders] Program loaded: world1/gbuffers_textured\n")
    events = parse_shader_logs(log)
    check("world_folder_loads_positive_evidence",
          set(events.get("world_folder_loads", [])) == {"world-1/", "world1/"},
          f"world_folder_loads={events.get('world_folder_loads')}")
    caps = evaluate_capabilities(
        events, {}, Path("/tmp/opencode/reny-p0-no-such-optifine.jar"),
        Path("/tmp/opencode/reny-p0-no-instance"), None,
    )
    check("world_capability_positive_control",
          caps["world<id>"]["status"] == "PASS",
          f"status={caps['world<id>']['status']}: {caps['world<id>']['evidence']}")


def test_overworld_pattern_uses_target_specific_marker() -> None:
    """Overworld return must use the pack-root reload marker, never world0/."""
    import re
    from run_p0_suite import dimension_pattern_for
    pattern = dimension_pattern_for("overworld")
    check("overworld_pattern_has_no_world0",
          "world0" not in pattern,
          f"pattern={pattern!r}")
    # Real observed return-to-Overworld signature (2026-09-23 client_stdout.log,
    # 16:28:59 'Block placed' -> Uninit -> pack-root gbuffers reload):
    # the End/Nether folders use world1//world-1/ prefixes, the Overworld uses
    # the pack root, so a bare 'Program loaded: gbuffers_*' line is the marker.
    root_reload = ("[Shaders] Uninit\n"
                   "[Shaders] Program loaded: gbuffers_basic\n"
                   "[Shaders] Program loaded: gbuffers_textured\n")
    check("overworld_pattern_matches_root_reload",
          re.search(pattern, root_reload) is not None,
          f"pattern={pattern!r}")
    generic_reinit = ("[Shaders] Reset world renderers\n"
                      "[Shaders] Framebuffer created.\n")
    check("overworld_pattern_rejects_generic_reinit",
          re.search(pattern, generic_reinit) is None,
          f"pattern={pattern!r}")



def main() -> int:
    print("=== P0 HARNESS FAIL-CLOSED VERIFICATION ===\n")
    test_x11_command_failure()
    test_screenshot_failure()
    test_log_read_failure()
    test_stale_log_match()
    test_rotation_is_not_accepted_as_fresh_evidence()
    test_scale_tristate()
    test_capability_predicates_require_specific_evidence()
    test_verified_command_no_window()
    test_mandatory_fail_exit()
    test_xml_and_plain_logs_normalize_to_same_events()
    test_world_capability_is_required_and_strict()
    test_mandatory_capabilities_happy_path_has_no_failures()
    test_generic_reinit_does_not_prove_dimension_target()
    test_probe_mode_parser_handles_real_lines()
    test_probe_mode_parser_bounded_transitions()
    test_dimension_events_separated_from_world_folder_loads()
    test_world_capability_negative_control()
    test_world_capability_positive_control()
    test_overworld_pattern_uses_target_specific_marker()
    print(f"\n{PASS_COUNT} negative controls passed, {len(FAILURES)} failed: {FAILURES}")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
