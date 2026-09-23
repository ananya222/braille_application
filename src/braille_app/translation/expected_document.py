"""Provenance-preserving expected-Braille document generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .liblouis_translator import LiblouisTranslator
from .mixed_translator import MathMarkerError, translate_marked_text
from .profiles import CONTRACTED_UEB_BANA_NEMETH, TranslationProfile, get_profile
from .source_normalization import (
    UnsupportedSourceError,
    normalize_uncontracted_case1,
    normalize_uncontracted_case2,
    normalize_uncontracted_case3,
    normalize_uncontracted_case4,
    normalize_uncontracted_phase1,
)


@dataclass(frozen=True)
class ExpectedBlock:
    source_text: str
    source_page: int
    source_block: int | str
    braille: str
    region_type: str
    rule_status: str = "PENDING"
    rule_results: tuple[Any, ...] = field(default_factory=tuple)
    math_records: tuple[Any, ...] = field(default_factory=tuple)
    capital_sites: tuple[Any, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExpectedPage:
    number: int
    blocks: tuple[ExpectedBlock, ...]

    def flatten(self) -> str:
        return "\u2800".join(block.braille for block in self.blocks if block.braille)


@dataclass(frozen=True)
class ExpectedBrailleDocument:
    pages: tuple[ExpectedPage, ...]
    profile: TranslationProfile

    def flatten(self) -> str:
        return "\f".join(page.flatten() for page in self.pages)

    @property
    def blocks(self) -> tuple[ExpectedBlock, ...]:
        return tuple(block for page in self.pages for block in page.blocks)

    @property
    def math_span_count(self) -> int:
        return sum(len(block.math_records) for block in self.blocks)

    @property
    def review_count(self) -> int:
        return sum(block.rule_status == "REVIEW" for block in self.blocks)

    @property
    def excluded_count(self) -> int:
        return sum(block.rule_status == "EXCLUDED_OUT_OF_SCOPE" for block in self.blocks)


def _load_master(master_document: Any) -> dict:
    if isinstance(master_document, dict):
        return _partition_page_markers(master_document)
    if isinstance(master_document, (str, Path)):
        from braille_app.doc_extractor import DocumentExtractor

        return _partition_page_markers(DocumentExtractor().extract(str(master_document)))
    if isinstance(master_document, Iterable):
        return _partition_page_markers({"pages": list(master_document)})
    raise TypeError("master_document must be an extractor dictionary, path, or page iterable")


def _partition_page_markers(master: dict) -> dict:
    """Recognize the explicit page markers used by reconstructed master DOCX files."""

    source_pages = master.get("pages", [])
    if not any(
        str(block.get("text", "")).startswith("=== PAGE ")
        for page in source_pages
        for block in page.get("blocks", [])
    ):
        return master
    pages: list[dict] = []
    current: dict | None = None
    for page in source_pages:
        for block in page.get("blocks", []):
            text = block.get("text", "") or ""
            if text.startswith("=== PAGE "):
                if current is not None:
                    pages.append(current)
                try:
                    number = int(text.split()[2])
                except (IndexError, ValueError):
                    number = len(pages) + 1
                current = {"print_page_number": number, "blocks": [block]}
            else:
                if current is None:
                    current = {"print_page_number": len(pages) + 1, "blocks": []}
                current["blocks"].append(block)
    if current is not None:
        pages.append(current)
    return {"pages": pages}


def _block_groups(blocks: list[dict]) -> list[list[dict]]:
    """Group only blocks whose explicit math markers cross a block boundary."""

    groups: list[list[dict]] = []
    pending: list[dict] = []
    balance = 0
    for block in blocks:
        text = block.get("text", "") or ""
        starts = text.count("[[*ts*]]")
        ends = text.count("[[*te*]]")
        if pending:
            pending.append(block)
            balance += starts - ends
            if balance == 0:
                groups.append(pending)
                pending = []
            continue
        if starts > ends:
            pending = [block]
            balance = starts - ends
        else:
            groups.append([block])
    if pending:
        groups.append(pending)
    return groups


def _translate_group(
    group: list[dict],
    page_number: int,
    translator: LiblouisTranslator,
    profile: TranslationProfile,
    group_index: int,
) -> ExpectedBlock:
    source_parts = [(item.get("text", "") or "") for item in group]
    source_for_translation = " ".join(source_parts)
    source_for_record = "\n".join(source_parts)
    first = group[0]
    if not source_for_translation.strip():
        return ExpectedBlock(source_for_record, page_number, group_index, "", "empty")
    if source_for_translation.startswith("=== PAGE "):
        return ExpectedBlock(source_for_record, page_number, group_index, "", "control")
    try:
        if profile.case1_scope:
            source_for_translation = normalize_uncontracted_case1(source_for_translation)
            from .uncontracted_case1 import translate_source

            return ExpectedBlock(
                source_for_record,
                page_number,
                group_index,
                translate_source(source_for_translation, translator),
                "text",
                "PENDING",
                (),
                (),
            )
        if profile.case2_scope:
            source_for_translation = normalize_uncontracted_case2(source_for_translation)
            from .uncontracted_case2 import translate_source

            return ExpectedBlock(
                source_for_record,
                page_number,
                group_index,
                translate_source(source_for_translation, translator),
                "text",
                "PENDING",
                (),
                (),
            )
        if profile.case3_scope:
            source_for_translation = normalize_uncontracted_case3(source_for_translation)
            from .uncontracted_case3 import translate_source

            return ExpectedBlock(
                source_for_record,
                page_number,
                group_index,
                translate_source(source_for_translation, translator),
                "text",
                "PENDING",
                (),
                (),
            )
        if profile.case4_scope:
            source_for_translation = normalize_uncontracted_case4(source_for_translation)
            from .uncontracted_case4 import translate_source

            return ExpectedBlock(
                source_for_record,
                page_number,
                group_index,
                translate_source(source_for_translation, translator),
                "text",
                "PENDING",
                (),
                (),
            )
        if profile.phase1_scope:
            source_for_translation = normalize_uncontracted_phase1(source_for_translation)
            from .uncontracted_phase1 import translate_source

            return ExpectedBlock(
                source_for_record,
                page_number,
                group_index,
                translate_source(source_for_translation, translator),
                "text",
                "PENDING",
                (),
                (),
            )
        translated = translate_marked_text(source_for_translation, translator, profile)
    except (MathMarkerError, UnsupportedSourceError) as exc:
        # A malformed source is not silently repaired.  Preserve it as review.
        return ExpectedBlock(
            source_for_record,
            page_number,
            group_index,
            "",
            "review",
            "REVIEW",
            (str(exc),),
            (),
        )
    region_type = "mixed" if translated.has_math else "text"
    math_records = tuple(span.math for span in translated.spans if span.math is not None)
    return ExpectedBlock(
        source_for_record,
        page_number,
        group_index,
        translated.braille,
        region_type,
        "PENDING",
        (),
        math_records,
    )


def generate_expected_braille(
    master_document: Any,
    profile: str | TranslationProfile = CONTRACTED_UEB_BANA_NEMETH,
    translator: LiblouisTranslator | None = None,
):
    """Generate verified expected Braille without flattening provenance."""

    selected = get_profile(profile)
    translator = translator or LiblouisTranslator(selected)
    master = _load_master(master_document)
    pages: list[ExpectedPage] = []
    for fallback_number, page in enumerate(master.get("pages", []), start=1):
        page_number = int(page.get("print_page_number", fallback_number))
        raw_blocks = list(page.get("blocks", []))
        generated: list[ExpectedBlock] = []
        for group_index, group in enumerate(_block_groups(raw_blocks)):
            generated.append(
                _translate_group(group, page_number, translator, selected, group_index)
            )
        pages.append(ExpectedPage(page_number, tuple(generated)))
    document = ExpectedBrailleDocument(tuple(pages), selected)
    if selected.case1_scope:
        from .uncontracted_case1 import verify_document

        return verify_document(document, translator)
    if selected.case2_scope:
        from .uncontracted_case2 import verify_document

        return verify_document(document, translator)
    if selected.case3_scope:
        from .uncontracted_case3 import verify_document

        return verify_document(document, translator)
    if selected.case4_scope:
        from .uncontracted_case4 import verify_document

        return verify_document(document, translator)
    if selected.phase1_scope:
        from .uncontracted_phase1 import verify_document

        return verify_document(document, translator)
    from braille_app.rules.rule_engine import RuleEngine

    return RuleEngine().verify_document(document)
