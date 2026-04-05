"""
CAM Debug Dump command.
Dumps all setup and operation parameters to docs/DEBUG_DUMP/DUMP_SETUP.txt.
Writes a confirmation line to the Text Commands panel.
"""
import adsk.core
import adsk.cam
import traceback
import os

COMMAND_ID      = 'FusionCamAudit_DumpSetup'
COMMAND_NAME    = 'CAM Debug Dump'
COMMAND_TOOLTIP = 'Dump all CAM setup/operation parameters to DEBUG_DUMP/DUMP_SETUP.txt'
PANEL_ID        = 'CAMManagePanel'

_app = adsk.core.Application.get()
_ui  = _app.userInterface

_handlers = []
_cmd_def  = None


def _addon_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _tc_write(msg):
    """Write a line to the Text Commands panel."""
    try:
        tc = _ui.palettes.itemById('TextCommands')
        if tc:
            tc.writeText(msg)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def start(external_handlers):
    global _cmd_def

    cmd_defs = _ui.commandDefinitions
    existing = cmd_defs.itemById(COMMAND_ID)
    if existing:
        existing.deleteMe()

    _cmd_def = cmd_defs.addButtonDefinition(
        COMMAND_ID,
        COMMAND_NAME,
        COMMAND_TOOLTIP
    )

    on_created = DumpCommandCreatedHandler()
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
# CommandCreated
# ---------------------------------------------------------------------------

class DumpCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False

            on_execute = DumpCommandExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)

        except Exception:
            _ui.messageBox('DumpCommandCreatedHandler:\n' + traceback.format_exc())


# ---------------------------------------------------------------------------
# Execute — runs dump
# ---------------------------------------------------------------------------

class DumpCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            _run_dump()
        except Exception:
            _ui.messageBox('DumpCommandExecuteHandler:\n' + traceback.format_exc())


# ---------------------------------------------------------------------------
# Dump logic
# ---------------------------------------------------------------------------

def _run_dump():
    app = adsk.core.Application.get()
    doc = app.activeDocument
    cam = None
    for i in range(doc.products.count):
        p = doc.products.item(i)
        if p.objectType == adsk.cam.CAM.classType():
            cam = p
            break

    if cam is None:
        _tc_write('[CAM Dump] No CAM product found.')
        return

    lines = []
    lines.append('=' * 60)
    lines.append('CAM DEBUG DUMP')
    lines.append('=' * 60)

    for si in range(cam.setups.count):
        setup = cam.setups.item(si)
        setup_name = _safe(lambda: setup.name, '?')
        lines.append('')
        lines.append('SETUP [{}]: {}'.format(si, setup_name))
        lines.append('-' * 40)

        # All setup parameters
        try:
            params = setup.parameters
            for pi in range(params.count):
                param = params.item(pi)
                name_p = _safe(lambda: param.name, '?')
                expr   = _safe(lambda: param.expression, '?')
                lines.append('  {} = {}'.format(name_p, expr))
        except Exception as e:
            lines.append('  [param error: {}]'.format(e))

        # All operations
        try:
            for oi in range(setup.allOperations.count):
                op = setup.allOperations.item(oi)
                op_name = _safe(lambda: op.name, '?')
                lines.append('')
                lines.append('  OP [{}]: {}'.format(oi, op_name))
                lines.append('  ' + '-' * 36)
                try:
                    op_params = op.parameters
                    for pi in range(op_params.count):
                        param = op_params.item(pi)
                        name_p = _safe(lambda: param.name, '?')
                        expr   = _safe(lambda: param.expression, '?')
                        lines.append('    {} = {}'.format(name_p, expr))
                except Exception as e:
                    lines.append('    [op param error: {}]'.format(e))
        except Exception as e:
            lines.append('  [operations error: {}]'.format(e))

    lines.append('')
    lines.append('=' * 60)

    dump_path = os.path.join(_addon_root(), 'docs', 'DEBUG_DUMP', 'DUMP_SETUP.txt')
    os.makedirs(os.path.dirname(dump_path), exist_ok=True)
    with open(dump_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    _tc_write('[CAM Dump] Written to: {}'.format(dump_path))


def _safe(fn, default):
    try:
        return fn()
    except Exception:
        return default
