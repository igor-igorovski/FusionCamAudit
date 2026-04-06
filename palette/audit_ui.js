(function () {
  'use strict';

  function byId(id) {
    return document.getElementById(id);
  }

  function el(tag, cls) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    return node;
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  var OPERATION_ICON_FILES = {
    adaptive_2d:           { ext: 'png' },
    adaptive_clearing:     { ext: 'png' },
    advanced_swarf:        { ext: 'svg' },
    blend:                 { ext: 'svg' },
    bore:                  { ext: 'png' },
    chamfer_2d:            { ext: 'png' },
    circular:              { ext: 'png' },
    contour_2d:            { ext: 'png' },
    corner:                { ext: 'png' },
    deburr:                { ext: 'svg' },
    drill:                 { ext: 'png' },
    engrave:               { ext: 'png' },
    face:                  { ext: 'png' },
    flat:                  { ext: 'png' },
    geodesic:              { ext: 'svg' },
    horizontal:            { ext: 'png' },
    morph:                 { ext: 'png' },
    morphed_spiral:        { ext: 'png' },
    multi_axis_clearing:   { ext: 'svg' },
    multi_axis_contour:    { ext: 'png' },
    multi_axis_finishing:  { ext: 'png' },
    parallel:              { ext: 'png' },
    pencil:                { ext: 'png' },
    pocket_2d:             { ext: 'png' },
    pocket_clearing:       { ext: 'png' },
    project:               { ext: 'png' },
    radial:                { ext: 'png' },
    ramp:                  { ext: 'png' },
    rotary_contour:        { ext: 'svg' },
    rotary_parallel:       { ext: 'png' },
    rotary_pocket:         { ext: 'svg' },
    scallop:               { ext: 'png' },
    slot:                  { ext: 'png' },
    spiral:                { ext: 'png' },
    steep_and_shallow:     { ext: 'png' },
    swarf:                 { ext: 'png' },
    thread:                { ext: 'png' },
    trace:                 { ext: 'png' }
  };

  var OPERATION_TYPE_META = {
    adaptive:              { label: 'Adaptive Clearing', iconKey: 'adaptive_clearing' },
    adaptive2d:            { label: '2D Adaptive Clearing', iconKey: 'adaptive_2d' },
    advancedswarf:         { label: 'Advanced Swarf', iconKey: 'advanced_swarf' },
    blend:                 { label: 'Blend', iconKey: 'blend' },
    bore:                  { label: 'Bore', iconKey: 'bore' },
    circular:              { label: 'Circular', iconKey: 'circular' },
    contour:               { label: 'Contour', iconKey: 'contour_2d' },
    contour2d:             { label: '2D Contour', iconKey: 'contour_2d' },
    deburr:                { label: 'Deburr', iconKey: 'deburr' },
    automaticdeburring:    { label: 'Deburr', iconKey: 'deburr' },
    automatic_deburring:   { label: 'Deburr', iconKey: 'deburr' },
    moduleworksautomaticdeburring: { label: 'Deburr', iconKey: 'deburr' },
    moduleworks_automatic_deburring: { label: 'Deburr', iconKey: 'deburr' },
    moduleworks_automatic_deburring_derived: { label: 'Deburr', iconKey: 'deburr' },
    drill:                 { label: 'Drill', iconKey: 'drill' },
    engrave:               { label: 'Engrave', iconKey: 'engrave' },
    face:                  { label: 'Face', iconKey: 'face' },
    flat:                  { label: 'Flat', iconKey: 'flat' },
    flow:                  { label: 'Flow', iconKey: 'multi_axis_contour' },
    geodesic:              { label: 'Geodesic', iconKey: 'geodesic' },
    horizontal:            { label: 'Horizontal', iconKey: 'horizontal' },
    horizontalnew:         { label: 'Flat', iconKey: 'flat' },
    horizontal_new:        { label: 'Flat', iconKey: 'flat' },
    morphedspiral:         { label: 'Morphed Spiral', iconKey: 'morphed_spiral' },
    morph:                 { label: 'Morph', iconKey: 'morph' },
    multicaxisclearing:    { label: 'Multi-Axis Clearing', iconKey: 'multi_axis_clearing' },
    multiaxisclearing:     { label: 'Multi-Axis Clearing', iconKey: 'multi_axis_clearing' },
    multi_axis_clearing:   { label: 'Multi-Axis Clearing', iconKey: 'multi_axis_clearing' },
    multicaxiscontour:     { label: 'Multi-Axis Contour', iconKey: 'multi_axis_contour' },
    multiaxiscontour:      { label: 'Multi-Axis Contour', iconKey: 'multi_axis_contour' },
    multi_axis_contour:    { label: 'Multi-Axis Contour', iconKey: 'multi_axis_contour' },
    multicaxisfinishing:   { label: 'Multi-Axis Finishing', iconKey: 'multi_axis_finishing' },
    multiaxisfinishing:    { label: 'Multi-Axis Finishing', iconKey: 'multi_axis_finishing' },
    multi_axis_finishing:  { label: 'Multi-Axis Finishing', iconKey: 'multi_axis_finishing' },
    parallel:              { label: 'Parallel', iconKey: 'parallel' },
    pencil:                { label: 'Pencil', iconKey: 'pencil' },
    pocket:                { label: 'Pocket Clearing', iconKey: 'pocket_clearing' },
    pocket2d:              { label: '2D Pocket', iconKey: 'pocket_2d' },
    project:               { label: 'Project', iconKey: 'project' },
    radial:                { label: 'Radial', iconKey: 'radial' },
    ramp:                  { label: 'Ramp', iconKey: 'ramp' },
    rotarycontour:         { label: 'Rotary Contour', iconKey: 'rotary_contour' },
    rotary_contour:        { label: 'Rotary Contour', iconKey: 'rotary_contour' },
    rotaryparallel:        { label: 'Rotary Parallel', iconKey: 'rotary_parallel' },
    rotary_parallel:       { label: 'Rotary Parallel', iconKey: 'rotary_parallel' },
    rotarypocket:          { label: 'Rotary Pocket', iconKey: 'rotary_pocket' },
    rotary_pocket:         { label: 'Rotary Pocket', iconKey: 'rotary_pocket' },
    scallop:               { label: 'Scallop', iconKey: 'scallop' },
    slot:                  { label: 'Slot', iconKey: 'slot' },
    spiral:                { label: 'Spiral', iconKey: 'spiral' },
    steepandshallow:       { label: 'Steep And Shallow', iconKey: 'steep_and_shallow' },
    swarf:                 { label: 'Swarf', iconKey: 'swarf' },
    thread:                { label: 'Thread', iconKey: 'thread' },
    path3d:                { label: 'Trace', iconKey: 'trace' },
    trace:                 { label: 'Trace', iconKey: 'trace' },
    trace3d:               { label: 'Trace', iconKey: 'trace' },
    chamfer2d:             { label: '2D Chamfer', iconKey: 'chamfer_2d' }
  };

  function normalizeOpType(opType) {
    return String(opType || '').trim().toLowerCase().replace(/[\s-]+/g, '').replace(/[^\w]/g, '');
  }

  function humanizeOpType(opType) {
    return String(opType || '')
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .replace(/[_-]+/g, ' ')
      .replace(/\s+/g, ' ')
      .replace(/\b\w/g, function (chr) { return chr.toUpperCase(); })
      .trim();
  }

  function getOperationMeta(opType) {
    var normalized = normalizeOpType(opType);
    return OPERATION_TYPE_META[normalized] || {
      label: humanizeOpType(opType) || 'Operation',
      iconKey: 'generic'
    };
  }

  function getOperationIconPath(iconKey) {
    var base = state.mode === 'preview' ? '../palette/resources/op-icons/' : './resources/op-icons/';
    var key = String(iconKey || 'generic');
    var meta = OPERATION_ICON_FILES[key] || { ext: 'png' };
    var suffix = state.theme === 'dark' ? '_dark' : '';
    return base + key + suffix + '.' + meta.ext;
  }

  function countChecks(checks) {
    var counts = { pass: 0, fail: 0, warning: 0, nc: 0 };
    (checks || []).forEach(function (check) {
      var key = check.status === 'not_checked' ? 'nc' : (check.status || 'nc');
      if (counts[key] !== undefined) counts[key]++;
    });
    return counts;
  }

  function hasAnyFailInChecks(checks) {
    for (var i = 0; i < (checks || []).length; i++) {
      if (((checks[i] && checks[i].status) || '') === 'fail') {
        return true;
      }
    }
    return false;
  }

  function hasAnyFailInSetup(setup) {
    if (hasAnyFailInChecks(setup.checks || [])) {
      return true;
    }
    var ops = setup.operations || [];
    for (var i = 0; i < ops.length; i++) {
      if (hasAnyFailInChecks(ops[i].checks || [])) {
        return true;
      }
    }
    return false;
  }

  function createDefaultBridge(mode) {
    if (mode === 'fusion') {
      return {
        send: function (action, payload) {
          adsk.fusionSendData(action, payload !== undefined ? JSON.stringify(payload) : '{}');
        }
      };
    }

    return {
      send: function () {}
    };
  }

  var config = {};
  var bridge = createDefaultBridge('fusion');
  var state = {
    mode: 'fusion',
    mockResult: null,
    lastResult: null,
    showUnchecked: false,
    showFailOnly: false,
    statusTimer: null
  };

  var refs = {
    title: byId('app-title'),
    headerBadges: byId('header-badges'),
    versionBadge: byId('badge-version'),
    previewBadge: byId('badge-preview'),
    btnRun: byId('btn-run'),
    btnTheme: byId('btn-theme'),
    btnToggleNc: byId('btn-toggle-nc'),
    btnToggleFail: byId('btn-toggle-fail'),
    btnExport: byId('btn-export'),
    btnExportMd: byId('btn-export-md'),
    summaryBar: byId('summary-bar'),
    summaryInfo: byId('summary-info'),
    inlineStatus: byId('inline-status'),
    cntPass: byId('cnt-pass'),
    cntFail: byId('cnt-fail'),
    cntWarning: byId('cnt-warning'),
    cntNc: byId('cnt-nc'),
    results: byId('results')
  };

  function getStoredTheme() {
    try {
      return window.localStorage ? window.localStorage.getItem('camAuditTheme') : null;
    } catch (e) {
      return null;
    }
  }

  function setStoredTheme(theme) {
    try {
      if (window.localStorage) {
        window.localStorage.setItem('camAuditTheme', theme);
      }
    } catch (e) {
      return;
    }
  }

  function applyTheme(themeRaw, isDark) {
    var resolved;
    if (typeof isDark === 'boolean') {
      resolved = isDark ? 'dark' : 'light';
    } else {
      resolved = themeRaw === 'light' ? 'light' : 'dark';
    }
    state.theme = resolved;
    document.body.setAttribute('data-theme', resolved);
    if (refs.btnTheme) {
      refs.btnTheme.textContent = resolved === 'light' ? 'Dark mode' : 'Light mode';
    }
  }

    function syncHeader() {
      if (refs.title && config.title) refs.title.textContent = config.title;
      if (refs.versionBadge) {
        refs.versionBadge.textContent = config.versionLabel || '';
        refs.versionBadge.style.display = config.versionLabel ? 'inline-block' : 'none';
      }
      if (refs.previewBadge) {
        refs.previewBadge.style.display = state.mode === 'preview' ? 'inline-block' : 'none';
        refs.previewBadge.textContent = (config.previewBadgeLabel || 'Preview Mode');
      }
      if (refs.headerBadges && !config.versionLabel && state.mode !== 'preview') {
        refs.headerBadges.style.display = 'none';
      }
    }

    function toggleTheme() {
      var nextTheme = state.theme === 'light' ? 'dark' : 'light';
      applyTheme(nextTheme);
      setStoredTheme(nextTheme);
    }

    function showInlineStatus(msg, tone) {
      if (state.statusTimer) {
        clearTimeout(state.statusTimer);
        state.statusTimer = null;
      }
      refs.summaryInfo.style.display = 'block';
      refs.inlineStatus.className = 'inline-status visible ' + (tone || 'info');
      refs.inlineStatus.textContent = msg || '';
      state.statusTimer = setTimeout(function () {
        clearInlineStatus();
      }, state.mode === 'preview' ? 2600 : 3000);
    }

    function clearInlineStatus() {
      refs.inlineStatus.className = 'inline-status';
      refs.inlineStatus.textContent = '';
      refs.summaryInfo.style.display = 'none';
    }

    function syncFilterButtons() {
      refs.btnToggleNc.textContent = state.showUnchecked ? 'Hide unchecked' : 'Show unchecked';
      refs.btnToggleFail.textContent = state.showFailOnly ? 'Show all items' : 'Show FAIL only';
      refs.btnToggleNc.classList.toggle('active', state.showUnchecked);
      refs.btnToggleFail.classList.toggle('active', state.showFailOnly);
    }

    function applyFailOnlyFilter() {
      var setupBlocks = document.querySelectorAll('.setup-block');
      for (var i = 0; i < setupBlocks.length; i++) {
        var setupBlock = setupBlocks[i];
        setupBlock.style.display = (!state.showFailOnly || setupBlock.getAttribute('data-has-fail') === 'true') ? 'block' : 'none';
      }

      var opBlocks = document.querySelectorAll('.op-block');
      for (var j = 0; j < opBlocks.length; j++) {
        var opBlock = opBlocks[j];
        opBlock.style.display = (!state.showFailOnly || opBlock.getAttribute('data-has-fail') === 'true') ? 'block' : 'none';
      }

      var setupInfoBlocks = document.querySelectorAll('.setup-info-block');
      for (var m = 0; m < setupInfoBlocks.length; m++) {
        var infoBlock = setupInfoBlocks[m];
        infoBlock.style.display = (!state.showFailOnly || infoBlock.getAttribute('data-has-fail') === 'true') ? 'block' : 'none';
      }

      var checkRows = document.querySelectorAll('.check-row');
      for (var k = 0; k < checkRows.length; k++) {
        var row = checkRows[k];
        var status = row.getAttribute('data-status');
        if (state.showFailOnly) {
          row.style.display = status === 'fail' ? 'flex' : 'none';
        } else if (status === 'nc') {
          row.style.display = state.showUnchecked ? 'flex' : 'none';
        } else {
          row.style.display = 'flex';
        }
      }
    }

    function buildCheckRow(chk) {
      var statusKey = chk.status === 'not_checked' ? 'nc' : (chk.status || 'nc');
      var row = el('div', 'check-row' + (statusKey === 'nc' ? ' nc' : ''));
      row.setAttribute('data-status', statusKey);

      var statusMap = { pass: '\u2713', fail: '\u2715', warning: '!', not_checked: '\u2013' };
      var icon = el('div', 'status-icon ' + statusKey);
      icon.textContent = statusMap[chk.status] || '\u2013';

      var body = el('div', 'check-body');
      var code = el('div', 'check-code');
      code.textContent = chk.code || '';
      var msg = el('div', 'check-msg');
      msg.textContent = chk.message || '';

      body.appendChild(code);
      body.appendChild(msg);
      row.appendChild(icon);
      row.appendChild(body);
      return row;
    }

    function buildOpActionButton(label, actionName, operationRef) {
      var btn = el('button', 'op-action-btn');
      btn.type = 'button';
      btn.textContent = label;
      btn.onclick = function (event) {
        event.stopPropagation();
        if (state.mode === 'preview') {
          var target = operationRef.setupName + ' / ' + operationRef.operationName;
          var prefix = actionName === 'edit_tool' ? 'Preview only: Edit Tool' : 'Preview only: ' + label;
          showInlineStatus(prefix + ' for ' + target + ' would be sent to Fusion.', 'info');
          return;
        }
        bridge.send('operation_action', {
          action: actionName,
          operationId: operationRef.operationId || '',
          setupName: operationRef.setupName || '',
          operationName: operationRef.operationName || '',
          operationType: operationRef.operationType || ''
        });
      };
      return btn;
    }

    function buildOpBlock(setup, op) {
      var block = el('div', 'op-block');
      block.setAttribute('data-has-fail', hasAnyFailInChecks(op.checks || []) ? 'true' : 'false');

      var counts = countChecks(op.checks || []);
      var opMeta = getOperationMeta(op && op.op_type ? op.op_type : '');
      var operationRef = {
        operationId: op && op.operation_id ? op.operation_id : '',
        setupName: setup && setup.name ? setup.name : '',
        operationName: op && op.name ? op.name : '',
        operationType: op && op.op_type ? op.op_type : ''
      };

      var hdr = el('div', 'op-header');
      var caret = el('span', 'caret');
      caret.textContent = '\u25b6';

      var iconEl = el('img', 'op-type-icon');
      iconEl.alt = '';
      iconEl.src = getOperationIconPath(opMeta.iconKey);
      iconEl.onerror = function () {
        if (iconEl.getAttribute('data-fallback') === '1') return;
        iconEl.setAttribute('data-fallback', '1');
        iconEl.src = getOperationIconPath('generic');
      };

      var nameEl = el('span', 'op-name');
      var opNameLabel = op && op.name ? String(op.name) : '(unnamed)';
      nameEl.textContent = opMeta.label ? (opMeta.label + ' : ' + opNameLabel) : opNameLabel;
      nameEl.title = nameEl.textContent;

      var toolEl = el('span', 'op-tool');
      if (op.tool && op.tool.description) {
        toolEl.textContent = 'T' + (op.tool.number || '?') + ' ' + op.tool.description;
        toolEl.title = toolEl.textContent;
      } else {
        toolEl.textContent = 'No tool info';
        toolEl.className += ' empty';
      }

      var metaEl = el('div', 'op-meta');
      metaEl.appendChild(iconEl);
      metaEl.appendChild(nameEl);
      metaEl.appendChild(toolEl);

      var statsEl = el('div', 'op-stats');
      ['fail', 'warning', 'pass'].forEach(function (key) {
        if (counts[key] > 0) {
          var chip = el('span', 'chip-sm ' + key);
          chip.textContent = counts[key];
          statsEl.appendChild(chip);
        }
      });

      var actionsEl = el('div', 'op-actions');
      actionsEl.appendChild(buildOpActionButton('Find', 'find', operationRef));
      actionsEl.appendChild(buildOpActionButton('Open', 'open', operationRef));
      actionsEl.appendChild(buildOpActionButton('Edit Tool', 'edit_tool', operationRef));

      hdr.appendChild(caret);
      hdr.appendChild(metaEl);
      hdr.appendChild(statsEl);
      hdr.appendChild(actionsEl);
      block.appendChild(hdr);

      var body = el('div', 'op-body');
      var checksDiv = el('div', 'op-checks');
      (op.checks || []).forEach(function (chk) {
        checksDiv.appendChild(buildCheckRow(chk));
      });
      body.appendChild(checksDiv);
      block.appendChild(body);

      hdr.onclick = function () {
        var open = body.style.display === '' || body.style.display === 'none';
        body.style.display = open ? 'block' : 'none';
        caret.classList.toggle('open', open);
      };

      return block;
    }

    function buildSetupInfoBlock(checks) {
      var setupInfoBlock = el('div', 'setup-info-block');
      setupInfoBlock.setAttribute('data-has-fail', hasAnyFailInChecks(checks || []) ? 'true' : 'false');

      var setupInfoHeader = el('div', 'setup-info-header');
      var setupInfoCaret = el('span', 'caret');
      setupInfoCaret.textContent = '\u25b6';
      var setupInfoTitle = el('span', 'setup-info-title');
      setupInfoTitle.textContent = 'Setup Info';
      var setupInfoBody = el('div', 'setup-info-body');
      var setupChecks = el('div', 'setup-checks');

      var setupCounts = countChecks(checks || []);
      var setupStats = el('div', 'setup-info-stats');
      ['fail', 'warning', 'pass'].forEach(function (key) {
        if (setupCounts[key] > 0) {
          var chip = el('span', 'chip-sm setup-' + key);
          chip.textContent = setupCounts[key];
          setupStats.appendChild(chip);
        }
      });

      (checks || []).forEach(function (chk) {
        setupChecks.appendChild(buildCheckRow(chk));
      });
      setupInfoBody.appendChild(setupChecks);

      setupInfoHeader.appendChild(setupInfoCaret);
      setupInfoHeader.appendChild(setupInfoTitle);
      setupInfoHeader.appendChild(setupStats);
      setupInfoHeader.onclick = function (event) {
        event.stopPropagation();
        var open = setupInfoBody.style.display === '' || setupInfoBody.style.display === 'none';
        setupInfoBody.style.display = open ? 'block' : 'none';
        setupInfoCaret.classList.toggle('open', open);
      };

      setupInfoBlock.appendChild(setupInfoHeader);
      setupInfoBlock.appendChild(setupInfoBody);
      return setupInfoBlock;
    }

    function buildSetupBlock(setup) {
      var block = el('div', 'setup-block');
      block.setAttribute('data-has-fail', hasAnyFailInSetup(setup) ? 'true' : 'false');

      var allChecks = (setup.checks || []).slice();
      (setup.operations || []).forEach(function (op) {
        (op.checks || []).forEach(function (check) { allChecks.push(check); });
      });
      var counts = countChecks(allChecks);

      var hdr = el('div', 'setup-header');
      var caret = el('span', 'caret');
      caret.textContent = '\u25b6';
      var nameEl = el('span', 'setup-name');
      nameEl.textContent = setup.name || '(unnamed setup)';
      var statsEl = el('div', 'setup-stats');

      ['fail', 'warning', 'pass'].forEach(function (key) {
        if (counts[key] > 0) {
          var chip = el('span', 'chip-sm ' + key);
          chip.textContent = counts[key];
          statsEl.appendChild(chip);
        }
      });

      hdr.appendChild(caret);
      hdr.appendChild(nameEl);
      hdr.appendChild(statsEl);
      block.appendChild(hdr);

      var body = el('div', 'setup-body');
      if ((setup.checks || []).length > 0) {
        body.appendChild(buildSetupInfoBlock(setup.checks));
      }

      (setup.operations || []).forEach(function (op) {
        body.appendChild(buildOpBlock(setup, op));
      });
      block.appendChild(body);

      hdr.onclick = function () {
        var open = body.style.display === '' || body.style.display === 'none';
        body.style.display = open ? 'block' : 'none';
        caret.classList.toggle('open', open);
      };

      return block;
    }

    function renderResult(result) {
      state.lastResult = result;
      if (state.mode === 'fusion') {
        applyTheme(result ? result.themeRaw : null, result ? result.isDark : false);
      }
      refs.btnRun.disabled = false;

      var summary = result.summary || {};
      refs.cntPass.textContent = summary.pass || 0;
      refs.cntFail.textContent = summary.fail || 0;
      refs.cntWarning.textContent = summary.warning || 0;
      refs.cntNc.textContent = summary.not_checked || 0;
      refs.summaryBar.style.display = 'flex';
      refs.summaryInfo.style.display = 'block';

      if (result.message) {
        refs.results.innerHTML = '<div class="state-placeholder"><div class="icon">\u231b</div><p>' + escHtml(result.message) + '</p></div>';
        return;
      }

      if (!result.setups || result.setups.length === 0) {
        refs.results.innerHTML = '<div class="state-placeholder"><p>No CAM setups found in the active document.</p></div>';
        return;
      }

      refs.results.innerHTML = '';
      result.setups.forEach(function (setup) {
        refs.results.appendChild(buildSetupBlock(setup));
      });

      refs.btnExport.disabled = state.mode !== 'fusion';
      refs.btnExportMd.disabled = state.mode !== 'fusion';
      refs.btnToggleNc.disabled = false;
      refs.btnToggleFail.disabled = false;
      applyFailOnlyFilter();
    }

    function showLoading() {
      refs.results.innerHTML = '<div class="state-placeholder"><div class="spinner"></div><p>Running audit...</p></div>';
      refs.summaryBar.style.display = 'none';
      refs.summaryInfo.style.display = 'none';
      refs.btnRun.disabled = true;
      refs.btnToggleNc.disabled = true;
      refs.btnToggleFail.disabled = true;
      refs.btnExport.disabled = true;
      refs.btnExportMd.disabled = true;
    }

    function showError(msg) {
      refs.results.innerHTML = '<div class="state-placeholder"><div class="icon" style="color:#f44">\u26a0</div><p>' + escHtml(msg) + '</p></div>';
      refs.btnRun.disabled = false;
      showInlineStatus(msg, 'error');
    }

    function runAudit() {
      state.showUnchecked = false;
      state.showFailOnly = false;
      syncFilterButtons();
      clearInlineStatus();

      if (state.mode === 'preview') {
        renderResult(state.mockResult || { summary: {}, setups: [] });
        showInlineStatus(config.previewLoadMessage || 'Preview loaded with mock CAM audit data.', 'ok');
        return;
      }

      showLoading();
      bridge.send('run_audit', {});
    }

    function exportReport() {
      if (state.mode !== 'fusion' || !state.lastResult) {
        showInlineStatus('Preview only: export is disabled outside Fusion.', 'info');
        return;
      }
      bridge.send('export_json', state.lastResult);
    }

    function exportMarkdown() {
      if (state.mode !== 'fusion' || !state.lastResult) {
        showInlineStatus('Preview only: export is disabled outside Fusion.', 'info');
        return;
      }
      bridge.send('export_md', state.lastResult);
    }

    function toggleUnchecked() {
      state.showUnchecked = !state.showUnchecked;
      syncFilterButtons();
      applyFailOnlyFilter();
    }

    function toggleFailOnly() {
      state.showFailOnly = !state.showFailOnly;
      syncFilterButtons();
      applyFailOnlyFilter();
    }

    function handleOperationActionResult(result) {
      var status = result && result.status ? result.status : 'info';
      var message = result && result.message ? result.message : 'Operation action finished.';
      var tone = status;
      if (tone !== 'error' && tone !== 'ok' && tone !== 'partial') {
        tone = 'info';
      }
      showInlineStatus(message, tone);
    }

    function bindToolbar() {
      refs.btnRun.onclick = runAudit;
      if (refs.btnTheme) refs.btnTheme.onclick = toggleTheme;
      refs.btnToggleNc.onclick = toggleUnchecked;
      refs.btnToggleFail.onclick = toggleFailOnly;
      refs.btnExport.onclick = exportReport;
      refs.btnExportMd.onclick = exportMarkdown;
    }

    function installFusionBridge() {
      window.fusionJavaScriptHandler = {
        handle: function (action, data) {
          try {
            if (action === 'audit_result') {
              renderResult(JSON.parse(data));
            } else if (action === 'operation_action_result') {
              handleOperationActionResult(JSON.parse(data));
            }
          } catch (e) {
            showError('Failed to parse audit result: ' + e.message);
          }
          return 'ok';
        }
      };
    }

    function init(userConfig) {
      config = userConfig || {};
      bridge = config.bridge || createDefaultBridge(config.mode);
      state.mode = config.mode || 'fusion';
      state.mockResult = config.mockResult || null;
      state.theme = state.mode === 'preview'
        ? (config.theme || getStoredTheme() || 'light')
        : 'dark';
      syncHeader();
      applyTheme(state.theme, state.theme === 'dark');
      bindToolbar();
      syncFilterButtons();

      if (state.mode === 'fusion') {
        installFusionBridge();
        if (refs.btnTheme) refs.btnTheme.style.display = 'none';
        refs.btnToggleNc.disabled = true;
        refs.btnToggleFail.disabled = true;
        refs.btnExport.disabled = true;
        refs.btnExportMd.disabled = true;
        showLoading();

        // adsk.fusionSendData is injected by Fusion after the page loads.
        // Poll until it is available before sending the first message.
        (function waitForAdsk() {
          if (typeof adsk !== 'undefined' && typeof adsk.fusionSendData === 'function') {
            bridge.send('palette_ready', {});
          } else {
            setTimeout(waitForAdsk, 50);
          }
        }());
      } else {
        if (refs.btnTheme) refs.btnTheme.style.display = '';
        refs.btnToggleNc.disabled = false;
        refs.btnToggleFail.disabled = false;
        refs.btnExport.disabled = false;
        refs.btnExportMd.disabled = false;
        renderResult(state.mockResult || { summary: {}, setups: [] });
        showInlineStatus(config.previewHintMessage || 'Open this file in VS Code Live Preview or a browser for fast UI iteration.', 'info');
      }
    }

  window.CamAuditUI = {
    init: init
  };
})();
