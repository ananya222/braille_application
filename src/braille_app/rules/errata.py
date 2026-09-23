"""Nemeth 2025 errata overrides used by the rule engine.

The complete October 2025 errata PDF was read and its 46 table-of-change
entries are recorded below.  Only code-affecting entries are eligible for
runtime activation; editorial, example-only, print-only, and spatial-format
changes remain catalogue metadata until their scope is implemented.
"""

from __future__ import annotations

from dataclasses import dataclass

from .sources import NEMETH_ERRATA_2025


@dataclass(frozen=True)
class NemethErrataOverride:
    original_rule: str
    source: str
    pdf_page: int
    action: str
    runtime_status: str
    corrected_behavior: str
    original_rule_reference: str = ""


# The table is exhaustive for the 46 entries listed on PDF pages i-iii.
ERRATA_OVERRIDES: tuple[NemethErrataOverride, ...] = (
    NemethErrataOverride("3.3.1", NEMETH_ERRATA_2025, 5, "commentary", "CATALOGUED", "Correct Example 3-13 commentary."),
    NemethErrataOverride("3.3.1", NEMETH_ERRATA_2025, 5, "example", "CATALOGUED", "Correct capitalization in Example 3-16."),
    NemethErrataOverride("3.4.3", NEMETH_ERRATA_2025, 6, "print-example", "CATALOGUED", "Correct partitioned-number print example."),
    NemethErrataOverride("3.5.2", NEMETH_ERRATA_2025, 6, "heading", "CATALOGUED", "Correct enclosed-list heading."),
    NemethErrataOverride("3.6.2", NEMETH_ERRATA_2025, 7, "heading", "CATALOGUED", "Correct base-12 heading."),
    NemethErrataOverride("4.2", NEMETH_ERRATA_2025, 8, "replace", "ACTIVE", "No contractions inside switch indicators; opening switch is followed by a space and terminator is preceded by a space.", "Nemeth 4.2"),
    NemethErrataOverride("4.5.3", NEMETH_ERRATA_2025, 9, "example", "CATALOGUED", "Correct transcriber's-note example braille."),
    NemethErrataOverride("4.6.8.c", NEMETH_ERRATA_2025, 10, "replace", "CATALOGUED", "Single-word switch is unspaced from the affected word and terminates at a space.", "Nemeth 4.6.8.c"),
    NemethErrataOverride("4.8.2", NEMETH_ERRATA_2025, 11, "replace", "CATALOGUED", "Clarify placement of switch indicators and attached punctuation at runover."),
    NemethErrataOverride("6.4.2", NEMETH_ERRATA_2025, 12, "replace", "CATALOGUED", "No English-letter indicator after a function name or abbreviation."),
    NemethErrataOverride("7.2.1", NEMETH_ERRATA_2025, 13, "cross-reference", "CATALOGUED", "Add cross-reference for letters in hyphenated expressions."),
    NemethErrataOverride("7.3.3", NEMETH_ERRATA_2025, 14, "replace", "CATALOGUED", "Add hyphenated-expression heading and examples."),
    NemethErrataOverride("7.3.5", NEMETH_ERRATA_2025, 14, "example", "CATALOGUED", "Correct Example 7-19 braille."),
    NemethErrataOverride("8.2.4", NEMETH_ERRATA_2025, 15, "replace", "CATALOGUED", "Use punctuation indicator after long dash or ellipsis in mathematical context."),
    NemethErrataOverride("8.2.13", NEMETH_ERRATA_2025, 15, "heading", "CATALOGUED", "Correct Example 8-21 heading."),
    NemethErrataOverride("8.2.16", NEMETH_ERRATA_2025, 16, "commentary", "CATALOGUED", "Correct Example 8-26 heading and commentary."),
    NemethErrataOverride("8.8.2", NEMETH_ERRATA_2025, 16, "heading", "CATALOGUED", "Clarify Example 8-64 heading."),
    NemethErrataOverride("8.8.2", NEMETH_ERRATA_2025, 17, "commentary", "CATALOGUED", "Add Example 8-65 ellipsis commentary."),
    NemethErrataOverride("9.1", NEMETH_ERRATA_2025, 18, "replace", "CATALOGUED", "Restore recommended checkmark representation."),
    NemethErrataOverride("9.3.2", NEMETH_ERRATA_2025, 19, "example", "CATALOGUED", "Correct asterisk placement example."),
    NemethErrataOverride("10.1.1.a", NEMETH_ERRATA_2025, 20, "heading", "REMOVED", "Initialism heading correction removed from approved errata."),
    NemethErrataOverride("10.1.1.a", NEMETH_ERRATA_2025, 20, "heading", "REMOVED", "Initialism heading correction removed from approved errata."),
    NemethErrataOverride("10.6.1", NEMETH_ERRATA_2025, 21, "commentary", "CATALOGUED", "Correct the name of the right parenthesis."),
    NemethErrataOverride("10.6.3", NEMETH_ERRATA_2025, 21, "replace", "CATALOGUED", "Degrees C/F unspaced from degree symbol do not require English-letter indicator."),
    NemethErrataOverride("11.1.4", NEMETH_ERRATA_2025, 22, "replace", "CATALOGUED", "Omission symbols follow the spacing and mathematical punctuation rules of the material replaced."),
    NemethErrataOverride("15.2.1", NEMETH_ERRATA_2025, 23, "example", "CATALOGUED", "Correct modified-expression example and include switches."),
    NemethErrataOverride("15.7", NEMETH_ERRATA_2025, 23, "print-example", "CATALOGUED", "Correct tilde over subscripted x in print."),
    NemethErrataOverride("15.7", NEMETH_ERRATA_2025, 24, "print-example", "CATALOGUED", "Correct tildes over subscripted x and y in print."),
    NemethErrataOverride("17.1.c", NEMETH_ERRATA_2025, 25, "replace", "CATALOGUED", "Standard bullets are not shapes and may be used in either context."),
    NemethErrataOverride("20.6", NEMETH_ERRATA_2025, 26, "heading", "CATALOGUED", "Correct minus-and-plus heading."),
    NemethErrataOverride("23.symbol-list", NEMETH_ERRATA_2025, 27, "add", "CATALOGUED", "Add crossed d to miscellaneous symbols."),
    NemethErrataOverride("23.4", NEMETH_ERRATA_2025, 27, "replace", "CATALOGUED", "Add crossed-d wording and example."),
    NemethErrataOverride("23.13", NEMETH_ERRATA_2025, 28, "replace", "CATALOGUED", "Add spatial-arrangement monetary-unit exception."),
    NemethErrataOverride("23.17", NEMETH_ERRATA_2025, 28, "example", "CATALOGUED", "Correct barred-letter English-letter indicator."),
    NemethErrataOverride("24.1.e", NEMETH_ERRATA_2025, 29, "delete", "ACTIVE", "Delete the superseded multipurpose-indicator subsection and examples."),
    NemethErrataOverride("25.3.3", NEMETH_ERRATA_2025, 30, "replace", "OUT_OF_SCOPE", "Clarify spatial monetary-symbol placement."),
    NemethErrataOverride("25.3.4", NEMETH_ERRATA_2025, 31, "print-example", "OUT_OF_SCOPE", "Correct spatial subtraction print example."),
    NemethErrataOverride("25.8.2.b", NEMETH_ERRATA_2025, 31, "cross-reference", "OUT_OF_SCOPE", "Correct spatial runover cross-reference."),
    NemethErrataOverride("25.8.2.c", NEMETH_ERRATA_2025, 32, "cross-reference", "OUT_OF_SCOPE", "Correct spatial runover cross-reference."),
    NemethErrataOverride("25.10", NEMETH_ERRATA_2025, 32, "print-example", "OUT_OF_SCOPE", "Correct aligned-system print example."),
    NemethErrataOverride("26.1.4.b", NEMETH_ERRATA_2025, 33, "example", "OUT_OF_SCOPE", "Correct spatial placement and grouping example."),
    NemethErrataOverride("26.3.5", NEMETH_ERRATA_2025, 34, "commentary", "OUT_OF_SCOPE", "Correct degree-abbreviation commentary."),
    NemethErrataOverride("26.5.3.b", NEMETH_ERRATA_2025, 35, "print-example", "OUT_OF_SCOPE", "Correct nested-links print example."),
    NemethErrataOverride("Appendix B", NEMETH_ERRATA_2025, 36, "replace", "CATALOGUED", "Clarify opening-switch placement exceptions."),
    NemethErrataOverride("Appendix D D-27", NEMETH_ERRATA_2025, 37, "add", "CATALOGUED", "Add crossed-d to the symbol index."),
    NemethErrataOverride("Appendix D D-32", NEMETH_ERRATA_2025, 37, "delete", "CATALOGUED", "Delete the opening Nemeth indicator from the index entry."),
)


ACTIVE_RUNTIME_OVERRIDES = {
    entry.original_rule: entry
    for entry in ERRATA_OVERRIDES
    if entry.runtime_status == "ACTIVE"
}
