"""Named translation profiles for the expected-Braille generator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TranslationProfile:
    name: str
    literary_table: str
    math_table: str
    switch_start: str
    switch_end: str
    switch_start_ascii: str
    switch_end_ascii: str
    phase1_scope: bool = False
    case1_scope: bool = False
    case2_scope: bool = False
    case3_scope: bool = False
    case4_scope: bool = False


CONTRACTED_UEB_BANA_NEMETH = TranslationProfile(
    name="contracted_ueb_bana_nemeth",
    literary_table="en-ueb-g2.ctb",
    math_table="nemeth_probe.ctb",
    switch_start="⠸⠩",
    switch_end="⠸⠱",
    switch_start_ascii="_%",
    switch_end_ascii="_:",
)


UNCONTRACTED_UEB_PHASE1 = TranslationProfile(
    name="uncontracted_phase1",
    literary_table="en-ueb-g1.ctb",
    math_table="",
    switch_start="",
    switch_end="",
    switch_start_ascii="",
    switch_end_ascii="",
    phase1_scope=True,
)


UNCONTRACTED_UEB_CASE1 = TranslationProfile(
    name="uncontracted_case1_alphabet_words",
    literary_table="en-ueb-g1.ctb",
    math_table="",
    switch_start="",
    switch_end="",
    switch_start_ascii="",
    switch_end_ascii="",
    case1_scope=True,
)


UNCONTRACTED_UEB_CASE2 = TranslationProfile(
    name="uncontracted_case2_capitalization",
    literary_table="en-ueb-g1.ctb",
    math_table="",
    switch_start="",
    switch_end="",
    switch_start_ascii="",
    switch_end_ascii="",
    case2_scope=True,
)


UNCONTRACTED_UEB_CASE3 = TranslationProfile(
    name="uncontracted_case3_numbers",
    literary_table="en-ueb-g1.ctb",
    math_table="",
    switch_start="",
    switch_end="",
    switch_start_ascii="",
    switch_end_ascii="",
    case3_scope=True,
)


UNCONTRACTED_UEB_CASE4 = TranslationProfile(
    name="uncontracted_case4_punctuation",
    literary_table="en-ueb-g1.ctb",
    math_table="",
    switch_start="",
    switch_end="",
    switch_start_ascii="",
    switch_end_ascii="",
    case4_scope=True,
)


PROFILES = {
    CONTRACTED_UEB_BANA_NEMETH.name: CONTRACTED_UEB_BANA_NEMETH,
    UNCONTRACTED_UEB_PHASE1.name: UNCONTRACTED_UEB_PHASE1,
    UNCONTRACTED_UEB_CASE1.name: UNCONTRACTED_UEB_CASE1,
    UNCONTRACTED_UEB_CASE2.name: UNCONTRACTED_UEB_CASE2,
    UNCONTRACTED_UEB_CASE3.name: UNCONTRACTED_UEB_CASE3,
    UNCONTRACTED_UEB_CASE4.name: UNCONTRACTED_UEB_CASE4,
    "uncontracted": UNCONTRACTED_UEB_PHASE1,
    "uncontracted_ueb": UNCONTRACTED_UEB_PHASE1,
    "uncontracted_ueb_phase1": UNCONTRACTED_UEB_PHASE1,
    "grade_1": UNCONTRACTED_UEB_PHASE1,
    "g1": UNCONTRACTED_UEB_PHASE1,
    "uncontracted_case1": UNCONTRACTED_UEB_CASE1,
    "uncontracted_case2": UNCONTRACTED_UEB_CASE2,
    "uncontracted_case3": UNCONTRACTED_UEB_CASE3,
    "uncontracted_case4": UNCONTRACTED_UEB_CASE4,
}


def get_profile(profile: str | TranslationProfile) -> TranslationProfile:
    if isinstance(profile, TranslationProfile):
        return profile
    try:
        return PROFILES[profile]
    except KeyError as exc:
        raise ValueError(f"Unknown translation profile: {profile}") from exc
