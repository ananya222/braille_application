"""Expected-vs-actual Braille validation services."""

from .validator import BrailleValidator, ValidationReport

__all__ = ["BrailleValidator", "ValidationReport"]
from .api import ValidationIssue, ValidationResult, adapt_validation_report, validate_document

__all__ = ["ValidationIssue", "ValidationResult", "adapt_validation_report", "validate_document"]
