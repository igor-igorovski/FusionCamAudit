# Fusion CAM Audit – Phase Task List

PHASE 1
Add-in shell
- manifest
- entrypoint
- command button
- palette window
- mock UI

PHASE 2
Models and schema
- SetupRow
- OperationRow
- ToolInfo
- FieldCheck
- AuditResult
- report schema

PHASE 3
Setup audit
Checks:
- setup naming
- support setup exceptions (`Dovetail Stock Prep`, `Soft jaw` / `Soft jaws`, `DON'T POST`)
- program number format
- program comment
- work offset
- fixture type
- machine model

PHASE 4
Tool and operation audit
Checks:
- tool exists
- tool number (required)
- tool number matches .S prefix (e.g. .S101 → T101)
- tools without .S prefix must use reserved range T900–T999
- tool description
- tool preset matches operation name (FINISH WALL, FINISH FLOOR, PROFIL, ENGRAVE…)
- holder assigned
- operation comment
- compensation type
- cycle time
- toolpath exists
- tool count threshold
- nullPass (Repeat Finishing Pass) checks per operation type
- doMultipleFinishingPasses checks per operation type

PHASE 5
CAM strategy and structure audit
Checks:
- chamfer before thread mill
- preset vs strategy compatibility
- folder structure if >50 ops
- expected setup structure
- roughing vs finishing rules

PHASE 6
Reporting and export
Generate:
- cam_audit_report.json
- cam_audit_summary.md
