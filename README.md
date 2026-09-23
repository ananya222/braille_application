# Braille Validator workspace

## Run the demo

Open `dist/BrailleValidator/BrailleValidator.exe`.
The same folder contains `START_HERE.txt`, `DEMO_ERRORS.txt`, and separate
Math and Capitalization examples under `Demos`, with Word masters and clean/error
Braille PDFs. Keep this folder intact
when copying the app to another location.

## Folder guide

| Folder | Contents |
| --- | --- |
| `dist/BrailleValidator` | Current Windows app and ready-to-use demo files |
| `data/chapter1` | Stable developer/regression DOCX, BRF and DXB references |
| `data/chapter1/original` | Original English DOCX |
| `data/chapter1/earlier_versions` | Earlier reconstructed source |
| `data/chapter1/demo_evidence` | Corrupted BRF and recorded demo validation evidence |
| `data/test_documents` | Existing textbook/test-document collection |
| `data/mock_files` | Small generated sample documents |
| `src` | Production application source |
| `tests` | Automated checks |
| `experiments` | Experimental and historical comparison tools |
| `scripts` | Standalone utility scripts |
| `packaging` | Windows packaging support and acceptance utilities |
| `rules` | Authoritative standards PDFs |
| `vendor` | Required bundled translation dependencies |
| `output` | Generated source-mode validation PDFs/reports |
| `reports` | Implementation, audit and regression reports |
| `_archive` | Retained old builds, legacy distributions and historical scratch work |

Root entry points and build configuration remain here intentionally:
`main.py`, `main_gui.py`, `pyproject.toml`, `build_windows.bat`,
`BrailleValidator.spec`, and `ueb_corrections.yaml`.

## Notes

- Active fixture paths were updated to `data/`; production rule behavior was not changed.
- The developer reference DOCX is deliberately retained separately from the
  copy distributed with the app, so rebuilding the app does not delete test input.
- Historical reports and archived scripts retain their original paths as records
  of those runs. Archived scratch scripts are not active tools; restore/update
  their paths before rerunning them.
- Previous releases are retained under `_archive/legacy_distribution` and
  `_archive/cleanup_2026-09-11/old_builds`.
- No documents were discarded during this organization pass.
