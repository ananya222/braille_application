"""Source-guided tolerance for the observed Duxbury operation-spacing artifact.

Only the comparison view drops cells. Raw actual cells and their PDF positions
are retained. Operators are NEVER replaced with the source's expected symbols.
"""
from dataclasses import dataclass
from bisect import bisect_left

from braille_app.translation.simple_math import (
    parse, render, LinearExpression, NumberNode, LetterNode, OperatorNode, RelationNode,
)
from braille_app.translation.braille_cells import unicode_to_cells
from .alignment import CellOpcode, align_cells


def align_with_operator_anchors(document, expected, view):
    """Anchor equal-width supported operator slots to their ordered operands.

    Repeated operands must not let a sequence matcher move an operator to a
    different slot. Only already evaluated, equal-length math payloads whose
    non-operator cells match exactly qualify. Other cases retain normal diffing.
    Raw provenance remains owned by ComparisonView.project.
    """
    actual_spans = iter(view.evaluated_spans)
    anchors = []
    ordinal = 0
    page_base = 0
    for page in document.pages:
        block_base = page_base
        for block in page.blocks:
            if not block.braille:
                continue
            within = 0
            for record in block.math_records:
                offset = block.braille.find(record.braille, within)
                within = offset + len(record.braille)
                evaluated = view.source_span_evaluated[ordinal]
                ordinal += 1
                if not evaluated:
                    continue
                raw_start, raw_end = next(actual_spans)
                expression = parse(record.source)
                if expression is None or offset < 0:
                    continue
                canonical = unicode_to_cells(render(expression))
                if canonical != unicode_to_cells(record.braille):
                    continue
                left = bisect_left(view.raw_indices, raw_start)
                right = bisect_left(view.raw_indices, raw_end) - 1
                if (left >= len(view.cells) or right < left
                        or view.cells[left] != 0 or view.cells[right] != 0):
                    continue
                left += 1
                if right-left != len(canonical):
                    continue
                operator_positions = set()
                for i, node in enumerate(expression.nodes):
                    prefix = len(render(LinearExpression(expression.nodes[:i])))
                    if isinstance(node, RelationNode):
                        operator_positions.update((prefix+1, prefix+2))
                    elif isinstance(node, OperatorNode):
                        operator_positions.update(range(prefix, prefix+(2 if node.text in '×÷' else 1)))
                actual = view.cells[left:right]
                if any(a != b and i not in operator_positions
                       for i, (a, b) in enumerate(zip(canonical, actual))):
                    continue
                start = block_base + offset
                if expected[start:start+len(canonical)] == canonical:
                    anchors.append((start, start+len(canonical), left, right))
            block_base += len(block.braille)+1
        page_base += len(unicode_to_cells(page.flatten()))+1
    result = []
    epos = apos = 0
    for es, ee, astart, aend in anchors:
        if es < epos or astart < apos:
            continue
        result.extend(CellOpcode(op.tag, op.expected_start+epos, op.expected_end+epos,
                                 op.actual_start+apos, op.actual_end+apos)
                      for op in align_cells(expected[epos:es], view.cells[apos:astart]))
        i = 0
        while i < ee-es:
            tag = 'equal' if expected[es+i] == view.cells[astart+i] else 'replace'
            j = i+1
            while j < ee-es and ('equal' if expected[es+j] == view.cells[astart+j] else 'replace') == tag:
                j += 1
            result.append(CellOpcode(tag, es+i, es+j, astart+i, astart+j))
            i = j
        epos, apos = ee, aend
    result.extend(CellOpcode(op.tag, op.expected_start+epos, op.expected_end+epos,
                             op.actual_start+apos, op.actual_end+apos)
                  for op in align_cells(expected[epos:], view.cells[apos:]))
    return tuple(result)

OPEN=(56,41)
CLOSE=(56,49)

@dataclass(frozen=True)
class ComparisonView:
    cells: tuple[int,...]
    raw_indices: tuple[int,...]
    raw_length: int
    normalized_spans: tuple[tuple[int,int],...] = ()
    skipped_spans: tuple[tuple[int,int,str],...] = ()
    evaluated_spans: tuple[tuple[int,int],...] = ()
    source_span_evaluated: tuple[bool,...] = ()
    joined_page_breaks: int = 0

    def project(self, opcode):
        """Project comparison alignment into the unchanged actual-cell stream."""
        a,b=opcode.actual_start,opcode.actual_end
        if opcode.tag=='equal':
            # Equal anchors must remain genuinely contiguous for the existing
            # capitalization and annotation code's offset arithmetic.
            start=a
            for i in range(a+1,b+1):
                if i==b or self.raw_indices[i]!=self.raw_indices[i-1]+1:
                    yield CellOpcode('equal',opcode.expected_start+start-a,
                                     opcode.expected_start+i-a,
                                     self.raw_indices[start],self.raw_indices[i-1]+1)
                    start=i
        else:
            left=self.raw_indices[a] if a<len(self.raw_indices) else self.raw_length
            right=self.raw_indices[b-1]+1 if b>a else left
            yield CellOpcode(opcode.tag,opcode.expected_start,opcode.expected_end,left,right)

def _passages(cells):
    spans=[];problems=[];start=None;i=0
    while i<len(cells)-1:
        pair=cells[i:i+2]
        if pair==OPEN:
            if start is not None:
                problems.append((start-2,i,'Nested or unclosed opening switch'))
            start=i+2;i+=2
        elif pair==CLOSE:
            if start is None:
                problems.append((i,i+2,'Unmatched closing switch'))
            else:
                spans.append((start,i));start=None
            i+=2
        else:i+=1
    if start is not None:
        problems.append((start-2,len(cells),'Unclosed opening switch'))
    return spans,problems

def _artifact_cells(source,actual,physical_breaks=frozenset()):
    """Find a unique tokenization with unchanged source operands.

    Exact operands anchor the operator slots. One or two actual operator cells
    (including wrong symbols) are kept. Only zero/one blank beside a binary
    operator, and a numeric sign immediately after its right blank, can be
    removed. One post-unary blank before a numeric operand is also admitted.
    Equality's two surrounding blanks and numeric restarts remain untouched.
    Only explicitly identified synthetic page separators may be skipped inside
    tokens. Actual blank cells retain the existing spacing rules.
    """
    expression=parse(source)
    if expression is None:return None
    nodes=expression.nodes
    def starts(pos):
        """A synthetic page separator may be a space or no cell at all."""
        removed=set()
        yield pos,frozenset()
        while pos in physical_breaks:
            removed.add(pos);pos+=1
            yield pos,frozenset(removed)

    def read(pos,values=None,width=None):
        states=[(pos,(),frozenset())]
        for i in range(len(values) if values is not None else width):
            following=[]
            for cursor,cells,dropped in states:
                for at,skipped in starts(cursor):
                    if at>=len(actual):continue
                    cell=actual[at]
                    if values is not None:
                        if cell!=values[i]:continue
                    elif cell in (0,60,56):continue
                    following.append((at+1,cells+(cell,),dropped|skipped))
            states=following
        return states

    def advance(n,pos,numeric_start,artifact_indicator):
        answers=[]
        for at,skipped in starts(pos):
            for state,dropped in advance_at(n,at,numeric_start,artifact_indicator):
                answers.append((state,dropped|skipped))
        return answers

    def advance_at(n,pos,numeric_start,artifact_indicator):
        node=nodes[n]
        if isinstance(node,(NumberNode,LetterNode)):
            expected=unicode_to_cells(render(LinearExpression((node,))))
            prefixes=[(pos,frozenset())]
            if isinstance(node,NumberNode):
                digits=expected[1:]
                if numeric_start:
                    prefixes=[(end,dropped) for end,_,dropped in read(pos,(60,))]
                elif actual[pos:pos+1]==(60,):
                    if not artifact_indicator:return ()
                    prefixes=[(pos+1,frozenset((pos,)))]
                expected=digits
            answers=[]
            for at,prefix_drop in prefixes:
                for end,_,dropped in read(at,expected):
                    answers.append(((end,False,False),prefix_drop|dropped))
            return answers
        relation=isinstance(node,RelationNode)
        unary=isinstance(node,OperatorNode) and node.unary
        dropped=set()
        if relation:
            if actual[pos:pos+1]!=(0,):return ()
            pos+=1
        elif not unary and actual[pos:pos+1]==(0,):
            dropped.add(pos);pos+=1
        answers=[]
        for width in (1,2):
            for symbol_end,symbol,inside_drop in read(pos,width=width):
                for end,after_drop in starts(symbol_end):
                    local=set(dropped)|set(inside_drop)|set(after_drop)
                    gap=actual[end:end+1]==(0,)
                    if relation:
                        if not gap:continue
                        end+=1
                    elif gap:
                        if unary and (n+1==len(nodes) or not isinstance(nodes[n+1],NumberNode)):continue
                        local.add(end);end+=1
                    next_numeric = True if relation else numeric_start if unary else False
                    # Only the already verified leading-plus reconversion.
                    if (n == 0 and unary and symbol == (44,) and not gap
                            and n + 1 < len(nodes) and isinstance(nodes[n + 1], NumberNode)
                            and actual[end:end+1] != (60,)):
                        next_numeric = False
                    answers.append(((end,next_numeric,
                                     bool(gap and not relation and not unary)),frozenset(local)))
        return tuple(answers)
    # Iterative states avoid imposing a new expression-length restriction.
    # Two distinct histories per state suffice to establish ambiguity: removed
    # positions are behind the cursor and cannot converge in later steps.
    states={(0,True,False):{frozenset()}}
    for n in range(len(nodes)):
        next_states={}
        for state,histories in states.items():
            for target,removed in advance(n,*state):
                bucket=next_states.setdefault(target,set())
                for history in histories:
                    if len(bucket)<2:bucket.add(history|removed)
        states=next_states
        if not states:return None
    results={history|removed for (pos,_numeric,_artifact),histories in states.items()
             for end,removed in starts(pos) if end==len(actual) for history in histories}
    return set(next(iter(results))) if len(results)==1 else None

def comparison_view(expected_page,raw,physical_breaks=frozenset()):
    # Find switches across physical boundaries, without deleting real blanks.
    scan_indices=tuple(i for i in range(len(raw)) if i not in physical_breaks)
    scan=tuple(raw[i] for i in scan_indices)
    compact_spans,compact_problems=_passages(scan)
    spans=[(scan_indices[s-1]+1,scan_indices[e]) for s,e in compact_spans]
    passage_problems=[(scan_indices[s],scan_indices[e-1]+1,reason) for s,e,reason in compact_problems]
    switch_breaks={span:physical_breaks.intersection(
        range(scan_indices[s-2],scan_indices[s-1]+1))|physical_breaks.intersection(
        range(scan_indices[e],scan_indices[e+1]+1))
        for span,(s,e) in zip(spans,compact_spans)}
    records=[record for block in expected_page.blocks for record in block.math_records]
    dropped=set();normalized=[];skipped=list(passage_problems)
    evaluated=[]
    source_evaluated=[False for _ in records]

    def candidate(record,span):
        start,end=span
        lefts=[start];rights=[end-1]
        while lefts[-1] in physical_breaks:lefts.append(lefts[-1]+1)
        while rights[-1] in physical_breaks:rights.append(rights[-1]-1)
        for left in lefts:
            for right in rights:
                if right-left<2 or raw[left]!=0 or raw[right]!=0:continue
                artifact=_artifact_cells(record.source,raw[left+1:right],
                    {i-left-1 for i in physical_breaks if left+1<=i<right})
                if artifact is not None:
                    removed=set(range(start,left))|set(range(right+1,end))
                    removed.update(left+1+i for i in artifact)
                    return {i-start-1 for i in removed}
        expected_payload=unicode_to_cells(record.braille)
        return set() if raw[start+1:end-1]==expected_payload else None

    if len(spans)==len(records):
        pairs=[(i,i) for i in range(len(records))]
    else:
        # Ordered maximum matching lets one missing/broken span remain
        # unresolved without disabling tolerance for every later span.
        rows,cols=len(records),len(spans)
        dp=[[0]*(cols+1) for _ in range(rows+1)]
        for i in range(rows-1,-1,-1):
            for j in range(cols-1,-1,-1):
                match=1+dp[i+1][j+1] if candidate(records[i],spans[j]) is not None else -1
                dp[i][j]=max(match,dp[i+1][j],dp[i][j+1])
        pairs=[];i=j=0
        while i<rows and j<cols:
            if candidate(records[i],spans[j]) is not None and dp[i][j]==1+dp[i+1][j+1]:
                pairs.append((i,j));i+=1;j+=1
            elif dp[i+1][j]>=dp[i][j+1]:i+=1
            else:j+=1
        paired_actual={j for _,j in pairs}
        for j,span in enumerate(spans):
            if j not in paired_actual:skipped.append((*span,'Unpaired actual math passage'))

    for record_index,span_index in pairs:
        start,end=spans[span_index];record=records[record_index]
        # Inner code-switch blanks are not normalization targets.
        if end-start<3 or raw[start]!=0 or raw[end-1]!=0:
            skipped.append((start,end,'Missing inner switch blank'));continue
        artifact=candidate(record,(start,end))
        if artifact is None:
            skipped.append((start,end,'Unsupported or ambiguous tokenization; comparison unchanged'));continue
        source_evaluated[record_index]=True
        evaluated.append((start,end))
        dropped.update(switch_breaks[(start,end)])
        if artifact:
            removed={start+1+i for i in artifact}
            dropped.update(removed)
            if removed-physical_breaks:normalized.append((start,end))
    indices=tuple(i for i in range(len(raw)) if i not in dropped)
    return ComparisonView(tuple(raw[i] for i in indices),indices,len(raw),tuple(normalized),tuple(skipped),tuple(evaluated),tuple(source_evaluated),len(dropped&physical_breaks))
