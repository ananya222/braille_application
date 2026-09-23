# Windows packaging acceptance - 2026-09-11

Status: **WINDOWS BUILD CREATED — RUNTIME ISSUE REMAINS**

The remaining acceptance issue is external PDF viewing, not validation or PDF
generation. The packaged GUI's Open Annotated PDF action launched the associated
Firefox instance, whose title became "Problem loading page". Further viewer
inspection could not proceed because Computer Use app approval timed out.
The exact exported PDF independently parses and renders correctly. No browser
settings, file associations or security settings were changed.

## Build

- EXE: `O:\braille_0.2\dist\BrailleValidator\BrailleValidator.exe`
- Mode: PyInstaller onedir; Windows GUI subsystem 2; no console.
- Architecture: AMD64/x64 (`0x8664`).
- Build Python: 3.12.4 x64.
- PyInstaller: 6.21.0; hooks 2026.6.
- Tested OS: Windows 11, build 26200.
- 430 files, 200,735,826 bytes; move/copy the entire folder, not only the EXE.
- EXE SHA256: `f04fcee1990062f5ecabac9b166e83b7b88d172195206e5ebec71fda208ac390`.
- Every file in the external copied release folder matches the dist copy by SHA256.
- No clean VM or second Windows version was tested; Python remains installed on
  the test host, although the running app uses its bundled interpreter/runtime.

External tested release:
`C:\Users\minec\AppData\Local\Temp\BrailleValidatorPackaging-20260911\BrailleValidator\BrailleValidator.exe`

The diagnostic build also completed clean validation and PDF/report export from
the separate `DebugRebuilt` folder before the final GUI build was produced.

## Dependencies and inventory

Actual entry point: `main_gui.py`, existing PySide6 QtCore/QtGui/QtWidgets GUI and
QThread validation worker. Qt 6.11.1, platform plugins and transitive QtNetwork
support are collected by PyInstaller. No existing application icon was found.
The current GUI uses a system PDF viewer, not an embedded viewer.

Liblouis 3.38.0: vendored Python binding compiled into the archive, native x64
DLL beside its frozen `louis` package, and the recursive table include closure.
The production `braille_app/translation/nemeth_probe.ctb` is included unchanged.
Bundled vendor files:

```
braille-patterns.cti
en-chardefs.cti
en-ueb-chardefs.uti
en-ueb-g1.ctb
en-ueb-g2.ctb
en-ueb-math.ctb
latinLetterDef6Dots.uti
latinUppercaseComp6.uti
loweredDigits6Dots.uti
nemethdefs.cti
spaces.uti
text_nabcc.dis
unicode.dis
```

PDF/document stack: pypdf 6.14.2, pdfplumber 0.11.10, python-docx 1.2.0,
lxml/pdfminer plus their collected Pillow/pypdfium2/numpy dependencies.
Rule metadata is compiled Python, not runtime standards PDFs. No legacy YAML
correction loader is used by this flow. No external translator executable or
Poppler installation is required by the app. Poppler was used only for QA.
Development fixtures, reports, experiments, standards PDFs, Git data and loose
source caches are not bundled.

## Packaging changes only

| File | Purpose |
|---|---|
| `BrailleValidator.spec` | Explicit onedir dependency collection, table include closure, console/release mode, controlled native DLL search PATH |
| `build_windows.bat` | Reproducible Python 3.12 x64 build, scoped PyInstaller cleanup, fail-fast |
| `packaging/requirements-build.txt` | Pinned principal build dependencies |
| `packaging/frozen_runtime.py` | Frozen log/table paths and optional real-translation/isolation diagnostics |
| `src/braille_app/runtime_paths.py` | Shared source/frozen resource and writable output paths |
| `src/braille_app/translation/liblouis_translator.py` | Resource-root lookup and frozen binding import paths only |
| `main_gui.py` | Writable output helper in export/folder action, frozen statistics logging only |
| `packaging/prepare_smoke_inputs.py` | External-only test input preparation using existing fixture helper |
| `packaging/verify_smoke_outputs.py` | Read-only binary/JSON/PDF acceptance checks; not bundled |
| `packaging/README.md` | Build/run instructions and known limitations |
| `reports/windows_packaging_status.md` | This acceptance record |

Existing unrelated dirty/untracked files were preserved. No standards rules,
translation decisions, alignment, highlighting, REVIEW thresholds or GUI result
semantics were changed. Main GUI output remains confirmed-error-only; coverage
counts remain available in the generated diagnostic reports.

Frozen reports go to `%LOCALAPPDATA%\BrailleValidator\output`; the log goes to
`%LOCALAPPDATA%\BrailleValidator\runtime.log`. Source-mode output remains the
project `output` directory. Generated data is not written into `_internal`.

The initial diagnostic build failed because a foreign Poppler `icuuc.dll` was
collected from the development PATH and lacked Qt's required unversioned ICU
exports. Changing VC runtime DLLs in a disposable test copy did not solve it.
The reproducible fix was to constrain DLL discovery in the spec. The fresh
diagnostic and final copies work without manual DLL replacement/removal.

## Actual copied EXE acceptance

| Test | Result | Evidence |
|---|---|---|
| Startup | PASS | Final GUI rendered, no console or import/DLL error |
| File selectors and Validate | PASS | External DOCX and clean/corrupt PDF selected through native GUI |
| Clean Chapter 1 | PASS | 771 raw differences, ERROR 0, REVIEW 182, exclusions 4 |
| Controlled corruption | PASS | 772 raw differences, ERROR 1, REVIEW 182, exclusions 4 |
| Liblouis runtime | PASS | Actual packaged DLL version/path and successful production translation logged |
| PDF highlighting | PASS | Clean: zero blue boxes. Corrupt: one exact solid blue cell box on page 1 |
| JSON/report generation | PASS | Normal and diagnostic exports physically exist and parse |
| Isolated location | PASS | External EXE and inputs; source-open/list audit guard enabled; all runtime resources point into bundle |
| System PDF viewer | NOT PASSED | Firefox opened with "Problem loading page"; inspection approval timed out |
| Open Output Folder | NOT TESTED | Existing action preserved; not claimed as verified |

Real frozen translation:
`Hello world!` -> `⠠⠓⠑⠇⠇⠕⠀⠸⠺⠖`.
Loaded DLL:
`C:\Users\minec\AppData\Local\Temp\BrailleValidatorPackaging-20260911\BrailleValidator\_internal\louis\liblouis.dll`.

Isolation used empty PYTHONPATH, external working directory and
`BRAILLE_PACKAGING_DENY_ROOT=O:\braille_0.2`. The guard intercepts Python-level
opens/listing, not all native OS file access; it is not a filesystem sandbox.
The original source directory was not deleted, renamed or made inaccessible.

## Regression evidence

The final frozen GUI clean PDF run reproduced the baseline raw/review/error
counts. The existing source regression suite was separately rerun with the same
build interpreter; these supplemental tests are not misrepresented as frozen
GUI runs:

| Metric | Result |
|---|---:|
| Raw discrepancies | 771 |
| REVIEW | 182 |
| Confirmed errors (frozen GUI) | 0 |
| Switching in/out | 358 / 358 |
| Missing inner spaces | 0 |
| Unaligned pages | 0 |
| Baseline corruption suite | 5/5 detected |
| Boundary verifier | 5/5 test groups |
| Boundary corruptions | 8/8 detected |
| Prose-context generator tests | 7/7 |

`pytest` is not installed in the build interpreter. The existing executable
test-file entry points were used successfully instead. The full known-failing
test suite was not rerun or changed. The documented 10 pre-existing failures
and `10:30-?` gap remain open.

## PDF evidence

Both fixtures retain 17 pages and exactly the same extracted text in their
annotated copies. Both map 25,811 validator cells to 25,811 PDF provenance cells,
with unmatched cells 0 and unexplained offsets 0. External copies of the source
DOCX/BRF match the project originals by SHA256.

These smoke PDFs are ASCII/Courier coordinate fixtures from the existing
BRF-to-PDF helper, not newly reconstructed chapter text or actual Duxbury PDF
exports. Their layouts are test fixtures, not publication-ready Braille pages.

Corruption: `,*APT` -> `,*BPT`; `UEB_ERROR`, `UEB_RULE_001`, source/PDF page 1;
actual half-open cell range `[2,3)`; expected `⠁`, actual `⠃`.
Overlay in PDF coordinates: x=60.000, y=758.060, width=6.000, height=10.000;
solid blue (`0.12 0.48 1.0 RG`), line width 1.5. Visually verified on a rendered
first page. Clean normal PDF has no blue overlays anywhere.

Exports:

```
C:\Users\minec\AppData\Local\BrailleValidator\output\clean_validator_annotated.pdf
C:\Users\minec\AppData\Local\BrailleValidator\output\clean_validator_report.json
C:\Users\minec\AppData\Local\BrailleValidator\output\corrupted_validator_annotated.pdf
C:\Users\minec\AppData\Local\BrailleValidator\output\corrupted_validator_report.json
```

Corresponding `_validator_diagnostic.pdf` and `_validator_diagnostic_report.json`
files were generated automatically too. No further backend changes are needed
or authorized for resolving the outstanding external-viewer acceptance item.
