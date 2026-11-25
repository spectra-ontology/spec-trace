"""CR producer deletion provenance and exact parent interval slices.

Spec: CR revision text and chunking source character preservation.
Ontology: Existing CR chunk schema; no public proof transport fields.
Cycle: RAN source parser DEL boundary repair.
배경: Keep source deletion state across soft overlap and hard token boundaries.
사용: Pass actual XML collision proof and native splitter into interval rendering.
LLM 호출: 없음.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Sequence
import hashlib
import re
import xml.etree.ElementTree as ET

MARK = re.compile(r"\[/?DEL\]")
W_P = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
PROOF_VERSION = "cr-xml-generated-del-v1"
PRIVATE = "_crDelProof"


class UnprovenDeletionState(ValueError):
    pass


def reject_literals(values):
    """Raw metadata is not a MARK reader output and cannot authorize markers."""
    if isinstance(values, str):
        if MARK.search(values):
            raise UnprovenDeletionState("Literal DEL marker in metadata")
    elif isinstance(values, dict):
        for value in values.values():
            reject_literals(value)
    elif isinstance(values, (list, tuple)):
        for value in values:
            reject_literals(value)


def _digest_text(digest, value):
    value = str(value)
    digest.update(str(len(value)).encode("ascii") + b":")
    for start in range(0, len(value), 1 << 18):
        digest.update(value[start:start + (1 << 18)].encode("utf-8"))


def prove_xml(roots, keep_paragraph: Callable[[object], str], raw_metadata=()):
    """Use original in-memory XML and actual native KEEP; do not serialize XML.

    Literal collision returns an explicit unproven status so a general parser
    preserves its legacy content. A targeted replay must require proven status.
    Reader failures still propagate. The fingerprint is an in-memory view pin,
    not a replacement for source ZIP bytes/source-generation guards.
    """
    roots = list(roots)
    if not roots:
        raise UnprovenDeletionState("No original XML supplied")
    digest = hashlib.sha256()
    paragraphs, collisions, reasons = 0, 0, []
    def check(values, reason):
        nonlocal collisions
        try:
            reject_literals(values)
        except UnprovenDeletionState:
            collisions += 1
            if reason not in reasons:
                reasons.append(reason)
    check(raw_metadata, "raw_metadata_literal_marker")
    for root in roots:
        for node in root.iter():
            values = [str(node.tag), node.text or "", node.tail or ""]
            for key, value in sorted(node.attrib.items()):
                values.extend((key, value))
            for value in values:
                _digest_text(digest, value)
            check(values[1:], "original_xml_or_annotation_literal_marker")
            if node.tag == W_P:
                paragraphs += 1
                value = keep_paragraph(node)
                if not isinstance(value, str):
                    raise UnprovenDeletionState("Native KEEP paragraph is not text")
                check(value, "native_keep_paragraph_literal_marker")
                _digest_text(digest, value)
    return {"version": PROOF_VERSION, "sourceViewSha256": digest.hexdigest(),
            "roots": len(roots), "paragraphs": paragraphs,
            "literalMarkers": collisions, "proven": collisions == 0,
            "unprovenReasons": reasons}


def is_proven(proof):
    return (isinstance(proof, dict) and proof.get("version") == PROOF_VERSION
            and proof.get("proven") is True and proof.get("literalMarkers") == 0
            and proof.get("roots", 0) > 0
            and re.fullmatch(r"[0-9a-f]{64}", proof.get("sourceViewSha256", "")) is not None)


def with_metadata(proof, values):
    if proof is None:
        return None
    try:
        reject_literals(values)
    except UnprovenDeletionState:
        proof = dict(proof, proven=False, literalMarkers=proof.get("literalMarkers", 0) + 1,
                     unprovenReasons=list(dict.fromkeys(proof.get("unprovenReasons", [])
                                                       + ["raw_metadata_literal_marker"])))
    return proof


def proof_summary(chunks):
    docs = {}
    for chunk in chunks:
        proof = chunk.get(PRIVATE)
        tdoc = chunk.get("tdocNumber", "")
        status = {"proven": is_proven(proof),
                  "unprovenReasons": (proof or {}).get("unprovenReasons", ["missing_source_proof"])}
        if tdoc in docs and docs[tdoc] != status:
            raise UnprovenDeletionState("Inconsistent proof status for one CR")
        docs[tdoc] = status
    return {"provenDocuments": sum(x["proven"] for x in docs.values()),
            "legacyUnprovenDocuments": [{"tdocNumber": k, **v} for k, v in docs.items() if not v["proven"]]}


def require_proof(proof):
    if not is_proven(proof):
        raise UnprovenDeletionState("Missing original XML literal collision proof")


@dataclass(frozen=True)
class Parent:
    text: str
    spans: tuple[tuple[int, int, bool], ...]
    marks: tuple[tuple[int, int], ...]

    @classmethod
    def read(cls, text: str, proof):
        require_proof(proof)
        spans, marks = [], []
        deleted, pos = False, 0
        for mark in MARK.finditer(text):
            if pos < mark.start():
                spans.append((pos, mark.start(), deleted))
            opening = mark.group() == "[DEL]"
            if opening == deleted:
                raise UnprovenDeletionState("Original rendered parent has nested or unbalanced DEL")
            deleted = opening
            marks.append((mark.start(), mark.end()))
            pos = mark.end()
        if deleted:
            raise UnprovenDeletionState("Original rendered parent has unclosed DEL")
        if pos < len(text):
            spans.append((pos, len(text), False))
        return cls(text, tuple(spans), tuple(marks))

    def edge(self, pos: int, start: bool):
        if not 0 <= pos <= len(self.text):
            raise ValueError("Source interval outside parent")
        for a, b in self.marks:
            if a < pos < b:
                # Mark tokens have no source content. Select an atomic edge using
                # the proven parent state, never the broken child fragment.
                return b if start else a
        return pos

    def render(self, start: int, end: int):
        start, end = self.edge(start, True), self.edge(end, False)
        if end < start:
            return ""
        def active_before(position):
            active = False
            for a, b in self.marks:
                if b > position:
                    break
                active = self.text[a:b] == "[DEL]"
            return active
        # Preserve every complete interior marker, including adjacent and empty
        # intervals. Only a boundary cut inside deletion adds a missing wrapper.
        value = self.text[start:end]
        opened = active_before(start)
        closed = active_before(end)
        # A boundary at the end of a deletion must not synthesize an empty
        # pair around its closing marker. The symmetric end boundary must not
        # synthesize an empty pair after a terminal opening marker. Interior
        # complete markers, including original empty pairs, remain byte exact.
        if opened and value.startswith("[/DEL]"):
            value = value[6:]
            opened = False
        if closed and value.endswith("[DEL]"):
            value = value[:-5]
            closed = False
        return ("[DEL]" if opened else "") + value + ("[/DEL]" if closed else "")


def split_paragraphs(paragraphs, target, overlap, minimum, count, proof, trim_word=False):
    """Native paragraph selection and overlap with source interval state.

    Paragraph offsets come from the producer's actual ordered list composition;
    there is no find(). MARK parents are validated before any cut. Raw paragraph
    counts retain strategy/selection thresholds; final hardening counts wrappers.
    """
    text = "\n".join(paragraphs)
    parent = Parent.read(text, proof)
    intervals, pos = [], 0
    for p in paragraphs:
        intervals.append((pos, pos + len(p)))
        pos += len(p) + 1
    current, result = [], []
    tokens = carried = 0
    for span in intervals:
        pt = count(text[span[0]:span[1]])
        if tokens + pt > target and current and tokens - carried >= minimum:
            result.append(parent.render(current[0][0], current[-1][1]))
            tail, tail_tokens = [], 0
            for lo, hi in reversed(current):
                value = text[lo:hi]
                qt = count(value)
                if tail_tokens + qt > overlap:
                    if not tail:
                        cut = max(lo, hi - overlap * 4)
                        if trim_word and cut > lo and not text[cut - 1].isspace():
                            space = text.find(" ", cut, hi)
                            if 0 <= space < hi - 1:
                                cut = space + 1
                        cut = parent.edge(cut, True)
                        tail = [(cut, hi)]
                        tail_tokens = count(text[cut:hi])
                    break
                tail.insert(0, (lo, hi))
                tail_tokens += qt
            current, tokens, carried = tail, tail_tokens, tail_tokens
        current.append(span)
        tokens += pt
    if current:
        result.append(parent.render(current[0][0], current[-1][1]))
    return result


def _all_matches(text, value, maximum=4096):
    if not value:
        return []
    out, at = [], 0
    while True:
        at = text.find(value, at)
        if at < 0:
            return out
        out.append((at, at + len(value), False))
        if len(out) > maximum:
            raise UnprovenDeletionState("Too many exact parent interval candidates")
        at += 1


def exact_intervals(text: str, pieces: Sequence[str]):
    """Resolve exact full-parent intervals, requiring a unique complete path.

    Optional repeated first line is a separately rendered interval.
    Permitted overlap is the pinned common splitter 400-character window.
    Contiguous force cuts and whitespace-separated rows use no overlap. First-match
    selection is forbidden. Missing/ambiguous/gapped coverage is unresolved.
    This accepts only exact native fragments, before any marker is reconstructed.
    """
    header_end = text.find("\n") + 1
    header = text[:header_end] if header_end else ""
    paths = [[]]
    for i, piece in enumerate(pieces):
        choices = _all_matches(text, piece)
        if i and header and piece.startswith(header):
            choices += [(a, b, True) for a, b, _ in _all_matches(text, piece[len(header):])]
        choices = list(dict.fromkeys(choices))
        updated = []
        for path in paths:
            for span in choices:
                a, b, lead = span
                if not path:
                    okay = not lead and (a == 0 or text[:a].isspace())
                    if okay:
                        span = (0, b, lead)
                else:
                    previous = path[-1]
                    reach = max(s[1] for s in path)
                    gap = text[reach:a]
                    # Native char windows overlap exactly SPLIT_OVERLAP * 4 = 400.
                    # Force splits are contiguous; rows may drop only whitespace.
                    # Arbitrary overlaps create false paths in repeated content.
                    terminal_tail = b == reach == len(text) and 0 < reach - a <= 400
                    okay = (a > previous[0]
                            and (a == reach or reach - a == 400 or terminal_tail
                                 or (a > reach and gap.isspace())))
                    if okay and a > reach:
                        # Native whitespace loss is explicit source material,
                        # assigned once to the following interval, not dropped.
                        span = (reach, b, lead)
                if okay:
                    updated.append(path + [span])
                    if len(updated) > 64:
                        raise UnprovenDeletionState("Ambiguous native split interval paths")
        paths = updated
        if not paths:
            raise UnprovenDeletionState("Native fragment has no exact covering parent interval")
    complete = []
    for path in paths:
        reach = max((span[1] for span in path), default=0)
        if path and (reach == len(text) or text[reach:].isspace()):
            path = path[:-1] + [(path[-1][0], len(text), path[-1][2])]
            if path not in complete:
                complete.append(path)
    paths = complete
    if len(paths) != 1:
        raise UnprovenDeletionState("Native fragments do not have one complete parent interval mapping")
    return paths[0], header_end


def split_parent(text, native_split, count, limit, minimum, proof):
    """Reuse native split boundaries, then render proven state and count again."""
    parent = Parent.read(text, proof)
    raw = list(native_split(text, limit))
    spans, head_end = exact_intervals(text, raw)
    def render(span):
        a, b, lead = span
        return (parent.render(0, head_end) if lead else "") + parent.render(a, b)
    # Same parent intervals let a short tail merge without string-find guesses.
    stuck = set()
    while len(spans) > 1:
        small = next((i for i, s in enumerate(spans)
                      if tuple(s) not in stuck and count(render(s)) < minimum), None)
        if small is None:
            break
        for neighbour in (small - 1, small + 1):
            if not 0 <= neighbour < len(spans):
                continue
            lo, hi = min(small, neighbour), max(small, neighbour)
            joined = (spans[lo][0], max(spans[lo][1], spans[hi][1]), spans[lo][2])
            if count(render(joined)) <= limit:
                spans[lo:hi + 1] = [joined]
                break
        else:
            stuck.add(tuple(spans[small]))
    output = []
    for a, b, lead in spans:
        prefix = parent.render(0, head_end) if lead else ""
        start = parent.edge(a, True)
        end = parent.edge(b, False)
        while start < end:
            stop = end
            while True:
                piece = prefix + parent.render(start, stop)
                if count(piece) <= limit:
                    break
                first = next((max(start, x) for x, y, _ in parent.spans if y > start), end)
                minimum_end = first + 1
                if stop <= minimum_end:
                    raise UnprovenDeletionState("Context plus smallest source content exceeds hard max")
                stop = parent.edge(max(minimum_end, start + (stop - start) // 2), False)
                if stop < minimum_end:
                    stop = minimum_end
            if piece:
                output.append(piece)
            start = stop
    if not output and text:
        raise UnprovenDeletionState("No source content in split result")
    if any(count(p) > limit for p in output):
        raise UnprovenDeletionState("Balanced piece exceeds hard maximum")
    return output


def take_group_proof(group):
    """Strip private transport proof before any externally persisted output."""
    proofs = [c.get(PRIVATE) for c in group]
    present = [p for p in proofs if p is not None]
    if present and (len(present) != len(group) or any(p != present[0] for p in present)):
        raise UnprovenDeletionState("Inconsistent CR source proof transport")
    for c in group:
        c.pop(PRIVATE, None)
    if present and is_proven(present[0]):
        return present[0]
    return None


def harden_group(group, native, legacy_merge, count, limit, minimum, renumber, base):
    """RAN5 existing ID collision and group renumber policy with proven parents."""
    proof = take_group_proof(group)
    if proof is None or not any(MARK.search(c.get("text") or "") for c in group):
        hardened = native(group, hard_max=limit)
        return legacy_merge(group, hardened, limit, minimum, count, renumber, base)
    reserved = {c["chunkId"] for c in group if isinstance(c.get("chunkId"), str)}
    generated, final, split = set(), [], False
    for chunk in group:
        text = chunk.get("text") or ""
        tokens = count(text)
        if tokens <= limit:
            Parent.read(text, proof)
            final.append(dict(chunk, tokenCount=tokens))
            continue
        if MARK.search(text):
            pieces = split_parent(text, lambda t, n: [c["text"] for c in native([dict(chunk, text=t)], hard_max=n)],
                                  count, limit, minimum, proof)
        else:
            values = native([chunk], hard_max=limit)
            values = legacy_merge([chunk], values, limit, minimum, count, renumber, base)
            pieces = [c["text"] for c in values]
        split = True
        pid = chunk.get("chunkId") or "chunk"
        for i, piece in enumerate(pieces, 1):
            cid = pid
            if len(pieces) > 1:
                suffix = i
                cid = f"{pid}-{suffix:03d}"
                while cid in reserved or cid in generated:
                    suffix += 1
                    cid = f"{pid}-{suffix:03d}"
            generated.add(cid)
            final.append(dict(chunk, text=piece, tokenCount=count(piece), chunkId=cid,
                              chunkIndex=i, totalChunks=len(pieces), _hardMaxEnforced=True,
                              _originalTokenCount=tokens))
    if split:
        renumber(final, base=base)
    return final
