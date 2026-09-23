#!/usr/bin/env python3
"""
Reny Shaders — P0 Capability Probe & Validation Harness
Target: Minecraft 1.7.10 / Forge 10.13.4.1614 / OptiFine 1.7.10 HD U E7

Evidence policy:
- No capability is PASS without an observed predicate that entails the claim.
- INCONCLUSIVE / UNPROVEN is never promoted to PASS.
- Mandatory FAIL forces a non-zero process exit code.
- scale.<program> uses a tri-state bytecode verdict (never REJECTED on error).
- Reports record tested_tree_sha (tree actually executed) separately from the
  HEAD that carries the generated evidence files, plus an allowlist delta proof.
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
import zipfile
from dataclasses import dataclass
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
INSTALL_DIR = Path(
    os.environ.get(
        "MINECRAFT_INSTALL_DIR",
        str(Path.home() / "Documents/curseforge/minecraft/Install"),
    )
)
JAVA_BIN = INSTALL_DIR / "java" / "jre-legacy" / "bin" / "java"
PACK_NAME = "Reny-Capability-Probe"
SCREENSHOT_DIR = Path(os.environ.get("P0_SCREENSHOT_DIR", "/tmp/opencode/p0_probe_artifacts"))

# Files that a post-test evidence commit is allowed to touch.
# Anything else in tested_tree_sha..HEAD invalidates the provenance claim.
EVIDENCE_ALLOWLIST = {
    "benchmarks/reports/p0_probe_report.json",
    "benchmarks/reports/p0_probe_report.md",
    "benchmarks/artifacts/p0_probe/MANIFEST.md",
}

# Capabilities whose FAIL must fail the process. Everything else
# (Forge mod mapping, custom textures/noise, scale verdict) is informative.
MANDATORY_CAPABILITIES = {
    "EXP-P0-STACK",
    "deferred",
    "composite",
    "final",
    "shadow",
    "includes",
    "world<id>",
    "profiles/options",
    "block.properties (vanilla)",
    "buffer_formats (FP16 / R11F)",
    "colortex_skip_clear",
    "frameCounter / frameTime",
}


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


def get_git_state() -> Tuple[str, bool]:
    res_sha = run_cmd(["git", "rev-parse", "HEAD"])
    commit_sha = res_sha.stdout.strip() if res_sha.returncode == 0 else "unknown"
    res_status = run_cmd(["git", "status", "--porcelain"])
    is_clean = (res_status.returncode == 0) and (len(res_status.stdout.strip()) == 0)
    return commit_sha, is_clean


def check_evidence_delta(tested_sha: str, head_sha: str) -> Tuple[bool, List[str], Optional[str]]:
    """Prove tested_tree_sha..HEAD touches only allowlisted evidence files."""
    if not tested_sha or tested_sha == "unknown" or not head_sha or head_sha == "unknown":
        return False, [], "tested_sha or head_sha unknown; cannot prove delta"
    if tested_sha == head_sha:
        return True, [], None
    res = run_cmd(["git", "diff", "--name-only", f"{tested_sha}..{head_sha}"])
    if res.returncode != 0:
        return False, [], f"git diff failed: {res.stdout[:300]}"
    files = [l.strip() for l in res.stdout.splitlines() if l.strip()]
    non_allowlisted = [f for f in files if f not in EVIDENCE_ALLOWLIST]
    if non_allowlisted:
        return False, files, f"non-evidence files in delta: {non_allowlisted}"
    return True, files, None


def detect_system_info() -> Dict[str, str]:
    info = {
        "os": "Linux",
        "kernel": "unknown",
        "gpu": "unknown",
        "gpu_vendor": "unknown",
        "opengl": "unknown",
        "glsl": "unknown",
        "driver": "unknown",
        "java": "unknown",
    }
    res = run_cmd(["uname", "-srm"])
    if res.returncode == 0:
        info["kernel"] = res.stdout.strip()
    res = run_cmd(["glxinfo"])
    if res.returncode == 0:
        for line in res.stdout.splitlines():
            if "OpenGL vendor string:" in line:
                info["gpu_vendor"] = line.split(":", 1)[1].strip()
            elif "OpenGL renderer string:" in line:
                info["gpu"] = line.split(":", 1)[1].strip()
            elif "OpenGL version string:" in line:
                info["opengl"] = line.split(":", 1)[1].strip()
            elif "OpenGL shading language version string:" in line:
                info["glsl"] = line.split(":", 1)[1].strip()
    if JAVA_BIN.exists():
        res = run_cmd([str(JAVA_BIN), "-version"])
        first_line = res.stdout.splitlines()[0] if res.stdout.splitlines() else "unknown"
        info["java"] = first_line.strip()
    return info


@dataclass
class ScaleVerdict:
    outcome: str  # PRESENT | ABSENT_REJECTED | INCONCLUSIVE
    message: str


def verify_scale_bytecode(optifine_jar: Path) -> ScaleVerdict:
    """Tri-state bytecode inspection; errors never masquerade as REJECTED."""
    if not optifine_jar.is_file():
        return ScaleVerdict(
            "INCONCLUSIVE",
            f"OptiFine jar absent at {optifine_jar}; scale.<program> cannot be judged (need jar)",
        )
    try:
        with zipfile.ZipFile(optifine_jar) as z:
            names = z.namelist()
    except zipfile.BadZipFile as exc:
        return ScaleVerdict("INCONCLUSIVE", f"OptiFine jar is not a valid ZIP: {exc}")
    except OSError as exc:
        return ScaleVerdict("INCONCLUSIVE", f"OptiFine jar unreadable: {exc}")
    targets = ["shadersmod/client/Shaders.class", "shadersmod/client/ShaderPackParser.class"]
    found_targets = [t for t in targets if t in names]
    if not found_targets:
        return ScaleVerdict(
            "INCONCLUSIVE",
            f"Neither {targets} found in OptiFine jar namelist; inspection inconclusive",
        )
    try:
        with zipfile.ZipFile(optifine_jar) as z:
            for cls_name in found_targets:
                data = z.read(cls_name)
                if b"scale." in data or b"programScale" in data:
                    return ScaleVerdict("PRESENT", f"Scale directive symbol present in {cls_name}")
        return ScaleVerdict(
            "ABSENT_REJECTED",
            "Inspected Shaders.class and ShaderPackParser.class in OptiFine E7 jar: "
            "scale.<program> symbols absent (composite-scale commit 5b0151b4 is 2018, post-E7)",
        )
    except (zipfile.BadZipFile, KeyError, OSError) as exc:
        return ScaleVerdict("INCONCLUSIVE", f"Bytecode inspection failed, cannot judge scale: {exc}")


def deploy_shaderpack(instance_dir: Path, target_mode: int = 0) -> Path:
    pack_dir = instance_dir / "shaderpacks" / PACK_NAME
    dest_shaders = pack_dir / "shaders"
    dest_shaders.parent.mkdir(parents=True, exist_ok=True)
    if dest_shaders.is_symlink() or dest_shaders.is_file():
        dest_shaders.unlink()
    elif dest_shaders.is_dir():
        shutil.rmtree(dest_shaders)
    dest_shaders.symlink_to(SHADERS_DIR, target_is_directory=True)
    dest_zip = instance_dir / "shaderpacks" / f"{PACK_NAME}.zip"
    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(SHADERS_DIR):
            for f in files:
                full = Path(root) / f
                rel = full.relative_to(SHADERS_DIR.parent)
                z.write(full, str(rel))
    options_shaders = instance_dir / "optionsshaders.txt"
    options_shaders.parent.mkdir(parents=True, exist_ok=True)
    with options_shaders.open("w", encoding="utf-8") as f:
        f.write(f"shaderPack={PACK_NAME}\n")
        f.write("antialiasingLevel=0\n")
        f.write("normalMapEnabled=true\n")
        f.write("specularMapEnabled=true\n")
        f.write("renderResMul=1.0\n")
        f.write("shadowResMul=1.0\n")
        f.write("handDepthMul=0.125\n")
        f.write("cloudShadow=false\n")
        f.write("oldHandLight=default\n")
        f.write("oldLighting=default\n")
        f.write("tweakBlockDamage=false\n")
        f.write("shadowClipFrustrum=true\n")
        f.write(f"PROBE_MODE={target_mode}\n")
    return pack_dir


def evidence_log_files(instance_dir: Path) -> List[Path]:
    # JVM stdout carries the [Shaders] loader lines while latest.log carries
    # server lines; the exact routing depends on launch flags, so parse both.
    return [
        instance_dir / "logs" / "client_stdout.log",
        instance_dir / "logs" / "latest.log",
    ]


def read_evidence_logs(paths: List[Path], explicit: Optional[Path] = None) -> Tuple[str, List[str], Optional[str]]:
    """Concatenate all readable evidence logs; fail only if NONE are usable."""
    sources = [explicit] if explicit else paths
    parts: List[str] = []
    parsed: List[str] = []
    errors: List[str] = []
    for p in sources:
        try:
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
            parsed.append(str(p))
        except FileNotFoundError:
            errors.append(f"missing: {p}")
        except OSError as exc:
            errors.append(f"unreadable {p}: {exc}")
    if not parsed:
        return "", parsed, "no evidence log readable: " + "; ".join(errors)
    return "\n".join(parts), parsed, None


_CDATA_RE = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.DOTALL)
_XML_TAG_RE = re.compile(r"<[^>]+>")


def normalize_log_line(line: str) -> str:
    """Return the semantic payload from plain text or Log4j XML output."""
    match = _CDATA_RE.search(line)
    if match:
        return match.group(1).strip()
    return _XML_TAG_RE.sub("", line).strip()


def _append_unique(items: List[Any], value: Any) -> None:
    if value not in items:
        items.append(value)


def parse_shader_logs(log_text: str) -> Dict[str, Any]:
    """Parse evidence logs for OptiFine shader loader events and errors."""
    results: Dict[str, Any] = {
        "pack_loaded": False,
        "pack_name": None,
        "worlds_detected": None,
        "block_mapping_parsed": False,
        "block_mapping_accepted_ids": [],
        "block_mapping_warnings": [],
        "block_mapping_invalid_ids": [],
        "probe_mode_registration": False,
        "probe_mode_transition_values": [],
        "dimension_events": [],
        "world_folder_loads": [],
        "uniforms_exercised": False,
        "custom_uniforms": [],
        "buffer_formats": {},
        "skip_clear_buffers": [],
        "ping_pong_flips": [],
        "programs_loaded": [],
        "programs_disabled": [],
        "custom_textures_loaded": [],
        "custom_noise_loaded": False,
        "framebuffer_created": False,
        "errors": [],
        "warnings": [],
    }
    for line in log_text.splitlines():
        line = normalize_log_line(line)
        if "[Shaders] Loaded shaderpack:" in line:
            results["pack_loaded"] = True
            results["pack_name"] = line.split("Loaded shaderpack:", 1)[1].strip()
        elif "[Shaders] Loading shader pack:" in line:
            results["pack_loaded"] = True
            results["pack_name"] = line.split("Loading shader pack:", 1)[1].strip()
        elif "[Shaders] Worlds:" in line:
            results["worlds_detected"] = line.split("Worlds:", 1)[1].strip()
        elif m_dim := re.search(r"Loading dimension\s*(-?\d+)", line):
            # Dimension lifecycle is NOT shader-folder evidence: the integrated
            # server emits these lines at startup for every dimension, so they
            # can never promote world<id> on their own. Recorded separately.
            try:
                _append_unique(results["dimension_events"], int(m_dim.group(1)))
            except ValueError:
                pass
        elif re.search(r"Program loaded:\s*world-1/", line):
            # Shader-loader-specific folder evidence: OptiFine resolved a
            # program from the world-1/ (Nether) override directory.
            _append_unique(results["world_folder_loads"], "world-1/")
        elif re.search(r"Program loaded:\s*world1/", line):
            # Shader-loader-specific folder evidence: OptiFine resolved a
            # program from the world1/ (End) override directory.
            _append_unique(results["world_folder_loads"], "world1/")
        elif "Parsing block mappings:" in line:
            results["block_mapping_parsed"] = True
        elif "[Shaders] Invalid block ID mapping:" in line or "Block not found for name:" in line:
            results["block_mapping_warnings"].append(line.strip())
            m = re.search(r"block\.(\d+)", line)
            if m:
                results["block_mapping_invalid_ids"].append(f"block.{m.group(1)}")
        elif "[Shaders] Custom uniform:" in line:
            u_name = line.split("Custom uniform:", 1)[1].strip()
            results["custom_uniforms"].append(u_name)
        elif "format:" in line and "[Shaders]" in line:
            match = re.search(r"\[Shaders\]\s+(\w+)\s+format:\s+(\w+)", line)
            if match:
                results["buffer_formats"][match.group(1)] = match.group(2)
        elif "clear disabled" in line and "[Shaders]" in line:
            match = re.search(r"\[Shaders\]\s+(\w+)\s+clear disabled", line)
            if match:
                results["skip_clear_buffers"].append(match.group(1))
        elif "flipped buffers after" in line and "[Shaders]" in line:
            results["ping_pong_flips"].append(line.strip())
        elif "[Shaders] Program loaded:" in line:
            prog = line.split("Program loaded:", 1)[1].strip()
            results["programs_loaded"].append(prog)
        elif "[Shaders] Program disabled:" in line:
            prog = line.split("Program disabled:", 1)[1].strip()
            results["programs_disabled"].append(prog)
        elif re.search(r"PROBE_MODE\s*(?:registered|option|profile)", line, re.IGNORECASE):
            results["probe_mode_registration"] = True
        elif m_probe := re.search(r"PROBE_MODE\s*(?:changed|set|persisted)\s*[:=]\s*(\d+)", line, re.IGNORECASE):
            results["probe_mode_transition_values"].append(int(m_probe.group(1)))
        elif re.search(r"(?:uniforms?|HUD).*(?:frameCounter|frameTime).*(?:exercised|heartbeat|updated)", line, re.IGNORECASE):
            results["uniforms_exercised"] = True
        elif re.search(r"(?:accepted|mapped).*(?:block\.(?:10[0-9]))", line, re.IGNORECASE):
            results["block_mapping_accepted_ids"].append(re.search(r"(block\.10[0-9])", line, re.IGNORECASE).group(1))
        elif "[Shaders] Framebuffer created." in line:
            results["framebuffer_created"] = True
        elif "[Shaders] Loading custom texture:" in line:
            results["custom_textures_loaded"].append(line.strip())
        elif "[Shaders] Loading custom noise texture:" in line or "noiseTextureResolution" in line:
            results["custom_noise_loaded"] = True
        elif "[Shaders] Error:" in line or ("error:" in line.lower() and "shader" in line.lower()):
            results["errors"].append(line.strip())
        elif "OpenGL error" in line or "GL_INVALID" in line:
            results["errors"].append(line.strip())
    for key in (
        "block_mapping_warnings", "block_mapping_invalid_ids",
        "block_mapping_accepted_ids", "custom_uniforms", "skip_clear_buffers",
        "ping_pong_flips", "programs_loaded", "programs_disabled",
        "custom_textures_loaded", "errors", "warnings",
    ):
        results[key] = list(dict.fromkeys(results[key]))
    return results


def read_probe_mode_from_options(instance_dir: Path) -> Tuple[Optional[int], str]:
    p = instance_dir / "optionsshaders.txt"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None, f"optionsshaders.txt absent at {p}"
    except OSError as exc:
        return None, f"optionsshaders.txt unreadable: {exc}"
    m = re.search(r"^PROBE_MODE\s*[:=]\s*(\d+)\s*$", text, re.MULTILINE)
    if not m:
        return None, "PROBE_MODE key absent in optionsshaders.txt"
    try:
        v = int(m.group(1))
    except ValueError:
        return None, f"PROBE_MODE non-integer: {m.group(1)!r}"
    if 0 <= v <= 5:
        return v, f"optionsshaders.txt persists PROBE_MODE:{v}"
    return None, f"PROBE_MODE out of range 0-5: {v}"


def _glsl_references(names: List[str]) -> Dict[str, bool]:
    found = {n: False for n in names}
    try:
        files = list(SHADERS_DIR.rglob("*.fsh")) + list(SHADERS_DIR.rglob("*.vsh")) + list(SHADERS_DIR.rglob("*.glsl"))
    except OSError:
        return found
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for n in names:
            if n in text:
                found[n] = True
    return found


def evaluate_capabilities(
    log_analysis: Dict[str, Any],
    system_info: Dict[str, Any],
    optifine_jar: Path,
    instance_dir: Path,
    screenshot_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Classify E7 capabilities; evidence text never exceeds the checked predicate."""
    progs = set(log_analysis.get("programs_loaded", []))
    errors = log_analysis.get("errors", [])
    has_errors = len(errors) > 0
    pack_loaded = log_analysis.get("pack_loaded", False)
    fb_created = log_analysis.get("framebuffer_created", False)
    capabilities: Dict[str, Any] = {}

    def fail_or_inconclusive() -> str:
        return "FAIL" if pack_loaded else "INCONCLUSIVE"

    # 1. EXP-P0-STACK
    if pack_loaded and fb_created and not has_errors and len(progs) >= 10:
        stack_status, stack_ev = "PASS", (
            f"Pack '{log_analysis.get('pack_name')}' loaded; framebuffer created; "
            f"{len(progs)} distinct program entries with 0 observed errors"
        )
    elif pack_loaded and has_errors:
        stack_status, stack_ev = "FAIL", f"Pack loaded but errors observed: {errors[:2]}"
    else:
        stack_status, stack_ev = "INCONCLUSIVE", "Insufficient log evidence for full stack execution"
    capabilities["EXP-P0-STACK"] = {
        "status": stack_status,
        "description": "Forge 1614 + OptiFine E7 minimal pipeline execution on target hardware",
        "evidence": stack_ev,
        "notes": "Overworld/Nether/End execution is evidenced by the P0 suite gates, not by this predicate alone",
    }

    # 2/3/4/5. deferred / composite / final / shadow (log predicates only)
    if "deferred" in progs and "deferred_last" in progs:
        d_st, d_ev = "PASS", "Log shows 'Program loaded: deferred' and 'deferred_last' restore entry"
    elif "deferred" in progs:
        d_st, d_ev = "PASS", "Log shows 'Program loaded: deferred'"
    else:
        d_st, d_ev = fail_or_inconclusive(), "Program 'deferred' absent from runtime log"
    capabilities["deferred"] = {
        "status": d_st,
        "description": "Deferred pass stage loaded between terrain and translucent passes",
        "evidence": d_ev,
        "notes": "Inter-pass data flow is a separate visual-manifest observation, not proven by load lines",
    }

    if "composite" in progs:
        c_st, c_ev = "PASS", f"Log shows 'Program loaded: composite' ({len(log_analysis.get('ping_pong_flips', []))} flip lines observed)"
    else:
        c_st, c_ev = fail_or_inconclusive(), "Program 'composite' absent from runtime log"
    capabilities["composite"] = {
        "status": c_st, "description": "Post-translucent composite stage loaded",
        "evidence": c_ev, "notes": "Runs at display resolution in E7; no scaling is claimed",
    }

    if "final" in progs:
        f_st, f_ev = "PASS", "Log shows 'Program loaded: final'"
    else:
        f_st, f_ev = fail_or_inconclusive(), "Program 'final' absent from runtime log"
    capabilities["final"] = {
        "status": f_st, "description": "Final presentation pass loaded",
        "evidence": f_ev, "notes": "HUD content is evidenced by captures listed in the manifest",
    }

    if "shadow" in progs:
        s_st, s_ev = "PASS", "Log shows 'Program loaded: shadow'"
    else:
        s_st, s_ev = fail_or_inconclusive(), "Program 'shadow' absent from runtime log"
    capabilities["shadow"] = {
        "status": s_st, "description": "Directional shadow depth pass loaded",
        "evidence": s_ev, "notes": "Minimal shadow pass compiled without observed error",
    }

    # 6b. world<id>: target-specific runtime folders, not generic renderer reloads.
    worlds = str(log_analysis.get("worlds_detected") or "")
    loaded_folders = set(log_analysis.get("world_folder_loads", []))
    required_folders = {"world-1/", "world1/"}
    if required_folders.issubset(loaded_folders):
        w_st, w_ev = "PASS", f"Runtime loaded target folders: {sorted(required_folders)}"
    elif pack_loaded and any(token in worlds for token in ("-1", "1")):
        w_st, w_ev = "INCONCLUSIVE", (
            "World IDs were listed, but target-specific folder load evidence is incomplete"
        )
    else:
        w_st, w_ev = fail_or_inconclusive(), "No target-specific world<id> runtime evidence"
    capabilities["world<id>"] = {
        "status": w_st,
        "description": "OptiFine E7 world<id> dimension routing",
        "evidence": w_ev,
        "notes": "Generic renderer reset/reload lines do not prove dimension routing",
    }

    # 6. includes: predicate is clean compile of shaders that contain #include lines.
    refs_inc = _glsl_references(["#include"])
    has_include_source = any(refs_inc.values())
    common_glsl = SHADERS_DIR / "lib" / "common.glsl"
    probe_cfg = SHADERS_DIR / "lib" / "probe_config.glsl"
    if has_include_source and common_glsl.is_file() and probe_cfg.is_file() and not has_errors and len(progs) > 0:
        i_st, i_ev = "PASS", "Repo shaders contain #include lines and compiled with 0 observed errors"
    elif has_errors:
        i_st, i_ev = "FAIL", f"Compilation errors observed; include resolution unproven: {errors[:1]}"
    else:
        i_st, i_ev = "INCONCLUSIVE", "No compile evidence confirming include resolution"
    capabilities["includes"] = {
        "status": i_st, "description": "GLSL #include preprocessor directive support in E7",
        "evidence": i_ev, "notes": "Depth-10 nesting is parser documentation, not measured here",
    }

    # 8. profiles/options: require registration plus an observed transition
    # and persisted target value; current-file presence alone is insufficient.
    props_file = SHADERS_DIR / "shaders.properties"
    probe_val, probe_msg = read_probe_mode_from_options(instance_dir)
    transitions = log_analysis.get("probe_mode_transition_values", [])
    mode_specific = (
        props_file.is_file()
        and log_analysis.get("probe_mode_registration", False)
        and len(transitions) >= 2
        and probe_val is not None
        and probe_val in transitions
    )
    if mode_specific and pack_loaded and not has_errors:
        p_st, p_ev = "PASS", f"PROBE_MODE registered, changed through {transitions}, and {probe_msg}"
    else:
        p_st, p_ev = "INCONCLUSIVE", (
            "profiles/options unproven: requires registration, at least two observed "
            f"mode values, and persisted value; registration={log_analysis.get('probe_mode_registration')}, "
            f"transitions={transitions}, persisted={probe_msg}"
        )
    capabilities["profiles/options"] = {
        "status": p_st,
        "description": "Profile declarations and PROBE_MODE option registration/persistence",
        "evidence": p_ev,
        "notes": "Mode-cycle persistence is additionally evidenced by suite mode_change gates",
    }

    # 9. block.properties (vanilla): every expected ID must be observed accepted.
    invalid_ids = set(log_analysis.get("block_mapping_invalid_ids", []))
    vanilla_ids = {f"block.{i}" for i in range(100, 110)}
    vanilla_rejected = sorted(vanilla_ids & invalid_ids)
    vanilla_accepted = set(log_analysis.get("block_mapping_accepted_ids", []))
    props_src = SHADERS_DIR / "block.properties"
    try:
        props_text = props_src.read_text(encoding="utf-8", errors="replace") if props_src.is_file() else ""
    except OSError as exc:
        props_text = ""
        read_error = str(exc)
    else:
        read_error = None
    vanilla_declared = all(f"block.{i}=" in props_text for i in range(100, 110))
    missing_accepted = sorted(vanilla_ids - vanilla_accepted)
    if vanilla_declared and not vanilla_rejected and not missing_accepted:
        b_st, b_ev = "PASS", f"Parser accepted vanilla mappings: {sorted(vanilla_accepted)}"
    elif vanilla_rejected:
        b_st, b_ev = "FAIL", f"Vanilla mappings rejected by parser: {vanilla_rejected}"
    else:
        b_st, b_ev = "INCONCLUSIVE", (
            "Vanilla mapping unproven: parser acceptance for expected IDs missing"
            f" ({missing_accepted}); source_error={read_error}"
        )
    capabilities["block.properties (vanilla)"] = {
        "status": b_st,
        "description": "Vanilla block ID alias mapping accepted without rejection",
        "evidence": b_ev,
        "notes": "mc_Entity.x transport is shader-source fact, verified visually in Mode 3 captures",
    }

    # 10. Forge mod mapping: always UNPROVEN in clean baseline.
    blk_warnings = log_analysis.get("block_mapping_warnings", [])
    if blk_warnings:
        m_ev = (f"Parser tolerated namespaced keys but emitted {len(blk_warnings)} "
                "'Block not found' warnings; modded mapping not exercised")
    else:
        m_ev = "Modded block coverage not exercised in clean baseline environment"
    capabilities["Forge mod block mapping"] = {
        "status": "INCONCLUSIVE / UNPROVEN",
        "description": "Forge namespaced block ID mapping (e.g. thaumcraft:*)",
        "evidence": m_ev,
        "notes": "Requires modded workload; not claimed here",
    }

    # 11. custom textures / noise: always UNPROVEN in minimal probe.
    if log_analysis.get("custom_textures_loaded") and log_analysis.get("custom_noise_loaded"):
        t_st, t_ev = "PASS", f"Loaded {len(log_analysis['custom_textures_loaded'])} custom textures plus noise"
    else:
        t_st, t_ev = "INCONCLUSIVE / UNPROVEN", "Custom texture/noise assets not loaded or not logged in this probe run"
    capabilities["custom textures / noise"] = {
        "status": t_st, "description": "Custom textures and noise texture loading",
        "evidence": t_ev, "notes": "Mechanism documented in E7 parser docs; assets unexercised in P0 minimal probe",
    }

    # 12. buffer formats: exact lines required, no overclaim.
    fmts = log_analysis.get("buffer_formats", {})
    if fmts.get("colortex2") == "RGBA16F" and fmts.get("colortex4") == "R11F_G11F_B10F" and not has_errors:
        fm_st, fm_ev = "PASS", ("Log shows colortex2 format: RGBA16F and colortex4 format: R11F_G11F_B10F "
                                "with no observed FBO error")
    elif fmts:
        fm_st, fm_ev = "INCONCLUSIVE", f"Partial format evidence only: {fmts}"
    else:
        fm_st, fm_ev = "INCONCLUSIVE", "No buffer format lines observed in log"
    capabilities["buffer_formats (FP16 / R11F)"] = {
        "status": fm_st, "description": "Wide/compact buffer formats accepted by driver",
        "evidence": fm_ev, "notes": "FBO completeness is inferred from absence of errors plus rendered captures",
    }

    # 13. skip-clear: exact line required.
    skips = log_analysis.get("skip_clear_buffers", [])
    if "colortex3" in skips:
        sk_st, sk_ev = "PASS", "Log shows 'colortex3 clear disabled'"
    elif skips:
        sk_st, sk_ev = "INCONCLUSIVE", f"Clear-disabled observed on {skips}, not colortex3"
    else:
        sk_st, sk_ev = "INCONCLUSIVE", "No 'clear disabled' line observed in log"
    capabilities["colortex_skip_clear"] = {
        "status": sk_st, "description": "Skip framebuffer clear on colortex3 (colortex3Clear = false)",
        "evidence": sk_ev, "notes": "Temporal persistence across frames is evidenced by Mode 2 captures in the manifest",
    }
    # 14. frameCounter / frameTime: source references are not exercise evidence.
    refs = _glsl_references(["frameCounter", "frameTime"])
    mode1_path = (screenshot_dir / "exp_p0_cap_mode1_uniforms_hud.png") if screenshot_dir else None
    mode1_ok, mode1_msg = False, "Mode 1 uniform exercise not observed"
    if log_analysis.get("uniforms_exercised"):
        mode1_ok, mode1_msg = True, "runtime log explicitly records uniform exercise"
    if pack_loaded and not has_errors and refs.get("frameCounter") and refs.get("frameTime") and mode1_ok:
        fc_st, fc_ev = "PASS", f"shader references and {mode1_msg}"
    else:
        parts = []
        if not pack_loaded:
            parts.append("pack load unobserved")
        if has_errors:
            parts.append(f"{len(errors)} errors observed")
        if not refs.get("frameCounter"):
            parts.append("frameCounter unreferenced in shader sources")
        if not refs.get("frameTime"):
            parts.append("frameTime unreferenced in shader sources")
        parts.append(mode1_msg)
        fc_st, fc_ev = "INCONCLUSIVE", "Uniform exercise unproven: " + "; ".join(parts)
    capabilities["frameCounter / frameTime"] = {
        "status": fc_st, "description": "Built-in frame counter and frame delta time uniforms exercised",
        "evidence": fc_ev, "notes": "Heartbeat/bar motion is a visual-manifest observation, not a log predicate",
    }

    # 15. scale.<program>: tri-state, never REJECTED on error.
    verdict = verify_scale_bytecode(optifine_jar)
    if verdict.outcome == "ABSENT_REJECTED":
        sc_st, sc_ev = "REJECTED IN E7", verdict.message
    elif verdict.outcome == "PRESENT":
        sc_st, sc_ev = "PASS", verdict.message
    else:
        sc_st, sc_ev = "INCONCLUSIVE", verdict.message
    capabilities["scale.<program>"] = {
        "status": sc_st, "description": "Internal composite/deferred program downscaling directive",
        "evidence": sc_ev, "notes": "Scaling added upstream in 2018, post-E7; E7 packs must not rely on it",
    }

    return capabilities

def evaluator_exit_code(capabilities: Dict[str, Any]) -> int:
    """Return the process status used by the strict capability evaluator."""
    return 2 if mandatory_failures(capabilities) else 0


def mandatory_failures(capabilities: Dict[str, Any]) -> List[str]:
    failed = []
    for name in MANDATORY_CAPABILITIES:
        entry = capabilities.get(name)
        if entry is None:
            failed.append(f"{name} (missing)")
        elif entry.get("status") == "FAIL":
            failed.append(name)
    return failed


def generate_report(
    system_info: Dict[str, Any],
    log_analysis: Dict[str, Any],
    capabilities: Dict[str, Any],
    output_json: Path,
    output_md: Path,
    tested_tree_sha: str,
    probe_mode_value: Optional[int],
) -> Tuple[List[str], Optional[str]]:
    head_sha, is_clean = get_git_state()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    delta_ok, delta_files, delta_err = check_evidence_delta(tested_tree_sha, head_sha)
    failed = mandatory_failures(capabilities)

    report_data = {
        "timestamp": timestamp,
        "tested_tree_sha": tested_tree_sha,
        "report_head_sha": head_sha,
        "working_tree_clean_at_report": is_clean,
        "evidence_delta": {
            "from": tested_tree_sha,
            "to": head_sha,
            "files": delta_files,
            "allowlisted_only": delta_ok,
            "error": delta_err,
            "allowlist": sorted(EVIDENCE_ALLOWLIST),
        },
        "provenance_note": (
            "tested_tree_sha is the tree actually executed by the suite. "
            "If report_head_sha is ahead, the delta must contain only allowlisted evidence files; "
            "otherwise the provenance claim is invalid."
        ),
        "target_stack": {
            "minecraft": "1.7.10", "forge": "10.13.4.1614",
            "optifine": "1.7.10 HD U E7", "java": system_info.get("java"),
        },
        "hardware_environment": {
            "gpu": system_info.get("gpu"), "gpu_vendor": system_info.get("gpu_vendor"),
            "driver": system_info.get("opengl"), "glsl": system_info.get("glsl"),
            "os": system_info.get("os"), "kernel": system_info.get("kernel"),
        },
        "probe_mode_persisted": probe_mode_value,
        "log_analysis": log_analysis,
        "capabilities": capabilities,
        "mandatory_failures": failed,
        "anecdotal_observations": {
            "note": ("FPS values from the F3 screen are anecdotal host observations only, "
                     "not reproducible GPU timer benchmarks, and must not be cited as frame-time conclusions."),
        },
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with output_json.open("w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    lines = [
        "# Reny Shaders — P0 Capability Probe Report",
        "",
        f"- **Date:** `{timestamp}`",
        f"- **Tested tree SHA (actually executed):** `{tested_tree_sha}`",
        f"- **Report HEAD SHA:** `{head_sha}`",
        f"- **Working Tree Clean at report:** `{'Yes' if is_clean else 'No'}`",
        f"- **Evidence delta allowlisted-only:** `{'Yes' if delta_ok else 'No'}`",
        f"- **Evidence delta files:** `{', '.join(delta_files) if delta_files else '(none — reports generated on tested tree)'}`",
        (f"- **Evidence delta error:** `{delta_err}`" if delta_err else "- **Evidence delta error:** `(none)`"),
        f"- **PROBE_MODE persisted at evaluation:** `{probe_mode_value if probe_mode_value is not None else 'unreadable'}`",
        "- **Minecraft:** `1.7.10`",
        "- **Forge:** `10.13.4.1614`",
        "- **OptiFine:** `1.7.10 HD U E7`",
        f"- **Java Runtime:** `{system_info.get('java')}`",
        f"- **GPU:** `{system_info.get('gpu')}`",
        f"- **Driver / GL:** `{system_info.get('opengl')}`",
        f"- **GLSL Version:** `{system_info.get('glsl')}`",
        "",
        "## Provenance",
        "",
        "Tested tree SHA is the tree the suite executed. If the report HEAD is ahead, "
        "the `tested_tree_sha..report_head_sha` delta must contain only allowlisted evidence files "
        f"(`{', '.join(sorted(EVIDENCE_ALLOWLIST))}`). A wider delta invalidates the provenance claim.",
        "",
        "## Capability Matrix Results",
        "",
        "| Capability | Status | Evidence | Notes |",
        "|---|---|---|---|",
    ]
    for key, val in capabilities.items():
        lines.append(f"| `{key}` | **{val['status']}** | {val['evidence']} | {val['notes']} |")
    lines.extend(["", "## Programs Compiled and Loaded in Target Runtime", ""])
    for prog in sorted(log_analysis.get("programs_loaded", [])):
        lines.append(f"- `{prog}`")
    if log_analysis.get("errors"):
        lines.extend(["", "## Runtime Errors Observed", ""])
        for err in log_analysis["errors"]:
            lines.append(f"- `{err}`")
    else:
        lines.extend(["", "## Runtime Errors Observed", "",
                      "**None observed in parsed log.** Absence of parsed errors is not a proof of zero driver warnings."])
    lines.extend(["", "## Mandatory Gate Policy", "",
                  f"- Mandatory FAIL capabilities: `{', '.join(sorted(failed)) if failed else '(none)'}`",
                  "- Any entry above forces a non-zero evaluator exit code.",
                  "- `INCONCLUSIVE / UNPROVEN` is reported separately and is never promoted to PASS.", ""])
    lines.extend(["", "## Anecdotal Performance Observations (NOT a benchmark)", "",
                  "- F3 FPS values, when recorded during manual observation, are host anecdotes only.",
                  "- They must not be cited as GPU frame-time conclusions.", ""])
    with output_md.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return failed, delta_err


def main() -> int:
    parser = argparse.ArgumentParser(description="Reny Shaders P0 Capability Probe Runner")
    parser.add_argument("--instance", type=Path, default=DEFAULT_INSTANCE)
    parser.add_argument("--mode", type=int, default=0)
    parser.add_argument("--deploy-only", action="store_true")
    parser.add_argument("--check-only", action="store_true",
                        help="Evaluate capabilities without overwriting report files")
    parser.add_argument("--parse-log", type=Path, help="Analyze existing latest.log without running game")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "benchmarks" / "reports")
    parser.add_argument("--optifine-jar", type=Path, default=DEFAULT_INSTANCE / "mods" / "OptiFine_1.7.10_HD_U_E7.jar")
    parser.add_argument("--tested-sha", type=str, default="",
                        help="Tested tree SHA actually executed (defaults to current HEAD)")
    parser.add_argument("--screenshot-dir", type=Path, default=SCREENSHOT_DIR if "SCREENSHOT_DIR" in globals() else None)
    args = parser.parse_args()

    head_sha, is_clean = get_git_state()
    tested_sha = args.tested_sha.strip() or head_sha
    print("=== Reny Shaders P0 Capability Probe Harness ===")
    system_info = detect_system_info()
    print(f"Tested tree SHA: {tested_sha}")
    print(f"Report HEAD SHA: {head_sha} (clean: {is_clean})")
    print(f"GPU:        {system_info.get('gpu')}")
    print(f"GL/Mesa:    {system_info.get('opengl')}")
    print(f"Java:       {system_info.get('java')}")

    pack_dir = None
    if not args.check_only:
        pack_dir = deploy_shaderpack(args.instance, target_mode=args.mode)
        print(f"Deployed shaderpack to: {pack_dir}")
    else:
        print("Check-only: skipping shaderpack redeploy (runtime state preserved).")

    if args.deploy_only:
        print("Deploy complete (--deploy-only specified).")
        return 0

    log_text, log_sources, log_err = read_evidence_logs(
        evidence_log_files(args.instance), args.parse_log
    )
    if log_err is not None:
        print(f"FAIL: {log_err}")
        return 1
    print(f"Analyzing logs: {log_sources}")
    log_analysis = parse_shader_logs(log_text)
    log_analysis["log_sources_parsed"] = log_sources
    shot_dir = args.screenshot_dir
    if shot_dir is not None and not isinstance(shot_dir, Path):
        shot_dir = Path(shot_dir)
    capabilities = evaluate_capabilities(log_analysis, system_info, args.optifine_jar, args.instance, shot_dir)

    failed = mandatory_failures(capabilities)
    print("Evaluation results:")
    for k, v in capabilities.items():
        print(f"  [{v['status']}] {k}: {v['evidence']}")
    if failed:
        print(f"MANDATORY FAILURES: {failed} -> evaluator exit will be non-zero")

    if not args.check_only:
        probe_val, probe_msg = read_probe_mode_from_options(args.instance)
        print(f"PROBE_MODE at evaluation: {probe_msg}")
        out_json = args.output_dir / "p0_probe_report.json"
        out_md = args.output_dir / "p0_probe_report.md"
        failed_now, _ = generate_report(system_info, log_analysis, capabilities,
                                        out_json, out_md, tested_sha, probe_val)
        print(f"Generated report: {out_json}")
        print(f"Generated Markdown: {out_md}")
        failed = failed_now

    # Explicit exit policy: mandatory FAIL => non-zero; INCONCLUSIVE alone => zero.
    return evaluator_exit_code(capabilities)


if __name__ == "__main__":
    sys.exit(main())
