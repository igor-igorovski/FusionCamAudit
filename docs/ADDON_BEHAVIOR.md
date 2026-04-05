# FusionCamAudit — Opis ponašanja add-ina

## Pregled

FusionCamAudit je Fusion 360 Python add-in koji provodi **determinističku CAM audit** aktivnog dokumenta.
Ne koristi nikakvu AI logiku — sve provjere su eksplicitna pravila definirana u `config/rules.json`.

---

## Pokretanje

Add-in se registrira pri učitavanju Fusiona (ili ručno u Add-Ins manageru).

Po pokretanju (`run(context)`):
- Registrira gumb **CAM Audit** u `CAMManagePanel` (CAM workspace, Manage tab)
- Registrira gumb **CAM Debug Dump** u istom panelu
- Svi event handleri čuvaju se u globalnom `handlers = []` da ne budu garbage-collected

Po zaustavljanju (`stop(context)`):
- Uklanja oba gumba iz panela
- Briše paletu ako je otvorena
- Čisti handler listu

---

## Gumb: CAM Audit

Otvara **HTML paletu** zadokiranom s desne strane (800×600 px, `PaletteDockStateRight`).

Paleta se svaki put iznova kreira (ne reciklira) kako bi se osiguralo da se učita svježi HTML pri svakom reloadu add-ina.

### Sučelje palete

**Header** — naziv "CAM Audit" + verzija badge (trenutno `v0.1 · Phase 4`)

**Toolbar:**
- `▶ Run Audit` — pokreće audit aktivnog CAM dokumenta
- `Show unchecked` — toggle; skriva/prikazuje provjere sa statusom `not_checked` (sivim); aktivan = plav
- `Export JSON` — šalje rezultat Pythonu za zapis u `cam_audit_report.json` (disabled dok audit nije pokrenut)
- `Export MD` — šalje rezultat Pythonu za zapis u `cam_audit_summary.md` (disabled dok audit nije pokrenut)

**Summary bar** (pojavljuje se nakon audita):
- zeleni chip: broj ✓ pass provjera
- crveni chip: broj ✗ fail provjera
- narančasti chip: broj ! warning provjera
- sivi chip: broj – not_checked provjera

**Rezultati** — lista setup blokova (collapsible, default collapsed)

### Tijek audita (Run Audit)

1. HTML šalje `run_audit` poruku Pythonu
2. Python svježe učitava sve core module (`core/models.py`, `core/rules_loader.py`, `core/extractor.py`, `core/setup_auditor.py`, `core/operation_auditor.py`) koristeći `importlib.util` — zaobilazi `sys.modules` cache za hot-reload bez restarta Fusiona
3. Dohvaća aktivni CAM produkt iz dokumenta (`adsk.cam.CAM`)
4. Ako CAM produkt ne postoji → prikazuje poruku greške
5. Učitava pravila iz `config/rules.json`
6. Ekstrahira sve setupove (`extractor.extract_setups(cam)`)
7. Za svaki setup:
   - Provjerava `skip_audit` pravila (npr. DON'T POST → preskače cijeli setup)
   - Evaluira sva setup-level pravila → lista `FieldCheck` objekata
   - Za svaku operaciju: evaluira sva operation-level pravila → lista `FieldCheck` objekata
8. Gradi `AuditResult` model, serijalizira u JSON
9. Šalje JSON paleti via `palette.sendInfoToHTML('audit_result', ...)`
10. Paleta prikazuje rezultate

---

## Gumb: CAM Debug Dump

**Nema paletu** — rezultat ide direktno u datoteku.

Po kliku:
1. Dohvaća aktivni CAM produkt
2. Iterira sve setupove i sve operacije unutar svakog setupa
3. Za svaki setup i operaciju ispisuje sve parametre (`param.name = param.expression`)
4. Zapisuje u `docs/DEBUG_DUMP/DUMP_SETUP.txt` (overwrite svaki put)
5. Kratku potvrdu (putanja do fajla) ispisuje u **Text Commands** panel

Korisno za otkrivanje točnih naziva Fusion CAM parametara.

---

## Prikaz rezultata u paletti

### Setup blok (collapsible)

Svaki setup prikazuje se kao **collapsible blok**:
- **Header** (klik → expand/collapse):
  - `▶/▼` caret
  - Ime setupa
  - Mini chipovi s brojem fail / warning / pass (zbroj setup provjera + svih op provjera)
- **Tijelo** (skriveno po defaultu):
  - **Setup checks sekcija** — lista provjera setup-level pravila
  - **Op blokovi** — jedan po operaciji (vidi niže)

### Op blok (collapsible, unutar setup tijela)

Svaka operacija prikazuje se kao **collapsible podblok**:
- **Header** (klik → expand/collapse):
  - `▶/▼` caret
  - Ime operacije
  - Alat: `T[broj] [opis]`
  - Mini chipovi fail / warning / pass
- **Tijelo** (skriveno po defaultu):
  - Lista provjera za tu operaciju

### Check row

Svaka provjera prikazuje:
- Kružni status ikone: zeleni `✓` / crveni `✗` / narančasti `!` / sivi `–`
- Kod pravila (monospace, sivo)
- Poruka greške (prikazuje se samo za fail i warning; pass i not_checked nemaju poruku)

`not_checked` redovi su skriveni po defaultu. Prikazuju se klikom na **Show unchecked**.

---

## Ekstrakcija podataka (`core/extractor.py`)

Čita Fusion CAM API i vraća plain dict objekte (bez Fusion model objekata).

### Setup polja

| Polje | Fusion param | Opis |
|---|---|---|
| `name` | `setup.name` | Ime setupa |
| `programNumber` | `job_programName` | NC program broj (npr. `1001`) |
| `programComment` | `job_programComment` | Komentar programa |
| `workOffset` | `job_workOffset` | Radni offset (int 1–6 → G54–G59) |
| `machineModel` | `job_machine_type` ili `job_machine_configuration` | Model stroja |
| `fixtureType` | `job_fixture` | `'present'` ako je fixture dodijeljen, inače `''` |
| `axisMode` | Parsira se iz imena setupa | `'3AX'`, `'4AX'`, `'5AX'` ili `''` |
| `hasProbeStrategy` | `op.operationType` contains `probe`/`inspect` | `True` ako ima probe operaciju |

### Operation polja

| Polje | Fusion param | Opis |
|---|---|---|
| `name` | `op.name` | Ime operacije |
| `operationType` | `strategy` param | Tip strategije (npr. `'face'`, `'contour2d'`) |
| `compensationType` | `compensationType` param | Tip kompenzacije (npr. `'wear'`, `'off'`) |
| `hasToolpath` | `op.hasToolpath` | Je li toolpath generiran |
| `cycleTimeSec` | N/A — nije dostupno | Uvijek `None` |
| `comment` | N/A — nije dostupno | Uvijek `''` |

### Tool polja (unutar operacije)

| Polje | Fusion param | Opis |
|---|---|---|
| `number` | `tool.number` / `tool_number` param | Broj alata |
| `description` | `tool.description` | Opis alata |
| `type` | `tool_type` param | Tip alata (npr. `'flat end mill'`, `'drill'`) |
| `preset` | N/A — nije dostupno | Uvijek `''` |
| `holderName` | `holder_description` param | Opis holdera |

---

## Pravila (`config/rules.json`)

Verzija: `1.0.0`, profil: `hp_cam_guide_v1_1`

Ukupno: **~98 pravila** (setup + operation)

### Tipovi statusa

| Status | Značenje |
|---|---|
| `pass` | Provjera prošla |
| `fail` | Provjera pala |
| `warning` | Prošla uvjetno (npr. pogrešna kapitalizacija) |
| `not_checked` | Nije evaluirano (uvjet nije zadovoljen ili polje nije dostupno) |

### Tipovi težine (severity)

| Severity | Značenje |
|---|---|
| `error` | Kritična greška, mora se ispraviti |
| `warning` | Preporuka, nije blokator |
| `info` | Informativno |

### Podržani tipovi pravila — Setup

| Tip | Opis |
|---|---|
| `skip_audit` | Cijeli setup se preskače (npr. `DON'T POST`) |
| `required` | Polje mora biti neprazno |
| `regex` | Case-sensitive match = pass; case-insensitive only = warning; no match = fail |
| `regex_optional` | Match = pass; no match = not_checked (nikad fail) |
| `conditional_allowed_values` | Vrijednost mora biti u listi, ali samo kad `when` uvjet vrijedi |
| `conditional_regex` | Regex provjera samo kad `when` uvjet vrijedi |

### Podržani tipovi pravila — Operation (Phase 4)

| Tip | Opis |
|---|---|
| `required` | Polje mora biti neprazno |
| `equals` | Vrijednost mora biti jednaka `expected` |
| `allowed_values` | Vrijednost mora biti u `allowed` listi |
| `conditional_required` | Obavezno samo kad `when` uvjet vrijedi |
| `conditional_regex` | Regex provjera samo kad `when` uvjet vrijedi |
| `conditional_not_regex` | Vrijednost NE smije matchirati pattern kad `when` vrijedi |
| `conditional_allowed_values` | Vrijednost mora biti u listi kad `when` vrijedi |
| `conditional_contains` | Vrijednost mora sadržavati substring kad `when` vrijedi |
| `conditional_not_contains` | Vrijednost NE smije sadržavati substring kad `when` vrijedi |
| `conditional_equals` | Vrijednost mora biti jednaka `expected` kad `when` vrijedi |

### Tipovi pravila — ostaju `not_checked` u Phase 4

| Tip | Razlog |
|---|---|
| `conditional_preferred` / `preferred` | Nije obavezno, samo preporuka |
| `conditional_target_numeric` | Nema numeričkih vrijednosti iz API-a |
| `conditional_min_numeric` | Isto |
| `conditional_not_strategy_group` | `strategyGroup` nije dostupan u Fusion API |
| `conditional_not_allowed` | `diameterIn` zahtijeva unit conversion |
| `sequence_predecessor_required` | Phase 5 (cross-operation analiza) |
| `conditional_preferred_order` | Samo preporuka |

### Mehanizmi iznimaka

**`skip_audit`** — pravilo tipa `skip_audit` s `when` uvjetom: ako setup ime odgovara, cijeli setup se preskače. Primjer: `DON'T POST` setup.

**`excludeWhen`** — polje na bilo kojem pravilu: ako uvjet vrijedi, provjera se vraća kao `not_checked`. Primjer: `AXIS_MODE_REQUIRED` se preskače za `SOFT JAW`/`SOFT JAWS` setupe.

**Quote normalizacija** — `DON'T POST` može imati ravni (`'`) ili kosi (`'` / `\u2019`) apostrof. Evaluator normalizira sve varijante.

### Primjeri setup pravila

| Kod | Tip | Provjava |
|---|---|---|
| `SETUP_NAME_FORMAT` | regex | Ime mora biti `Op[N] [3/4/5]AX`, `Dovetail Stock Prep`, `SOFT JAW(S)`, ili `DON'T POST` |
| `PROGRAM_NUMBER_FORMAT` | regex | Program broj mora biti format `O1XXX` |
| `PROGRAM_COMMENT_FORMAT` | regex | Komentar mora završavati s brojem dijela i OP oznakom |
| `WORK_OFFSET_VALID` | conditional_allowed_values | Offset mora biti G54–G59 |
| `MACHINE_MODEL_PRESENT` | required | Stroj mora biti odabran |
| `FIXTURE_TYPE_PRESENT` | required | Fixture mora biti dodijeljen |

### Primjeri operation pravila

| Kod | Tip | Provjava |
|---|---|---|
| `TOOL_REQUIRED` | required | Operacija mora imati alat |
| `TOOL_DESCRIPTION_REQUIRED` | required | Alat mora imati opis |
| `TOOL_TYPE_REQUIRED` | required | Tip alata mora biti definiran |
| `TOOLPATH_EXISTS` | equals | `hasToolpath` mora biti `true` |
| `COMPENSATION_REQUIRED` | required | Kompenzacija mora biti definirana |
| `STANDARD_TOOL_PREFIX_REQUIRED` | conditional_regex | Standardni alati moraju imati `.S` prefix |
| `ONE_OFF_TOOL_PREFIX_REMOVED` | conditional_not_regex | Modified alati NE smiju imati `.S` prefix |
| `FLAT_EM_FINISH_WALL_PRESET_FOR_CONTOUR` | conditional_allowed_values | Flat end mill na 2D Contour mora koristiti `FINISH WALL` preset |

---

## Struktura podatkovnih modela

```
AuditResult
├── status: 'ok' | 'error'
├── message: str
├── summary: { pass, fail, warning, not_checked }
└── setups: list[SetupRow]
      ├── name, programNumber, programComment, workOffset, machineModel
      ├── checks: list[FieldCheck]
      │     └── code, field, status, severity, message, guide_refs
      └── operations: list[OperationRow]
            ├── name, op_type
            ├── tool: ToolInfo | None
            │     └── number, description, preset_name, holder_name
            └── checks: list[FieldCheck]
```

---

## Arhitektura koda

```
FusionCamAudit/
├── FusionCamAudit.py           # Entry point; run() / stop()
├── FusionCamAudit.manifest     # Add-in metadata
├── commands/
│   ├── audit/
│   │   └── entry.py            # CAM Audit button + palette + audit orchestration
│   └── dump/
│       └── entry.py            # CAM Debug Dump button → DUMP_SETUP.txt
├── core/
│   ├── models.py               # Plain Python data classes (no dataclasses)
│   ├── rules_loader.py         # JSON rule loader s cache
│   ├── extractor.py            # Fusion API → plain dicts
│   ├── setup_auditor.py        # Evaluira setup-level pravila
│   └── operation_auditor.py    # Evaluira operation-level pravila
├── config/
│   └── rules.json              # ~98 determinističkih pravila (hp_cam_guide_v1_1)
├── palette/
│   └── audit_palette.html      # Dark-theme UI; adsk.fusionSendData komunikacija
└── docs/
    ├── ADDON_BEHAVIOR.md       # Ovaj dokument
    ├── PROJECT_BLUEPRINT.md
    ├── TASKLIST.md
    ├── RULES_INTEGRATION.md
    ├── FUSION_ADDON_TEMPLATE.md
    └── DEBUG_DUMP/
        └── DUMP_SETUP.txt      # Output CAM Debug Dump gumba
```

### Važne tehničke napomene

**Hot-reload**: core moduli se učitavaju svaki put iznova via `importlib.util.spec_from_file_location()` i brišu iz `sys.modules` — izmjene u Python kodu djeluju bez ponovnog pokretanja Fusiona.

**Palette hot-reload**: `palette.deleteMe()` u `start()` osigurava da se HTML uvijek učita svježe pri svakom reloadu add-ina.

**No dataclasses**: Fusion 360 embedded Python (`3.x`) ima problem s `dataclasses.field()` — svi modeli su klasični `__init__` klase.

**Putanje**: `os.path.join()` na Windowsu vraća backslashe; Fusion palette URL zahtijeva forward slasheve → `path.replace('\\', '/')`.

**Plain dicts iz ekstraktora**: Extractor vraća samo Python dictove — nema Fusion CAM API objekata koji bi mogli istjeći izvan event handlera.

---

## Razvojne faze

| Faza | Status | Opis |
|---|---|---|
| Phase 1 | ✅ Završeno | Add-in shell, gumb, paleta, mock UI |
| Phase 2 | ✅ Završeno | Modeli, rules loader, report schema |
| Phase 3 | ✅ Završeno | Setup audit (name, program, offset, machine, fixture) |
| Phase 4 | ✅ Završeno | Tool ekstrakcija, operation audit, debug dump gumb |
| Phase 5 | ⬜ Planirano | CAM strategija i struktura (chamfer-before-thread, sekvence) |
| Phase 6 | ⬜ Planirano | Export: `cam_audit_report.json` + `cam_audit_summary.md` |
