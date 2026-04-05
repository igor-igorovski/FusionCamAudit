PROMPT 1 – Build Phase 1 skeleton

Read docs/PROJECT_BLUEPRINT.md and docs/TASKLIST.md

Generate:
- FusionCamAudit.py
- FusionCamAudit.manifest
- commands/audit/entry.py
- palette HTML UI

Do NOT implement CAM extraction yet.

---

PROMPT 2 – Models

Generate:
models/
  setup_row.py
  operation_row.py
  tool_info.py
  field_check.py
  audit_result.py

Create schema for report export.

---

PROMPT 3 – Setup Audit

Implement:
- setup extraction
- setup checks
- palette rendering for setups

Use status:
pass fail warning not_checked

---

PROMPT 4 – Tool and Operation Audit

Read docs/PROJECT_BLUEPRINT.md and docs/TASKLIST.md

Implement:
- tool extraction
- operation extraction
- deterministic rule checks

Do not use any AI logic.

---

PROMPT 5 – Strategy Checks

Implement:
- threading sequence checks
- strategy vs preset checks
- browser organization checks

---

PROMPT 6 – Reporting

Implement export:

cam_audit_report.json
cam_audit_summary.md

JSON must contain:
metadata
summary
setups
operations
checks
