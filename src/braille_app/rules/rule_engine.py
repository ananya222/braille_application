"""Traceable BANA/UEB/Nemeth verification orchestration."""

from __future__ import annotations

from dataclasses import replace

from .bana_rules import verify_switching_block
from .nemeth_rules import verify_math_block
from .rule_catalog import DEFAULT_REGISTRY, ValidationContext
from .rule_result import RuleResult
from .sources import NEMETH_2022
from .ueb_rules import verify_ueb_block
from .letter_grouping import RULE_ID as LETTER_GROUP_RULE, record_promotion_contexts, verify_record
from .boundary_punctuation import RULE_ID as BOUNDARY_RULE, inspect_block
from .basic_capitalization import inspect_block as inspect_capitalization


class RuleEngine:
    """Apply only supported deterministic rules and surface uncertainty."""

    def __init__(self, registry=DEFAULT_REGISTRY):
        self.registry = registry

    def verify_block(self, block):
        page = block.source_page
        block_id = block.source_block
        if block.rule_status == "REVIEW":
            result = RuleResult(
                rule_id="SOURCE_RULE_001",
                status="REVIEW",
                source=block.source_text,
                original_braille=block.braille,
                corrected_braille=block.braille,
                explanation="The source block could not be translated deterministically.",
                page=page,
                block=block_id,
                standard_area="BANA",
                family="source-integrity",
                source_document=NEMETH_2022,
                source_rule="1.3.1 Interpretation",
                source_page="1-2 (PDF pp. 20-21)",
                source_construct="source block marked REVIEW",
                original_cells=(),
                expected_cells=(),
                corrected_cells=(),
                justification="The source/math record is not deterministic enough for automatic validation.",
            )
            return replace(block, rule_status="REVIEW", rule_results=(result,))
        source_type = "mixed" if block.math_records else "text"
        context = ValidationContext(
            code="MIXED" if block.math_records else "UEB",
            nemeth_switch_open=bool(block.math_records),
        )
        candidates = self.registry.rules_for(context, source_type, block.source_text)
        candidate_families = {rule.family for rule in candidates}
        results = []
        if candidates and any(rule.standard == "UEB" for rule in candidates):
            results.append(verify_ueb_block(block, page, block_id))
        if any(rule.rule_id == "UEB_8" for rule in candidates) and not any(
            result.status == 'EXCLUDED_OUT_OF_SCOPE' for result in results
        ):
            sites, capital_result = inspect_capitalization(block, context)
            block = replace(block, capital_sites=sites)
            if capital_result is not None:
                results.append(capital_result)
        if block.math_records and any(rule.standard == "NEMETH" for rule in candidates):
            grouping_enabled = any(rule.rule_id == LETTER_GROUP_RULE for rule in candidates)
            results.append(verify_math_block(block, page, block_id, allow_letter_grouping=grouping_enabled,
                allow_simple_math=any(rule.rule_id == "NEMETH_SIMPLE_LINEAR_001" for rule in candidates)))
            if grouping_enabled and all(record_promotion_contexts(block)):
                for record in block.math_records:
                    proof = verify_record(record, ValidationContext(code="NEMETH"), page, block_id)
                    if proof is not None:
                        results.append(proof)
        if block.math_records and any(rule.family == "switching" for rule in candidates):
            results.append(verify_switching_block(block, page, block_id))
        # A source node with no candidate is not silently accepted.  It is a
        # catalogue/applicability gap and therefore follows the existing
        # conservative REVIEW policy.
        if not results:
            results.append(
                RuleResult(
                    rule_id="RULE_DISPATCH_001",
                    status="REVIEW",
                    source=block.source_text,
                    original_braille=block.braille,
                    corrected_braille=block.braille,
                    explanation="No standards rule was applicable to this source node.",
                    page=page,
                    block=block_id,
                    standard_area="BANA",
                    family="dispatcher",
                    source_document=NEMETH_2022,
                    source_rule="Rule catalogue applicability",
                    source_page="catalogue",
                    source_construct=source_type,
                    justification=f"Candidate families: {sorted(candidate_families)}",
                )
            )
        status = "PASS"
        if (any(r.status == "REVIEW" for r in results)
                and any(r.rule_id == BOUNDARY_RULE for r in candidates)):
            results.extend(inspect_block(block))
        if any(result.status == "REVIEW" for result in results):
            status = "REVIEW"
        elif any(result.status == "EXCLUDED_OUT_OF_SCOPE" for result in results):
            status = "EXCLUDED_OUT_OF_SCOPE"
        elif any(result.status == "CORRECTED" for result in results):
            status = "CORRECTED"
        return replace(block, rule_status=status, rule_results=tuple(results))

    def verify_document(self, document):
        pages = tuple(
            replace(page, blocks=tuple(self.verify_block(block) for block in page.blocks))
            for page in document.pages
        )
        return replace(document, pages=pages)
