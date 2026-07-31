import os
import re
import sys
import yaml
from typing import List, Dict, Any

class UEBCorrectionValidationError(Exception):
    pass

def load_and_validate_corrections(yaml_path: str) -> List[Dict[str, Any]]:
    resolved_path = yaml_path
    if not os.path.exists(resolved_path):
        if hasattr(sys, "_MEIPASS"):
            resolved_path = os.path.join(sys._MEIPASS, yaml_path)
        else:
            main_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            resolved_path = os.path.join(main_dir, yaml_path)

    if not os.path.exists(resolved_path):
        raise FileNotFoundError(f"Corrections file not found at {yaml_path} or fallback {resolved_path}")
        
    with open(resolved_path, "r", encoding="utf-8") as f:
        try:
            entries = yaml.safe_load(f)
        except Exception as e:
            raise UEBCorrectionValidationError(f"Invalid YAML syntax: {e}")
            
    if not isinstance(entries, list):
        raise UEBCorrectionValidationError("Corrections file root must be a list of entries.")
        
    validated_entries = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise UEBCorrectionValidationError("Each correction entry must be a dictionary.")
            
        # 1. Check required base fields
        entry_id = entry.get("id")
        grade = entry.get("grade")
        category = entry.get("category")
        
        if not entry_id:
            raise UEBCorrectionValidationError("Entry missing required 'id' field.")
        if not grade:
            raise UEBCorrectionValidationError(f"Entry '{entry_id}' missing required 'grade' field.")
        if not category:
            raise UEBCorrectionValidationError(f"Entry '{entry_id}' missing required 'category' field.")
            
        # 2. Check grade validity
        if grade not in ["1", "2", "both"]:
            raise UEBCorrectionValidationError(
                f"Entry '{entry_id}' has invalid grade '{grade}'. Must be '1', '2', or 'both'."
            )
            
        # 3. Check category validity
        if category not in ["A", "B", "C", "D"]:
            raise UEBCorrectionValidationError(
                f"Entry '{entry_id}' has invalid category '{category}'. Must be 'A', 'B', 'C', or 'D'."
            )
            
        # 4. Loader-level safeguards for A, B, C
        if category in ["A", "B", "C"]:
            source = entry.get("source")
            verified = entry.get("verified")
            
            if source is None or source == "":
                raise UEBCorrectionValidationError(
                    f"Entry '{entry_id}' is Category {category} but 'source' is null or empty."
                )
            if not isinstance(verified, bool) or verified is not True:
                raise UEBCorrectionValidationError(
                    f"Entry '{entry_id}' is Category {category} but 'verified' is not set to true."
                )
                
        validated_entries.append(entry)
        
    return validated_entries

class UEBCorrectionsManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(UEBCorrectionsManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.initialized = False
        return cls._instance
        
    def __init__(self, yaml_path: str = "ueb_corrections.yaml"):
        if self.initialized:
            return
        self.yaml_path = yaml_path
        self.entries = load_and_validate_corrections(self.yaml_path)
        self.initialized = True
        
    def get_post_process_rules(self, grade: int) -> List[Dict[str, Any]]:
        """Filter to category A/B and grade matching requested grade or 'both'."""
        grade_str = str(grade)
        filtered = []
        for entry in self.entries:
            if entry["category"] in ["A", "B"]:
                entry_grade = entry["grade"]
                if entry_grade == "both" or entry_grade == grade_str:
                    filtered.append(entry)
        return filtered

    def get_category_c_rules(self, grade: int) -> List[Dict[str, Any]]:
        """Filter to category C and grade matching requested grade or 'both'."""
        grade_str = str(grade)
        filtered = []
        for entry in self.entries:
            if entry["category"] == "C":
                entry_grade = entry["grade"]
                if entry_grade == "both" or entry_grade == grade_str:
                    filtered.append(entry)
        return filtered
