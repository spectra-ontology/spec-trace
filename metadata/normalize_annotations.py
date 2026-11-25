#!/usr/bin/env python3
"""normalize_annotations — reproduce the English annotation normalization.

Spec: metadata discovery and annotation-language consistency.
Ontology: package vocabulary 1.2.0 and construction snapshot 7.3.0.
Cycle: resource annotation normalization.
Background: exact translations align English tags; a repository annotation identifies the current artifact.
Usage: python3 -B metadata/normalize_annotations.py --release . [--apply]
LLM calls: none. This program performs deterministic local transformations.
"""
from __future__ import annotations

__version__ = "1.0.0"

import argparse
import hashlib
import json
import re
from pathlib import Path

from rdflib import Graph, Literal, RDFS, Namespace, URIRef
from rdflib.compare import isomorphic

SH = Namespace("http://www.w3.org/ns/shacl#")
OLD_REPOSITORY = URIRef("https://github.com/spectra-ontology/spectra")
CURRENT_REPOSITORY = URIRef("https://github.com/spectra-ontology/spec-trace")
FILES = ("docs/spectra.ttl", "docs/spectra-shapes.ttl", "ontology/tdoc-ontology.ttl", "ontology/tdoc-ontology-shapes.ttl")
TRANSLATIONS = {
    "Meeting where this Resolution was made (1..*, COVID-19 이중 Meeting 허용, Phase-2 Spec §6 P2-D09)": "Meeting where this Resolution was made (1..*, including dual meetings during COVID-19; Phase-2 Spec §6 P2-D09)",
    "TDoc that replies to this TDoc (복수 WG 답변 허용, Phase-1 Spec §10 P1-D09)": "TDoc that replies to this TDoc (multiple WG replies supported; Phase-1 Spec §10 P1-D09)",
    "Feature는 3GPP standardization feature. Release 표시 필수. v3.0 신규: usesIE / hasCapability / hasProcedure / disjointWith 관계 shape.": "Feature represents a 3GPP standardization feature and requires a release identifier. Entity layer 3.0 introduced shapes for usesIE, hasCapability, hasProcedure and disjointWith.",
    "release-aware hybrid Spec 무결성: 허브/release-키 역할의 상호 배타 + release-키의 허브 연결 의무.": "Release-aware hybrid Spec integrity: hub and release-keyed roles are mutually exclusive, and each release-keyed Spec must link to its hub.",
    "inReleaseOf의 타깃은 항상 허브 — release-키 변형끼리의 연결(체인) 금지.": "The target of inReleaseOf is always a Spec hub; release-keyed variants link directly to their hub.",
    "granularity must be one of: item (v3.0 신규) / section (legacy) / sub-item": "granularity must be one of: item (introduced in entity layer 3.0) / section (legacy) / sub-item",
    "Procedure는 spec body protocol procedure. PHY/MAC/RRC/NW interface spec만. v3.0: independent class.": "Procedure represents a protocol procedure in the body of a PHY, MAC, RRC or network-interface specification. Entity layer 3.0 defines it as an independent class.",
    "CapabilityItem은 UE capability item. spec은 38.306 (UE-cap) / 38.101-x (UE RF cap) / 38.508-1 (test cap). v3.0: independent class.": "CapabilityItem represents a UE capability item from 38.306 (UE capability), 38.101-x (UE RF capability) or 38.508-1 (test capability). Entity layer 3.0 defines it as an independent class.",
    "hasSection 은 최상위 절만 — 하위 절의 소속은 belongsToSpec 으로만 표현한다.": "hasSection links top-level sections only; membership of subsections is expressed through belongsToSpec only.",
    "ConformanceTest는 UE/BS conformance test spec body. RAN5 UE test (38.508-x, 38.509, 38.521-x, 38.523-1, 38.533) + RAN4 BS test (38.141-x, 38.181). v3.0: independent class.": "ConformanceTest represents a conformance test in a UE or BS test specification: RAN5 UE tests (38.508-x, 38.509, 38.521-x, 38.523-1, 38.533) and RAN4 BS tests (38.141-x, 38.181). Entity layer 3.0 defines it as an independent class.",
    "RRCParameter는 ASN.1 IE 본질. specNumber는 실제 ASN.1 IE 입력이 있는 38.331, 38.355 및 NW interface 규격을 사용한다. Entity는 Section과 definedInSection으로 연결한다.": "RRCParameter represents an ASN.1 information element. Its specNumber identifies an observed ASN.1 IE source in 38.331, 38.355 or the listed network-interface specifications. The entity links to its Section through definedInSection.",
    "PerformanceRequirement는 RRM/RF perf req spec body. 38.133 RRM / 38.101-x UE RF / 38.104 BS RF만. v3.0: independent class.": "PerformanceRequirement represents a requirement in an RRM or RF specification: 38.133 (RRM), 38.101-x (UE RF) or 38.104 (BS RF). Entity layer 3.0 defines it as an independent class.",
    "Section은 release-키 Spec에만 귀속 — 허브 직접 귀속 금지 (release별 Section 우주 분리 보장). Section의 specNumber는 그 소속 Spec의 specNumber 사본이다.": "Each Section belongs to a release-keyed Spec, keeping section membership separate by release. The Section's specNumber is a copy of its owning Spec's specNumber.",
    "Feature 노드는 entity 클래스 (5종)와 동시에 속할 수 없다 (의미적 disjoint).": "Feature is semantically disjoint with each of the five entity classes."
}


def structural_graph(graph: Graph) -> Graph:
    result = Graph()
    for s, p, o in graph:
        if p not in (RDFS.comment, SH.message, RDFS.seeAlso):
            result.add((s, p, o))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--apply", action="store_true", help="Write exact annotation mappings after validating all four files")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    prepared = []
    files = []
    occurrences = {old: 0 for old in TRANSLATIONS}
    reverse = {new: old for old, new in TRANSLATIONS.items()}
    for rel in FILES:
        path = args.release / rel
        before = path.read_bytes()
        text = before.decode("utf-8")
        graph = Graph().parse(data=text, format="turtle")
        changed = 0
        changed_links = 0
        for s, p, o in graph:
            if o == OLD_REPOSITORY:
                assert p == RDFS.seeAlso, (rel, s, p)
                assert text.count(OLD_REPOSITORY.n3()) == 1
                text = text.replace(OLD_REPOSITORY.n3(), CURRENT_REPOSITORY.n3())
                changed_links += 1
            if not isinstance(o, Literal):
                continue
            value = str(o)
            if re.search("[가-힣]", value):
                assert p in (RDFS.comment, SH.message) and value in TRANSLATIONS, (rel, s, p, value)
                old_literal, new_literal = o.n3(), Literal(TRANSLATIONS[value], lang="en").n3()
                assert text.count(old_literal) == 1
                text = text.replace(old_literal, new_literal)
                changed += 1
                occurrences[value] += 1
            elif value in reverse:
                assert p in (RDFS.comment, SH.message) and o.language == "en", (rel, s, p, value)
                occurrences[reverse[value]] += 1
        after = text.encode("utf-8")
        normalized = Graph().parse(data=text, format="turtle")
        assert len(graph) == len(normalized), rel
        assert isomorphic(structural_graph(graph), structural_graph(normalized)), rel
        assert not any(isinstance(o, Literal) and re.search("[가-힣]", str(o)) for _, _, o in normalized), rel
        prepared.append((path, before, after))
        files.append({"path": rel, "changed_annotations": changed, "changed_see_also_links": changed_links, "before_sha256": hashlib.sha256(before).hexdigest(), "after_sha256": hashlib.sha256(after).hexdigest(), "non_annotation_graph_isomorphic": True, "triple_count_unchanged": True})
    assert all(count == 2 for count in occurrences.values()), occurrences
    pending_literals = sum(row["changed_annotations"] for row in files)
    pending_links = sum(row["changed_see_also_links"] for row in files)
    pending = pending_literals + pending_links
    if args.apply:
        for path, before, after in prepared:
            assert path.read_bytes() == before, str(path)
        for path, before, after in prepared:
            if before != after:
                path.write_bytes(after)
    result = {"status": "pass" if not pending or args.apply else "pending", "applied": args.apply, "changed_annotations": pending_literals, "changed_see_also_links": pending_links, "exact_translation_pairs": len(TRANSLATIONS), "repository_annotation_mapping": {"predicate": str(RDFS.seeAlso), "before": str(OLD_REPOSITORY), "after": str(CURRENT_REPOSITORY)}, "verified_annotation_occurrences": sum(occurrences.values()), "files": files}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if pending and not args.apply:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
