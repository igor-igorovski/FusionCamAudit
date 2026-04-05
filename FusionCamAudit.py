import adsk.core
import traceback

from .commands.audit import entry as audit_cmd
from .commands.dump  import entry as dump_cmd
from .commands.dump_commands import entry as dump_commands_cmd
from .commands.probe_open import entry as probe_open_cmd
from .commands.trace_edit import entry as trace_edit_cmd

# Global handler list — keeps all event handlers alive for the session
handlers = []


def run(context):
    try:
        audit_cmd.start(handlers)
        dump_cmd.start(handlers)
        dump_commands_cmd.start(handlers)
        probe_open_cmd.start(handlers)
        trace_edit_cmd.start(handlers)
    except Exception:
        adsk.core.Application.get().userInterface.messageBox(
            'FusionCamAudit failed to start:\n' + traceback.format_exc()
        )


def stop(context):
    try:
        audit_cmd.stop()
        dump_cmd.stop()
        dump_commands_cmd.stop()
        probe_open_cmd.stop()
        trace_edit_cmd.stop()
    except Exception:
        adsk.core.Application.get().userInterface.messageBox(
            'FusionCamAudit failed to stop:\n' + traceback.format_exc()
        )
