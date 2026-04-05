"""
Operation audit layer — Phase 4.
Evaluates operation-level rules from rules.json against extracted operation dicts.
Returns list of FieldCheck objects.

Supported rule types:
  required                  — field must be non-empty / non-None
  equals                    — field value must equal expected
  allowed_values            — field value must be in allowed list
  conditional_required      — required only when 'when' conditions match
  conditional_regex         — regex check when 'when' conditions match
  conditional_not_regex     — field must NOT match regex when 'when' conditions match
  conditional_allowed_values— value must be in allowed list when conditions match
  conditional_contains      — field must contain substring when conditions match
  conditional_not_contains  — field must NOT contain substring when conditions match
  conditional_equals        — field must equal expected when conditions match
  conditional_contains_all  — when.containsAll word-set match on trigger field, then mustContainAll on value
  name_contains_fail        — fail if operation.name contains any phrase from containsAny list
"""
import re


# Fields that cannot be read from the Fusion CAM API — always not_checked
_UNAVAILABLE_FIELDS = {
    'operation.comment',       # no user comment param in Fusion API
    'operation.cycleTimeSec',  # cycleTime not exposed as param
    # operation.tool.preset — available via op.toolPreset API property (not a param)
}


def audit_operation(op_dict, rules, models):
    """
    Run all appliesTo='operation' rules against a single operation dict.

    Args:
        op_dict: raw dict from extractor._extract_operation()
        rules:   full parsed rules.json dict
        models:  the fca_models module (for FieldCheck class)

    Returns:
        list of FieldCheck instances
    """
    op_rules = [r for r in rules.get('rules', []) if r.get('appliesTo') == 'operation']
    checks = []
    for rule in op_rules:
        field = rule.get('field', '')
        # Fields not available from Fusion API → always not_checked
        if field in _UNAVAILABLE_FIELDS:
            checks.append(models.FieldCheck(
                code=rule.get('code', ''), field=field, status='not_checked',
                severity=rule.get('severity', 'info'), message='', guide_refs=rule.get('guideRefs', []),
            ))
            continue
        check = _evaluate_rule(rule, op_dict, models)
        checks.append(check)
    return checks


def _evaluate_rule(rule, op_dict, models):
    """Evaluate a single rule against op_dict. Returns FieldCheck."""
    code       = rule.get('code', '')
    field_path = rule.get('field', '')
    severity   = rule.get('severity', 'info')
    message    = rule.get('message', '')
    guide_refs = rule.get('guideRefs', [])
    rule_type  = rule.get('type', '')

    value = _resolve_field(field_path, op_dict)

    # excludeWhen — skip rule if condition matches
    if _when_matches_key(rule, 'excludeWhen', op_dict):
        return models.FieldCheck(
            code=code, field=field_path, status='not_checked',
            severity=severity, message='', guide_refs=guide_refs,
        )

    if rule_type == 'required':
        status = _eval_required(value)
    elif rule_type == 'equals':
        status = _eval_equals(rule.get('expected'), value)
    elif rule_type == 'allowed_values':
        status = _eval_allowed_values(rule.get('allowed', []), value)
    elif rule_type == 'conditional_required':
        status = _eval_conditional_required(rule, op_dict, value)
    elif rule_type == 'conditional_regex':
        status = _eval_conditional_regex(rule, op_dict, value)
    elif rule_type == 'conditional_not_regex':
        status = _eval_conditional_not_regex(rule, op_dict, value)
    elif rule_type == 'conditional_allowed_values':
        status = _eval_conditional_allowed(rule, op_dict, value)
    elif rule_type == 'conditional_contains':
        status = _eval_conditional_contains(rule, op_dict, value)
    elif rule_type == 'conditional_not_contains':
        status = _eval_conditional_not_contains(rule, op_dict, value)
    elif rule_type == 'conditional_equals':
        status = _eval_conditional_equals(rule, op_dict, value)
    elif rule_type == 'conditional_contains_all':
        status = _eval_conditional_contains_all(rule, op_dict, value)
    elif rule_type == 'name_contains_fail':
        status = _eval_name_contains_fail(rule, op_dict)
    else:
        status = 'not_checked'

    return models.FieldCheck(
        code=code,
        field=field_path,
        status=status,
        severity=severity,
        message=message if status in ('fail', 'warning') else '',
        guide_refs=guide_refs,
    )


# ---------------------------------------------------------------------------
# Evaluators
# ---------------------------------------------------------------------------

def _eval_required(value):
    if value is None or str(value).strip() == '':
        return 'fail'
    return 'pass'


def _eval_equals(expected, value):
    if value is None:
        return 'fail'
    # Handle bool comparison: expected may be JSON bool
    if isinstance(expected, bool):
        if isinstance(value, bool):
            return 'pass' if value == expected else 'fail'
        return 'pass' if str(value).lower() == str(expected).lower() else 'fail'
    return 'pass' if value == expected else 'fail'


def _eval_allowed_values(allowed, value):
    if value is None or str(value).strip() == '':
        return 'not_checked'
    return 'pass' if value in allowed else 'fail'


def _eval_regex(pattern, value):
    """
    - case-sensitive match        → pass
    - case-insensitive match only → warning
    - no match                    → fail
    """
    if value is None or str(value).strip() == '':
        return 'fail'
    v = str(value)
    try:
        if re.match(pattern, v):
            return 'pass'
        if re.match(pattern, v, re.IGNORECASE):
            return 'warning'
        return 'fail'
    except re.error:
        return 'not_checked'


def _eval_conditional_required(rule, op_dict, value):
    if not _when_matches_key(rule, 'when', op_dict):
        return 'not_checked'
    return _eval_required(value)


def _eval_conditional_regex(rule, op_dict, value):
    if not _when_matches_key(rule, 'when', op_dict):
        return 'not_checked'
    return _eval_regex(rule.get('pattern', ''), value)


def _eval_conditional_not_regex(rule, op_dict, value):
    """Condition met + value matches pattern → fail (pattern should NOT match)."""
    if not _when_matches_key(rule, 'when', op_dict):
        return 'not_checked'
    if value is None or str(value).strip() == '':
        return 'not_checked'
    try:
        return 'fail' if re.match(rule.get('pattern', ''), str(value)) else 'pass'
    except re.error:
        return 'not_checked'


def _eval_conditional_allowed(rule, op_dict, value):
    if not _when_matches_key(rule, 'when', op_dict):
        return 'not_checked'
    return 'pass' if value in rule.get('allowed', []) else 'fail'


def _eval_conditional_contains(rule, op_dict, value):
    """Condition met → field must contain expectedContains substring."""
    if not _when_matches_key(rule, 'when', op_dict):
        return 'not_checked'
    if value is None:
        return 'fail'
    expected = rule.get('expectedContains', '')
    return 'pass' if expected in str(value) else 'fail'


def _eval_conditional_not_contains(rule, op_dict, value):
    """Condition met → field must NOT contain expectedContains substring."""
    if not _when_matches_key(rule, 'when', op_dict):
        return 'not_checked'
    if value is None:
        return 'not_checked'
    expected = rule.get('expectedContains', '')
    return 'fail' if expected in str(value) else 'pass'


def _eval_conditional_equals(rule, op_dict, value):
    if not _when_matches_key(rule, 'when', op_dict):
        return 'not_checked'
    return _eval_equals(rule.get('expected'), value)


def _eval_conditional_contains_all(rule, op_dict, value):
    """
    when: each field maps to { containsAll: [...] } — all words must appear in field value.
    If when matches → check that 'value' (the rule's field) contains all words in mustContainAll.
    Case-insensitive, word-set matching (order doesn't matter).
    """
    when = rule.get('when', {})
    for when_field, condition in when.items():
        actual = str(_resolve_field(when_field, op_dict) or '').upper()
        if isinstance(condition, list):
            # plain list → exact-match (same as _when_matches_key behaviour)
            if actual not in [str(v).upper() for v in condition]:
                return 'not_checked'
        else:
            # dict → { containsAll: [...] } word-set match
            words = [w.upper() for w in condition.get('containsAll', [])]
            if not all(w in actual for w in words):
                return 'not_checked'
    val_upper = str(value or '').upper()
    must = [w.upper() for w in rule.get('mustContainAll', [])]
    if not must:
        return 'not_checked'
    return 'pass' if all(w in val_upper for w in must) else 'fail'


def _eval_name_contains_fail(rule, op_dict):
    """Fail if operation.name contains any phrase from containsAny (case-insensitive)."""
    name = str(_resolve_field('operation.name', op_dict) or '').upper()
    phrases = [p.upper() for p in rule.get('containsAny', [])]
    return 'fail' if any(p in name for p in phrases) else 'not_checked'


# ---------------------------------------------------------------------------
# Field resolver — supports nested paths like operation.tool.number
# ---------------------------------------------------------------------------

def _resolve_field(field_path, op_dict):
    """
    Resolve a dotted field path like 'operation.tool.number' against op_dict.
    The 'operation.' prefix is stripped — op_dict IS the operation.
    Supports arbitrary nesting via recursive dict traversal.
    """
    parts = field_path.split('.')
    if parts and parts[0] == 'operation':
        parts = parts[1:]

    obj = op_dict
    for part in parts:
        if obj is None:
            return None
        if isinstance(obj, dict):
            obj = obj.get(part)
        else:
            return None
    return obj


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_quotes(s):
    """Normalize curly/smart apostrophes to straight apostrophe."""
    return str(s).replace('\u2019', "'").replace('\u2018', "'").replace('\u02bc', "'")


def _when_matches_key(rule, key, op_dict):
    """
    Generic condition evaluator for any rule key ('when', 'excludeWhen', etc.).
    Returns True if ALL field conditions in the given key match op_dict values.
    Returns False if the key is absent or any condition doesn't match.
    """
    conditions = rule.get(key, {})
    if not conditions:
        return False
    for when_field, when_values in conditions.items():
        actual = _resolve_field(when_field, op_dict)
        actual_norm = _normalize_quotes(str(actual)) if actual is not None else ''
        # when_values may be a list or a scalar
        if isinstance(when_values, list):
            when_values_norm = [_normalize_quotes(str(v)) for v in when_values]
            if actual_norm not in when_values_norm:
                return False
        elif isinstance(when_values, dict) and 'containsAll' in when_values:
            words = [w.upper() for w in when_values['containsAll']]
            if not all(w in actual_norm.upper() for w in words):
                return False
        else:
            # scalar comparison (e.g. diameterMaxMm: 6.0)
            try:
                if float(actual) != float(when_values):
                    return False
            except (TypeError, ValueError):
                if actual_norm != _normalize_quotes(str(when_values)):
                    return False
    return True
