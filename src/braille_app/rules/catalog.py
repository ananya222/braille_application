"""Machine-readable inventory of the rule families in the three standards.

This is intentionally a coverage catalogue, not a claim that every family is
already implemented.  ``IMPLEMENTED`` entries have production code; the
``tests`` field records whether an independent regression test is present.
``PARTIAL`` entries have only the explicitly listed subset;
``SOURCE_REQUIRED`` remains review-only until the cited material is encoded.
"""

from __future__ import annotations

from dataclasses import dataclass

from .sources import NEMETH_2022, NEMETH_ERRATA_2025, UEB_2024


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    standard_area: str
    family: str
    source_document: str
    source_rule: str
    source_page: str
    description: str
    status: str
    implementation: str
    tests: tuple[str, ...] = ()
    overrides: str = ""
    # Applicability metadata.  The original fields above are retained for
    # compatibility with the Phase 4 reports and tests; these fields make the
    # catalogue usable by the dispatcher instead of making it documentation
    # only.
    standard: str = ""
    scope: str = ""
    trigger: str = ""
    preconditions: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()
    priority: int = 100
    depends_on: tuple[str, ...] = ()
    mutually_exclusive_with: tuple[str, ...] = ()
    opens_mode: tuple[str, ...] = ()
    closes_mode: tuple[str, ...] = ()
    required_behavior: str = ""
    implementation_status: str = ""
    test_status: str = ""

    def __post_init__(self) -> None:
        """Fill conservative defaults for legacy catalogue constructors."""

        if not self.standard:
            object.__setattr__(self, "standard", self.standard_area)
        if not self.scope:
            if self.standard_area == "UEB":
                scope = "ueb_boundary" if self.family == "code-switching" else "ueb_prose"
            elif self.standard_area == "NEMETH":
                scope = "code_boundary" if self.family == "switching" else "nemeth_math"
            else:
                scope = "mixed_boundary"
            object.__setattr__(self, "scope", scope)
        if not self.trigger:
            object.__setattr__(self, "trigger", self.family)
        if self.priority == 100:
            priority_by_family = {
                "switching": 10,
                "code-switching": 10,
                "numeric": 20,
                "indicators": 20,
                "contractions": 30,
                "capitalisation": 35,
                "punctuation": 40,
                "operations": 45,
                "comparison": 45,
                "grouping": 50,
                "fractions": 60,
                "scripts": 60,
                "radicals": 70,
                "functions": 70,
            }
            object.__setattr__(self, "priority", priority_by_family.get(self.family, 100))
        if not self.depends_on:
            dependency_by_family = {
                "numeric": ("NEMETH_2",),
                "fractions": ("NEMETH_2", "NEMETH_3"),
                "scripts": ("NEMETH_2",),
                "radicals": ("NEMETH_2", "NEMETH_19"),
                "functions": ("NEMETH_2", "NEMETH_6"),
                "code-switching": ("NEMETH_4",),
                "single-word-switch": ("NEMETH_4",),
            }
            object.__setattr__(
                self,
                "depends_on",
                dependency_by_family.get(self.family, ()),
            )
        if not self.opens_mode and not self.closes_mode:
            if self.family in {"switching", "code-switching", "single-word-switch"}:
                object.__setattr__(self, "opens_mode", ("NEMETH",))
                object.__setattr__(self, "closes_mode", ("UEB",))
            elif self.family == "numeric":
                object.__setattr__(self, "opens_mode", ("numeric_mode",))
                object.__setattr__(self, "closes_mode", ("numeric_termination",))
        if not self.preconditions:
            object.__setattr__(
                self,
                "preconditions",
                (f"source context is {self.scope}",),
            )
        if not self.exclusions:
            if self.scope == "ueb_prose":
                exclusions = ("inside an explicit Nemeth math span",)
            elif self.scope == "nemeth_math":
                exclusions = ("ordinary prose outside an explicit math span",)
            else:
                exclusions = ()
            object.__setattr__(self, "exclusions", exclusions)
        if not self.required_behavior:
            object.__setattr__(self, "required_behavior", self.description)
        if not self.implementation_status:
            object.__setattr__(self, "implementation_status", self.status)
        if not self.test_status:
            object.__setattr__(
                self,
                "test_status",
                "TESTED" if self.tests else "NOT_TESTED",
            )


def _ueb(section: str, page: str, family: str, description: str, status: str, implementation: str, *tests: str) -> RuleDefinition:
    return RuleDefinition(
        f"UEB_{section.replace('.', '_')}", "UEB", family, UEB_2024,
        section, page, description, status, implementation, tuple(tests),
    )


def _nemeth(rule: str, page: str, family: str, description: str, status: str, implementation: str, *tests: str) -> RuleDefinition:
    return RuleDefinition(
        f"NEMETH_{rule.replace('.', '_')}", "NEMETH", family, NEMETH_2022,
        rule, page, description, status, implementation, tuple(tests),
    )


UEB_RULES: tuple[RuleDefinition, ...] = (
    _ueb("1", "1-1", "introduction", "Scope and code principles", "PARTIAL", "scope metadata"),
    _ueb("2", "7", "general/modes", "Terminology, standing-alone and general rules", "SOURCE_REQUIRED", "review only"),
    _ueb("3", "21", "symbols/indicators", "General symbols and indicators", "PARTIAL", "Liblouis candidate"),
    _ueb("4", "45", "letters/modifiers", "Letters and modifiers", "PARTIAL", "Liblouis candidate"),
    _ueb("5", "57", "grade-1", "Grade 1 mode", "SOURCE_REQUIRED", "review only"),
    _ueb("6", "65", "numeric", "Numeric mode and termination", "PARTIAL", "Liblouis candidate"),
    _ueb("7", "75", "punctuation", "Punctuation", "PARTIAL", "Liblouis candidate"),
    RuleDefinition('UEB_8', 'UEB', 'capitalisation', UEB_2024,
        '8.1.1; 8.2.1; 8.3.1-3', '89-90 (PDF 117-118)',
        'Single word-initial capitals in regular UEB prose; broader capitals excluded.',
        'PARTIAL', 'basic_capitalization.inspect_block/localized_defect; validation.api',
        ('tests/test_basic_capitalization.py',), scope='ueb_prose',
        trigger='regular titlecase or lowercase word at a resolved UEB source position',
        preconditions=('known UEB prose prefix', 'monotone exact candidate/source map', 'equal aligned following letter/contraction', 'single capital, no inherited capital mode'),
        exclusions=('all capitals', 'internal capitals', 'modifiers/typeforms', 'numeric/grade-1 interactions', 'post-Nemeth inherited context', 'non-AIO isolated capitals'),
        depends_on=('UEB_10',), closes_mode=('after following letter',),
        required_behavior='Require dot 6 before capitalized first letter/contraction; prohibit it at a lowercase word start. Missing-prefix box anchors to the following equal actual cell. Other deletion/insertion handling is unchanged.'),
    _ueb("9", "101", "typeforms", "Typeforms", "SOURCE_REQUIRED", "review only"),
    _ueb("10", "113", "contractions", "Contracted English", "PARTIAL", "en-ueb-g2.ctb candidate", "test_rule_results_include_traceability"),
    _ueb("11", "181", "technical", "Technical material and spacing", "PARTIAL", "Nemeth routing", "test_mixed_translation_uses_verified_switches"),
    _ueb("12", "193", "early-english", "Early forms of English", "OUT_OF_SCOPE", "not in declared textbook scope"),
    _ueb("13", "197", "foreign-language", "Foreign language", "OUT_OF_SCOPE", "not in declared textbook scope"),
    _ueb("14", "211", "code-switching", "UEB code switching", "PARTIAL", "Nemeth switching layer"),
    _ueb("15", "223", "scansion", "Scansion, stress and tone", "OUT_OF_SCOPE", "not in declared textbook scope"),
    _ueb("16", "229", "line-mode", "Line mode and guide dots", "OUT_OF_SCOPE", "layout layer excluded"),
)


NEMETH_RULES: tuple[RuleDefinition, ...] = (
    RuleDefinition(
        rule_id="NEMETH_LETTER_GROUP_001", standard_area="NEMETH", standard="NEMETH",
        family="letter-grouping", source_document=NEMETH_2022,
        source_rule="6.3.1; 6.4.8; 6.4.11; 19.1.1; 5.1.1/5.3.1",
        source_page="6-6,6-14–15;19-1–2;5-1–2 (PDF 91,99–100,253–254,84–85)",
        description="Exact canonical proof for whole regular-letter/group ASTs; not named functions.",
        status="PARTIAL", implementation="letter_grouping.verify_record; nemeth_rules context gate",
        tests=("tests/test_letter_grouping.py",), scope="nemeth_math", trigger="whole-record Letter/Group/LetterApplication AST",
        preconditions=("NEMETH context; baseline script level; no active numeric/grade1/capital mode; regular mathematical letters",
                       "candidate equals independently derived canonical cells", "source markers map in exact record order",
                       "all outer boundaries separated from prose tokens or punctuation"),
        exclusions=("numeric arguments", "tuple/comma/colon punctuation", "scripts or primes", "named functions and narrative words",
                    "typeforms, enlarged or modified groups", "unbalanced/mixed grouping", "attached outer prose/punctuation"),
        depends_on=("NEMETH_5", "NEMETH_6", "NEMETH_19"),
        overrides="6.4.8 non-use overrides 6.3.1 general single-letter criteria inside a simple group",
        opens_mode=("no mode change; requires NEMETH",), closes_mode=("local proof ends at whole math record",),
        required_behavior="No indicator for both-sided contact; callee before grouping is not single under 6.3.1. Preserve ordinary grouping and per-letter capitals. Candidate mismatch retains REVIEW; no cells rewritten.",
    ),
    _nemeth("1", "1-1", "principles", "Nemeth scope and literal interpretation", "PARTIAL", "source/technical scope"),
    _nemeth("2", "2-1", "indicators", "Nemeth indicators", "PARTIAL", "nemeth_probe.ctb", "test_mixed_translation_uses_verified_switches"),
    _nemeth("3", "3-1", "numeric", "Numeric signs and symbols", "PARTIAL", "nemeth_probe.ctb", "test_unproved_nemeth_calibration_constructs_are_reviewed"),
    _nemeth("4", "4-1", "switching", "UEB/Nemeth code switching", "IMPLEMENTED", "mixed_translator.py", "test_mixed_translation_uses_verified_switches"),
    _nemeth("5", "5-1", "capitalisation", "Capitalisation in Nemeth", "PARTIAL", "nemeth_probe.ctb"),
    _nemeth("6", "6-1", "alphabets", "Letters and alphabets", "PARTIAL", "nemethdefs.cti", "test_vendored_nemeth_symbols_are_supported"),
    _nemeth("7", "7-1", "typeforms", "Typeforms", "SOURCE_REQUIRED", "review only"),
    _nemeth("8", "8-1", "punctuation", "Punctuation signs and symbols", "PARTIAL", "nemeth_probe.ctb"),
    _nemeth("9", "9-1", "reference-signs", "Reference signs, symbols and icons", "SOURCE_REQUIRED", "review only"),
    _nemeth("10", "10-1", "abbreviations", "Abbreviations", "SOURCE_REQUIRED", "review only"),
    _nemeth("11", "11-1", "omissions", "Omissions", "SOURCE_REQUIRED", "review only"),
    _nemeth("12", "12-1", "cancellation", "Cancellation", "OUT_OF_SCOPE", "spatial/cancellation layer"),
    _nemeth("13", "13-1", "fractions", "Fractions", "SOURCE_REQUIRED", "review only", "test_unproved_nemeth_calibration_constructs_are_reviewed"),
    _nemeth("14", "14-1", "scripts", "Superscripts and subscripts", "PARTIAL", "simple_script_tokens", "test_rule14_simple_scripts_are_supported", "test_rule14_nested_scripts_remain_reviewed"),
    _nemeth("15", "15-1", "modifiers", "Modifiers", "SOURCE_REQUIRED", "review only"),
    _nemeth("16", "16-1", "radicals", "Radicals", "SOURCE_REQUIRED", "review only"),
    _nemeth("17", "17-1", "shapes", "Shapes", "SOURCE_REQUIRED", "review only"),
    _nemeth("18", "18-1", "functions", "Function names", "SOURCE_REQUIRED", "review only"),
    _nemeth("19", "19-1", "grouping", "Grouping signs", "PARTIAL", "nemeth_probe.ctb"),
    _nemeth("20", "20-1", "operations", "Signs and symbols of operation", "PARTIAL", "nemeth_probe.ctb"),
    _nemeth("21", "21-1", "comparison", "Signs and symbols of comparison", "PARTIAL", "nemethdefs.cti"),
    _nemeth("22", "22-1", "arrows", "Arrows", "SOURCE_REQUIRED", "review only"),
    _nemeth("23", "23-1", "miscellaneous", "Miscellaneous signs and symbols", "PARTIAL", "nemethdefs.cti", "test_vendored_nemeth_symbols_are_supported"),
    _nemeth("24", "24-1", "multipurpose", "Multipurpose indicator", "SOURCE_REQUIRED", "review only"),
    _nemeth("25", "25-1", "spatial", "Spatial arrangements", "OUT_OF_SCOPE", "layout layer excluded"),
    _nemeth("26", "26-1", "format", "Nemeth format", "PARTIAL", "page/layout harness"),
)


BANA_RULES: tuple[RuleDefinition, ...] = (
    RuleDefinition(
        rule_id="BANA_4_2_INNER_SPACE", standard_area="BANA", standard="BANA",
        family="switching", source_document=NEMETH_ERRATA_2025,
        source_rule="4.2; placement excluded per 4.8.2", source_page="4 (PDF p.8); 7 (PDF p.11)",
        description="Inner blank at each already-selected linear Nemeth passage boundary only.",
        status="IMPLEMENTED", implementation="mixed_translator.serialize_nemeth_passage",
        tests=("tests/test_nemeth_boundary_spacing.py",), scope="mixed_boundary",
        trigger="serialization of an explicitly marked nonempty Nemeth span",
        preconditions=("canonical unformatted math payload", "UEB to Nemeth to UEB switch pair already selected by source routing"),
        exclusions=("empty payload", "physical line/page layout", "other switch profiles", "single-word switching and punctuation ownership decisions"),
        depends_on=("NEMETH_4",), overrides="Nemeth 4.2 amended text",
        opens_mode=("NEMETH after opening boundary",), closes_mode=("NEMETH at terminator; return to UEB",),
        required_behavior="Add only missing inner blanks; preserve payload and existing blanks. End at this passage terminator. Does not certify switching placement or interior content.",
    ),
    RuleDefinition(
        "BANA_4_2", "BANA", "switching", NEMETH_ERRATA_2025, "Rule 4.2", "4 (PDF p. 8)",
        "Opening switch is followed by a space and the terminator is preceded by a space; no contractions occur inside switches.",
        "PARTIAL", "bana_rules.py (pair counts); mixed_translator.py (inner blanks only)", ("test_mixed_translation_uses_verified_switches",), "Nemeth 4.2 override",
    ),
    RuleDefinition(
        "BANA_4_6_8_C", "BANA", "single-word-switch", NEMETH_ERRATA_2025, "Rule 4.6.8.c", "4-16 (PDF p. 10)",
        "Single-word switch is unspaced from the affected UEB word and terminates at a space.",
        "SOURCE_REQUIRED", "review only", (), "Nemeth 4.6.8.c override",
    ),
)


BOUNDARY_RULES = (
    RuleDefinition(
        rule_id="NEMETH_BOUNDARY_PUNCT_001", standard_area="NEMETH", standard="NEMETH",
        family="boundary-punctuation", source_document=f"{NEMETH_2022}; {UEB_2024}; {NEMETH_ERRATA_2025}",
        source_rule="Nemeth 4.6.5(b), amended 4.2; UEB 7.1.1, 7.5.1–4, 2.6.1–3",
        source_page="Nemeth 4-1,4-12; UEB 15–17,75–76,81; errata p.4 (PDF 8)",
        description="Independent local proof of attached sentence punctuation after Nemeth termination.",
        status="PARTIAL", implementation="boundary_punctuation.verify; boundary_punctuation.inspect_block",
        tests=("tests/test_boundary_verifier.py",), scope="mixed_boundary",
        trigger="source-resolved outer sentence punctuation after a complete math span",
        preconditions=("independent semantic ownership", "complete math node", "known inherited modes", "exact boundary cell interval", "resolved linear layout"),
        exclusions=("unknown context or provenance", "inner/list punctuation", "quotes/clusters", "active grade1/capital/typeform/script state", "standalone question marks"),
        depends_on=("NEMETH_4", "UEB_7"), priority=41,
        closes_mode=("NEMETH at terminator",), opens_mode=("UEB after terminator",),
        required_behavior="Compare exact interval with inner blank + Nemeth terminator + independently mapped UEB punctuation; effect ends at punctuation. Never certify containing block from local proof.",
    ),
)

SIMPLE_MATH_RULES = (
    RuleDefinition(
        rule_id="NEMETH_SIMPLE_LINEAR_001", standard_area="NEMETH", standard="NEMETH",
        family="simple-linear-math", source_document=NEMETH_2022,
        source_rule="3.3.1; 3.4.1; 6.3.1; 6.4.7; 20.1; 21.13",
        source_page="3-3,3-11; 6-6,6-12; 20-1 to 20-4; 21-15",
        description="Closed baseline integer/lowercase-variable arithmetic and equality.",
        status="PARTIAL", implementation="simple_math.py; nemeth_rules.verify_math_block",
        tests=("tests/test_simple_math_scope.py",), scope="nemeth_math",
        trigger="complete explicitly marked linear expression",
        preconditions=("full grammar parse", "regular baseline math", "explicit operators", "known operand boundaries"),
        exclusions=("radicals without structural metadata", "typeforms", "scripts", "grouping", "functions", "fractions", "runover within expression", "consecutive signs"),
        depends_on=("NEMETH_3", "NEMETH_6", "NEMETH_20", "NEMETH_21"),
        priority=40, closes_mode=("local numeric context at explicit math-span end",),
        required_behavior="Unspace operations; space equality; numeric sign at passage start/after equality, also after initial negative. No repeat indicator after binary operations. No English-letter indicator adjacent to operations/comparison. Unsupported complete parse remains REVIEW.",
    ),
)

ALL_RULES: tuple[RuleDefinition, ...] = UEB_RULES + NEMETH_RULES + BANA_RULES + BOUNDARY_RULES + SIMPLE_MATH_RULES


def coverage_rows() -> list[dict[str, int | str]]:
    rows: dict[tuple[str, str], dict[str, int | str]] = {}
    for rule in ALL_RULES:
        key = (rule.standard_area, rule.family)
        row = rows.setdefault(key, {"standard": rule.standard_area, "family": rule.family, "catalogued": 0, "implemented": 0, "tested": 0, "remaining": 0})
        row["catalogued"] += 1
        if rule.status in {"IMPLEMENTED", "PARTIAL"}:
            row["implemented"] += 1
        if rule.tests:
            row["tested"] += 1
        if rule.status in {"SOURCE_REQUIRED", "OUT_OF_SCOPE"}:
            row["remaining"] += 1
    return list(rows.values())
