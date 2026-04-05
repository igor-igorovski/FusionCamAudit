"""
Fusion CAM extraction layer.
Reads raw data from adsk.cam and returns plain dicts — no model objects here.
"""
import re
import adsk.core
import adsk.cam


def extract_setups(cam):
    """
    Extract all setups from a CAM object.
    Returns list of raw setup dicts.
    """
    result = []
    for i in range(cam.setups.count):
        setup = cam.setups.item(i)
        result.append(_extract_setup(setup))
    return result


def _extract_setup(setup):
    """Extract a single CAMSetup into a plain dict."""
    name = _safe(lambda: setup.name, '')

    # Correct param names discovered from DUMP_SETUP.txt
    program_number  = _strip_quotes(_safe(lambda: setup.parameters.itemByName('job_programName').expression, ''))
    program_comment = _strip_quotes(_safe(lambda: setup.parameters.itemByName('job_programComment').expression, ''))

    # work offset is an integer (1=G54 … 6=G59), normalize to G-code string
    work_offset_raw = _safe(lambda: setup.parameters.itemByName('job_workOffset').expression, '')
    work_offset = _normalize_work_offset(work_offset_raw)

    # Machine model — try job_machine_type, fall back to job_machine_configuration
    machine_model = (
        _strip_quotes(_safe(lambda: setup.parameters.itemByName('job_machine_type').expression, ''))
        or _strip_quotes(_safe(lambda: setup.parameters.itemByName('job_machine_configuration').expression, ''))
    )

    # Fixture type — Fusion has no dedicated classification param.
    # job_fixture = true means a fixture body is assigned → treat as 'present' (non-empty = pass for required rule).
    # job_fixture = false/missing → empty string → required rule fails.
    fixture_present = _safe(lambda: setup.parameters.itemByName('job_fixture').expression, 'false')
    fixture_type = 'present' if str(fixture_present).strip().lower() == 'true' else ''

    # Axis mode — parse from setup name suffix (e.g. "OP1 5AX" → "5AX")
    axis_mode = _axis_mode_from_name(name)

    # Probe strategy — check if any child operation is a probing op
    has_probe = _detect_probe_strategy(setup)

    operations = _filter_edit_ops(_extract_operations(setup))

    return {
        'name':             name,
        'programNumber':    program_number,
        'programComment':   program_comment,
        'workOffset':       work_offset,
        'machineModel':     machine_model,
        'fixtureType':      fixture_type,
        'axisMode':         axis_mode,
        'hasProbeStrategy': has_probe,
        'operations':       operations,
    }


def _extract_operations(setup):
    """Recursively extract all operations (including from folders)."""
    ops = []
    _collect_operations(setup, ops)
    return ops


def _collect_operations(node, ops):
    """Walk CAMSetup or CAMFolder children."""
    for i in range(node.allOperations.count):
        op = node.allOperations.item(i)
        ops.append(_extract_operation(op))


# Fusion creates these strategy types when the user manually edits a toolpath.
# They are helper records — not real CAM operations — and must be excluded from audit.
_EDIT_STRATEGY_PREFIX = 'toolpath_edit_'
_EDIT_STRATEGIES = {'toolpath_trim'}


def _filter_edit_ops(ops):
    """
    Remove Fusion toolpath-edit helper operations and deduplicate by name.

    Fusion appends 'toolpath_edit_*' / 'toolpath_trim' operations (same name as the
    original) whenever the user manually edits a toolpath. These are internal records,
    not auditable CAM operations.

    After removing edit helpers, duplicates with the same name are deduplicated.
    Priority order for master selection:
      1. has preset + hasToolpath  (best)
      2. has preset only
      3. hasToolpath only
      4. any (first seen)
    """
    real_ops = [
        op for op in ops
        if not (op.get('operationType', '').startswith(_EDIT_STRATEGY_PREFIX)
                or op.get('operationType', '') in _EDIT_STRATEGIES)
    ]

    def _score(op):
        tool = op.get('tool') or {}
        has_preset   = bool(tool.get('preset', ''))
        has_toolpath = bool(op.get('hasToolpath', False))
        return (has_preset and has_toolpath, has_preset, has_toolpath)

    seen = {}
    for op in real_ops:
        name = op.get('name', '')
        existing = seen.get(name)
        if existing is None or _score(op) > _score(existing):
            seen[name] = op
    return list(seen.values())


def _extract_operation(op):
    """Extract a single CAMOperation into a plain dict."""
    name    = _safe(lambda: op.name, '')
    operation_id = _safe(lambda: op.operationId, '')
    # strategy param (e.g. 'face', 'contour2d') is the real Fusion operation type identifier
    op_type = _safe(lambda: _strip_quotes(op.parameters.itemByName('strategy').expression), '')
    # compensationType param discovered from DUMP_SETUP.txt (not job_compensationType)
    comp = _strip_quotes(_safe(lambda: op.parameters.itemByName('compensationType').expression, ''))
    has_toolpath = _safe(lambda: op.hasToolpath, False)
    # cycleTime not available as operation param in Fusion API — leave as None
    # 'nullPass' = "Repeat Finishing Pass" checkbox in milling ops (contour2d etc.)
    null_pass_raw = _safe(lambda: op.parameters.itemByName('nullPass').expression, None)
    null_pass = (
        True if str(null_pass_raw).strip().lower() == 'true'
        else False if str(null_pass_raw).strip().lower() == 'false'
        else None
    )
    # 'doMultipleFinishingPasses' = "Multiple Finishing Passes" checkbox
    do_multi_raw = _safe(lambda: op.parameters.itemByName('doMultipleFinishingPasses').expression, None)
    do_multiple_finishing_passes = (
        True if str(do_multi_raw).strip().lower() == 'true'
        else False if str(do_multi_raw).strip().lower() == 'false'
        else None
    )

    tool_info = _extract_tool(op)

    return {
        'name':             name,
        'operationId':      operation_id,
        'operationType':    op_type,
        'comment':          '',     # no user comment param exists in Fusion CAM API
        'compensationType': comp,
        'hasToolpath':      has_toolpath,
        'cycleTimeSec':     None,   # not available via Fusion params
        'nullPass': null_pass,
        'doMultipleFinishingPasses': do_multiple_finishing_passes,
        'tool':             tool_info,
    }


def _extract_tool(op):
    """Extract tool info from an operation. Returns dict or None."""
    try:
        tool = op.tool
        if not tool:
            return None
        # tool.number is an API property; fallback to tool_number param
        number = (
            _safe(lambda: str(tool.number), '')
            or _strip_quotes(_safe(lambda: op.parameters.itemByName('tool_number').expression, ''))
        )
        # tool.description (API) returns full display string e.g. '#102 - Ø1/8" flat (.S102 ...)'
        # tool_description param returns the clean name e.g. '.S102 1/8 x 0.4375 3FL'
        # Use param for classification, API for display fallback
        description_param = _strip_quotes(_safe(lambda: op.parameters.itemByName('tool_description').expression, ''))
        description_api   = _safe(lambda: tool.description, '')
        description = description_param or description_api
        # tool_type param (e.g. 'flat end mill') discovered from DUMP_SETUP.txt
        tool_type   = _strip_quotes(_safe(lambda: op.parameters.itemByName('tool_type').expression, ''))
        # holder_attached = true means a holder body is assigned (analogous to job_fixture for setups)
        holder_attached = _safe(lambda: op.parameters.itemByName('holder_attached').expression, 'false')
        holder      = 'present' if str(holder_attached).strip().lower() == 'true' else ''
        holder_name = _strip_quotes(_safe(lambda: op.parameters.itemByName('holder_description').expression, ''))
        # op.toolPreset is a Fusion API property (not exposed as param — use property directly)
        preset      = _safe(lambda: op.toolPreset, None)
        preset_name = _safe(lambda: preset.name, '') if preset else ''

        # Derive tool classification fields
        has_s_prefix = str(description).startswith('.S')
        m = re.match(r'^\.S(\d+)', str(description))
        s_prefix_number = int(m.group(1)) if m else None
        try:
            number_int = int(str(number).strip())
        except (ValueError, TypeError):
            number_int = None
        in_reserved_range = (number_int is not None and 900 <= number_int <= 999)
        tool_number_matches_prefix = (
            s_prefix_number is not None and number_int == s_prefix_number
        ) if has_s_prefix else None

        return {
            'number':                  number,
            'description':             description,
            'type':                    tool_type,
            'preset':                  preset_name,
            'presetName':              preset_name,
            'holder':                  holder,
            'holderName':              holder_name,
            'hasSPrefix':              has_s_prefix,
            'sPrefixNumber':           s_prefix_number,
            'numberInt':               number_int,
            'inReservedRange':         in_reserved_range,
            'toolNumberMatchesPrefix': tool_number_matches_prefix,
        }
    except Exception:
        return None


def _detect_probe_strategy(setup):
    """Return True if any operation in setup is a probing operation."""
    try:
        for i in range(setup.allOperations.count):
            op = setup.allOperations.item(i)
            op_type = _safe(lambda: str(op.operationType), '').lower()
            if 'probe' in op_type or 'inspect' in op_type:
                return True
    except Exception:
        pass
    return False


def _strip_quotes(s):
    """Remove surrounding single or double quotes from a Fusion expression string."""
    if not s:
        return s
    return str(s).strip().strip('"').strip("'")


def _normalize_work_offset(raw):
    """
    Convert Fusion work offset expression to G-code string.
    Fusion stores work offset as integer: 1=G54, 2=G55, 3=G56, 4=G57, 5=G58, 6=G59.
    Also handles already-formatted strings like 'G59' or '59'.
    """
    if raw is None:
        return ''
    v = str(raw).strip().strip('"').strip("'")
    if not v:
        return ''
    # Already in G-code format
    if v.upper().startswith('G'):
        return v.upper()
    # Integer offset: 1-based offset from G53 (G54=1, G55=2, ..., G59=6)
    try:
        n = int(float(v))
        if 1 <= n <= 6:
            return 'G{}'.format(53 + n)
        # Extended offsets G54.1 P1..P48 — return raw for now
        return v
    except (ValueError, TypeError):
        return v


def _axis_mode_from_name(name):
    """
    Parse axis mode from setup name suffix.
    Examples: 'OP1 5AX' → '5AX', 'Op2 3ax' → '3AX', 'Setup1' → ''
    """
    import re
    m = re.search(r'(\d+AX)', str(name), re.IGNORECASE)
    return m.group(1).upper() if m else ''


def _safe(fn, default):
    """Call fn(), return default on any exception."""
    try:
        return fn()
    except Exception:
        return default
