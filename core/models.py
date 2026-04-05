class ToolInfo:
    def __init__(self, number='', description='', preset_name='', holder_name=''):
        self.number      = number
        self.description = description
        self.preset_name = preset_name
        self.holder_name = holder_name

    def to_dict(self):
        return {
            'number':      self.number,
            'description': self.description,
            'preset_name': self.preset_name,
            'holder_name': self.holder_name,
        }


class FieldCheck:
    def __init__(self, code='', field='', status='not_checked',
                 severity='info', message='', guide_refs=None):
        self.code       = code
        self.field      = field
        self.status     = status    # pass | fail | warning | not_checked
        self.severity   = severity  # info | warning | error
        self.message    = message
        self.guide_refs = guide_refs if guide_refs is not None else []

    def to_dict(self):
        return {
            'code':       self.code,
            'field':      self.field,
            'status':     self.status,
            'severity':   self.severity,
            'message':    self.message,
            'guide_refs': self.guide_refs,
        }


class OperationRow:
    def __init__(self, name='', op_type='', operation_id='', tool=None, checks=None):
        self.name         = name
        self.op_type      = op_type
        self.operation_id = operation_id
        self.tool         = tool     # ToolInfo | None
        self.checks       = checks if checks is not None else []  # list of FieldCheck

    def to_dict(self):
        return {
            'name':         self.name,
            'op_type':      self.op_type,
            'operation_id': self.operation_id,
            'tool':         self.tool.to_dict() if self.tool else None,
            'checks':       [c.to_dict() for c in self.checks],
        }


class SetupRow:
    def __init__(self, name='', program_number='', program_comment='',
                 work_offset='', machine_model='', operations=None, checks=None):
        self.name            = name
        self.program_number  = program_number
        self.program_comment = program_comment
        self.work_offset     = work_offset
        self.machine_model   = machine_model
        self.operations      = operations if operations is not None else []  # list of OperationRow
        self.checks          = checks if checks is not None else []          # list of FieldCheck

    def to_dict(self):
        return {
            'name':            self.name,
            'program_number':  self.program_number,
            'program_comment': self.program_comment,
            'work_offset':     self.work_offset,
            'machine_model':   self.machine_model,
            'operations':      [o.to_dict() for o in self.operations],
            'checks':          [c.to_dict() for c in self.checks],
        }


class AuditResult:
    def __init__(self, status='ok', setups=None, summary=None, message=''):
        self.status  = status
        self.setups  = setups  if setups  is not None else []  # list of SetupRow
        self.summary = summary if summary is not None else {}
        self.message = message

    def compute_summary(self):
        """Count pass/fail/warning/not_checked across all FieldChecks."""
        counts = {'pass': 0, 'fail': 0, 'warning': 0, 'not_checked': 0}
        for setup in self.setups:
            for chk in setup.checks:
                key = chk.status if chk.status in counts else 'not_checked'
                counts[key] += 1
            for op in setup.operations:
                for chk in op.checks:
                    key = chk.status if chk.status in counts else 'not_checked'
                    counts[key] += 1
        self.summary = counts

    def to_dict(self):
        self.compute_summary()
        return {
            'status':  self.status,
            'setups':  [s.to_dict() for s in self.setups],
            'summary': self.summary,
            'message': self.message,
        }
