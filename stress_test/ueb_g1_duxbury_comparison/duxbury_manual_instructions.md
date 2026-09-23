# Duxbury capture instructions

The installed executable is:

`C:\Program Files (x86)\Duxbury\DBT 14.1\dbtw.exe`

Version detected: `14.1.0.7124`.

1. Open `ueb_g1_5page_stress.docx`.
2. Set the document language to English and the braille code to Unified English Braille.
3. Set the document to uncontracted / Grade 1. Contractions must be disabled.
4. Do not enable Nemeth, mathematics, chemistry, or any specialist code.
5. Leave quote/apostrophe preferences at their explicit UEB defaults, and record the actual preference names and values shown by DBT.
6. Preserve source page breaks and meaningful spaces. Do not normalize NBSP, thin space, zero-width space, or repeated ordinary spaces before export.
7. Export the result as raw BRF or plain text without manual corrections. Save it as `duxbury_output.brf` or `duxbury_output.txt` in this directory.
8. Save a settings note containing the template name, language, UEB code, Grade 1/uncontracted choice, quote/apostrophe settings, and export options.

Do not hand-edit the exported cells. After the real output is present, rerun the audit comparison and adjudication steps. Until then, all comparison CSVs are intentionally empty.
