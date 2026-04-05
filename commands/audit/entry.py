import adsk.core
import adsk.cam
import traceback
import json
import os

COMMAND_ID      = 'FusionCamAudit_RunAudit'
COMMAND_NAME    = 'CAM Audit'
COMMAND_TOOLTIP = 'Run deterministic CAM audit on current document'
PANEL_ID        = 'CAMManagePanel'
PALETTE_ID      = 'FusionCamAuditPalette'

_app = adsk.core.Application.get()
_ui  = _app.userInterface

_handlers = []
_cmd_def  = None


# ---------------------------------------------------------------------------
# Core module loader — bypasses sys.modules cache for hot-reload
# ---------------------------------------------------------------------------

def _addon_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _import_core():
    """Load core modules fresh every time (bypasses sys.modules cache)."""
    import importlib.util
    import sys

    base = _addon_root()

    def _load(rel_path, mod_name):
        full = os.path.join(base, rel_path)
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        spec = importlib.util.spec_from_file_location(mod_name, full)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sys.modules[mod_name] = mod
        return mod

    models        = _load('core/models.py',             'fca_models')
    rules_loader  = _load('core/rules_loader.py',       'fca_rules_loader')
    extractor     = _load('core/extractor.py',          'fca_extractor')
    setup_auditor = _load('core/setup_auditor.py',      'fca_setup_auditor')
    op_auditor    = _load('core/operation_auditor.py',  'fca_op_auditor')
    return models, rules_loader, extractor, setup_auditor, op_auditor


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def start(external_handlers: list):
    global _cmd_def

    # Force palette recreation on every add-in reload
    palette = _ui.palettes.itemById(PALETTE_ID)
    if palette:
        palette.deleteMe()

    cmd_defs = _ui.commandDefinitions
    existing = cmd_defs.itemById(COMMAND_ID)
    if existing:
        existing.deleteMe()

    _cmd_def = cmd_defs.addButtonDefinition(
        COMMAND_ID,
        COMMAND_NAME,
        COMMAND_TOOLTIP
    )

    on_created = AuditCommandCreatedHandler()
    _cmd_def.commandCreated.add(on_created)
    _handlers.append(on_created)
    external_handlers.append(on_created)

    try:
        ws    = _ui.workspaces.itemById('CAMEnvironment')
        panel = ws.toolbarPanels.itemById(PANEL_ID)
        ctrl  = panel.controls.itemById(COMMAND_ID)
        if not ctrl:
            panel.controls.addCommand(_cmd_def)
    except Exception:
        pass


def stop():
    global _cmd_def

    palette = _ui.palettes.itemById(PALETTE_ID)
    if palette:
        palette.deleteMe()

    try:
        ws    = _ui.workspaces.itemById('CAMEnvironment')
        panel = ws.toolbarPanels.itemById(PANEL_ID)
        ctrl  = panel.controls.itemById(COMMAND_ID)
        if ctrl:
            ctrl.deleteMe()
    except Exception:
        pass

    if _cmd_def:
        _cmd_def.deleteMe()
        _cmd_def = None

    _handlers.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _palette_html_path():
    path = os.path.join(_addon_root(), 'palette', 'audit_palette.html')
    return path.replace('\\', '/')


def _get_ui_theme_payload():
    try:
        gp = getattr(_ui, 'generalPreferences', None)
        if gp is None:
            prefs = getattr(_app, 'preferences', None)
            gp = getattr(prefs, 'generalPreferences', None) if prefs else None
        raw = getattr(gp, 'userInterfaceTheme', None) if gp else None
        if hasattr(raw, 'value'):
            raw = raw.value
        n = int(raw) if raw is not None else 1
        return {'themeRaw': n, 'isDark': n == 2}
    except Exception:
        return {'themeRaw': 1, 'isDark': False}


def _get_active_cam_product():
    doc = _app.activeDocument
    if not doc:
        return None
    products = doc.products
    for i in range(products.count):
        product = products.item(i)
        if product.objectType == adsk.cam.CAM.classType():
            return product
    return None


def _iter_collection(coll):
    try:
        for i in range(coll.count):
            yield coll.item(i)
    except Exception:
        return


def _has_children(coll):
    try:
        return bool(coll) and coll.count > 0
    except Exception:
        return False


def _is_container_item(item):
    try:
        for attr in ('operations', 'folders', 'patterns'):
            if _has_children(getattr(item, attr, None)):
                return True
    except Exception:
        pass
    return False


def _find_operation_by_id(cam, operation_id):
    if cam is None or operation_id in (None, ''):
        return None

    target_id = str(operation_id).strip()
    try:
        ops = getattr(cam, 'allOperations', None)
        if _has_children(ops):
            for item in _iter_collection(ops):
                op = adsk.cam.Operation.cast(item)
                entity = op if op else item
                try:
                    if str(entity.operationId) == target_id:
                        return entity
                except Exception:
                    continue
    except Exception:
        pass

    try:
        return cam.allOperations.itemByOperationId(int(target_id))
    except Exception:
        return None


def _find_setup_for_operation(cam, target_operation):
    if cam is None or target_operation is None:
        return None
    try:
        return target_operation.parentSetup
    except Exception:
        pass

    try:
        for setup in _iter_collection(cam.setups):
            if _expand_to_operation_recursive(setup, target_operation, set(), 0, expand=False):
                return setup
    except Exception:
        pass
    return None


def _expand_to_operation(setup, target_operation):
    if not setup or not target_operation:
        return False
    return _expand_to_operation_recursive(setup, target_operation, set(), 0, expand=True)


def _expand_to_operation_recursive(container, target_operation, visited_ids, depth, expand):
    try:
        if depth > 50:
            return False

        container_id = id(container)
        if container_id in visited_ids:
            return False
        visited_ids.add(container_id)

        if expand and hasattr(container, 'isExpanded'):
            try:
                container.isExpanded = True
            except Exception:
                pass

        operations = getattr(container, 'operations', None)
        if _has_children(operations):
            for item in _iter_collection(operations):
                if not item:
                    continue
                if item == target_operation:
                    return True
                if _is_container_item(item):
                    if expand and hasattr(item, 'isExpanded'):
                        try:
                            item.isExpanded = True
                        except Exception:
                            pass
                    if _expand_to_operation_recursive(item, target_operation, visited_ids, depth + 1, expand):
                        return True

        folders = getattr(container, 'folders', None)
        if _has_children(folders):
            for folder in _iter_collection(folders):
                if not folder:
                    continue
                if expand and hasattr(folder, 'isExpanded'):
                    try:
                        folder.isExpanded = True
                    except Exception:
                        pass
                if _expand_to_operation_recursive(folder, target_operation, visited_ids, depth + 1, expand):
                    return True
    except Exception:
        return False
    return False


def _select_entity(entity):
    _ui.activeSelections.clear()
    _ui.activeSelections.add(entity)
    adsk.doEvents()
    adsk.doEvents()


def _find_in_browser(entity):
    if entity is None:
        return False

    _select_entity(entity)
    for command_id in ('CAMFindInBrowser', 'FindInBrowser', 'BrowserFind', 'CAMBrowserFind'):
        try:
            cmd = _ui.commandDefinitions.itemById(command_id)
            if cmd:
                cmd.execute()
                adsk.doEvents()
                return True
        except Exception:
            continue
    return False


def _open_operation_dialog(entity):
    if entity is None:
        return False

    _select_entity(entity)

    for command_id in ('IronEditOperation',):
        try:
            cmd = _ui.commandDefinitions.itemById(command_id)
            if cmd:
                cmd.execute()
                adsk.doEvents()
                return True
        except Exception:
            continue

    return False


def _open_tool_dialog(entity):
    if entity is None:
        return False

    _select_entity(entity)

    for command_id in ('IronEditTool',):
        try:
            cmd = _ui.commandDefinitions.itemById(command_id)
            if cmd:
                cmd.execute()
                adsk.doEvents()
                return True
        except Exception:
            continue

    return False


# ---------------------------------------------------------------------------
# CommandCreated
# ---------------------------------------------------------------------------

class AuditCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False

            on_execute = AuditCommandExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)

        except Exception:
            _ui.messageBox('AuditCommandCreatedHandler:\n' + traceback.format_exc())


# ---------------------------------------------------------------------------
# Execute — opens palette
# ---------------------------------------------------------------------------

class AuditCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            palette = _ui.palettes.itemById(PALETTE_ID)

            if not palette:
                palette = _ui.palettes.add(
                    PALETTE_ID,
                    'CAM Audit',
                    _palette_html_path(),
                    True, True, True,
                    800, 600
                )
                palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight

                on_html = AuditPaletteHTMLHandler()
                palette.incomingFromHTML.add(on_html)
                _handlers.append(on_html)
            else:
                palette.isVisible = True
                _run_audit(palette)

        except Exception:
            _ui.messageBox('AuditCommandExecuteHandler:\n' + traceback.format_exc())


# ---------------------------------------------------------------------------
# HTML → Python message handler
# ---------------------------------------------------------------------------

class AuditPaletteHTMLHandler(adsk.core.HTMLEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            action = args.action
            palette = _ui.palettes.itemById(PALETTE_ID)

            if action == 'palette_ready':
                if palette:
                    _run_audit(palette)

            elif action == 'run_audit':
                if palette:
                    _run_audit(palette)

            elif action == 'operation_action':
                if palette:
                    _handle_operation_action(palette, args.data)

            elif action == 'close':
                if palette:
                    palette.isVisible = False

        except Exception:
            _ui.messageBox('AuditPaletteHTMLHandler:\n' + traceback.format_exc())


def _handle_operation_action(palette, data):
    try:
        payload = json.loads(data) if data else {}
    except Exception:
        payload = {}

    action = str(payload.get('action', '')).strip().lower()
    operation_id = payload.get('operationId', '')
    setup_name = str(payload.get('setupName', '')).strip()
    op_name = str(payload.get('operationName', '')).strip()
    op_type = str(payload.get('operationType', '')).strip()

    if action not in ('find', 'open', 'edit_tool'):
        response = {
            'action': action,
            'status': 'error',
            'message': 'Unknown operation action.'
        }
    elif operation_id in (None, ''):
        response = {
            'action': action,
            'status': 'error',
            'message': 'Operation action payload is missing operationId.'
        }
    else:
        response = _execute_operation_action(
            action=action,
            operation_id=operation_id,
            setup_name=setup_name,
            op_name=op_name,
            op_type=op_type,
        )

    palette.sendInfoToHTML('operation_action_result', json.dumps(response))


def _execute_operation_action(action, operation_id, setup_name='', op_name='', op_type=''):
    target_label = op_name or 'operation'
    if setup_name:
        target_label = '{} / {}'.format(setup_name, target_label)
    if op_type:
        target_label = '{} ({})'.format(target_label, op_type)

    try:
        cam = _get_active_cam_product()
        if cam is None:
            return {
                'action': action,
                'status': 'error',
                'message': 'No CAM document is active.'
            }

        operation = _find_operation_by_id(cam, operation_id)
        if operation is None:
            return {
                'action': action,
                'status': 'error',
                'message': 'Operation not found in the active CAM document.'
            }

        setup = _find_setup_for_operation(cam, operation)
        if setup and hasattr(setup, 'isExpanded'):
            try:
                setup.isExpanded = True
            except Exception:
                pass

        _expand_to_operation(setup, operation)
        _select_entity(operation)
        browser_found = _find_in_browser(operation)

        if action == 'find':
            message = 'Operation selected in browser: {}.'.format(target_label) if browser_found else 'Operation selected: {}.'.format(target_label)
            return {
                'action': action,
                'status': 'ok',
                'message': message
            }

        if action == 'edit_tool':
            if _open_tool_dialog(operation):
                return {
                    'action': action,
                    'status': 'ok',
                    'message': 'Tool edit opened for {}.'.format(target_label)
                }

            return {
                'action': action,
                'status': 'partial',
                'message': 'Operation selected for {}, but tool dialog did not open.'.format(target_label)
            }

        if _open_operation_dialog(operation):
            return {
                'action': action,
                'status': 'ok',
                'message': 'Operation edit opened for {}.'.format(target_label)
            }

        return {
            'action': action,
            'status': 'partial',
            'message': 'Operation selected for {}, but edit dialog did not open.'.format(target_label)
        }
    except Exception:
        return {
            'action': action,
            'status': 'error',
            'message': traceback.format_exc()
        }


# ---------------------------------------------------------------------------
# Mock result — Phase 2: uses models + rules_loader
# ---------------------------------------------------------------------------

def _run_audit(palette):
    try:
        models, rules_loader, extractor, setup_auditor, op_auditor = _import_core()

        theme_payload = _get_ui_theme_payload()

        # Get active CAM product
        cam = _get_active_cam_product()

        if cam is None:
            result = models.AuditResult(
                status='error',
                message='No CAM product found in the active document. Open a CAM document first.'
            )
            payload = result.to_dict()
            payload.update(_get_ui_theme_payload())
            palette.sendInfoToHTML('audit_result', json.dumps(payload))
            return

        # Extract
        rules        = rules_loader.load_rules()
        raw_setups   = extractor.extract_setups(cam)

        # Build model objects + run setup audit
        setup_rows = []
        for raw in raw_setups:
            checks = setup_auditor.audit_setup(raw, rules, models)

            op_rows = []
            for raw_op in raw.get('operations', []):
                tool_info = None
                if raw_op.get('tool'):
                    t = raw_op['tool']
                    tool_info = models.ToolInfo(
                        number=t.get('number', ''),
                        description=t.get('description', ''),
                        preset_name=t.get('preset', t.get('presetName', '')),
                        holder_name=t.get('holderName', ''),
                    )
                op_checks = op_auditor.audit_operation(raw_op, rules, models)
                op_rows.append(models.OperationRow(
                    name=raw_op.get('name', ''),
                    op_type=str(raw_op.get('operationType', '')),
                    operation_id=str(raw_op.get('operationId', '')),
                    tool=tool_info,
                    checks=op_checks,
                ))

            setup_rows.append(models.SetupRow(
                name=raw.get('name', ''),
                program_number=raw.get('programNumber', ''),
                program_comment=raw.get('programComment', ''),
                work_offset=raw.get('workOffset', ''),
                machine_model=raw.get('machineModel', ''),
                operations=op_rows,
                checks=checks,
            ))

        result = models.AuditResult(status='ok', setups=setup_rows, message='')
        payload = result.to_dict()
        payload.update(_get_ui_theme_payload())
        palette.sendInfoToHTML('audit_result', json.dumps(payload))

    except Exception:
        payload = {
            'status': 'error',
            'summary': {'pass': 0, 'fail': 0, 'warning': 0, 'not_checked': 0},
            'setups': [],
            'message': traceback.format_exc()
        }
        payload.update(_get_ui_theme_payload())
        palette.sendInfoToHTML('audit_result', json.dumps(payload))
