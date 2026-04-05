# Fusion CAM Audit Add-in – Deterministic CAM Audit Blueprint

Goal:
Build a Fusion 360 Python add-in that performs deterministic CAM auditing only.

The add-in must:
- inspect CAM setups and operations
- validate them against explicit rules
- show results in an HTML palette
- export a structured report for external GPT analysis

The add-in must NOT:
- use any LLM internally
- make heuristic AI decisions
- hide uncertainty when a check is not implemented

Architecture layers:
1. Fusion extraction layer
2. normalization layer
3. deterministic rules engine
4. UI palette
5. export/report layer

Configuration note:
- Rule definitions live in `config/rules.json`
- Support setup exceptions from the HP CAM guide must be defined in rules, not scattered through Python code
- Current support setup names include `Dovetail Stock Prep`, `Soft jaw` / `Soft jaws`, and `DON'T POST`

Export outputs:
- cam_audit_report.json
- cam_audit_summary.md

Status types:
pass
fail
warning
not_checked

Severity:
info
warning
error
