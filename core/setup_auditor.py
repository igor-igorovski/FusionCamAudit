"""
Setup audit layer — Phase 3.
Evaluates setup-level rules from rules.json against extracted setup dicts.
Returns list of FieldCheck objects.

Supported rule types:
  required                  — field must be non-empty
  regex                     — case-sensitive match = pass, case-insensitive only = warning, no match = fail
  conditional_allowed_values— applies only when 'when' conditions match; checks value against 'allowed' list
  conditional_regex         — applies only when 'when' conditions match; evaluates regex on field
  regex_optional            — suggestion rule: pass if matches, not_checked if doesn't match (never fail)
"""
import re


def audit_setup(setup_dict, rules, models):
    """
    Run all appliesTo='setup' rules against a single setup dict.

    Args:
        setup_dict: raw dict from extractor.extract_setups()
        rules:      full parsed rules.json dict
        models:     the fca_models module (for FieldCheck class)

    Returns:
        list of FieldCheck instances
    """
    setup_rules = [r for r in rules.get('rules', []) if r.get('appliesTo') == 'setup']

    # Check for skip_audit rule before evaluating anything else
    for rule in setup_rules:
        if rule.get('type') == 'skip_audit' and _when_matches(rule, setup_dict):
            return []

    checks = []
    for rule in setup_rules:
        if rule.get('type') == 'skip_audit':
            continue  # skip_audit rules don't produce FieldCheck entries
        check = _evaluate_rule(rule, setup_dict, models)
        checks.append(check)

    return checks


def _evaluate_rule(rule, setup_dict, models):
    """Evaluate a single rule against setup_dict. Returns FieldCheck."""
    code       = rule.get('code', '')
    field_path = rule.get('field', '')
    severity   = rule.get('severity', 'info')
    message    = rule.get('message', '')
    guide_refs = rule.get('guideRefs', [])
    rule_type  = rule.get('type', '')

    value = _resolve_field(field_path, setup_dict)

    # excludeWhen — if condition matches, skip this rule for this setup
    if _when_matches_key(rule, 'excludeWhen', setup_dict):
        return models.FieldCheck(
            code=code, field=field_path, status='not_checked',
            severity=severity, message='', guide_refs=guide_refs,
        )

    if rule_type == 'required':
        status = _eval_required(value)
    elif rule_type == 'regex':
        status = _eval_regex(rule.get('pattern', ''), value)
    elif rule_type == 'conditional_allowed_values':
        status = _eval_conditional_allowed(rule, setup_dict, value)
    elif rule_type == 'conditional_regex':
        status = _eval_conditional_regex(rule, setup_dict, value)
    elif rule_type == 'regex_optional':
        status = _eval_regex_optional(rule.get('pattern', ''), value)
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


def _eval_regex(pattern, value):
    """
    Evaluate regex rule.
    - case-sensitive match        → pass
    - case-insensitive match only → warning (wrong casing)
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


def _eval_conditional_allowed(rule, setup_dict, value):
    """
    conditional_allowed_values — applies only when all 'when' conditions match.
    If condition not met → not_checked.
    If condition met → check value against 'allowed' list.
    """
    when    = rule.get('when', {})
    allowed = rule.get('allowed', [])

    for when_field, when_values in when.items():
        actual = _resolve_field(when_field, setup_dict)
        if actual not in when_values:
            return 'not_checked'

    return 'pass' if value in allowed else 'fail'


def _eval_conditional_regex(rule, setup_dict, value):
    """
    conditional_regex — applies only when all 'when' conditions match.
    If condition not met → not_checked.
    If condition met → evaluate regex on field value (same semantics as _eval_regex).
    """
    if not _when_matches_key(rule, 'when', setup_dict):
        return 'not_checked'
    return _eval_regex(rule.get('pattern', ''), value)


def _eval_regex_optional(pattern, value):
    """
    regex_optional — suggestion/informational rule, never generates a failure.
    - matches pattern → pass
    - doesn't match   → not_checked  (silently skipped)
    """
    if value is None or str(value).strip() == '':
        return 'not_checked'
    try:
        return 'pass' if re.match(pattern, str(value)) else 'not_checked'
    except re.error:
        return 'not_checked'


# ---------------------------------------------------------------------------
# Field resolver
# ---------------------------------------------------------------------------

def _resolve_field(field_path, setup_dict):
    """
    Resolve a dotted field path like 'setup.name' against setup_dict.
    The 'setup.' prefix is stripped — setup_dict IS the setup.
    """
    parts = field_path.split('.')
    if parts and parts[0] == 'setup':
        parts = parts[1:]

    key_map = {
        'name':             'name',
        'programNumber':    'programNumber',
        'programComment':   'programComment',
        'workOffset':       'workOffset',
        'machineModel':     'machineModel',
        'fixtureType':      'fixtureType',
        'axisMode':         'axisMode',
        'hasProbeStrategy': 'hasProbeStrategy',
    }

    if not parts:
        return None

    key = key_map.get(parts[0], parts[0])
    return setup_dict.get(key)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_quotes(s):
    """Normalize curly/smart apostrophes to straight apostrophe for comparison."""
    return str(s).replace('\u2019', "'").replace('\u2018', "'").replace('\u02bc', "'")


def _when_matches_key(rule, key, setup_dict):
    """
    Generic condition evaluator for any rule key ('when', 'excludeWhen', etc.).
    Returns True if ALL field conditions in the given key match setup_dict values.
    Returns False if the key is absent or any condition doesn't match.
    """
    conditions = rule.get(key, {})
    if not conditions:
        return False
    for when_field, when_values in conditions.items():
        actual = _resolve_field(when_field, setup_dict)
        actual_norm = _normalize_quotes(str(actual)) if actual is not None else ''
        when_values_norm = [_normalize_quotes(str(v)) for v in when_values]
        if actual_norm not in when_values_norm:
            return False
    return True


def _when_matches(rule, setup_dict):
    """Return True if all 'when' conditions in the rule match setup_dict values."""
    return _when_matches_key(rule, 'when', setup_dict)
