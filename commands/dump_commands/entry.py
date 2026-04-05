"""
Fusion command definitions dump command.
Writes all available Fusion commandDefinitions to docs/DEBUG_DUMP.
"""
import adsk.core
import traceback
import os
import json

COMMAND_ID = 'FusionCamAudit_DumpCommands'
COMMAND_NAME = 'Dump Fusion Commands'
COMMAND_TOOLTIP = 'Dump Fusion commandDefinitions to DEBUG_DUMP/COMMAND_DEFINITIONS.json'
PANEL_ID = 'CAMManagePanel'

_app = adsk.core.Application.get()
_ui = _app.userInterface

_handlers = []
_cmd_def = None


def _addon_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _tc_write(msg):
    try:
        tc = _ui.palettes.itemById('TextCommands')
        if tc:
            tc.writeText(msg)
    except Exception:
        pass


def _safe_attr(obj, name, default=''):
    try:
        value = getattr(obj, name)
        return value if value is not None else default
    except Exception:
        return default


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

    on_created = DumpCommandsCreatedHandler()
    _cmd_def.commandCreated.add(on_created)
    _handlers.append(on_created)
    external_handlers.append(on_created)

    try:
        ws = _ui.workspaces.itemById('CAMEnvironment')
        panel = ws.toolbarPanels.itemById(PANEL_ID)
        ctrl = panel.controls.itemById(COMMAND_ID)
        if not ctrl:
            panel.controls.addCommand(_cmd_def)
    except Exception:
        pass


def stop():
    global _cmd_def

    try:
        ws = _ui.workspaces.itemById('CAMEnvironment')
        panel = ws.toolbarPanels.itemById(PANEL_ID)
        ctrl = panel.controls.itemById(COMMAND_ID)
        if ctrl:
            ctrl.deleteMe()
    except Exception:
        pass

    if _cmd_def:
        _cmd_def.deleteMe()
        _cmd_def = None

    _handlers.clear()


class DumpCommandsCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False

            on_execute = DumpCommandsExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)
        except Exception:
            _ui.messageBox('DumpCommandsCreatedHandler:\n' + traceback.format_exc())


class DumpCommandsExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            _run_dump()
        except Exception:
            _ui.messageBox('DumpCommandsExecuteHandler:\n' + traceback.format_exc())


def _run_dump():
    rows = []
    filtered = []
    filters = ('cam', 'manufacture', 'operation', 'edit', 'toolpath')

    cmd_defs = _ui.commandDefinitions
    for i in range(cmd_defs.count):
        cmd = cmd_defs.item(i)
        row = {
            'index': i,
            'id': _safe_attr(cmd, 'id', ''),
            'name': _safe_attr(cmd, 'name', ''),
            'tooltip': _safe_attr(cmd, 'tooltip', ''),
        }
        rows.append(row)

        haystack = ' '.join([row['id'], row['name'], row['tooltip']]).lower()
        if any(token in haystack for token in filters):
            filtered.append(row)

    out_dir = os.path.join(_addon_root(), 'docs', 'DEBUG_DUMP')
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, 'COMMAND_DEFINITIONS.json')
    txt_path = os.path.join(out_dir, 'COMMAND_DEFINITIONS_FILTERED.txt')

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    lines = []
    lines.append('FUSION COMMAND DEFINITIONS FILTERED')
    lines.append('=' * 60)
    lines.append('Filters: {}'.format(', '.join(filters)))
    lines.append('Total commands: {}'.format(len(rows)))
    lines.append('Filtered commands: {}'.format(len(filtered)))
    lines.append('')

    for row in filtered:
        lines.append('[{index}] {id}'.format(**row))
        lines.append('  Name: {}'.format(row['name']))
        lines.append('  Tooltip: {}'.format(row['tooltip']))
        lines.append('')

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    _tc_write('[Fusion Commands Dump] JSON: {}'.format(json_path))
    _tc_write('[Fusion Commands Dump] Filtered TXT: {}'.format(txt_path))
