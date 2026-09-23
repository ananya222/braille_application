# Phase 7B Function / Definition-Punctuation Inventory

This inventory is an experiment-only decomposition of the original
116-region priority cluster. Labels are structural and do not affect
production rule behavior. The later generic promotion experiment was
reverted after the full rendered-BRF regression introduced definite Nemeth
and UEB mismatches; all 116 cases therefore remain REVIEW.

## Structural decomposition

| Subcluster | Count | Example structure | Governing rule candidates | Existing support |
| --- | ---: | --- | --- | --- |
| function application parentheses | 52 | `(L₁, L₂) ∈ R, (L₂, L₃) ∈ R but (L₁, L₃) ∉ R` | Nemeth 18.1, 18.4; Nemeth 8.2.13 | NEMETH_RULE_003 review |
| function/mapping definition colon | 40 | `f : X → Y` | Nemeth 8.5; Nemeth 18.1, 18.5 | NEMETH_RULE_003 review |
| set-builder condition colon | 12 | `{(a, b) ∈ A × B: a is brother of b}` | Nemeth 8.5; Nemeth 19 | NEMETH_RULE_003 review |
| ordered-pair or tuple comma | 9 | `R = {(1, 1), (2, 2), (3, 3), (1, 2), (2, 3)}` | Nemeth 8.6; Nemeth 19 | NEMETH_RULE_003 review |
| definition/colon context | 2 | `f : {1, 2, 3} → {1, 2, 3}` | Nemeth 8.5 | NEMETH_RULE_003 review |
| logical/relation punctuation | 1 | `f : {2, 3, 4, 5} → {3, 4, 5, 9} and g : {3, 4, 5, 9} → {7, 11, 15}` | Nemeth 8; Nemeth 20–21 | NEMETH_RULE_003 review |
| **Total** | **116** |  |  |  |

## Detailed cases

The JSON companion contains complete candidate/actual cell arrays and
all requested provenance fields. The table below keeps the complete
source-level inventory readable while retaining one row per case.

| ID | Source page | BRF page | Block | Subcluster | Function/identifiers | Punctuation | Current rule |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| FUNC-001 | 1 | 1 | 26 | set-builder condition colon | B | `{ ( , ) : }` | NEMETH_RULE_003 |
| FUNC-002 | 1 | 1 | 28 | set-builder condition colon | B | `{ ( , ) : }` | NEMETH_RULE_003 |
| FUNC-003 | 1 | 1 | 30 | set-builder condition colon | B | `{ ( , ) : }` | NEMETH_RULE_003 |
| FUNC-004 | 1 | 1 | 32 | set-builder condition colon | B | `{ ( , ) : }` | NEMETH_RULE_003 |
| FUNC-005 | 1 | 1 | 34 | set-builder condition colon | B | `{ ( , ) : }` | NEMETH_RULE_003 |
| FUNC-006 | 3 | 3 | 24 | function application parentheses | but | `( , ) , ( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-007 | 3 | 3 | 30 | ordered-pair or tuple comma | none | `{ ( , ) , ( , ) , ( , ) , ( , ) , ( , ) }` | NEMETH_RULE_003 |
| FUNC-008 | 3 | 3 | 32 | function application parentheses | and | `( , ) , ( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-009 | 3 | 3 | 33 | function application parentheses | but | `( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-010 | 3 | 3 | 34 | function application parentheses | and, but | `( , ) ( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-011 | 3 | 3 | 40 | function application parentheses | divides, Z, a | `( ) ( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-012 | 3 | 3 | 41 | function application parentheses | and | `( , ) ( , ) ( ) ( ) ( )` | NEMETH_RULE_003 |
| FUNC-013 | 4 | 4 | 2 | ordered-pair or tuple comma | none | `( , ) , ( , )` | NEMETH_RULE_003 |
| FUNC-014 | 4 | 4 | 3 | ordered-pair or tuple comma | none | `( , ) , ( , )` | NEMETH_RULE_003 |
| FUNC-015 | 4 | 4 | 33 | set-builder condition colon | Z | `{ : } { . . . , , , , , , . . . }` | NEMETH_RULE_003 |
| FUNC-016 | 4 | 4 | 35 | set-builder condition colon | Z | `{ : } { . . . , , , , , , . . . }` | NEMETH_RULE_003 |
| FUNC-017 | 4 | 4 | 37 | set-builder condition colon | Z | `{ : } { . . . , , , , , , . . . }` | NEMETH_RULE_003 |
| FUNC-018 | 5 | 5 | 3 | function application parentheses | R, and | `( , ) ( , ) ( , ) ( , ) ( , ) , , , ( , )` | NEMETH_RULE_003 |
| FUNC-019 | 6 | 6 | 2 | ordered-pair or tuple comma | none | `{ , , } { ( , ) , ( , ) }` | NEMETH_RULE_003 |
| FUNC-020 | 6 | 6 | 14 | set-builder condition colon | Z | `{ : }` | NEMETH_RULE_003 |
| FUNC-021 | 6 | 6 | 36 | ordered-pair or tuple comma | none | `( , )` | NEMETH_RULE_003 |
| FUNC-022 | 7 | 7 | 3 | ordered-pair or tuple comma | none | `{ ( , ) , ( , ) , ( , ) , ( , ) , ( , ) , ( , ) , ( , ) }` | NEMETH_RULE_003 |
| FUNC-023 | 7 | 7 | 16 | function application parentheses | R | `( , ) ( , ) ( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-024 | 7 | 7 | 38 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-025 | 7 | 7 | 39 | function application parentheses | f | `, , ( ) ( )` | NEMETH_RULE_003 |
| FUNC-026 | 7 | 7 | 45 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-027 | 8 | 8 | 6 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-028 | 8 | 8 | 8 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-029 | 8 | 8 | 13 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-030 | 8 | 8 | 14 | function application parentheses | f | `( )` | NEMETH_RULE_003 |
| FUNC-031 | 8 | 8 | 22 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-032 | 8 | 8 | 25 | function application parentheses | f | `( ) ( )` | NEMETH_RULE_003 |
| FUNC-033 | 8 | 8 | 26 | function application parentheses | f | `( )` | NEMETH_RULE_003 |
| FUNC-034 | 9 | 9 | 2 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-035 | 9 | 9 | 4 | function application parentheses | f | `( ) ( )` | NEMETH_RULE_003 |
| FUNC-036 | 9 | 9 | 11 | function/mapping definition colon | f | `: ( ) ( ) ( )` | NEMETH_RULE_003 |
| FUNC-037 | 9 | 9 | 14 | function application parentheses | f | `( ) ( ) ,` | NEMETH_RULE_003 |
| FUNC-038 | 9 | 9 | 15 | function application parentheses | f | `( )` | NEMETH_RULE_003 |
| FUNC-039 | 9 | 9 | 16 | function application parentheses | f | `( )` | NEMETH_RULE_003 |
| FUNC-040 | 9 | 9 | 18 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-041 | 9 | 9 | 19 | function application parentheses | f | `( )` | NEMETH_RULE_003 |
| FUNC-042 | 9 | 9 | 21 | function application parentheses | f | `( ) ( )` | NEMETH_RULE_003 |
| FUNC-043 | 9 | 9 | 32 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-044 | 9 | 9 | 34 | function application parentheses | f | `( ) , , ,` | NEMETH_RULE_003 |
| FUNC-045 | 10 | 10 | 7 | function application parentheses | f | `( ) ( )` | NEMETH_RULE_003 |
| FUNC-046 | 10 | 10 | 11 | definition/colon context | f | `: { , , } { , , }` | NEMETH_RULE_003 |
| FUNC-047 | 10 | 10 | 18 | definition/colon context | f | `: { , , } { , , }` | NEMETH_RULE_003 |
| FUNC-048 | 10 | 10 | 24 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-049 | 10 | 10 | 25 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-050 | 10 | 10 | 37 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-051 | 10 | 10 | 39 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-052 | 10 | 10 | 41 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-053 | 10 | 10 | 43 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-054 | 10 | 10 | 45 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-055 | 11 | 11 | 2 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-056 | 11 | 11 | 5 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-057 | 11 | 11 | 7 | function application parentheses | f | `( ) , , ,` | NEMETH_RULE_003 |
| FUNC-058 | 11 | 11 | 11 | ordered-pair or tuple comma | none | `{ , , } , { , , , } { ( , ) , ( , ) , ( , ) }` | NEMETH_RULE_003 |
| FUNC-059 | 11 | 11 | 17 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-060 | 11 | 11 | 19 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-061 | 11 | 11 | 21 | function/mapping definition colon | f | `: ( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-062 | 11 | 11 | 24 | function/mapping definition colon | f | `: ( ) ( ) , ,` | NEMETH_RULE_003 |
| FUNC-063 | 11 | 11 | 27 | function/mapping definition colon | f | `{ } { } :` | NEMETH_RULE_003 |
| FUNC-064 | 11 | 11 | 28 | function application parentheses | f | `( ) ( ) ( )` | NEMETH_RULE_003 |
| FUNC-065 | 11 | 11 | 30 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-066 | 11 | 11 | 35 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-067 | 12 | 12 | 4 | function/mapping definition colon | f, g | `: :` | NEMETH_RULE_003 |
| FUNC-068 | 12 | 12 | 5 | function/mapping definition colon | gof | `:` | NEMETH_RULE_003 |
| FUNC-069 | 12 | 12 | 6 | function application parentheses | gof, g, f | `( ) ( ( ) ) ,` | NEMETH_RULE_003 |
| FUNC-070 | 12 | 12 | 12 | logical/relation punctuation | f, g | `: { , , , } { , , , } : { , , , } { , , }` | NEMETH_RULE_003 |
| FUNC-071 | 12 | 12 | 13 | function application parentheses | f, g | `( ) , ( ) , ( ) ( ) ( ) ( ) ( ) ( )` | NEMETH_RULE_003 |
| FUNC-072 | 12 | 12 | 15 | function application parentheses | gof, g, f | `( ) ( ( ) ) ( ) , ( ) ( ( ) ) ( ) , ( ) ( ( ) ) ( ) ( ) ( )` | NEMETH_RULE_003 |
| FUNC-073 | 12 | 12 | 17 | function/mapping definition colon | f, g | `: :` | NEMETH_RULE_003 |
| FUNC-074 | 12 | 12 | 18 | function application parentheses | f, g | `( ) ( )` | NEMETH_RULE_003 |
| FUNC-075 | 12 | 12 | 20 | function application parentheses | gof, g, f | `( ) ( ( ) ) ( ) ( )` | NEMETH_RULE_003 |
| FUNC-076 | 12 | 12 | 21 | function application parentheses | fog, f, g, cos | `( ) ( ( ) ) ( ) ( ) ,` | NEMETH_RULE_003 |
| FUNC-077 | 12 | 12 | 24 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-078 | 12 | 12 | 33 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-079 | 12 | 12 | 34 | set-builder condition colon | N | `{ : }` | NEMETH_RULE_003 |
| FUNC-080 | 13 | 13 | 2 | function application parentheses | g, gof, f | `( ) ( ) ( ) ( ( ) ) ( ) ( )` | NEMETH_RULE_003 |
| FUNC-081 | 13 | 13 | 12 | function application parentheses | and | `( , ) ( , ) ( , ) ( , ) ( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-082 | 13 | 13 | 13 | function application parentheses | and | `( , ) ( , ) ( , ) ( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-083 | 13 | 13 | 17 | function application parentheses | R | `( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-084 | 13 | 13 | 19 | function application parentheses | R | `( , ) ( , ) , ( , )` | NEMETH_RULE_003 |
| FUNC-085 | 13 | 13 | 20 | function application parentheses | R, vx | `( , ) ( , ) ( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-086 | 13 | 13 | 21 | function application parentheses | R, and, hence | `( , ) ( , ) ( , ) ( , ) ( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-087 | 14 | 14 | 4 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-088 | 14 | 14 | 5 | set-builder condition colon | f | `{ ( , ) : ( ) ( ) }` | NEMETH_RULE_003 |
| FUNC-089 | 14 | 14 | 7 | function application parentheses | X, f | `( , ) ( ) ( )` | NEMETH_RULE_003 |
| FUNC-090 | 14 | 14 | 8 | function application parentheses | f | `( , ) ( ) ( ) ( ) ( ) ( , )` | NEMETH_RULE_003 |
| FUNC-091 | 14 | 14 | 9 | function application parentheses | and, f | `( , ) ( , ) ( ) ( ) ( ) ( ) ( ) ( ) ( , )` | NEMETH_RULE_003 |
| FUNC-092 | 14 | 14 | 19 | function application parentheses | and | `( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-093 | 14 | 14 | 22 | ordered-pair or tuple comma | none | `{ ( , ) , ( , ) , ( , ) , ( , ) , ( , ) , ( , ) }` | NEMETH_RULE_003 |
| FUNC-094 | 14 | 14 | 31 | function application parentheses | and | `( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-095 | 14 | 14 | 34 | function application parentheses | and | `( , ) ( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-096 | 14 | 14 | 36 | function application parentheses | and | `( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-097 | 15 | 15 | 16 | set-builder condition colon | f, R | `: { : } ( ) ( )` | NEMETH_RULE_003 |
| FUNC-098 | 15 | 15 | 19 | function/mapping definition colon | f | `: ( )` | NEMETH_RULE_003 |
| FUNC-099 | 15 | 15 | 21 | function application parentheses | P | `( )` | NEMETH_RULE_003 |
| FUNC-100 | 15 | 15 | 22 | function application parentheses | P | `( )` | NEMETH_RULE_003 |
| FUNC-101 | 15 | 15 | 24 | function application parentheses | P | `( )` | NEMETH_RULE_003 |
| FUNC-102 | 15 | 15 | 28 | function/mapping definition colon | g | `{ , , , } , { , , , } , :` | NEMETH_RULE_003 |
| FUNC-103 | 15 | 15 | 29 | function application parentheses | f, g | `( ) , ( ) ,` | NEMETH_RULE_003 |
| FUNC-104 | 15 | 15 | 30 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-105 | 15 | 15 | 31 | function/mapping definition colon | g, f | `: ( ) ( )` | NEMETH_RULE_003 |
| FUNC-106 | 16 | 16 | 2 | function application parentheses | and | `{ , , } ( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-107 | 16 | 16 | 6 | ordered-pair or tuple comma | none | `{ , , } ( , )` | NEMETH_RULE_003 |
| FUNC-108 | 16 | 16 | 21 | function application parentheses | implies | `( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-109 | 16 | 16 | 23 | function application parentheses | and, that | `( , ) ( , ) ( , )` | NEMETH_RULE_003 |
| FUNC-110 | 16 | 16 | 31 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-111 | 16 | 16 | 32 | function application parentheses | f | `( ) ( ) ,` | NEMETH_RULE_003 |
| FUNC-112 | 16 | 16 | 34 | function/mapping definition colon | f | `: ,` | NEMETH_RULE_003 |
| FUNC-113 | 16 | 16 | 35 | function application parentheses | f | `( )` | NEMETH_RULE_003 |
| FUNC-114 | 16 | 16 | 37 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-115 | 16 | 16 | 40 | function/mapping definition colon | f | `:` | NEMETH_RULE_003 |
| FUNC-116 | 17 | 17 | 22 | function application parentheses | f, F, φ | `( ) , ( ) , ( )` | NEMETH_RULE_003 |

## Ownership decision

Ownership is not assigned by punctuation symbol alone. Each case
retains its explicit math-span source, surrounding prose, and MIXED
ValidationContext. Nemeth ownership is considered only for punctuation
inside the marked span; punctuation outside that span remains a UEB
boundary concern and is not promoted by this inventory.

The original accounting invariant is preserved: 116 inventoried
regions, each with a stable audit ID and source block provenance.
