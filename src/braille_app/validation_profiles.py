"""Explicit validation profiles for literary and mixed technical modes.

The profile is deliberately small in Phase 1.  It selects the Liblouis table
and the rule policy; it does not infer a mode from the uploaded files.
"""

from __future__ import annotations

from dataclasses import dataclass


UNCONTRACTED = "uncontracted"
UNCONTRACTED_PHASE1 = "uncontracted_phase1"
UNCONTRACTED_CASE1 = "uncontracted_case1_alphabet_words"
UNCONTRACTED_CASE2 = "uncontracted_case2_capitalization"
UNCONTRACTED_CASE3 = "uncontracted_case3_numbers"
UNCONTRACTED_CASE4 = "uncontracted_case4_punctuation"
CONTRACTED = "contracted"
CONTRACTED_DOCUMENT = "contracted_document"
CONTRACTED_POETRY = "contracted_poetry"
CONTRACTED_TABLE = "contracted_table"
MATH = "math"


def uses_contracted_pdf_normalization(profile: str | "ValidationProfile" | None) -> bool:
    """Return whether a PDF uses the contracted/Duxbury glyph alphabet."""
    if isinstance(profile, ValidationProfile):
        return profile.contracted_pdf_normalization
    normalized = str(profile or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in {"", "legacy"}:
        return False
    try:
        return resolve_profile(normalized).contracted_pdf_normalization
    except ValueError:
        return False


@dataclass(frozen=True)
class ValidationProfile:
    name: str
    label: str
    grade: int
    table: str
    mode: int = 0
    typeform: str = "none"
    enabled_rules: frozenset[str] = frozenset()
    structured_docx_tables: bool = False
    technical_math_table: str | None = None
    mixed_math: bool = False
    # Capabilities are deliberately explicit so callers do not infer routing
    # from a display label or from a profile-name string.
    profile_kind: str = "uncontracted"
    contracted_pdf_normalization: bool = False
    contracted_provenance: bool = False
    contracted_document_provenance: bool = False
    # Minimum stable word-run length eligible for one-to-one document
    # provenance mapping.  It is a presentation-localization capability,
    # not a semantic comparison rule.
    document_stable_anchor_min_words: int | None = None
    # Maximum retained fraction for a sparse, locally-supported multi-line
    # table-cell review span in the Document profile.  Other profiles keep
    # the established conservative threshold.
    document_table_trim_max_ratio: float | None = None

    def allows_rule(self, rule_id: str) -> bool:
        return rule_id in self.enabled_rules


# These are the only rules treated as safe to share in Phase 1.  All existing
# source-conditioned equivalences remain uncontracted-only until independently
# proven for contracted client DXB output.
SHARED_SAFE_RULES = frozenset({"braces_terminator_placement"})
UNCONTRACTED_ONLY_RULES = frozenset({
    "source_capitalization_equivalence",
    "source_comma_equivalence",
    "source_text_hyphen_equivalence",
    "source_hyphen_minus_equivalence",
    "source_equals_equivalence",
    "source_numeric_parenthesis_equivalence",
    "source_word_final_period_equivalence",
    "source_word_final_colon_equivalence",
    "source_numeric_one_period_equivalence",
    "source_tilde_equivalence",
    "source_percent_parenthesis_period_equivalence",
})
CONTRACTED_UNVERIFIED_RULES = frozenset({
    "equals_sign_spacing",
    "single_quote_directional",
    "double_quote_mismatch",
    "rupee_sign_gap",
    "tilde_symbol_gap",
    "multiplication_dot_check",
    "plus_dot_check",
    "parentheses_dot_check",
    "brackets_dot_check",
    "contracted_source_en_dash_profile_difference",
    "contracted_source_en_dash_profile_equivalence",
    "contracted_source_placeholder_profile_difference",
})
MATH_CORRECTED_DXB_RULES = frozenset({
    "math_nested_delimiter_representation",
})

RULE_CLASSIFICATIONS = {
    **{rule: "SHARED_SAFE" for rule in SHARED_SAFE_RULES},
    **{rule: "UNCONTRACTED_ONLY" for rule in UNCONTRACTED_ONLY_RULES},
    **{rule: "CONTRACTED_UNVERIFIED" for rule in CONTRACTED_UNVERIFIED_RULES},
    **{rule: "MATH_CORRECTED_DXB_PROVEN" for rule in MATH_CORRECTED_DXB_RULES},
}

# Duxbury's contracted output has a stable printable-code representation for
# Unicode symbols that the bundled Liblouis UEB table leaves as an unresolved
# placeholder.  These are output encodings, not source-conditioned
# equivalences or suppression rules.
CONTRACTED_DUXBURY_SYMBOL_CODES = {
    0x20B9: '7"97',  # Unicode currency symbol encoded by the Duxbury profile.
}

_CONTRACTED_COMMON_RULES = SHARED_SAFE_RULES | frozenset({
    "contracted_source_en_dash_profile_equivalence",
})

UNCONTRACTED_PROFILE = ValidationProfile(
    name=UNCONTRACTED,
    label="Uncontracted UEB",
    grade=1,
    table="en-ueb-g1.ctb",
    enabled_rules=SHARED_SAFE_RULES | UNCONTRACTED_ONLY_RULES,
    structured_docx_tables=False,
    profile_kind="uncontracted",
)

UNCONTRACTED_CASE1_PROFILE = ValidationProfile(
    name=UNCONTRACTED_CASE1,
    label="Uncontracted UEB – Case 1: alphabet and words",
    grade=1,
    table="en-ueb-g1.ctb",
    enabled_rules=SHARED_SAFE_RULES,
    structured_docx_tables=False,
    profile_kind="uncontracted",
)

UNCONTRACTED_CASE2_PROFILE = ValidationProfile(
    name=UNCONTRACTED_CASE2,
    label="Uncontracted UEB – Case 2: capitalization",
    grade=1,
    table="en-ueb-g1.ctb",
    enabled_rules=SHARED_SAFE_RULES,
    structured_docx_tables=False,
    profile_kind="uncontracted",
)

UNCONTRACTED_CASE3_PROFILE = ValidationProfile(
    name=UNCONTRACTED_CASE3,
    label="Uncontracted UEB – Case 3: numbers",
    grade=1,
    table="en-ueb-g1.ctb",
    enabled_rules=SHARED_SAFE_RULES,
    structured_docx_tables=False,
    profile_kind="uncontracted",
)

UNCONTRACTED_CASE4_PROFILE = ValidationProfile(
    name=UNCONTRACTED_CASE4,
    label="Uncontracted UEB – Case 4: core punctuation",
    grade=1,
    table="en-ueb-g1.ctb",
    enabled_rules=SHARED_SAFE_RULES,
    structured_docx_tables=False,
    profile_kind="uncontracted",
)

CONTRACTED_DOCUMENT_PROFILE = ValidationProfile(
    name=CONTRACTED_DOCUMENT,
    label="Contracted UEB – Document",
    grade=2,
    table="en-ueb-g2.ctb",
    enabled_rules=_CONTRACTED_COMMON_RULES,
    structured_docx_tables=True,
    profile_kind="document",
    contracted_pdf_normalization=True,
    contracted_provenance=True,
    contracted_document_provenance=True,
    document_stable_anchor_min_words=4,
    document_table_trim_max_ratio=0.50,
)

CONTRACTED_POETRY_PROFILE = ValidationProfile(
    name=CONTRACTED_POETRY,
    label="Contracted UEB – Poetry",
    grade=2,
    table="en-ueb-g2.ctb",
    enabled_rules=_CONTRACTED_COMMON_RULES,
    structured_docx_tables=True,
    profile_kind="poetry",
    contracted_pdf_normalization=True,
    contracted_provenance=True,
)

CONTRACTED_TABLE_PROFILE = ValidationProfile(
    name=CONTRACTED_TABLE,
    label="Contracted UEB – Table",
    grade=2,
    table="en-ueb-g2.ctb",
    enabled_rules=_CONTRACTED_COMMON_RULES,
    structured_docx_tables=True,
    profile_kind="table",
    contracted_pdf_normalization=True,
    contracted_provenance=True,
)

# Backward-compatible name for older scripts and callers.  The former single
# contracted profile is now the explicit Document profile.
CONTRACTED_PROFILE = CONTRACTED_DOCUMENT_PROFILE

# The corrected Maths DXB uses the bundled technical/Nemeth-style symbol
# encodings for mathematical spans while ordinary prose remains contracted
# UEB.  The table is selected by its observed corrected-DXB families rather
# than by a fixture-specific rule or correction list.
MATH_PROFILE = ValidationProfile(
    name=MATH,
    label="Contracted UEB + Math",
    grade=2,
    table="en-ueb-g2.ctb",
    enabled_rules=SHARED_SAFE_RULES | MATH_CORRECTED_DXB_RULES,
    structured_docx_tables=False,
    # en-ueb-g2.ctb includes the bundled en-ueb-math.ctb technical rules.
    # The mixed translator applies only generic corrected-DXB representation
    # normalization to math spans after Liblouis translation.
    technical_math_table="en-ueb-g2.ctb",
    mixed_math=True,
    profile_kind="math",
    contracted_pdf_normalization=True,
)


def resolve_profile(profile: str | ValidationProfile | None = None, grade: int | None = None) -> ValidationProfile:
    """Resolve an explicit profile while retaining the old grade API.

    Existing callers that pass ``grade=1`` or ``grade=2`` continue to work.
    New UI/pipeline callers pass a named profile explicitly.
    """
    if isinstance(profile, ValidationProfile):
        return profile
    if profile is None:
        if grade == 1:
            return UNCONTRACTED_PROFILE
        if grade == 2:
            return CONTRACTED_PROFILE
        return UNCONTRACTED_PROFILE
    normalized = str(profile).strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in {UNCONTRACTED, UNCONTRACTED_PHASE1, "uncontracted_ueb", "uncontracted_ueb_phase1", "grade_1", "g1"}:
        return UNCONTRACTED_PROFILE
    if normalized in {UNCONTRACTED_CASE1, "uncontracted_case1", "case1", "case_1"}:
        return UNCONTRACTED_CASE1_PROFILE
    if normalized in {UNCONTRACTED_CASE2, "uncontracted_case2", "case2", "case_2"}:
        return UNCONTRACTED_CASE2_PROFILE
    if normalized in {UNCONTRACTED_CASE3, "uncontracted_case3", "case3", "case_3"}:
        return UNCONTRACTED_CASE3_PROFILE
    if normalized in {UNCONTRACTED_CASE4, "uncontracted_case4", "case4", "case_4"}:
        return UNCONTRACTED_CASE4_PROFILE
    if normalized in {CONTRACTED, CONTRACTED_DOCUMENT, "grade_2", "g2"}:
        return CONTRACTED_DOCUMENT_PROFILE
    if normalized == CONTRACTED_POETRY:
        return CONTRACTED_POETRY_PROFILE
    if normalized == CONTRACTED_TABLE:
        return CONTRACTED_TABLE_PROFILE
    if normalized in {
        MATH,
        "contracted_ueb_math",
        "contracted_math",
        "maths",
        "contracted_ueb_bana_nemeth",
    }:
        return MATH_PROFILE
    raise ValueError(f"Unknown validation profile: {profile!r}")
