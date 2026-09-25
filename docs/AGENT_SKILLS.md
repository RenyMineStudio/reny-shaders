# Agent skills profile

Status: **planned integration; no skill sync implemented in this repository**.

`RenyMineStudio/agent-skills` is the canonical source of reusable worker skills. The normal Reny Shaders worker stays scoped to this repository and receives only skills relevant to shader development and its supporting Minecraft workflow.

## Intended groups

- `common`;
- `minecraft`;
- `shaders`.

MDT-oriented skills can be selected when a task needs semantic Minecraft tooling, but the shaderpack remains a consumer: it must not gain Forge/MDT ownership merely because a worker uses those skills.

## Isolation

The future resolver must not import manifests from `../reny-optimization`, `../minecraft-dev-toolkit`, `../The-Reawakening` or other siblings automatically. Cross-project access exists only for an explicitly cross-repo task.

A cross-repo profile adds coordination knowledge, not permissions or hidden dependencies.

## Planned materialization

Selected skills should be direct children of `.agents/skills/`, preferably relative per-skill symlinks to the sibling `../agent-skills` checkout on the local workstation, with a future lock pinning the catalog commit.

Canonical design: `RenyMineStudio/agent-skills/docs/superpowers/specs/2026-09-25-agent-skills-distribution-design.md`.
