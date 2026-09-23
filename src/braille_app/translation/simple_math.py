"""Closed, baseline Nemeth grammar; no Liblouis or fixture oracle.

Nemeth 2022 3.3.1, 3.4.1, 6.3.1, 6.4.7, 20.1, 21.13.
No source typeform, spatial, script, or radical interpretation is inferred.
"""
from dataclasses import dataclass
import re


RULE_ID = "NEMETH_SIMPLE_LINEAR_001"
SOURCE_RULE = "3.3.1; 3.4.1; 6.3.1; 6.4.7; 20.1; 21.13"
SOURCE_PAGE = "3-3,3-11; 6-6,6-12; 20-1 to 20-4; 21-15"


@dataclass(frozen=True)
class NumberNode:
    text: str


@dataclass(frozen=True)
class LetterNode:
    text: str


@dataclass(frozen=True)
class OperatorNode:
    text: str
    unary: bool = False


@dataclass(frozen=True)
class RelationNode:
    text: str


@dataclass(frozen=True)
class LinearExpression:
    nodes: tuple


def parse(source: str) -> LinearExpression | None:
    # Tokenize without deleting whitespace between operands ("1 2" != "12").
    if not source or re.search(r"[^0-9a-z +−×÷=]", source):
        return None
    tokens = re.findall(r"[0-9]+|[a-z]|[+−×÷=]", source)
    nodes = []
    wants_operand = True
    equalities = 0
    for token in tokens:
        if wants_operand:
            if token == "−" and (not nodes or isinstance(nodes[-1], RelationNode)):
                nodes.append(OperatorNode(token, unary=True))
                continue
            if token.isascii() and token.isdigit():
                nodes.append(NumberNode(token))
            elif len(token) == 1 and "a" <= token <= "z":
                nodes.append(LetterNode(token))
            else:
                return None
            wants_operand = False
        else:
            if token == "=" and not equalities:
                nodes.append(RelationNode(token))
                equalities += 1
            elif token in "+−×÷":
                nodes.append(OperatorNode(token))
            else:
                return None
            wants_operand = True
    # A bare letter is a prose/identifier decision, not this expression scope.
    if wants_operand or not nodes or (len(nodes) == 1 and isinstance(nodes[0], LetterNode)):
        return None
    return LinearExpression(tuple(nodes))


_DIGITS = dict(zip("0123456789", "⠴⠂⠆⠒⠲⠢⠖⠶⠦⠔"))
_LETTERS = dict(zip("abcdefghijklmnopqrstuvwxyz", "⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚⠅⠇⠍⠝⠕⠏⠟⠗⠎⠞⠥⠧⠺⠭⠽⠵"))
_OPERATIONS = {"+": "⠬", "−": "⠤", "×": "⠈⠡", "÷": "⠨⠌"}


def render(expression: LinearExpression) -> str:
    """Emit only parsed baseline nodes. Termination is the explicit span end."""
    output = []
    numeric_start = True  # span follows the opening switch's inner blank
    for node in expression.nodes:
        if isinstance(node, RelationNode):
            output.append("⠀⠨⠅⠀")
            numeric_start = True
        elif isinstance(node, OperatorNode):
            output.append(_OPERATIONS[node.text])
            if not node.unary:
                numeric_start = False
        elif isinstance(node, NumberNode):
            output.append(("⠼" if numeric_start else "") + "".join(_DIGITS[d] for d in node.text))
            numeric_start = False
        else:
            # No standalone letter is admitted. Adjacent operation makes it
            # unspaced; adjacent comparison invokes 6.4.7.
            output.append(_LETTERS[node.text])
            numeric_start = False
    return "".join(output)


def expected(source: str) -> str | None:
    expression = parse(source)
    return render(expression) if expression is not None else None
