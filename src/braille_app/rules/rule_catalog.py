"""Executable standards catalogue and applicability dispatcher.

The definitions themselves live in :mod:`catalog` so existing imports remain
stable.  This module adds the small amount of runtime context needed to select
candidate rules before the specialised UEB, Nemeth, and BANA verifiers run.
It deliberately does not infer mathematical meaning from Braille alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .catalog import ALL_RULES, RuleDefinition


@dataclass(frozen=True)
class ValidationContext:
    """Persistent state relevant to standards-rule applicability."""

    code: str = "UEB"
    numeric_mode: bool = False
    grade1_mode: bool = False
    capitalization_mode: str | None = None
    script_level: int = 0
    nemeth_switch_open: bool = False


class RuleRegistry:
    """Select candidate rules by source context before evaluation.

    This is intentionally a candidate dispatcher, not a second translator.
    The source region and its math records are the applicability inputs; the
    specialised verifiers still decide PASS/REVIEW/CORRECTED.
    """

    def __init__(self, rules: Iterable[RuleDefinition] = ALL_RULES):
        self.rules = tuple(rules)
        self._by_id = {rule.rule_id: rule for rule in self.rules}

    def get(self, rule_id: str) -> RuleDefinition | None:
        return self._by_id.get(rule_id)

    def rules_for(
        self,
        context: ValidationContext,
        source_type: str,
        source_text: str = "",
    ) -> tuple[RuleDefinition, ...]:
        """Return only rules whose declared scope can see this source node."""

        del source_text  # reserved for future trigger-specific predicates
        source_type = source_type.lower()
        candidates: list[RuleDefinition] = []
        for rule in self.rules:
            if rule.scope == "ueb_prose":
                applies = source_type in {"text", "mixed"}
            elif rule.scope == "ueb_boundary":
                applies = source_type == "mixed"
            elif rule.scope == "nemeth_math":
                applies = source_type in {"math", "mixed"}
            elif rule.scope == "code_boundary":
                applies = source_type in {"mixed", "boundary"}
            elif rule.scope == "mixed_boundary":
                applies = source_type in {"mixed", "boundary"}
            else:
                applies = False

            if not applies:
                continue
            if rule.standard == "NEMETH" and rule.scope == "nemeth_math" and context.code not in {"NEMETH", "MIXED"}:
                continue
            candidates.append(rule)
        return tuple(sorted(candidates, key=lambda rule: (rule.priority, rule.rule_id)))


DEFAULT_REGISTRY = RuleRegistry()


__all__ = [
    "ALL_RULES",
    "DEFAULT_REGISTRY",
    "RuleDefinition",
    "RuleRegistry",
    "ValidationContext",
]
