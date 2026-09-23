"""Production Liblouis adapter using the application's vendored runtime."""

from __future__ import annotations

import ctypes
import hashlib
import importlib
import os
import sys
from functools import lru_cache
from pathlib import Path

from .profiles import CONTRACTED_UEB_BANA_NEMETH, TranslationProfile
from braille_app.runtime_paths import resource_root


PROJECT_ROOT = resource_root()
VENDOR_BINDINGS = PROJECT_ROOT / "vendor" / "liblouis-bindings"
VENDOR_TABLES = PROJECT_ROOT / "vendor" / "liblouis-win64" / "share" / "liblouis" / "tables"
VENDOR_DLL = PROJECT_ROOT / "vendor" / "liblouis-win64" / "bin" / "liblouis.dll"
PRODUCTION_MATH_TABLE = Path(__file__).resolve().parent / "nemeth_probe.ctb"


def _output_blanks(value: str, blank: str) -> str:
    """Canonicalize horizontal layout separators, one output position each.

    Liblouis can preserve a DOCX tab in its output. The logical cell stream
    has no physical tab stops, so retain it as one blank, not an invalid cell
    or a deleted separator. One-for-one replacement preserves position maps.
    Source text and all other output characters remain untouched.
    """
    return value.translate({ord("\u00a0"): blank, ord("\t"): blank})


@lru_cache(maxsize=1)
def load_liblouis():
    if not VENDOR_BINDINGS.is_dir():
        raise FileNotFoundError(f"Missing vendored Liblouis bindings: {VENDOR_BINDINGS}")
    if not VENDOR_TABLES.is_dir():
        raise FileNotFoundError(f"Missing vendored Liblouis tables: {VENDOR_TABLES}")
    if not VENDOR_DLL.is_file():
        raise FileNotFoundError(f"Missing vendored Liblouis runtime: {VENDOR_DLL}")
    for table in ("unicode.dis", "en-ueb-g1.ctb"):
        if not (VENDOR_TABLES / table).is_file():
            raise FileNotFoundError(f"Missing vendored Liblouis table: {VENDOR_TABLES / table}")
    os.environ["LOUIS_TABLEPATH"] = str(VENDOR_TABLES)
    if sys.platform == "win32":
        try:
            ctypes.CDLL("msvcrt")._wputenv(f"LOUIS_TABLEPATH={VENDOR_TABLES}")
        except Exception:
            pass
    binding_text = str(VENDOR_BINDINGS)
    if not getattr(sys, 'frozen', False) and binding_text not in sys.path:
        sys.path.insert(0, binding_text)
    louis = importlib.import_module("louis")
    module_path = Path(getattr(louis, "__file__", "")).resolve()
    if VENDOR_BINDINGS.resolve() not in module_path.parents:
        raise RuntimeError(
            f"Loaded non-vendored Liblouis bindings from {module_path}; "
            f"expected {VENDOR_BINDINGS}"
        )
    loaded_dll = Path(getattr(louis.liblouis, "_name", "")).resolve()
    if loaded_dll != VENDOR_DLL.resolve():
        raise RuntimeError(
            f"Loaded non-vendored Liblouis runtime from {loaded_dll}; "
            f"expected {VENDOR_DLL}"
        )
    return louis


def vendored_metadata(profile: TranslationProfile) -> dict[str, str]:
    """Return auditable runtime/table identity for a selected translation."""

    louis = load_liblouis()
    table_path = VENDOR_TABLES / profile.literary_table
    if not table_path.is_file():
        raise FileNotFoundError(f"Missing vendored Liblouis table: {table_path}")
    return {
        "version": str(louis.version()).strip(),
        "dll_path": str(VENDOR_DLL.resolve()),
        "table_path": str(table_path.resolve()),
        "table_hash_sha256": hashlib.sha256(table_path.read_bytes()).hexdigest(),
        "display_table": "unicode.dis",
        "display_table_path": str((VENDOR_TABLES / "unicode.dis").resolve()),
        "table_list": f"unicode.dis,{profile.literary_table}",
    }


class LiblouisTranslator:
    """Translate prose and raw Nemeth-table input without installing Liblouis."""

    def __init__(self, profile: TranslationProfile = CONTRACTED_UEB_BANA_NEMETH):
        self.profile = profile

    def translate_prose(self, text: str) -> str:
        louis = load_liblouis()
        value = louis.translateString(["unicode.dis", self.profile.literary_table], text)
        return _output_blanks(value, "\u2800")

    def translate_prose_with_positions(self, text: str) -> tuple[str, tuple[int, ...]]:
        """Return candidate cells and their source-character positions."""
        louis = load_liblouis()
        value, input_positions, _, _ = louis.translate(
            ["unicode.dis", self.profile.literary_table], text
        )
        return _output_blanks(value, "\u2800"), tuple(input_positions)

    def translate_math_ascii(self, text: str) -> str:
        if not PRODUCTION_MATH_TABLE.is_file():
            raise FileNotFoundError(f"Missing production math table: {PRODUCTION_MATH_TABLE}")
        louis = load_liblouis()
        value = louis.translateString(["text_nabcc.dis", str(PRODUCTION_MATH_TABLE)], text)
        return _output_blanks(value, " ")

    def version(self) -> str:
        return str(load_liblouis().version()).strip()
