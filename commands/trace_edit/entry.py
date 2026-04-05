"""
Trace native command activity while the user manually clicks Edit.
Logs commandStarting and commandCreated events to docs/DEBUG_DUMP.
"""
import adsk.core
import traceback
import os
import json
import time
import threading

COMMAND_ID = 'FusionCamAudit_TraceEdit'
COMMAND_NAME = 'Trace Edit Command'
COMMAND_TOOLTIP = 'Start tracing commandStarting/commandCreated so you can manually click Edit'
PANEL_ID = 'CAMManagePanel'
TRACE_DURATION_SEC = 20.0

_app = adsk.core.Application.get()
_ui = _app.userInterface

_handlers = []
_cmd_def = None
_trace_state = {
    'active': False,
    'started_at': 0.0,
    'events': [],
    'timer': None,
}


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


def _safe_selection_snapshot():
    items = []
    try:
        sels = _ui.activeSelections
        for i in range(sels.count):
            sel = sels.item(i)
            entity = _safe_attr(sel, 'entity', None)
            if not entity:
                continue
            items.append({
                'index': i,
                'name': _safe_attr(entity, 'name', ''),
                'objectType': _safe_attr(entity, 'objectType', ''),
            })
    except Exception:
        pass
    return items


def _record_event(kind, command_def):
    if not _trace_state['active']:
        return

    entry = {
        'ts': time.time(),
        'kind': kind,
        'id': _safe_attr(command_def, 'id', ''),
        'name': _safe_attr(command_def, 'name', ''),
        'tooltip': _safe_attr(command_def, 'tooltip', ''),
        'selection': _safe_selection_snapshot(),
    }
    _trace_state['events'].append(entry)


def _write_trace_dump():
    out_dir = os.path.join(_addon_root(), 'docs', 'DEBUG_DUMP')
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, 'EDIT_TRACE.json')
    txt_path = os.path.join(out_dir, 'EDIT_TRACE.txt')

    payload = {
        'started_at': _trace_state['started_at'],
        'duration_sec': TRACE_DURATION_SEC,
        'events': _trace_state['events'],
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    lines = []
    lines.append('EDIT TRACE')
    lines.append('=' * 60)
    lines.append('Duration: {} sec'.format(TRACE_DURATION_SEC))
    lines.append('Events: {}'.format(len(_trace_state['events'])))
    lines.append('')
    for item in _trace_state['events']:
        lines.append('{kind} :: {id} :: {name}'.format(**item))
        if item.get('tooltip', ''):
            lines.append('  tooltip: {}'.format(item['tooltip']))
        if item.get('selection'):
            for sel in item['selection']:
                lines.append('  selection[{index}]: {name} :: {objectType}'.format(**sel))
        lines.append('')

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    _tc_write('[Edit Trace] JSON: {}'.format(json_path))
    _tc_write('[Edit Trace] TXT: {}'.format(txt_path))


def _stop_trace():
    if not _trace_state['active']:
        return
    _trace_state['active'] = False
    _trace_state['timer'] = None
    _write_trace_dump()


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

    on_created = TraceEditCreatedHandler()
    _cmd_def.commandCreated.add(on_created)
    _handlers.append(on_created)
    external_handlers.append(on_created)

    on_starting = TraceCommandStartingHandler()
    _ui.commandStarting.add(on_starting)
    _handlers.append(on_starting)
    external_handlers.append(on_starting)

    on_command_created = TraceGlobalCommandCreatedHandler()
    _ui.commandCreated.add(on_command_created)
    _handlers.append(on_command_created)
    external_handlers.append(on_command_created)

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


class TraceEditCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False

            on_execute = TraceEditExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)
        except Exception:
            _ui.messageBox('TraceEditCreatedHandler:\n' + traceback.format_exc())


class TraceEditExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            if _trace_state.get('timer'):
                try:
                    _trace_state['timer'].cancel()
                except Exception:
                    pass
            _trace_state['active'] = True
            _trace_state['started_at'] = time.time()
            _trace_state['events'] = []
            timer = threading.Timer(TRACE_DURATION_SEC, _stop_trace)
            timer.daemon = True
            _trace_state['timer'] = timer
            timer.start()
            _tc_write('[Edit Trace] Listening for {} seconds. Manually click Edit now.'.format(int(TRACE_DURATION_SEC)))
        except Exception:
            _ui.messageBox('TraceEditExecuteHandler:\n' + traceback.format_exc())


class TraceCommandStartingHandler(adsk.core.ApplicationCommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            if not _trace_state['active']:
                return
            _record_event('commandStarting', args.commandDefinition)
        except Exception:
            pass


class TraceGlobalCommandCreatedHandler(adsk.core.ApplicationCommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            if not _trace_state['active']:
                return
            _record_event('commandCreated', args.commandDefinition)
        except Exception:
            pass
