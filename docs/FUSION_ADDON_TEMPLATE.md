# Fusion 360 Addon Template

> Univerzalni vodič za izradu bilo kojeg Fusion 360 addona bez ponavljanja istih grešaka.

---

## 1. Osnovni životni ciklus addona

Svaki Fusion 360 addon prati isti obrazac:

1. `run(context)`
2. registracija komande
3. dodavanje gumba u UI
4. `CommandCreatedHandler`
5. izrada dijaloga i inputa
6. `InputChangedHandler`
7. `ExecuteHandler`
8. `stop(context)`

Minimalna struktura:

```python
import adsk.core
import traceback

handlers = []


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            on_execute = ExecuteHandler()
            cmd.execute.add(on_execute)
            handlers.append(on_execute)

            on_input_changed = InputChangedHandler()
            cmd.inputChanged.add(on_input_changed)
            handlers.append(on_input_changed)

            inputs.addTextBoxCommandInput(
                'info',
                'Info',
                'Minimalni template addona.',
                2,
                True
            )
        except Exception:
            adsk.core.Application.get().userInterface.messageBox(traceback.format_exc())


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    _updating = False

    def notify(self, args):
        if InputChangedHandler._updating:
            return

        InputChangedHandler._updating = True
        try:
            pass
        except Exception:
            adsk.core.Application.get().userInterface.messageBox(traceback.format_exc())
        finally:
            InputChangedHandler._updating = False


class ExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            ui = adsk.core.Application.get().userInterface
            ui.messageBox('Addon radi.')
        except Exception:
            adsk.core.Application.get().userInterface.messageBox(traceback.format_exc())


def run(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        cmd_def = ui.commandDefinitions.itemById('MY_ADDON_CMD')
        if not cmd_def:
            cmd_def = ui.commandDefinitions.addButtonDefinition(
                'MY_ADDON_CMD',
                'My Addon',
                'Opis addona'
            )

        on_created = CommandCreatedHandler()
        cmd_def.commandCreated.add(on_created)
        handlers.append(on_created)

        ws = ui.workspaces.itemById('CAMEnvironment')
        panel = ws.toolbarPanels.itemById('CAMManagePanel')

        ctrl = panel.controls.itemById('MY_ADDON_CMD')
        if not ctrl:
            panel.controls.addCommand(cmd_def)
    except Exception:
        adsk.core.Application.get().userInterface.messageBox(traceback.format_exc())


def stop(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        ws = ui.workspaces.itemById('CAMEnvironment')
        panel = ws.toolbarPanels.itemById('CAMManagePanel')

        ctrl = panel.controls.itemById('MY_ADDON_CMD')
        if ctrl:
            ctrl.deleteMe()

        cmd_def = ui.commandDefinitions.itemById('MY_ADDON_CMD')
        if cmd_def:
            cmd_def.deleteMe()
    except Exception:
        adsk.core.Application.get().userInterface.messageBox(traceback.format_exc())
```

---

## 2. Redoslijed izrade novog addona

Kod svakog novog addona idi ovim redom:

1. Napravi `run()` i `stop()`.
2. Registriraj gumb u točan workspace i panel.
3. Potvrdi da se gumb vidi.
4. Dodaj `CommandCreatedHandler`.
5. Otvori prazan dijalog.
6. Dodaj jedan testni input.
7. Dodaj `ExecuteHandler`.
8. Potvrdi da klik na OK radi.
9. Tek onda dodaj poslovnu logiku.

Pravilo:
Prvo stabilan addon skeleton (kostur), tek onda CAM/Fusion logika.

---

## 3. Greške koje se stalno ponavljaju

### 1. Handleri nisu spremljeni globalno

Ako handler nije u globalnom `handlers` popisu, Fusion ga može otpustiti i event više ne radi.

```python
handlers.append(on_created)
handlers.append(on_execute)
handlers.append(on_input_changed)
```

### 2. Krivi panel ili workspace ID

Ne koristiti izmišljene nazive. Uvijek koristiti stvarne Fusion ID-jeve.

Česti primjeri:

```python
'CAMEnvironment'
'CAMManagePanel'
'CAMScriptsAddinsPanel'
'SolidScriptsAddinsPanel'
```

### 3. Nema `try/except` u `notify()`

Fusion često proguta exception bez korisne poruke. Svaki `notify()` mora biti omotan.

### 4. UI se mijenja bez reentrant guarda

Ako unutar `inputChanged` promijeniš drugi input, možeš izazvati beskonačnu rekurziju i crash.

Uvijek koristiti guard:

```python
if _updating:
    return
```

### 5. Mijenjanje inputa prerano

U `CommandCreated` ne raditi kompleksne dinamičke promjene nad UI-jem ako nisu nužne.
Najsigurnije je:
- kreirati inpute
- ostaviti default stanje
- dinamičke promjene raditi kasnije kroz `inputChanged`

### 6. Brisanje dropdown stavki od početka

Sigurno brisanje:

```python
for i in range(dd.listItems.count - 1, -1, -1):
    dd.listItems.item(i).deleteMe()
```

### 8. Palette HTML path s backslashevima

Na Windowsu `os.path.join()` vraća path s backslashevima (`\`).
Fusion 360 palette sustav očekuje forward slashes — inače dobijamo `ERR_INVALID_URL`.

Uvijek normalizirati path:

```python
def _palette_html_path() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, 'palette', 'my_palette.html')
    return path.replace('\\', '/')
```

### 8b. Dijeljeni palette UI asseti

Ako addon ima i stvarni Fusion palette i lokalni browser preview, nemoj duplicirati CSS i JavaScript.

Praktičan obrazac iz ovog projekta:

- glavni HTML entrypoint ostaje u `palette/audit_palette.html`
- zajednički UI asseti žive uz njega:
  - `palette/audit_ui.css`
  - `palette/audit_ui.js`
- preview wrapper u `docs/preview.html` referencira iste assete preko relativnih putanja

Time dobivaš:

- jedan izvor istine za stil i interakcije
- isti izgled u Fusionu i u VS Code/browser previewu
- manje regressija kad se mijenja UI

Preporuka:

- HTML entrypointi neka budu tanki
- shared render/filter/action logika neka bude u jednom JS fajlu
- mock podaci za preview neka ostanu u `docs/preview.html` ili zasebnom preview data fajlu, ne u Fusion runtime HTML-u

---

### 10. Kako otkriti stvarni native command ID

Ako znaš da neka Fusion UI akcija postoji ručno, ali ne znaš njen command ID, nemoj pogađati stringove naslijepo.

Pouzdaniji postupak:

1. napravi debug komandu koja sluša `commandStarting` i `commandCreated`
2. uključi trace na kratko vrijeme
3. ručno klikni traženu akciju u Fusion UI-ju
4. zapiši:
   - `args.commandDefinition.id`
   - `args.commandDefinition.name`
   - trenutnu selekciju
5. tek nakon toga zovi taj command iz addona

Primjer iz ovog projekta:

- ručnim klikom na `Edit` nad CAM operacijom trace je otkrio runtime command ID `IronEditOperation`
- tek nakon toga je `OPEN` implementiran preko:

```python
cmd = ui.commandDefinitions.itemById(‘IronEditOperation’)
if cmd:
    cmd.execute()
```

Pouka:

- `commandDefinitions` dump nije uvijek dovoljan
- neki commandovi se lakše otkriju tek kroz runtime event trace
- za CAM/Manufacture UI ovo je često bolji pristup od nagađanja `executeTextCommand(...)` stringova

---

### 11. Detekcija UI teme (light/dark)

`app.preferences.userInterfaceTheme` ne postoji — pravi put je `ui.generalPreferences.userInterfaceTheme`.

Vrijednosti: `1` = light, `2` = dark. Fusion vraća enum objekt — treba ga castati na `int` (ili dohvatiti `.value` ako `int()` ne radi direktno).

```python
def _get_ui_theme_payload():
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        gp = getattr(ui, 'generalPreferences', None)
        if gp is None:
            prefs = getattr(app, 'preferences', None)
            gp = getattr(prefs, 'generalPreferences', None) if prefs else None
        raw = getattr(gp, 'userInterfaceTheme', None) if gp else None
        if hasattr(raw, 'value'):
            raw = raw.value
        n = int(raw) if raw is not None else 1
        return {'themeRaw': n, 'isDark': n == 2}
    except Exception:
        return {'themeRaw': 1, 'isDark': False}
```

Na JS strani payload prima `themeRaw` (int) i `isDark` (bool):

```javascript
function applyTheme(themeRaw, isDark) {
    var resolved = (typeof isDark === 'boolean') ? (isDark ? 'dark' : 'light')
                   : (themeRaw === 1 ? 'light' : 'dark');
    document.body.setAttribute('data-theme', resolved);
}

// u renderResult():
applyTheme(result.themeRaw, result.isDark);
```

---

### 9. `dataclasses` modul ne radi u Fusion 360 embedded Pythonu

Fusion 360 koristi embedded Python okruženje gdje `dataclasses.field()` baca `TypeError: 'str' object is not callable`.

Ne koristiti `@dataclass` ni `field()`. Koristiti plain Python klase s `__init__`:

```python
# NE RADITI:
from dataclasses import dataclass, field

@dataclass
class MyModel:
    items: list = field(default_factory=list)

# RADITI:
class MyModel:
    def __init__(self, items=None):
        self.items = items if items is not None else []
```

---

### 7. Poslovna logika se dodaje prerano

Nemoj odmah spajati CAM operacije, alate, presete i UI sinkronizaciju u prvom prolazu.
Prvo testiraj da addon lifecycle radi stabilno.

---

## 4. Preporučeni razvojni checklist

Prije nego kažeš da je addon spreman, potvrdi:

- gumb se pojavljuje u pravom panelu
- klik na gumb otvara dijalog
- `OK` pokreće `execute`
- `stop()` briše UI elemente
- svi handleri su spremljeni u `handlers`
- svaki `notify()` ima `try/except`
- `inputChanged` ima reentrant guard
- dropdown/list UI se briše sigurno od kraja
- poslovna logika je dodana tek nakon stabilnog skeletona

---

## 5. Pravilo za svaki novi projekt

Ako krećeš novi addon, prvo kopiraj minimalni template i provjeri samo ove tri stvari:

1. gumb postoji
2. dijalog se otvara
3. `execute` radi

Ako te tri stvari nisu stabilne, nemoj još dodavati ostatak funkcionalnosti.

To je najjednostavniji način da se ne ponavljaju iste početne greške iz projekta u projekt.
