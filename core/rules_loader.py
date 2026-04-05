import json
import os

_rules_cache = None


def load_rules() -> dict:
    """Load config/rules.json once and cache in module scope."""
    global _rules_cache
    if _rules_cache is None:
        path = os.path.join(_addon_root(), 'config', 'rules.json')
        with open(path, encoding='utf-8') as f:
            _rules_cache = json.load(f)
    return _rules_cache


def get_rules_for(applies_to: str) -> list:
    """Return all rules whose appliesTo matches the given value."""
    return [r for r in load_rules()['rules'] if r.get('appliesTo') == applies_to]


def get_rule(code: str) -> dict:
    """Return a single rule by its code, or None if not found."""
    for r in load_rules()['rules']:
        if r.get('code') == code:
            return r
    return None


def _addon_root() -> str:
    # core/rules_loader.py → core/ → addon root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
