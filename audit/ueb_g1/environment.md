# Liblouis / UEB Grade 1 audit environment

Audit date: 2026-09-21
Python executable: `C:\Users\minec\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
Python version: `3.12.14`
Liblouis runtime version: `3.38.0`
Python binding package version: `3.38.0` (vendor/liblouis-bindings/pyproject.toml)
Loaded DLL: `O:\braille_0.2\vendor\liblouis-win64\bin\liblouis.dll`
Loaded DLL SHA-256: `0763ab5eb8b6ce2e2e0cc44573af07c753277e0dee0a142b859d52a012f1bfd6`
Production table path: `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables`
Production table list: `unicode.dis,en-ueb-g1.ctb` (matches `src/braille_app/translation/liblouis_translator.py`)
Project en-ueb-g1.ctb: `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\en-ueb-g1.ctb`
Project en-ueb-g1.ctb SHA-256: `446717b55e49ff41aef2c204b58ea1d2872a77a4473a821e766bffd51cee0b4d`
System en-ueb-g1.ctb: `C:\liblouis\share\liblouis\tables\en-ueb-g1.ctb`
System en-ueb-g1.ctb SHA-256: `1f77969efa61620b5af30eda2930068f8a239e18601b235505527601cc3d03ed`
Project and system table bytes identical: `False`

## Resolved table/include closure

The closure below follows the same two-table list used by the application (`unicode.dis,en-ueb-g1.ctb`).

| File | SHA-256 | Size |
|---|---|---:|
| `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\braille-patterns.cti` | `4fb5580c3dd8fb6629b1c2330cc95e8a5a603062604db1715f84ea77b99b493d` | 26718 |
| `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\en-ueb-chardefs.uti` | `d17f2c18e672bb5d3ad1045db0602cb6fe86b771ed5a3a951fa529da6f393258` | 28776 |
| `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\en-ueb-g1.ctb` | `446717b55e49ff41aef2c204b58ea1d2872a77a4473a821e766bffd51cee0b4d` | 5535 |
| `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\en-ueb-math.ctb` | `b9192d3b16633011194ac8b38760ae073414b41603182a95fc6250efb6214212` | 2116 |
| `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\latinLetterDef6Dots.uti` | `323fe46ee894216871675675823dd0681389669325d99b3b149ca0ea6550d842` | 2071 |
| `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\latinUppercaseComp6.uti` | `83e630db6763e96d2d4e6106632906a659f8748bd41111a23d79125c93802249` | 1946 |
| `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\spaces.uti` | `ea10c41e08e9f44b2b471b80a7f291f62d249f0bbb70b64f319e20e95388e2b9` | 2170 |
| `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\text_nabcc.dis` | `b9db7173799dcacdc88edfde46efeb5090690bad4e1f432ca023acd18ae35f47` | 22076 |
| `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\unicode.dis` | `28e39797dae5404cf3c0bdea3100f6da70eac8bdbd38a186d463462f4ace567c` | 6252 |

## Version/path conclusion

The application resolves the vendored Liblouis 3.38.0 DLL and vendored tables, not `C:\liblouis`. The system installation is also reported as Liblouis 3.38.0 by `C:\liblouis\bin\lou_translate.exe --version`, but its `en-ueb-g1.ctb` hash differs, so the two installations must not be treated as interchangeable.

The source checkout is `vendor/liblouis-src/liblouis-3.38.0`; the installed table header has no UEB-2024 authority citation and contains a TODO referring to braille-spec documentation. ICEB 2024 remains the correctness authority for this audit.
