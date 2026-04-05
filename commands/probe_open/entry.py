"""
Selection-context and executeTextCommand probe command.
Captures info about the current selection and tests a small set of text commands.
"""
import adsk.core
import adsk.cam
import traceback
import os
import json

COMMAND_ID = 'FusionCamAudit_ProbeOpen'
COMMAND_NAME = 'Probe CAM Open'
COMMAND_TOOLTIP = 'Probe selected CAM entity context and test a small set of open/edit text commands'
PANEL_ID = 'CAMManagePanel'

_app = adsk.core.Application.get()
_ui = _app.userInterface

_handlers = []
_cmd_def = None

_TEXT_COMMAND_CANDIDATES = (
    'NaNeuCAMUI.Edit',
    'NaNeuCAMUI.EditOperation',
    'NaNeuCAMUI.ShowDialog Edit',
    'Commands.Start EditCommand',
    'Commands.Start CAMEdit',
)

_COMMAND_ID_CANDIDATES = (
    'CAMFindInBrowser',
    'CAMEdit',
    'CAMEditCommand',
    'EditCommand',
    'Commands.Edit',
)


def _addon_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _tc_write(msg):
    try:
        tc = _ui.palettes.itemById('TextCommands')
        if tc:
            tc.writeText(msg)
    except Exception:
        pass


def _safe_call(fn, default=''):
    try:
        value = fn()
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

    on_created = ProbeOpenCreatedHandler()
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


class ProbeOpenCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False

            on_execute = ProbeOpenExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)
        except Exception:
            _ui.messageBox('ProbeOpenCreatedHandler:\n' + traceback.format_exc())


class ProbeOpenExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            _run_probe()
        except Exception:
            _ui.messageBox('ProbeOpenExecuteHandler:\n' + traceback.format_exc())


def _describe_selection():
    active = _ui.activeSelections
    items = []
    for i in range(active.count):
        sel = active.item(i)
        entity = _safe_call(lambda: sel.entity, None)
        if not entity:
            continue
        item = {
            'index': i,
            'name': _safe_call(lambda: entity.name, ''),
            'objectType': _safe_call(lambda: entity.objectType, ''),
            'classType': _safe_call(lambda: entity.classType(), ''),
            'isValid': _safe_call(lambda: entity.isValid, ''),
        }
        if adsk.cam.Operation.cast(entity):
            op = adsk.cam.Operation.cast(entity)
            item['selectionType'] = 'CAMOperation'
            item['operationId'] = _safe_call(lambda: op.operationId, '')
            item['operationType'] = _safe_call(lambda: op.operationType, '')
            item['strategy'] = _safe_call(lambda: op.parameters.itemByName('strategy').expression, '')
            item['parentSetupName'] = _safe_call(lambda: op.parentSetup.name, '')
        elif adsk.cam.Setup.cast(entity):
            setup = adsk.cam.Setup.cast(entity)
            item['selectionType'] = 'CAMSetup'
            item['setupName'] = _safe_call(lambda: setup.name, '')
        else:
            item['selectionType'] = 'Other'
        items.append(item)
    return items


def _probe_command_ids():
    results = []
    for command_id in _COMMAND_ID_CANDIDATES:
        cmd = _safe_call(lambda: _ui.commandDefinitions.itemById(command_id), None)
        results.append({
            'id': command_id,
            'exists': bool(cmd),
            'name': _safe_call(lambda: cmd.name, '') if cmd else '',
            'tooltip': _safe_call(lambda: cmd.tooltip, '') if cmd else '',
        })
    return results


def _probe_text_commands():
    results = []
    for text_cmd in _TEXT_COMMAND_CANDIDATES:
        try:
            response = _app.executeTextCommand(text_cmd)
            results.append({
                'command': text_cmd,
                'status': 'ok',
                'response': '' if response is None else str(response),
            })
        except Exception as exc:
            results.append({
                'command': text_cmd,
                'status': 'error',
                'response': str(exc),
            })
    return results


def _run_probe():
    out_dir = os.path.join(_addon_root(), 'docs', 'DEBUG_DUMP')
    os.makedirs(out_dir, exist_ok=True)

    data = {
      'selection': _describe_selection(),
      'command_id_candidates': _probe_command_ids(),
      'text_command_candidates': _probe_text_commands(),
    }

    json_path = os.path.join(out_dir, 'OPEN_PROBE.json')
    txt_path = os.path.join(out_dir, 'OPEN_PROBE.txt')

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    lines = []
    lines.append('OPEN PROBE')
    lines.append('=' * 60)
    lines.append('')
    lines.append('Selection')
    lines.append('-' * 20)
    if not data['selection']:
        lines.append('No active selection.')
    else:
        for item in data['selection']:
            lines.append('[{index}] {selectionType} :: {name}'.format(**item))
            lines.append('  objectType: {}'.format(item.get('objectType', '')))
            lines.append('  classType: {}'.format(item.get('classType', '')))
            if item.get('operationId', '') != '':
                lines.append('  operationId: {}'.format(item.get('operationId', '')))
            if item.get('operationType', '') != '':
                lines.append('  operationType: {}'.format(item.get('operationType', '')))
            if item.get('parentSetupName', ''):
                lines.append('  parentSetup: {}'.format(item.get('parentSetupName', '')))
            lines.append('')

    lines.append('Command ID Candidates')
    lines.append('-' * 20)
    for item in data['command_id_candidates']:
        lines.append('{id} :: exists={exists} :: name={name}'.format(**item))
        if item.get('tooltip', ''):
            lines.append('  tooltip: {}'.format(item['tooltip']))
    lines.append('')

    lines.append('Text Command Candidates')
    lines.append('-' * 20)
    for item in data['text_command_candidates']:
        lines.append('{command} :: {status}'.format(**item))
        if item.get('response', ''):
            lines.append('  response: {}'.format(item['response']))
    lines.append('')

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    _tc_write('[Open Probe] JSON: {}'.format(json_path))
    _tc_write('[Open Probe] TXT: {}'.format(txt_path))
