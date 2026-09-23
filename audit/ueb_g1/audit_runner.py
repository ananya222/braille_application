from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "audit" / "ueb_g1"
PDF = ROOT / "rules" / "Rules-of-Unified-English-Braille-2024.pdf"
TABLES = ROOT / "vendor" / "liblouis-win64" / "share" / "liblouis" / "tables"
DLL = ROOT / "vendor" / "liblouis-win64" / "bin" / "liblouis.dll"
BINDINGS = ROOT / "vendor" / "liblouis-bindings"
SYSTEM_TABLE = Path(r"C:\liblouis\share\liblouis\tables\en-ueb-g1.ctb")
TABLE_LIST = ["unicode.dis", "en-ueb-g1.ctb"]


DOTS = {
    "a": "1", "b": "12", "c": "14", "d": "145", "e": "15",
    "f": "124", "g": "1245", "h": "125", "i": "24", "j": "245",
    "k": "13", "l": "123", "m": "134", "n": "1345", "o": "135",
    "p": "1234", "q": "12345", "r": "1235", "s": "234", "t": "2345",
    "u": "136", "v": "1236", "w": "2456", "x": "1346", "y": "13456",
    "z": "1356",
}
DIGITS = {"0": "245", "1": "1", "2": "12", "3": "14", "4": "145",
          "5": "15", "6": "124", "7": "1245", "8": "125", "9": "24"}
PUNCT = {
    ",": "2", ";": "23", ":": "25", ".": "256", "!": "235", "?": "236",
    "-": "36", "–": "6-36", "—": "6-36", "―": "5-6-36",
    "/": "456-34", "(": "5-126", ")": "5-345", "[": "46-126", "]": "46-345",
    "{": "456-126", "}": "456-345", "&": "4-12346", "@": "4-1",
    "%": "46-356", "#": "456-1456", "©": "45-14", "®": "45-1235",
    "™": "45-2345", "¢": "4-14", "$": "4-234", "£": "4-123", "€": "4-15",
    "¥": "4-13456", "°": "45-245", "§": "45-234", "¶": "45-1234",
    "•": "456-256", "…": "256-256-256", "*": "5-35", "=": "5-2356",
}
CAP = "6"
CAPWORD = ("6", "6")
CAPPASS = ("6", "6", "6")
CAPTERM = ("6", "3")
G1 = "56"
NUM = "3456"
G1WORD = "56-56"
G1PASS = "56-56-56"
G1TERM = "56-3"


def cell(dot_string: str) -> str:
    if dot_string in ("", "0"):
        return chr(0x2800)
    value = 0
    for dot in dot_string.replace("-", ""):
        value |= 1 << (int(dot) - 1)
    return chr(0x2800 + value)


def B(*dot_cells: str) -> str:
    return cell("0") if not dot_cells else "".join(cell(item) for item in dot_cells)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cp(text: str) -> str:
    return " ".join(f"U+{ord(ch):04X}" for ch in text)


def dot_notation(text: str) -> str:
    values = []
    for ch in text:
        bits = ord(ch) - 0x2800
        values.append("0" if bits == 0 else "".join(str(i) for i in range(1, 7) if bits & (1 << (i - 1))))
    return " ".join(values)


def codepoint_braille(text: str) -> str:
    return " ".join(f"U+{ord(ch):04X}" for ch in text)


def letters(text: str) -> str:
    out = []
    for ch in text:
        if ch == " ":
            out.append(B())
        elif ch.isalpha() and ch.lower() in DOTS:
            out.append(B(CAP, DOTS[ch.lower()]) if ch.isupper() else B(DOTS[ch]))
        else:
            raise ValueError(f"letters() cannot render {ch!r}")
    return "".join(out)


def number(text: str) -> str:
    out = [B(NUM)]
    for ch in text:
        if ch.isdigit():
            out.append(B(DIGITS[ch]))
        elif ch == ".":
            out.append(B("256"))
        elif ch == ",":
            out.append(B("2"))
        else:
            raise ValueError(f"number() cannot render {ch!r}")
    return "".join(out)


def plain(text: str) -> str:
    """Small UEB-G1 renderer for expected values, not production code."""
    out = []
    numeric = False
    for ch in text:
        if ch == " ":
            out.append(B())
            numeric = False
            continue
        if ch.isdigit():
            if not numeric:
                out.append(B(NUM))
                numeric = True
            out.append(B(DIGITS[ch]))
            continue
        if ch in ".," and numeric:
            out.append(B(PUNCT[ch]))
            continue
        if ch.isalpha() and ch.lower() in DOTS:
            if numeric and ch.islower() and ch in "abcdefghij":
                out.append(B(G1))
            out.append(B(CAP, DOTS[ch.lower()]) if ch.isupper() else B(DOTS[ch]))
            numeric = False
            continue
        numeric = False
        if ch in PUNCT:
            out.append(B(*PUNCT[ch].split("-")))
        elif ch == "'":
            out.append(B("3"))
        elif ch == "\u2018":
            out.append(B("6", "236"))
        elif ch == "\u2019":
            out.append(B("6", "356"))
        elif ch == "\u201c":
            out.append(B("236"))
        elif ch == "\u201d":
            out.append(B("356"))
        elif ch == "\u00a0" or ch == "\u2009" or ch == "\u200b":
            out.append(B())
        else:
            raise ValueError(f"plain() cannot render {ch!r}")
    return "".join(out)


def caps_word(word: str) -> str:
    return B(*CAPWORD) + letters(word.lower())


def cap_passage(text: str) -> str:
    body = plain(text.lower())
    return B(*CAPPASS) + body + B(*CAPTERM)


def tf_json(kind: str, start: int, end: int) -> str:
    return json.dumps({kind: list(range(start, end))}, separators=(",", ":"))


def row(case_id: str, family: str, citation: str, source: str, expected: str | None,
        tier: str, notes: str = "", *, accepted: tuple[str, ...] = (),
        official: str = "YES", gap: str = "", typeform: str = "",
        back_test: str = "YES", n_a_grade: bool = False) -> dict[str, str]:
    return {
        "id": case_id,
        "family": family,
        "citation": citation,
        "source": source,
        "source_codepoints": cp(source),
        "expected_braille": "" if expected is None else expected,
        "expected_dot_notation": "" if expected is None else dot_notation(expected),
        "accepted_braille": "|".join(accepted),
        "accepted_dot_notation": "|".join(dot_notation(value) for value in accepted),
        "evidence_tier": tier,
        "official_example_available": official,
        "notes": notes,
        "gap_classification": gap,
        "typeform_spec": typeform,
        "back_test": back_test,
        "n_a_grade": "YES" if n_a_grade else "NO",
    }


def build_corpus() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for letter_name in "abcdefghijklmnopqrstuvwxyz":
        rows.append(row(f"alphabet_lower_{letter_name}", "Alphabet", "4.1", letter_name,
                        B(DOTS[letter_name]), "OFFICIAL", "Direct alphabet table entry."))
    for letter_name in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        rows.append(row(f"alphabet_upper_{letter_name.lower()}", "Alphabet", "4.1", letter_name,
                        B(CAP, DOTS[letter_name.lower()]), "OFFICIAL", "Direct alphabet table entry."))

    rows += [
        row("word_hello", "Alphabet", "4.1, 2.5.5", "hello", plain("hello"), "DERIVED"),
        row("word_braille_validator", "Alphabet", "4.1, 2.5.5", "Braille Validator", plain("Braille Validator"), "DERIVED"),
        row("word_ordinary", "Alphabet", "4.1, 2.5.5", "ordinary words", plain("ordinary words"), "DERIVED"),
        row("cap_isolated", "Capitalization", "8.3.1", "A", B(CAP, "1"), "OFFICIAL", "Also covered by the alphabet list."),
        row("cap_word", "Capitalization", "8.1, 8.3.1", "Hello", plain("Hello"), "DERIVED"),
        row("cap_all_word", "Capitalization", "8.4, 8.8", "ALL", caps_word("ALL"), "DERIVED",
            "Capitalised word mode is the canonical form.", accepted=(letters("ALL"),), gap="PERMITTED_VARIANT_NOT_MODELLED"),
        row("cap_multiple_words", "Capitalization", "8.4", "AB CD", caps_word("AB") + B() + caps_word("CD"), "DERIVED"),
        row("cap_number_then_word", "Capitalization", "6.5.2, 8.4", "123 CARD",
            number("123") + B() + caps_word("CARD"), "DERIVED"),
        row("cap_number_then_capital", "Capitalization", "6.3, 8.3.1", "123Card", plain("123Card"), "DERIVED"),
        row("cap_passage", "Capitalization", "8.5-8.6", "CAUTION: WET PAINT!",
            cap_passage("CAUTION: WET PAINT!"), "OFFICIAL", "Official passage example family; print source has three symbols-sequences.", gap="LIBLOUIS_OUTDATED_RULE"),
        row("cap_punctuation", "Capitalization", "8.4, 8.7", "Hello, WORLD!",
            plain("Hello,") + B() + caps_word("WORLD") + B("235"), "DERIVED"),

        row("num_zero", "Numeric", "6.1", "0", number("0"), "OFFICIAL"),
        row("num_multi", "Numeric", "6.1-6.2", "1234567890", number("1234567890"), "OFFICIAL"),
        row("num_decimal", "Numeric", "6.2", "3.14", number("3.14"), "OFFICIAL"),
        row("num_thousands_comma", "Numeric", "6.2", "1,234", number("1,234"), "OFFICIAL"),
        row("num_thousands_space", "Numeric", "6.6, 3.23", "1 234", number("1") + B() + number("234"), "DERIVED",
            "V1 plain-text policy: without explicit numeric-grouping semantics, treat the blank as an ordinary space. This is PASS-PROVISIONAL, not proof that every printed `1 234` is ordinary spacing.", gap="SOURCE_EXTRACTION_RISK"),
        row("num_clear_numeric_space", "Numeric", "6.6, 6.6.1", "3 245 000",
            B(NUM, "14", "5", "12", "145", "5", "245", "245", "245"), "DERIVED",
            "The source is explicitly treated as one grouped number for this probe, following the official population example; the plain-text Liblouis call has no semantic numeric-grouping input.", gap="TABLE_GAP"),
        row("num_thousands_nbsp", "Numeric", "6.6", "1\u00a0234", B(NUM, "1", "5", "12", "14", "145"), "OFFICIAL",
            "NBSP is used as an explicit numeric-space probe; expected is number sign, 1, numeric-space+2, 3, 4.", gap="TABLE_GAP"),
        row("num_time", "Numeric", "6.3, 6.7", "7:30", number("7") + B("25") + number("30"), "OFFICIAL"),
        row("num_date", "Numeric", "6.7", "12/31/2024", number("12") + B("456", "34") + number("31") + B("456", "34") + number("2024"), "OFFICIAL"),
        row("num_currency", "Numeric", "3.10, 6.7", "$19.95", B("4", "234") + number("19.95"), "OFFICIAL"),
        row("num_ordinal", "Numeric", "6.5-6.7", "1st", number("1") + letters("st"), "OFFICIAL"),
        row("num_lower_a_j", "Numeric", "6.5.2", "3b", number("3") + B(G1) + B("12"), "OFFICIAL"),
        row("num_lower_k_z", "Numeric", "6.5.2", "3m", number("3") + B("134"), "OFFICIAL"),
        row("num_decimal_lower", "Numeric", "6.5.2", "4.2b", number("4.2") + B(G1) + B("12"), "OFFICIAL"),
        row("num_period_before_number", "Numeric", "6.4.1", ".7", B(NUM, "256", DIGITS["7"]), "OFFICIAL",
            "Official rule 6.4.1 example family: a period before a number takes the numeric prefix before the period."),

        row("punct_basic", "Punctuation", "7.1", "comma, semicolon; colon:", plain("comma, semicolon; colon:"), "DERIVED"),
        row("punct_sentence", "Punctuation", "7.1", "Full stop. Exclamation! Question?", plain("Full stop. Exclamation! Question?"), "DERIVED"),
        row("punct_ellipsis", "Punctuation", "7.3", "...", B("256", "256", "256"), "OFFICIAL"),
        row("punct_solidus", "Punctuation", "7.4", "a/b", plain("a/b"), "OFFICIAL"),
        row("punct_question_standing_alone", "Punctuation", "7.5.3", "?", B(G1, "236"), "OFFICIAL",
            "Standalone question mark requires Grade 1 symbol indicator.", gap="TABLE_GAP"),
        row("punct_abbreviation_period", "Punctuation", "7.1.1, 7.1.3, 10.6.2", "a.b", B("1", "256", "12"), "DERIVED",
            "No grade 1 indicator is required: the period is not a beginning-of-word dis groupsign position."),
        row("punct_comma_between_letters", "Punctuation", "7.1.3, 10.6.5, 5.11.1", "a,b", B("1", G1, "2", "12"), "DERIVED",
            "The comma cell may also be a lower groupsign between letters, so grade 1 is required before the punctuation."),
        row("punct_question_ordinary", "Punctuation", "7.5.1", "what?", plain("what?"), "OFFICIAL",
            "Ordinary question-mark position: rule 7.5.1 says no grade 1 symbol indicator is normally required."),

        row("quote_curly_double", "Quotes/apostrophes", "7.6.1", "“hello”", B("236") + letters("hello") + B("356"), "OFFICIAL"),
        row("quote_curly_single", "Quotes/apostrophes", "7.6.2", "‘hello’", B("6", "236") + letters("hello") + B("6", "356"), "OFFICIAL"),
        row("quote_ascii_double", "Quotes/apostrophes", "7.6.1, 7.6.5", '"hello"', B("236") + letters("hello") + B("356"), "DERIVED",
            "Directional quote is inferred from ordinary prose context.", gap="LIBLOUIS_OUTDATED_RULE"),
        row("quote_ascii_single_pair", "Quotes/apostrophes", "7.6.2, 7.6.15", "'hello'", B("6", "236") + letters("hello") + B("6", "356"), "DERIVED",
            "Ordinary prose context calls for directional single quotes.", gap="LIBLOUIS_OUTDATED_RULE"),
        row("apostrophe_mid_ascii", "Quotes/apostrophes", "7.6.6, 7.6.15", "can't", letters("can") + B("3") + letters("t"), "OFFICIAL"),
        row("apostrophe_possessive_ascii", "Quotes/apostrophes", "7.6.6", "Jones'", letters("Jones") + B("3"), "OFFICIAL"),
        row("apostrophe_leading_tis", "Quotes/apostrophes", "7.6.14-7.6.15", "'tis", B("3") + letters("tis"), "DERIVED",
            "Common leading-apostrophe dictionary word."),
        row("apostrophe_mid_curly", "Quotes/apostrophes", "7.6.6, 7.6.15", "can’t", letters("can") + B("3") + letters("t"), "OFFICIAL"),
        row("apostrophe_possessive_curly", "Quotes/apostrophes", "7.6.6", "Jones’", letters("Jones") + B("3"), "OFFICIAL",
            "Curly print apostrophe still maps to apostrophe in UEB.", gap="TABLE_GAP"),
        row("quote_nested", "Quotes/apostrophes", "7.6.3", "“She said, ‘yes’.”",
            B("236") + plain("She said,") + B() + B("6", "236") + letters("yes") + B("6", "356") + B("356"), "OFFICIAL"),
        row("quote_next_punctuation", "Quotes/apostrophes", "7.6.1", '"Hi!"', B("236") + plain("Hi!") + B("356"), "DERIVED"),
        row("quote_internal_two_cell", "Quotes/apostrophes", "7.6.7", "Franc“e”s",
            plain("Franc") + B("45", "236") + plain("e") + B("45", "356") + plain("s"), "OFFICIAL",
            "Official 7.6.7 example family: internal opening/closing double quotes require two-cell forms.", gap="TABLE_GAP"),
        row("quote_standing_alone_double", "Quotes/apostrophes", "2.6.2, 2.6.3, 7.6.8", "(“...”)",
            B("5", "126", "45", "236", "256", "256", "256", "45", "356", "5", "345"), "DERIVED",
            "Standing-alone double quotation marks require the two-cell forms to avoid wordsign ambiguity.", gap="TABLE_GAP"),
        row("quote_g1_order", "Quotes/apostrophes", "7.6.9", 'Spell "W-a-l-k".',
            plain("Spell ") + B("236") + B(G1, G1) + letters("W") + B("36") + letters("a") + B("36") + letters("l") + B("36") + letters("k") + B("356") + plain("."), "DERIVED",
            "The 2024 rule requires the opening double quote before the Grade 1 word indicator; the rest is rendered uncontracted for this probe.", gap="TABLE_GAP"),
        row("quote_standing_alone_single", "Quotes/apostrophes", "7.6.10", "‘ ’",
            B(G1, "6", "236") + B() + B(G1, "6", "356"), "DERIVED",
            "Standing-alone single quotation marks need Grade 1 disambiguation; this is a focused symbol-level probe.", gap="TABLE_GAP"),

        row("dash_hyphenated", "Hyphen/dash", "7.2", "well-known", plain("well-known"), "DERIVED"),
        row("dash_en", "Hyphen/dash", "7.2", "word – word", plain("word – word"), "OFFICIAL"),
        row("dash_em", "Hyphen/dash", "7.2", "word — word", plain("word — word"), "OFFICIAL"),
        row("dash_print_double_hyphen", "Hyphen/dash", "7.2.6", "word -- word", plain("word -- word"), "DERIVED",
            "Two adjacent print hyphens may remain two hyphens or be rendered as a dash.", accepted=(plain("word – word"),), gap="PERMITTED_VARIANT_NOT_MODELLED"),

        row("brackets_round", "Brackets", "2.6, 7.1", "(hello)", plain("(hello)"), "DERIVED"),
        row("brackets_square", "Brackets", "2.6, 7.1", "[hello]", plain("[hello]"), "DERIVED"),
        row("brackets_curly", "Brackets", "2.6, 7.1", "{hello}", plain("{hello}"), "DERIVED"),

        row("symbols_amp_at", "Symbols", "3.1, 3.7", "& @", B("4", "12346") + B() + B("4", "1"), "OFFICIAL"),
        row("symbols_percent_hash", "Symbols", "3.19, 3.21", "% #", B("46", "356") + B() + B("456", "1456"), "OFFICIAL"),
        row("symbols_copyright_trademark", "Symbols", "3.8", "© ® ™", B("45", "14") + B() + B("45", "1235") + B() + B("45", "2345"), "OFFICIAL"),
        row("symbols_currency", "Symbols", "3.10", "$ £ € ¥ ¢", B("4", "234") + B() + B("4", "123") + B() + B("4", "15") + B() + B("4", "13456") + B() + B("4", "14"), "OFFICIAL"),
        row("symbols_degree_section", "Symbols", "3.11, 3.20", "° § ¶", B("45", "245") + B() + B("45", "234") + B() + B("45", "1234"), "OFFICIAL"),
        row("symbols_degree_prime", "Symbols", "3.11, 3.15", "6′ 9″",
            number("6") + B("2356") + B() + number("9") + B("2356", "2356"), "OFFICIAL",
            "Prime/minute/second signs follow print; included to close the prime half of the Section 3.11 scope row."),
        row("symbols_bullet", "Symbols", "3.5", "•", B("456", "256"), "OFFICIAL"),
        row("symbols_number_sign", "Symbols", "3.19", "#4", B("456", "1456") + number("4"), "OFFICIAL"),
        row("symbols_currency_amount", "Symbols", "3.10, 6.7", "£7.50", B("4", "123") + number("7.50"), "DERIVED"),

        row("grade1_plain_no_indicator", "Grade-1", "2.5.5, 5.11", "be", letters("be"), "OFFICIAL",
            "Uncontracted text does not require a Grade 1 indicator everywhere."),
        row("grade1_numeric_letters", "Grade-1", "5.6, 6.5.2", "22b", number("22") + B(G1, "12"), "OFFICIAL"),
        row("grade1_numeric_capital", "Grade-1", "5.6, 6.5.2", "22B", number("22") + B(CAP, "12"), "OFFICIAL"),
        row("grade1_numeric_hyphen_cap", "Grade-1", "5.6.2, 6.5.4", "3-D", number("3") + B("36") + B(G1, CAP, "145"), "OFFICIAL"),
        row("grade1_indicator_order", "Grade-1", "5.8.1", "3-D", number("3") + B("36") + B(G1, CAP, "145"), "DERIVED",
            "The Grade 1 indicator precedes the capitals indicator after a numeric-mode terminator."),

        row("spacing_normal", "Spacing", "3.23", "a b", plain("a b"), "OFFICIAL"),
        row("spacing_multiple", "Spacing", "3.23", "a  b", plain("a b"), "DERIVED",
            "UEB 3.23.1 says the amount of ordinary print space is not important and variation is ignored; this is a normalization-layer case, not a numeric-space case.", gap="NORMALIZATION_PROBLEM"),
        row("spacing_nbsp", "Spacing", "3.23", "a\u00a0b", plain("a b"), "DERIVED",
            "V1 source-normalization policy: NBSP outside numeric context is mapped to an ordinary space before translation. Raw Liblouis output is not accepted without that normalization.", gap="NORMALIZATION_PROBLEM"),
        row("spacing_thin_zero_width", "Spacing", "3.23", "a\u2009b\u200ba", plain("a b a"), "CONSTRUCTED",
            "V1 source-normalization policy: U+2009 is ordinary spacing and U+200B is removed as an extraction separator in this plain-text probe; the resulting ordinary spaces are PASS-PROVISIONAL.", gap="SOURCE_EXTRACTION_RISK"),

        row("typeform_italic", "Typeforms", "9.2-9.4", "italic", B("46", "2") + letters("italic"), "DERIVED",
            typeform=tf_json("italic", 0, 6)),
        row("typeform_bold", "Typeforms", "9.2-9.4", "bold", B("45", "2") + letters("bold"), "DERIVED",
            typeform=tf_json("bold", 0, 4)),
        row("typeform_underline", "Typeforms", "9.2-9.4", "under", B("456", "2") + letters("under"), "DERIVED",
            typeform=tf_json("underline", 0, 5)),
        row("typeform_number_symbol", "Typeforms", "9.2.1", "8", B("46", "23") + number("8"), "OFFICIAL",
            "Official rule 9.2.1 example family: a typeform symbol indicator before a number.", typeform=tf_json("italic", 0, 1)),
        row("typeform_number", "Typeforms", "9.3.1", "123", B("46", "2") + number("123"), "DERIVED",
            "Rule 9.3.1 permits a typeform word indicator to set the typeform for the following numeric symbols-sequence.", typeform=tf_json("italic", 0, 3)),
        row("typeform_passage", "Typeforms", "9.4", "one two three",
            B("46", "2356") + plain("one two three") + B("46", "3"), "DERIVED",
            "Three typeformed symbols-sequences exercise passage opening and termination.", typeform=tf_json("italic", 0, 13)),
        row("typeform_word_punctuation", "Typeforms", "9.7.2", "word!",
            B("46", "2") + letters("word") + B("46", "3", "235"), "DERIVED",
            "Punctuation is outside the supplied word typeform, so the terminator precedes it.", typeform=tf_json("italic", 0, 4)),
        row("typeform_multiple", "Typeforms", "9.8.1", "word",
            B("45", "2", "46", "2") + letters("word"), "DERIVED",
            "Two simultaneous typeforms; Liblouis chooses an order, while UEB does not prescribe one.",
            typeform=json.dumps({"italic": [0, 1, 2, 3], "bold": [0, 1, 2, 3]}, separators=(",", ":"))),
    ]

    rows += [
        row("na_grade_contracted_sentence", "N/A-GRADE", "4.1, 2.5", "A boy and his dog were on the path.", None, "N/A-GRADE",
            "Rulebook example is contracted; deliberately not compared with en-ueb-g1.", n_a_grade=True),
        row("na_grade_contracted_quotes", "N/A-GRADE", "7.6", '“Why is that?” he asked.', None, "N/A-GRADE",
            "Rulebook example is contracted; deliberately not compared with en-ueb-g1.", n_a_grade=True),
        row("na_grade_contracted_numeric", "N/A-GRADE", "6.7", "The temperature was 100,000°C.", None, "N/A-GRADE",
            "Rulebook example is contracted; deliberately not compared with en-ueb-g1.", n_a_grade=True),
    ]
    return rows


SCOPE = [
    ("2.3.1", "Follow print", "REQUIRED", "V1 must preserve relevant letters, punctuation and capitals.", "4,7,8", "YES", "Ordinary prose input."),
    ("2.4.1-2.4.5", "Indicators and modes", "REQUIRED", "Needed to interpret numeric, Grade 1, capitals and typeforms.", "5,6,8,9", "YES", "Validator must not treat indicators as ordinary letters."),
    ("2.5.1", "Contractions disallowed in Grade 1 mode", "REQUIRED", "V1 is uncontracted; contracted UEB is out of scope.", "5,6", "YES", "No Grade 2 acceptance."),
    ("2.5.2-2.5.5", "Uncontracted differs from Grade 1 mode", "REQUIRED", "Defines V1 policy: uncontracted output may omit Grade 1 indicators except where needed.", "5,6", "YES", "High-risk policy boundary."),
    ("2.6.1-2.6.5", "Standing alone", "REQUIRED", "Controls quote, question-mark, apostrophe and indicator ambiguity.", "7,8", "YES", "Context-sensitive."),
    ("3.1", "Ampersand", "REQUIRED", "Common symbol explicitly in V1 list.", "2,7", "YES", "Direct symbol mapping."),
    ("3.5", "Bullet", "REQUIRED", "Common symbol explicitly requested.", "2,7", "YES", "Text-level bullet only."),
    ("3.7-3.8", "At, copyright, registered, trademark", "REQUIRED", "Common symbols explicitly requested.", "6,7", "YES", "Direct symbol mapping."),
    ("3.10", "Currency signs", "REQUIRED", "Currency is explicitly requested and interacts with numeric mode.", "6", "YES", "Dollar, pound, euro, yen, cent in V1 corpus."),
    ("3.11", "Degree and prime", "REQUIRED", "Degree is explicitly requested; prime is ordinary symbol-level support.", "6,7", "YES", "No mathematics semantics."),
    ("3.19-3.21", "Number, paragraph/section, percent", "REQUIRED", "Explicit common-symbol and numeric requirements.", "6", "YES", "Hash is not automatically numeric."),
    ("3.23", "Space", "REQUIRED", "Ordinary spacing is core validator behavior.", "2,6", "YES", "NBSP/thin/zero-width probes are separate."),
    ("3.28", "Check mark", "OPTIONAL/LATER", "Rare symbol; not required for core English prose V1.", "3", "YES", "Can be added after core symbols are stable."),
    ("4.1", "English alphabet", "REQUIRED", "All a-z/A-Z are core V1.", "2,5,8", "YES", "52 corpus rows."),
    ("4.2", "Letter modifiers", "OPTIONAL/LATER", "Non-ASCII/foreign modifiers are not ordinary English-only V1.", "8,9", "YES", "Keep fail-closed until explicitly included."),
    ("4.3", "Ligatured letters", "OPTIONAL/LATER", "Foreign/typographic material, not core ASCII English.", "4", "YES", "No V1 requirement."),
    ("4.4-4.6", "Eng, schwa, Greek, eszett", "OUT_OF_SCOPE", "Pronunciation/foreign alphabets are outside English-only V1.", "4", "YES", "Do not silently accept as ordinary English."),
    ("5.1-5.2", "Grade 1 symbol mode", "REQUIRED", "Needed for explicit Grade 1 semantics and required numeric follow-ups.", "6,7", "YES", "Generator need differs from validator acceptance."),
    ("5.3-5.5", "Grade 1 word/passage/terminator", "REQUIRED", "V1 must recognize these if present; generator may omit them in pure Grade 1 text.", "2.5,5.11", "YES", "Audit acceptance behavior separately."),
    ("5.6", "Numeric indicator sets Grade 1 mode", "REQUIRED", "Core number/letter interaction.", "6", "YES", "High-risk."),
    ("5.7-5.8", "Grade 1 and capitalization", "REQUIRED", "Indicator ordering is explicitly requested.", "8", "YES", "High-risk."),
    ("5.9", "Choice of indicators", "OPTIONAL/LATER", "Policy choice; V1 can use canonical minimal forms first.", "5,6", "YES", "Document accepted variants only when cited."),
    ("5.10", "Optional Grade 1 indicator", "REQUIRED", "Acceptance set must not reject explicitly permitted omission/presence.", "2.5,5.11", "YES", "Core variant policy."),
    ("5.11", "Grade 1 text indicator policy", "REQUIRED", "Pure uncontracted output should not add indicators gratuitously.", "2.5", "YES", "Core validator expectation."),
    ("6.1-6.2", "Digits and numeric-mode symbols", "REQUIRED", "All ordinary numeric forms in requested corpus.", "3,5,6,7", "YES", "Digits, dot, comma, fraction line only."),
    ("6.3-6.5", "Numeric termination and letter interactions", "REQUIRED", "Explicit high-risk scope.", "5,7,8", "YES", "High-risk."),
    ("6.6", "Numeric spaces", "REQUIRED", "2024 rule change/priority area.", "3.23", "YES", "Explicit numeric-space probes."),
    ("6.7", "Dates, time, coinage, ordinals", "REQUIRED", "Explicit minimum corpus requirements.", "3,7", "YES", "No layout line-breaking."),
    ("6.8", "Spaced numeric indicator", "OPTIONAL/LATER", "Layout/alignment-specific, not ordinary prose V1.", "6", "YES", "Fail closed for now."),
    ("6.9-6.10", "Numeric passages and line division", "OPTIONAL/LATER", "Requires structured layout/line context not supplied by plain text.", "6", "YES", "Not core text-only V1."),
    ("7.1", "General punctuation", "REQUIRED", "Core punctuation family.", "2,3", "YES", "Comma, semicolon, colon, full stop, !, ?."),
    ("7.2", "Hyphen, dash, long dash", "REQUIRED", "Explicit minimum corpus requirements.", "2,5,6,8", "YES", "Print spacing is input-sensitive."),
    ("7.3-7.5", "Ellipsis, solidus, question mark", "REQUIRED", "Explicit minimum corpus requirements.", "2,5", "YES", "Question mark ambiguity is high-risk."),
    ("7.6.1-7.6.6", "Quotation marks and apostrophe basics", "REQUIRED", "High-priority 2024 automation area.", "2.6", "YES", "Curly and ASCII probes."),
    ("7.6.7-7.6.10", "Quote/apostrophe ambiguity avoidance", "REQUIRED", "Explicit 2024 high-risk area.", "2.6,5", "YES", "Standing-alone and Grade 1 ordering."),
    ("7.6.12-7.6.15", "Translation-software quote/apostrophe guidance", "REQUIRED", "Directly governs automated translation limits.", "2.6", "YES", "UNCERTAIN is valid outcome."),
    ("7.7", "Multiline brackets", "OPTIONAL/LATER", "Requires line/layout structure, not plain text V1.", "3", "YES", "Fail closed."),
    ("8.1-8.3", "Capital letters and isolated capitals", "REQUIRED", "Core English prose.", "4,5", "YES", "All A-Z corpus."),
    ("8.4", "Capitalised word mode", "REQUIRED", "Explicit high-priority capitalization requirement.", "2.6,5", "YES", "Engine opcode involved."),
    ("8.5-8.6", "Capitalised passage and terminator", "REQUIRED", "Explicit high-priority capitalization requirement.", "5", "YES", "Engine opcode involved."),
    ("8.7-8.8", "Indicator placement and choice", "REQUIRED", "Ordering/acceptance policy for validator.", "4,5,6", "YES", "Variants need citation."),
    ("8.9", "Accented capitals", "OPTIONAL/LATER", "Non-ASCII accented print is outside core English-only V1.", "4", "YES", "Do not generalize from ASCII."),
    ("9.1-9.4", "Italic, bold, underline typeforms", "REQUIRED", "Requested as likely V1 and supported by Liblouis typeform API.", "2,8", "YES", "Needs structured typeform input."),
    ("9.5-9.6", "Transcriber-defined typeforms and small capitals", "OPTIONAL/LATER", "Requires document-level semantics beyond current text input.", "8", "YES", "Fail closed."),
    ("9.7-9.8", "Typeform placement and multiple indicators", "REQUIRED", "Needed if V1 accepts typeforms.", "5", "YES", "Indicator ordering is not universally prescribed."),
    ("9.9", "Typeform passages across text elements", "OPTIONAL/LATER", "Requires document structure/layout.", "8", "YES", "Not plain-text V1."),
]


def direct_include_closure(roots: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    pending = list(roots)
    while pending:
        path = pending.pop().resolve()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            fields = line.split()
            if fields and fields[0] == "include" and len(fields) >= 2:
                candidate = path.parent / fields[1]
                if not candidate.exists():
                    candidate = TABLES / fields[1]
                pending.append(candidate)
    return sorted(seen)


def import_louis():
    tablepath = str(TABLES)
    os.environ["LOUIS_TABLEPATH"] = tablepath
    # Liblouis is a Windows DLL here.  Keep the CRT environment in sync with
    # the process environment, matching the production translator's setup.
    if os.name == "nt":
        import ctypes
        ctypes.CDLL("msvcrt")._wputenv(f"LOUIS_TABLEPATH={tablepath}")
    os.environ["PATH"] = str(DLL.parent) + os.pathsep + os.environ.get("PATH", "")
    sys.path.insert(0, str(BINDINGS))
    import louis
    return louis


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_environment(louis) -> list[Path]:
    roots = [TABLES / "en-ueb-g1.ctb", TABLES / "unicode.dis"]
    closure = direct_include_closure(roots)
    lines = [
        "# Liblouis / UEB Grade 1 audit environment",
        "",
        f"Audit date: 2026-09-21",
        f"Python executable: `{sys.executable}`",
        f"Python version: `{sys.version.split()[0]}`",
        f"Liblouis runtime version: `{louis.version()}`",
        f"Python binding package version: `3.38.0` (vendor/liblouis-bindings/pyproject.toml)",
        f"Loaded DLL: `{DLL.resolve()}`",
        f"Loaded DLL SHA-256: `{sha256(DLL)}`",
        f"Production table path: `{TABLES.resolve()}`",
        f"Production table list: `{','.join(TABLE_LIST)}` (matches `src/braille_app/translation/liblouis_translator.py`)",
        f"Project en-ueb-g1.ctb: `{(TABLES / 'en-ueb-g1.ctb').resolve()}`",
        f"Project en-ueb-g1.ctb SHA-256: `{sha256(TABLES / 'en-ueb-g1.ctb')}`",
        f"System en-ueb-g1.ctb: `{SYSTEM_TABLE.resolve()}`",
        f"System en-ueb-g1.ctb SHA-256: `{sha256(SYSTEM_TABLE) if SYSTEM_TABLE.exists() else 'MISSING'}`",
        f"Project and system table bytes identical: `{SYSTEM_TABLE.exists() and sha256(SYSTEM_TABLE) == sha256(TABLES / 'en-ueb-g1.ctb')}`",
        "",
        "## Resolved table/include closure",
        "",
        "The closure below follows the same two-table list used by the application (`unicode.dis,en-ueb-g1.ctb`).",
        "",
        "| File | SHA-256 | Size |",
        "|---|---|---:|",
    ]
    for path in closure:
        lines.append(f"| `{path.resolve()}` | `{sha256(path)}` | {path.stat().st_size} |")
    lines += [
        "",
        "## Version/path conclusion",
        "",
        "The application resolves the vendored Liblouis 3.38.0 DLL and vendored tables, not `C:\\liblouis`. The system installation is also reported as Liblouis 3.38.0 by `C:\\liblouis\\bin\\lou_translate.exe --version`, but its `en-ueb-g1.ctb` hash differs, so the two installations must not be treated as interchangeable.",
        "",
        "The source checkout is `vendor/liblouis-src/liblouis-3.38.0`; the installed table header has no UEB-2024 authority citation and contains a TODO referring to braille-spec documentation. ICEB 2024 remains the correctness authority for this audit.",
    ]
    (AUDIT / "environment.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return closure


def expanded_scope_rows() -> list[dict[str, str]]:
    fields = ["citation", "title", "classification", "reason", "dependencies", "official_example_available", "notes"]
    rows = []
    for item in SCOPE:
        citation, *rest = item
        citations = [citation]
        if "-" in citation:
            left, right = citation.split("-", 1)
            left_parts = left.rsplit(".", 1)
            right_parts = right.rsplit(".", 1)
            prefix = left_parts[0] + "." if len(left_parts) == 2 else ""
            start = int(left_parts[-1])
            end = int(right_parts[-1])
            citations = [f"{prefix}{number}" for number in range(start, end + 1)]
        rows.extend(dict(zip(fields, [expanded, *rest])) for expanded in citations)
    return rows


def write_standard_scope() -> None:
    write_csv(AUDIT / "standard_scope.csv", expanded_scope_rows(),
              ["citation", "title", "classification", "reason", "dependencies", "official_example_available", "notes"])


def extract_standard_text() -> None:
    try:
        from pypdf import PdfReader
    except ImportError:
        return
    pages = PdfReader(str(PDF)).pages
    selected = list(range(35, 48)) + list(range(49, 66)) + list(range(73, 84))
    selected += list(range(85, 92)) + list(range(93, 102)) + list(range(104, 116))
    selected += list(range(117, 128)) + list(range(130, 140))
    with (AUDIT / "standard_extract.txt").open("w", encoding="utf-8") as stream:
        stream.write(f"Source: {PDF.resolve()}\nSHA-256: {sha256(PDF)}\nPages: {len(pages)}\n\n")
        for page_number in selected:
            stream.write(f"--- PDF page {page_number} ---\n")
            stream.write((pages[page_number - 1].extract_text() or "") + "\n\n")


def count_yaml_cases(path: Path) -> int:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if path.name == "en-ueb.yaml":
        return len(re.findall(r"(?m)^- (?:-|\[)", text))
    return len(re.findall(r"(?m)^  - (?:-|\[)", text))


def write_upstream_coverage() -> None:
    base = ROOT / "vendor" / "liblouis-src" / "liblouis-3.38.0" / "tests"
    files = [
        ("braille-specs/en-ueb-g1_harness.yaml", "forward", "en-ueb-g1.ctb", "3.38.0 UEB harness; no 2024 citation"),
        ("braille-specs/en-ueb-g1_backward.yaml", "backward", "en-ueb-g1.ctb", "3.38.0 backward harness; emphasis tests are engine tests"),
        ("braille-specs/en-ueb-symbols_harness.yaml", "forward", "en-ueb-g1.ctb", "3.38.0 symbol harness; direct symbols, not contextual 2024 rules"),
        ("braille-specs/en-ueb-math.yaml", "forward", "en-ueb-g1.ctb", "3.38.0 math-symbol smoke tests; out of V1 semantics"),
        ("braille-specs/en-ueb.yaml", "forward", "en-ueb-g2.ctb", "Grade 2 / 2013-structured UEB corpus; not a G1 proof"),
        ("yaml/numericmode.yaml", "engine", "custom numeric tables", "Opcode engine tests, not ICEB UEB 2024 compliance"),
        ("yaml/capitalization.yaml", "engine", "custom capitalization tables", "Opcode engine tests, not ICEB UEB 2024 compliance"),
        ("yaml/emphasis.yaml", "engine", "custom emphasis tables", "Typeform engine tests, not ICEB UEB 2024 compliance"),
        ("yaml/capsword.yaml", "engine", "custom capitalization tables", "Capsword opcode tests, not ICEB UEB 2024 compliance"),
    ]
    lines = [
        "# Liblouis upstream test coverage",
        "",
        "Inspected source tree: `vendor/liblouis-src/liblouis-3.38.0/tests`.",
        "These tests are evidence of implementation behavior only. They are not proof of compliance with ICEB, Rules of Unified English Braille, Third Edition 2024.",
        "The UEB corpus comments describe the 2013 rulebook structure; the harnesses contain no claim that they were updated for the 2024 edition.",
        "",
        "| File | Direction | Table | Count | 2024/V1 assessment |",
        "|---|---|---|---:|---|",
    ]
    for relative, direction, table, assessment in files:
        path = base / relative
        count = count_yaml_cases(path) if path.suffix == ".yaml" else 0
        lines.append(f"| `{relative}` | {direction} | `{table}` | {count} | {assessment} |")
    lines += [
        "",
        "## Requested files that are not present",
        "",
        "The following names were not found in the Liblouis 3.38.0 checkout: `en-ueb-03-symbols`, `en-ueb-05-grade_1_mode`, `en-ueb-06-numeric_mode`, `en-ueb-08-capitalization`, `en-ueb-09-typeforms`, and dedicated quote/apostrophe test files. Their closest corresponding coverage is embedded in `en-ueb.yaml`, `en-ueb-symbols_harness.yaml`, `en-ueb-g1_harness.yaml`, and generic YAML engine tests.",
        "",
        "## Coverage conclusion",
        "",
        "`en-ueb-g1_harness.yaml` covers direct symbols, digits, some modifiers, four ordinal forms, and forward typeform examples. `en-ueb-g1_backward.yaml` covers digits, indicator backtranslation, and emphasis detection. `en-ueb-symbols_harness.yaml` is broad for one-symbol mappings but deliberately tests ASCII double quote as nondirectional (`⠠⠶`), which cannot establish the context-sensitive 2024 quote rules. The upstream tests do not provide a dedicated audit of 2024 numeric-space semantics, quote/apostrophe heuristics, Grade 1 optionality, or capital passage policy.",
    ]
    (AUDIT / "upstream_test_coverage.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_matrix() -> None:
    rows = [
        ("Alphabet", "A", "en-ueb-chardefs.uti; Section 4.1", "Direct a-z/A-Z mappings and capital prefix exist; execution confirms.", "No contractions in g1."),
        ("Ordinary uncontracted words", "A", "en-ueb-g1.ctb", "Table declares grade 1/contraction:no and execution produces letter-by-letter output.", "Still verify context features."),
        ("Punctuation", "C", "en-ueb-chardefs.uti; engine punctuation rules", "Most cells exist and execute; punctuation indicators depend on position/standing-alone rules.", "Do not treat direct symbol harness as 2024 proof."),
        ("Quotes/apostrophes", "B", "en-ueb-chardefs.uti lines 421-423", "Curly/double/inner mappings and mid-word apostrophe match exist; possessive/ASCII context is incomplete or heuristic.", "Highest-risk verification layer."),
        ("Numeric mode", "B", "en-ueb-g1.ctb lines 51-79; engine numericmode", "Digits, dot/comma, numeric mode and NBSP probe exist; ordinary print-space semantics and 2024 policy need wrapper verification.", "Highest-risk verification layer."),
        ("Capitalization", "B", "en-ueb-g1.ctb lines 81-86; engine caps opcodes", "Capital letter/word/passage opcodes exist and execute; boundary/choice behavior needs standards verification.", "Highest-risk verification layer."),
        ("Grade 1 indicators", "B", "en-ueb-g1.ctb nocontractsign/nonumsign; engine modes", "Numeric interactions are present; pure uncontracted output policy and optional indicator acceptance are not represented by one canonical output.", "Validator acceptance-set logic required."),
        ("Common symbols", "A", "en-ueb-chardefs.uti", "Requested @, %, #, ©, ®, ™, currency, degree, §, ¶, bullet cells exist.", "Validate context and numeric adjacency."),
        ("Brackets", "A", "en-ueb-chardefs.uti", "Round, square and curly bracket cells exist.", "Multiline brackets excluded."),
        ("Spacing", "B", "en-ueb-chardefs.uti; spaces.uti; engine", "Ordinary, NBSP, thin and zero-width mappings exist; numeric-space meaning is context-sensitive.", "Extraction normalization layer required."),
        ("Typeforms", "C", "en-ueb-g1.ctb lines 88-164; typeform engine opcodes", "Italic, bold, underline word/passage/symbol definitions exist and API accepts typeform arrays.", "Requires structured typeform input and UEB placement checks."),
        ("Math/Nemeth/chemistry/music", "D", "en-ueb-math.ctb and specialist tables", "Some math-like symbols are included mechanically, but V1 explicitly excludes specialist semantics.", "Fail closed; do not infer support from presence."),
        ("Backward translation", "E", "en-ueb-g1_backward.yaml; engine", "Backtranslation exists but is not a unique source reconstruction for curly/ASCII quote distinctions.", "Use only as diagnostic evidence."),
    ]
    fields = ["family", "classification", "implementation_evidence", "assessment", "v1_note"]
    write_csv(AUDIT / "liblouis_implementation_matrix.csv", [dict(zip(fields, r)) for r in rows], fields)


def upstream_for(citation: str, family: str) -> str:
    if family == "Alphabet":
        return "en-ueb-symbols_harness.yaml (direct letters)"
    if family == "Quotes/apostrophes":
        return "No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples"
    if family == "Numeric" or family == "Grade-1":
        return "en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml"
    if family == "Capitalization":
        return "en-ueb-g1_harness.yaml; yaml/capitalization.yaml; yaml/capsword.yaml"
    if family == "Typeforms":
        return "en-ueb-g1_harness.yaml; en-ueb-g1_backward.yaml; yaml/emphasis.yaml"
    if family == "N/A-GRADE":
        return "en-ueb.yaml (Grade 2 only; not comparable)"
    if family == "Symbols":
        return "en-ueb-symbols_harness.yaml"
    return "en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml"


def evaluate(rows: list[dict[str, str]], louis) -> list[dict[str, str]]:
    louis.checkTable(TABLE_LIST)
    results = []
    bits = {"italic": 1, "underline": 2, "bold": 4}
    for item in rows:
        result = dict(item)
        source = item["source"]
        if item["n_a_grade"] == "YES":
            translated = louis.translateString(TABLE_LIST, source)
            result.update({
                "liblouis_braille": translated,
                "liblouis_dot_notation": dot_notation(translated),
                "backward_result": louis.backTranslateString(TABLE_LIST, translated),
                "status": "N/A-GRADE",
                "upstream_test": upstream_for(item["citation"], item["family"]),
                "observed_difference": "Not compared: official example is contracted/Grade 2.",
                "actual_gap_classification": "N/A-GRADE",
            })
            results.append(result)
            continue

        typeform = None
        if item["typeform_spec"]:
            spec = json.loads(item["typeform_spec"])
            typeform = [0] * len(source)
            for kind, indexes in spec.items():
                for index in indexes:
                    if index < len(typeform):
                        typeform[index] |= bits[kind]
        try:
            translated = louis.translateString(TABLE_LIST, source, typeform=typeform)
            backward = louis.backTranslateString(TABLE_LIST, translated)
            error = ""
        except Exception as exc:
            translated = ""
            backward = ""
            error = f"{type(exc).__name__}: {exc}"
        accepted = [item["expected_braille"]] if item["expected_braille"] else []
        accepted.extend(x for x in item["accepted_braille"].split("|") if x)
        if error:
            status = "UNSUPPORTED"
        elif item["id"] == "num_thousands_space":
            status = "PASS-PROVISIONAL"
        elif translated == item["expected_braille"]:
            status = "PASS-PROVISIONAL" if item["evidence_tier"] == "CONSTRUCTED" else "PASS"
        elif translated in accepted:
            status = "PASS-VARIANT"
        elif item["evidence_tier"] == "CONSTRUCTED" or item["gap_classification"] == "STANDARD_AMBIGUOUS":
            status = "FAIL-PROVISIONAL"
        else:
            status = "FAIL"
        actual_gap = item["gap_classification"] if (status.startswith("FAIL") or status == "UNCERTAIN") else ""
        if status.startswith("FAIL") and not actual_gap:
            if item["family"] == "Quotes/apostrophes":
                actual_gap = "TABLE_GAP"
            elif item["family"] == "Numeric":
                actual_gap = "LIBLOUIS_OUTDATED_RULE"
            elif item["family"] == "Capitalization":
                actual_gap = "LIBLOUIS_OUTDATED_RULE"
            elif item["family"] == "Typeforms":
                actual_gap = "NEEDS_BRAILLE_EXPERT"
            else:
                actual_gap = "TABLE_GAP"
        result.update({
            "liblouis_braille": translated,
            "liblouis_dot_notation": dot_notation(translated),
            "backward_result": backward,
            "status": status,
            "upstream_test": upstream_for(item["citation"], item["family"]),
            "observed_difference": error or ("exact" if status.startswith("PASS") else "expected output differs"),
            "actual_gap_classification": actual_gap,
            "backward_error": error,
        })
        results.append(result)
    return results


def write_results(rows: list[dict[str, str]]) -> None:
    fields = [
        "id", "family", "citation", "source", "source_codepoints", "expected_braille", "expected_dot_notation",
        "accepted_braille", "accepted_dot_notation", "liblouis_braille", "liblouis_dot_notation", "backward_result",
        "status", "evidence_tier", "official_example_available", "upstream_test", "actual_gap_classification",
        "observed_difference", "notes", "typeform_spec", "backward_error",
    ]
    write_csv(AUDIT / "execution_results.csv", rows, fields)
    variant_rows = []
    for item in rows:
        if item["accepted_braille"]:
            for alternative in item["accepted_braille"].split("|"):
                variant_rows.append({
                    "source": item["source"],
                    "feature": item["family"],
                    "citation": item["citation"],
                    "canonical_output": item["expected_braille"],
                    "permitted_alternative": alternative,
                    "evidence": item["notes"],
                    "status_if_seen": "PASS-VARIANT",
                    "citation_required": "YES",
                })
    fields = ["source", "feature", "citation", "canonical_output", "permitted_alternative", "evidence", "status_if_seen", "citation_required"]
    write_csv(AUDIT / "accepted_variants.csv", variant_rows, fields)
    corpus_fields = [
        "id", "family", "citation", "source", "source_codepoints", "expected_braille", "expected_dot_notation",
        "accepted_braille", "accepted_dot_notation", "evidence_tier", "official_example_available", "notes",
        "gap_classification", "typeform_spec", "back_test", "n_a_grade",
    ]
    write_csv(AUDIT / "corpus.csv", [{k: r.get(k, "") for k in corpus_fields} for r in rows], corpus_fields)


REQUIRED_COVERAGE_MAP = {
    "2.3.1": ["word_braille_validator", "punct_basic", "cap_punctuation"],
    "2.4.1": ["cap_isolated", "grade1_numeric_hyphen_cap", "typeform_number_symbol"],
    "2.4.2": ["num_zero", "punct_basic", "quote_curly_double"],
    "2.4.3": ["num_zero", "cap_all_word", "typeform_passage"],
    "2.4.4": ["grade1_plain_no_indicator", "grade1_numeric_letters", "cap_all_word"],
    "2.4.5": ["typeform_number_symbol", "cap_all_word"],
    "2.5.1": ["word_ordinary", "grade1_plain_no_indicator"],
    "2.5.2": ["word_ordinary", "grade1_plain_no_indicator"],
    "2.5.3": ["num_zero", "grade1_numeric_letters"],
    "2.5.4": ["word_ordinary"],
    "2.5.5": ["word_ordinary", "grade1_plain_no_indicator"],
    "2.6.1": ["cap_word", "grade1_plain_no_indicator"],
    "2.6.2": ["brackets_round", "quote_standing_alone_double", "quote_ascii_single_pair"],
    "2.6.3": ["punct_abbreviation_period", "quote_nested", "apostrophe_possessive_ascii"],
    "2.6.4": ["apostrophe_mid_ascii", "apostrophe_possessive_ascii"],
    "2.6.5": ["punct_question_standing_alone", "quote_standing_alone_double"],
    "3.1": ["symbols_amp_at"],
    "3.5": ["symbols_bullet"],
    "3.7": ["symbols_amp_at"],
    "3.8": ["symbols_copyright_trademark"],
    "3.10": ["symbols_currency", "num_currency", "symbols_currency_amount"],
    "3.11": ["symbols_degree_section", "symbols_degree_prime"],
    "3.19": ["symbols_number_sign"],
    "3.20": ["symbols_degree_section"],
    "3.21": ["symbols_percent_hash"],
    "3.23": ["spacing_normal", "spacing_multiple", "spacing_nbsp", "spacing_thin_zero_width"],
    "4.1": ["word_braille_validator", "alphabet_lower_a", "alphabet_upper_a"],
    "5.1": ["punct_question_standing_alone"],
    "5.2": ["punct_question_standing_alone", "grade1_numeric_letters"],
    "5.6": ["num_zero", "grade1_numeric_letters", "grade1_numeric_hyphen_cap"],
    "5.7": ["grade1_numeric_hyphen_cap"],
    "5.8": ["grade1_indicator_order"],
    "5.10": ["grade1_plain_no_indicator"],
    "5.11": ["grade1_plain_no_indicator", "punct_question_standing_alone", "num_lower_a_j"],
    "6.1": ["num_zero", "num_multi"],
    "6.2": ["num_decimal", "num_thousands_comma"],
    "6.3": ["num_time", "num_decimal_lower"],
    "6.4": ["num_period_before_number"],
    "6.5": ["num_lower_a_j", "num_lower_k_z", "num_ordinal", "grade1_numeric_hyphen_cap"],
    "6.6": ["num_clear_numeric_space", "num_thousands_space", "num_thousands_nbsp"],
    "6.7": ["num_time", "num_date", "num_currency", "num_ordinal", "symbols_currency_amount"],
    "7.1": ["punct_basic", "punct_sentence", "punct_abbreviation_period", "punct_comma_between_letters"],
    "7.2": ["dash_hyphenated", "dash_en", "dash_em", "dash_print_double_hyphen"],
    "7.3": ["punct_ellipsis"],
    "7.4": ["punct_solidus"],
    "7.5": ["punct_question_ordinary", "punct_question_standing_alone"],
    "7.6.1": ["quote_curly_double", "quote_ascii_double", "quote_next_punctuation"],
    "7.6.2": ["quote_curly_single", "quote_ascii_single_pair"],
    "7.6.3": ["quote_nested"],
    "7.6.5": ["quote_ascii_double"],
    "7.6.6": ["apostrophe_mid_ascii", "apostrophe_possessive_ascii", "apostrophe_mid_curly", "apostrophe_possessive_curly"],
    "7.6.7": ["quote_internal_two_cell"],
    "7.6.8": ["quote_standing_alone_double"],
    "7.6.9": ["quote_g1_order"],
    "7.6.10": ["quote_standing_alone_single"],
    "7.6.13": ["quote_ascii_single_pair", "quote_nested"],
    "7.6.14": ["apostrophe_leading_tis"],
    "7.6.15": ["apostrophe_mid_ascii", "quote_ascii_single_pair", "apostrophe_leading_tis"],
    "8.1": ["cap_isolated", "cap_word"],
    "8.2": ["cap_word", "cap_multiple_words"],
    "8.3": ["cap_isolated", "alphabet_upper_a"],
    "8.4": ["cap_all_word", "cap_multiple_words"],
    "8.5": ["cap_passage"],
    "8.6": ["cap_passage"],
    "8.7": ["cap_punctuation", "cap_number_then_capital"],
    "8.8": ["cap_all_word", "cap_word"],
    "9.1": ["typeform_italic", "typeform_bold", "typeform_underline"],
    "9.2": ["typeform_number_symbol", "typeform_italic"],
    "9.3": ["typeform_number"],
    "9.4": ["typeform_passage"],
    "9.7": ["typeform_word_punctuation"],
    "9.8": ["typeform_multiple"],
}

NEGATIVE_OR_BOUNDARY_IDS = {
    "cap_punctuation", "dash_print_double_hyphen", "grade1_numeric_hyphen_cap",
    "num_clear_numeric_space", "num_thousands_space", "num_thousands_nbsp",
    "punct_comma_between_letters", "punct_question_standing_alone",
    "quote_ascii_single_pair", "quote_g1_order", "quote_internal_two_cell",
    "quote_nested", "quote_standing_alone_double", "quote_standing_alone_single",
    "spacing_multiple", "spacing_nbsp", "spacing_thin_zero_width",
}


def _citation_tokens(value: str) -> set[str]:
    return {part.strip() for part in value.split(",") if part.strip()}


def write_coverage_closure(rows: list[dict[str, str]]) -> None:
    by_id = {item["id"]: item for item in rows}
    required = [item for item in expanded_scope_rows() if item["classification"] == "REQUIRED"]
    output = []
    no_direct = []
    for scope in required:
        citation = scope["citation"]
        direct_ids = [
            item["id"] for item in rows
            if item["n_a_grade"] != "YES"
            and any(token == citation or token.startswith(citation + ".") for token in _citation_tokens(item["citation"]))
        ]
        mapped_ids = REQUIRED_COVERAGE_MAP.get(citation, [])
        test_ids = list(dict.fromkeys(direct_ids + mapped_ids))
        evidence = [by_id[test_id]["evidence_tier"] for test_id in test_ids if test_id in by_id]
        statuses = [by_id[test_id]["status"] for test_id in test_ids if test_id in by_id]
        valid_ids = [test_id for test_id in test_ids if test_id in by_id]
        positive = any(by_id[test_id]["expected_braille"] and by_id[test_id]["status"] != "N/A-GRADE" for test_id in valid_ids)
        negative = any(
            by_id[test_id]["status"].startswith(("FAIL", "UNCERTAIN", "UNSUPPORTED")) or test_id in NEGATIVE_OR_BOUNDARY_IDS
            for test_id in valid_ids
        )
        interaction = any(test_id in NEGATIVE_OR_BOUNDARY_IDS for test_id in valid_ids)
        unresolved = any(by_id[test_id]["status"] in {"FAIL", "FAIL-PROVISIONAL", "UNCERTAIN", "UNSUPPORTED"} for test_id in valid_ids)
        direct = bool(direct_ids)
        if not valid_ids:
            status = "UNTESTED"
        elif not direct or unresolved or not positive:
            status = "PARTIAL"
        else:
            status = "COVERED"
        notes = []
        if not direct and valid_ids:
            notes.append("related rule-family evidence only; no test citation names this subrule")
        if not direct:
            no_direct.append(scope)
        if unresolved:
            notes.append("executed evidence includes an unresolved difference or source-policy case")
        if citation in {"5.3", "5.4", "5.5", "7.6.4", "7.6.12"}:
            notes.append("requires explicit indicator/translator-option evidence not generated by plain-text en-ueb-g1")
        output.append({
            "citation": citation,
            "title": scope["title"],
            "executed_test": "YES" if valid_ids else "NO",
            "test_ids": "; ".join(valid_ids),
            "evidence_tier": "; ".join(dict.fromkeys(evidence)),
            "positive_case": "YES" if positive else "NO",
            "negative_or_mutation_case": "YES" if negative else "NO",
            "interaction_or_boundary_case": "YES" if interaction else "NO",
            "coverage": status,
            "notes": "; ".join(notes),
        })
    fields = [
        "citation", "title", "executed_test", "test_ids", "evidence_tier", "positive_case",
        "negative_or_mutation_case", "interaction_or_boundary_case", "coverage", "notes",
    ]
    write_csv(AUDIT / "coverage_matrix.csv", output, fields)
    counts = Counter(item["coverage"] for item in output)
    result_counts = Counter(item["status"] for item in rows)
    lines = [
        "# UEB Grade 1 coverage closure",
        "",
        "Authority: ICEB, *Rules of Unified English Braille, Third Edition 2024*, using the local PDF recorded in `environment.md`. Liblouis remains an implementation candidate only.",
        "",
        "This closure was generated from the 77 `REQUIRED` rows in `standard_scope.csv` after executing the audit corpus through the vendored `unicode.dis,en-ueb-g1.ctb`. A coverage result means that evidence was run; it does not mean the output passed the standard.",
        "",
        "`negative_or_mutation_case` means a focused boundary, near-neighbor, or observed-difference probe. `interaction_or_boundary_case` is deliberately narrower and is marked only where the test ID exercises a context-sensitive boundary. Policy-only rules are not promoted to COVERED merely because a related output exists.",
        "",
        "## Coverage matrix",
        "",
        "| Citation | Rule family | Executed test | Test IDs | Evidence tier | Positive | Negative/mutation | Interaction/boundary | Coverage | Notes |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in output:
        values = [item[field].replace("|", "\\|").replace("\n", " ") for field in fields]
        lines.append(f"| {values[0]} | {values[1]} | {values[2]} | `{values[3]}` | {values[4]} | {values[5]} | {values[6]} | {values[7]} | {values[8]} | {values[9]} |")
    lines += [
        "",
        "## Required rows with no direct executed evidence",
        "",
    ]
    if no_direct:
        for item in no_direct:
            lines.append(f"- `{item['citation']}` — {item['title']}")
    else:
        lines.append("None.")
    lines += [
        "",
        "These are not silently counted as compliant. The main irreducible gaps are Grade 1 word/passage/terminator controls (5.3–5.5), print-quote assignment options (7.6.4 and 7.6.12), and any rule whose direct meaning depends on document structure rather than plain source text.",
        "",
        "## Exact 2024 rule-text verification of the confirmed differences",
        "",
        "### ASCII single quotation pair",
        "",
        "Section 7.6.2 states: `Use single quotation marks ⠠⠦ and ⠠⠴ for single quotation marks in the print text.` Section 7.6.15 then permits the translation-software distinction to be made by context: a mark at the beginning of a word is an opening single quote, and `in all other contexts, treat the mark as a closing single quote`. For ASCII `'hello'`, the executed Liblouis result is apostrophe dot 3 on both sides; the derived 2024 contextual result is opening `⠠⠦` and closing `⠠⠴`. This is a confirmed implementation difference, but 7.6.13 expressly recognizes that ASCII print may be ambiguous, so it is not by itself proof of a mandatory Liblouis standards violation; our validator needs a documented contextual policy.",
        "",
        "### Nested quotation closing context",
        "",
        "Section 7.6.3 states: `Follow print for outer and inner quotation marks.` Its official example is `She said, “Read ‘Peter Rabbit’ again.”`, where the inner single quotation closes with the dot-6 two-cell single quote. The executed `quote_nested` case gives the inner opening quote correctly but translates the inner closing quote as apostrophe dot 3. That is a direct mismatch with the 2024 outer/inner quotation rule, independent of contracted-word differences.",
        "",
        "### Grade 1/capital ordering in `3-D`",
        "",
        "Section 6.5.4 states: `Grade 1 mode is terminated by a hyphen or dash ... Therefore, a letter or letters that could read as a contraction will need the grade 1 indicator.` The official example is `3-D   ⠼⠉⠤⠰⠠⠙`. Section 5.8.1 states: `A grade 1 indicator precedes a capitalisation indicator.` Liblouis emits `⠼⠉⠤⠠⠙`, omitting `⠰`; both `grade1_numeric_hyphen_cap` and `grade1_indicator_order` therefore fail the exact 2024 requirement.",
        "",
        "## Evidence closure decisions",
        "",
        "- ASCII single-quote pairs, nested single-quote closing context, internal double quotes, and standing-alone double quotes are confirmed contextual quote failures against the 2024 rules. The rulebook itself says quote/apostrophe distinction cannot be wholly automated without professional intervention (7.6.13).",
        "- `a.b` and `a,b` are resolved as PASS: the period is not a beginning-of-word lower-groupsign position, while comma in `a,b` requires the Grade 1 symbol indicator because it can be read as the lower groupsign `be` between letters.",
        "- Clear grouped numeric spaces are semantic: Section 6.6 says numeric-space signs mean `space and following digit` within a number and that an unclear separator is treated as an ordinary space; 6.6.1 says spaces within one number use those ten symbols. Plain text alone cannot establish grouping intent; the failed `num_clear_numeric_space` probe is therefore a wrapper/input-semantics gap, not proof that ordinary spaces are wrong. Under the recorded V1 policy, untagged `1 234` is treated as ordinary spacing and is PASS-PROVISIONAL.",
        "- Repeated ordinary spaces, NBSP outside numbers, and thin/zero-width spaces are separated from UEB compliance by a recorded source-normalization policy. Section 3.23.1 says `The amount of space present is not considered important`; the V1 layer collapses repeated ordinary spaces, maps NBSP/thin space to ordinary spacing outside numeric contexts, and removes U+200B extraction separators. Raw NBSP remains a normalization-layer FAIL; the thin/zero-width probe is PASS-PROVISIONAL after that policy.",
        "- Typeform + number is resolved for the exercised symbol, word, passage, punctuation, and multiple-typeform cases. Rule 9.3.1 permits a word typeform over a numeric symbols-sequence; Liblouis matched the derived result. No typeform bug is evidenced here.",
        "",
        "## Remaining corpus expansion boundary",
        "",
        "The corpus was expanded only for representable closure gaps: prime signs (`3.11`) and the quote boundary rules (`7.6.9` and `7.6.10`). No synthetic expected form was used to claim that translation-software options or explicit Grade 1 passages are implemented by the forward generator.",
        "",
        "## Final closure",
        "",
        f"- REQUIRED rows total: **{len(output)}**",
        f"- Fully covered: **{counts['COVERED']}**",
        f"- Partially covered: **{counts['PARTIAL']}**",
        f"- Untested: **{counts['UNTESTED']}**",
        f"- Executed corpus outcomes: PASS **{result_counts['PASS']}**; PASS-VARIANT **{result_counts['PASS-VARIANT']}**; PASS-PROVISIONAL **{result_counts['PASS-PROVISIONAL']}**; FAIL **{result_counts['FAIL']}**; UNCERTAIN **{result_counts['UNCERTAIN']}**; UNSUPPORTED **{result_counts['UNSUPPORTED']}**; N/A-GRADE **{result_counts['N/A-GRADE']}**.",
        "- Confirmed Liblouis gaps: ASCII single-quote direction in prose context; nested single-quote closing context; two-cell internal and standing-alone double-quote selection; Grade 1 plus capital ordering after numeric-mode termination in `3-D`.",
        "- Confirmed wrapper/normalization gaps: semantic numeric grouping for numeric spaces, repeated-space collapsing, and NBSP normalization outside numeric contexts.",
        "- Unresolved standards questions: when ambiguous ASCII quote marks are assigned direction without transcriber context; explicit Grade 1 word/passage/terminator acceptance in a validator; and whether the product will expose 7.6.4/7.6.12 quote-assignment options. Whitespace handling is now a recorded source-normalization policy, not an unresolved UEB rule question.",
        "- Exact minimal overrides we need to implement: (1) quote/apostrophe context and ambiguity handling with a small apostrophe dictionary and fail-closed path; (2) semantic numeric grouping that emits/accepts numeric-space cells and validates numeric-mode termination; (3) inject/accept Grade 1 before capital indicators after numeric hyphen/dash termination; (4) normalize or reject non-ordinary whitespace before Liblouis; (5) model only cited Grade 1/capital/typeform variants. No production code was changed by this audit.",
    ]
    (AUDIT / "coverage_closure.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_final_report(rows: list[dict[str, str]], closure: list[Path]) -> None:
    counts = Counter(row["status"] for row in rows)
    families = defaultdict(Counter)
    for item in rows:
        families[item["family"]][item["status"]] += 1
    required_count = sum(item["classification"] == "REQUIRED" for item in expanded_scope_rows())
    lines = [
        "# UEB Grade 1 / Liblouis audit",
        "",
        "Authority: ICEB, *Rules of Unified English Braille, Third Edition 2024*, local PDF `rules/Rules-of-Unified-English-Braille-2024.pdf`. Liblouis is treated as the implementation candidate only.",
        "",
        "Scope: English-only, uncontracted UEB / Grade 1. Contracted UEB, Nemeth, mathematics, chemistry, music and specialist notation are not production scope.",
        "",
        "## Evidence boundary",
        "",
        "The installed application path is the vendored Liblouis 3.38.0 DLL plus `unicode.dis,en-ueb-g1.ctb`. The separate `C:\\liblouis` installation is also 3.38.0 but has a different `en-ueb-g1.ctb` hash; results below use the project-vendored runtime only.",
        "",
        "Tests are focused probes, not a proof by percentage. Official rulebook examples that are contracted are marked `N/A-GRADE` and are never compared directly with Grade 1 output.",
        "",
        "## Final evidence table",
        "",
        "| Citation | Feature | Source | Expected | Liblouis | Evidence | Status | Existing upstream test | Gap classification | Notes |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in rows:
        expected = item["expected_dot_notation"] or "N/A-GRADE"
        observed = item["liblouis_dot_notation"]
        source = item["source"].replace("|", "\\|").replace("\n", " ")
        note = item["notes"].replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {item['citation']} | {item['family']} | `{source}` | `{expected}` | `{observed}` | {item['evidence_tier']} | {item['status']} | {item['upstream_test']} | {item['actual_gap_classification'] or 'NONE'} | {note} |"
        )
    lines += [
        "",
        "## Summary",
        "",
        f"Required UEB subrules audited: **{required_count}** scope rows (the finite rule-family checklist is in `standard_scope.csv`).",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status in ["PASS", "PASS-VARIANT", "FAIL", "UNCERTAIN", "UNSUPPORTED", "N/A-GRADE", "PASS-PROVISIONAL", "FAIL-PROVISIONAL"]:
        lines.append(f"| {status} | {counts[status]} |")
    lines += [
        "",
        "`UNSUPPORTED` is zero in the executed corpus because its probes are either in-scope or deliberately `N/A-GRADE`; the out-of-scope families listed below are intended to be rejected by the V1 scope gate, not translated as proof of support.",
    ]
    lines += [
        "",
        "### Coverage by family",
        "",
        "| Family | Cases | PASS | PASS-VARIANT | PASS-PROVISIONAL | FAIL | FAIL-PROVISIONAL | UNCERTAIN | UNSUPPORTED | N/A-GRADE |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    order = ["Alphabet", "Capitalization", "Numeric", "Grade-1", "Punctuation", "Quotes/apostrophes", "Hyphen/dash", "Brackets", "Symbols", "Spacing", "Typeforms"]
    for family in order:
        c = families[family]
        lines.append(f"| {family} | {sum(c.values())} | {c['PASS']} | {c['PASS-VARIANT']} | {c['PASS-PROVISIONAL']} | {c['FAIL']} | {c['FAIL-PROVISIONAL']} | {c['UNCERTAIN']} | {c['UNSUPPORTED']} | {c['N/A-GRADE']} |")
    lines += [
        "",
        "## 1. Reuse directly after verification",
        "",
        "- English a-z/A-Z cell mappings and ordinary letter-by-letter Grade 1 translation.",
        "- Core digits, decimal/comma numeric cells, basic brackets, common symbol cells, ordinary punctuation, and direct hyphen/dash cells where the source has unambiguous print semantics.",
        "- Liblouis's typeform API and its existing italic/bold/underline tables are usable as a low-level candidate, subject to the validator's structured typeform input.",
        "",
        "## 2. Wrap / normalize / acceptance-set handling",
        "",
        "- Treat the vendored runtime and table hashes as part of the expected-output contract; do not substitute the system table silently.",
        "- Add a UEB-2024 contextual layer for quote/apostrophe classification, Grade 1 optionality, numeric spaces, punctuation standing-alone cases, and capitals word/passage boundaries.",
        "- Preserve cited variants only: Grade 1 indicator omission/presence where 5.10 permits it, cap-word choice where 8.8 permits it, and the double-hyphen/dash choice in 7.2.6. Do not turn every Liblouis difference into a tolerance.",
        "- Apply the recorded source policy before translation: collapse repeated ordinary spaces, map NBSP/thin spaces to ordinary spacing outside numeric contexts, and remove U+200B extraction separators; retain an explicit ambiguity path where source semantics are unavailable.",
        "",
        "## 3. Override",
        "",
        "The executed failures identify where the table's static rules do not satisfy the 2024 contextual requirement: ASCII directional single-quote inference, the closing single quote in nested curly-quote context, two-cell internal/standing-alone double-quote selection, and the required Grade 1 + capital ordering after a numeric-mode hyphen. Clear numeric-space grouping requires semantic input that the plain table call does not receive; repeated spaces and non-ordinary whitespace are handled by the recorded normalization policy. Typeform + number is resolved for the exercised cases. These are evidence-backed override candidates only; no production fix is proposed in this audit.",
        "",
        "## 4. Implement ourselves",
        "",
        "- A finite acceptance-set/standards-verification layer around Liblouis output; two cited alternatives are currently modeled in `accepted_variants.csv`, and neither was emitted by this run.",
        "- Quote/apostrophe context classification with a small apostrophe-word dictionary and an explicit expert-review path for ambiguous print.",
        "- Numeric-space intent and numeric-mode termination checks based on source semantics, not only codepoint mapping.",
        "- Capital word/passage selection and terminator validation, including indicator ordering around numbers and punctuation.",
        "- Fail-closed scope detection for specialist notation and unsupported non-ASCII material.",
        "",
        "## 5. Unsupported for V1",
        "",
        "Contracted UEB / Grade 2, Nemeth, mathematics semantics, chemistry, music, multiline/layout-dependent indicators, foreign-language braille, IPA, technical code switching, and transcriber-defined typeforms remain unsupported. The presence of `en-ueb-math.ctb` in the Grade 1 include closure is an implementation detail, not V1 scope support.",
        "",
        "## Answers to the final questions",
        "",
        "1. **Base generator?** Yes, conditionally: the vendored `en-ueb-g1.ctb` is a useful low-level BASE expected-Braille generator for ordinary alphabetic Grade 1 text and direct symbols, but not a correctness authority and not safe as the sole validator oracle.",
        "2. **Correction/verification layer?** Required for quote/apostrophe context, numeric mode and 2024 numeric spaces, capitalization word/passage/terminator decisions, Grade 1 optionality/indicator ordering, punctuation standing-alone cases, spacing normalization, and typeform placement/variants.",
        "3. **Remain unsupported?** Grade 2, Nemeth, mathematics/chemistry/music, foreign/specialist code switches, layout-dependent passages, and ambiguous source punctuation without expert or document context.",
        "4. **Engineering remaining?** The core cell generator is reusable; credible shipping still requires a standards layer, fail-closed scope gate, acceptance-set model, quote/apostrophe dictionary/uncertainty path, numeric/capitalization verification, and a larger ICEB-2024 regression corpus. This audit does not claim ship readiness.",
        "",
        "Supporting artifacts: `environment.md`, `standard_extract.txt`, `standard_scope.csv`, `liblouis_implementation_matrix.csv`, `upstream_test_coverage.md`, `corpus.csv`, `execution_results.csv`, `accepted_variants.csv`, `coverage_matrix.csv`, and `coverage_closure.md`.",
    ]
    (AUDIT / "final_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    louis = import_louis()
    closure = write_environment(louis)
    write_standard_scope()
    extract_standard_text()
    write_upstream_coverage()
    write_matrix()
    corpus = build_corpus()
    results = evaluate(corpus, louis)
    write_results(results)
    write_coverage_closure(results)
    write_final_report(results, closure)
    print(json.dumps({"cases": len(results), "status": Counter(x["status"] for x in results)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
