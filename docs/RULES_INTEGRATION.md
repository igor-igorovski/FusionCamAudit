# Rules Integration

## Put the file here

Place the generated rules file at:

`FusionCamAudit/config/rules.json`

This path should be treated as the default active rule profile for the add-in.

## Recommended future structure

If you later split rules by area, use:

- `config/rules.json` → top-level merged profile
- `config/setup_rules.json`
- `config/tool_rules.json`
- `config/operation_rules.json`

For now, keep a single file:
- `config/rules.json`

## Where to reference it in markdown files

### 1. docs/PROJECT_BLUEPRINT.md

Add this under the "Rule Sources" or "Configuration" section:

```md
Active deterministic audit rules are loaded from:
- `config/rules.json`

The file contains explicit rule codes, categories, severities, guide references, and check definitions.
All runtime CAM validation must resolve through this file and the deterministic validator layer.
```

### 2. docs/TASKLIST.md

Phase 2 should include:

```md
- create `config/rules.json`
- define initial HP CAM Guide rule set
- wire `core/rules_loader.py` to load `config/rules.json`
```

Phase 3–5 should refer to expanding checks from that file, for example:

```md
- implement setup checks from `config/rules.json`
- implement tool and operation checks from `config/rules.json`
- implement strategy and structure checks from `config/rules.json`
```

### 3. docs/CODEX_PROMPTS.md

In every relevant prompt, explicitly tell Codex to read the rules file.

Example additions:

#### Prompt 2
```md
Read:
- `docs/PROJECT_BLUEPRINT.md`
- `docs/TASKLIST.md`
- `config/rules.json`
```

#### Prompt 3
```md
Read:
- `docs/PROJECT_BLUEPRINT.md`
- `docs/TASKLIST.md`
- `config/rules.json`
```

#### Prompt 4
```md
Read:
- `docs/PROJECT_BLUEPRINT.md`
- `docs/TASKLIST.md`
- `config/rules.json`
```

#### Prompt 5
```md
Read:
- `docs/PROJECT_BLUEPRINT.md`
- `docs/TASKLIST.md`
- `config/rules.json`
```

#### Prompt 6
```md
Read:
- `docs/PROJECT_BLUEPRINT.md`
- `docs/TASKLIST.md`
- `config/rules.json`
```

## Runtime code reference

Wire the loader here:

- `core/rules_loader.py`

Expected loader responsibility:
- load `config/rules.json`
- validate schema
- expose rules to validator/rule_engine

Then reference rules in:
- `core/validator.py`
- `core/rule_engine.py`

## Important implementation rule

Do not duplicate business logic in code and JSON.

Code should:
- interpret rule definitions
- evaluate extracted CAM data

JSON should define:
- what to check
- how strict it is
- how to classify failures
- which HP guide section the rule maps to

Support setup exceptions should also live in `config/rules.json`.

Current HP CAM guide support setup names that must be represented in rules:
- `Dovetail Stock Prep`
- `Soft jaw`
- `Soft jaws`
- `DON'T POST`

The Python validator should interpret these as rule-driven exceptions, not as hardcoded one-off names spread across multiple modules.

## Suggested note in docs/PROJECT_BLUEPRINT.md

```md
Configuration-driven validation is mandatory.

Rule definitions live in `config/rules.json`.
Validator code must remain generic and interpret the rule file instead of hardcoding standards in multiple modules.
```
