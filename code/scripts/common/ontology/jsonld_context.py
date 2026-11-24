#!/usr/bin/env python3
"""jsonld_context.py — Publish formal instances with the core RDF contract.

Spec: docs/common/process/internal_ontology_guide.md
Ontology: ontology/schema/tdoc-ontology.ttl
Cycle: JSON-LD serialization and validation
배경: Producers retain compact identifiers used by the property-graph loaders;
      their JSON-LD contexts bind those identifiers and values to the core schema.
사용: canonical_document(document) before serializing an instance document.
LLM 호출: 없음
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import json
import re
from typing import Any, Iterable, Mapping
from urllib.parse import quote, unquote

from rdflib import Graph, OWL, RDF, RDFS, URIRef
from common import axis


PROJECT_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
SCHEMA_PATH = PROJECT_ROOT / "ontology/schema/tdoc-ontology.ttl"
SPECTRA_NAMESPACE = "https://w3id.org/spectra#"
XSD_NAMESPACE = "http://www.w3.org/2001/XMLSchema#"
# RAN1's Summary/SessionNotes serializers retain these raw loader field names.
# Their documents have the same presentation/agenda roles as other Tdoc artifacts.
PROPERTY_ALIASES = {"meeting": "presentedAt", "agenda": "belongsTo"}


@lru_cache(maxsize=8)
def _schema_terms(path: str, modified_ns: int) -> tuple[frozenset[str], tuple[tuple[str, URIRef], ...]]:
    """Cache a particular schema revision, including edits in a running process."""
    graph = Graph().parse(path, format="turtle")
    object_properties = frozenset(
        str(subject)[len(SPECTRA_NAMESPACE):]
        for subject in graph.subjects(RDF.type, OWL.ObjectProperty)
        if str(subject).startswith(SPECTRA_NAMESPACE)
    )
    datatypes = []
    for subject in graph.subjects(RDF.type, OWL.DatatypeProperty):
        if not str(subject).startswith(SPECTRA_NAMESPACE):
            continue
        ranges = list(graph.objects(subject, RDFS.range))
        if len(ranges) == 1 and isinstance(ranges[0], URIRef):
            datatypes.append((str(subject)[len(SPECTRA_NAMESPACE):], ranges[0]))
    return object_properties, tuple(sorted(datatypes))


def _terms(schema_path: str | Path | None = None):
    path = Path(schema_path or SCHEMA_PATH).resolve()
    return _schema_terms(str(path), path.stat().st_mtime_ns)


def schema_object_properties(schema_path: str | Path | None = None) -> frozenset[str]:
    """Return core object-property local names from the authoritative Turtle file."""
    return _terms(schema_path)[0]


def schema_datatypes(schema_path: str | Path | None = None) -> dict[str, URIRef]:
    """Return each core data-property local name and its declared datatype IRI."""
    return dict(_terms(schema_path)[1])


def canonical_reference(value: str, property_name: str | None = None) -> str:
    """Use the same Spec/Release identities as Phase-1 and release-aware TS.

    This operates on RDF references, never on literal text. TR and impact
    identifiers keep their compact spelling; their context prefixes share the
    core namespace. Phase-5's spec:/release:/rel: aliases need their *local*
    spelling normalized as well, so changing a prefix alone cannot join them.
    """
    for old in ("http://3gpp.org/ontology/tdoc#", "http://example.org/tdoc-ontology#"):
        if value.startswith(old):
            value = "tdoc:" + value[len(old):]
    if value.startswith(SPECTRA_NAMESPACE):
        value = "tdoc:" + value[len(SPECTRA_NAMESPACE):]
    for prefix in ("spec:", "http://example.org/tdoc-ontology/spec/"):
        if value.startswith(prefix):
            return "tdoc:spec/" + value[len(prefix):].replace(".", "_")
    for prefix in ("rel:", "release:", "http://example.org/tdoc-ontology/release/"):
        if value.startswith(prefix):
            return "tdoc:release/" + value[len(prefix):].replace("-", "_")
    if property_name == "targetRelease" and value.startswith("Rel-") and value[4:].isdigit():
        return "tdoc:release/" + value.replace("-", "_")
    if value.startswith("section:"):
        return "tdoc:section/" + value[len("section:"):]
    if value.startswith("tdoc:"):
        # External LS references sometimes contain a title rather than a TDoc
        # number. Preserve that spelling reversibly as an IRI; a space in a
        # compact identifier otherwise expands to the parser's file base.
        return "tdoc:" + quote(value[len("tdoc:"):], safe="/:@!$&'()*+,;=-._~%")
    return value


def reference_identifier(value: str | Mapping[str, Any] | None) -> str:
    """Decode both historical and canonical references for raw JSON loaders.

    Spec IDs decode to the specNumber and Release IDs to the releaseName, which
    are the properties used by existing Neo4j import queries. Other compact
    identifiers retain their local part (TR numbers, impact IDs, section IDs).
    """
    if isinstance(value, Mapping):
        value = value.get("@id")
    if not value:
        return ""
    canonical = canonical_reference(value)
    if canonical.startswith("tdoc:spec/"):
        return canonical[len("tdoc:spec/"):].replace("_", ".")
    if canonical.startswith("tdoc:release/"):
        return canonical[len("tdoc:release/"):].replace("_", "-")
    if canonical.startswith("tdoc:section/"):
        return canonical[len("tdoc:section/"):]
    if canonical.startswith("tdoc:tr/"):
        return canonical[len("tdoc:tr/"):].replace("_", ".")
    if canonical.startswith("tdoc:trimpact/"):
        return canonical[len("tdoc:trimpact/"):]
    return unquote(canonical.split(":", 1)[-1])


def identifier_component(raw: str) -> str:
    """Encode one raw entity key reversibly before constructing a compact ID.

    A literal percent, slash, space and underscore retain separate identities.
    Call this on the raw key, rather than on an already encoded reference.
    """
    return quote(str(raw), safe="-._~")


@lru_cache(maxsize=16)
def _company_aliases(path: str, modified_ns: int) -> dict[str, str]:
    """Use declared aliases, reject colliding canonical IDs and preserve alias ambiguity."""
    catalog = json.loads(Path(path).read_text(encoding="utf-8"))
    candidates: dict[str, set[str]] = {}
    canonical_ids = set()
    canonical_by_fold: dict[str, str] = {}
    for canonical, data in catalog.items():
        target = "tdoc:company/" + identifier_component(canonical)
        folded = target.casefold()
        previous = canonical_by_fold.get(folded)
        if previous is not None and previous != target:
            raise ValueError(
                f"Company canonical IDs collide under case-insensitive lookup: {previous}, {target}; "
                "choose distinct canonical IDs and declare alternative spellings as aliases")
        canonical_by_fold[folded] = target
        canonical_ids.add(target)
        for alias in [canonical, *data.get("aliases", [])]:
            for spelling in {alias, identifier_component(alias),
                             alias.strip().replace(" ", "_").replace("/", "_"),
                             re.sub(r"[^a-zA-Z0-9]", "_", alias)}:
                candidates.setdefault(("tdoc:company/" + spelling).casefold(), set()).add(target)
    result = {key: next(iter(targets)) for key, targets in candidates.items() if len(targets) == 1}
    # A declared canonical identifier always identifies that canonical company.
    result.update({identifier.casefold(): identifier for identifier in canonical_ids})
    return result


def company_reference_aliases(wg: str) -> dict[str, str]:
    """Return traceable URI aliases from the WG's significant company catalog."""
    path = axis.tree_path("ontology_intermediate", wg=wg, root=PROJECT_ROOT) / "phase-1/company_aliases_significant.json"
    if not path.exists():
        return {}
    return _company_aliases(str(path), path.stat().st_mtime_ns)


def canonical_company_reference(value: str, wg: str, *, allow_joint: bool = False) -> str | list[str]:
    """Resolve a company reference through declared aliases and Phase-1 ID syntax."""
    return _resolve_company_reference(value, company_reference_aliases(wg), allow_joint)


def _resolve_company_reference(value: str, aliases: Mapping[str, str], allow_joint: bool) -> str | list[str]:
    match = aliases.get(value.casefold())
    if match:
        return match
    local = unquote(value[len("tdoc:company/"):])
    if allow_joint and "," in local:
        pieces = ["tdoc:company/" + identifier_component(item.strip(" _")) for item in local.split(",")]
        targets = [aliases.get(item.casefold()) for item in pieces]
        if all(targets):
            return list(dict.fromkeys(targets))
    return "tdoc:company/" + identifier_component(local)


def canonical_context(
    existing: Mapping[str, Any] | None = None,
    graph: Iterable[Mapping[str, Any]] = (),
    schema_path: str | Path | None = None,
) -> dict[str, Any]:
    """Bind bare/prefixed fields, references and literals to the core schema.

    Both key spellings occur in the existing producers. Defining them together
    preserves raw JSON field names while standard JSON-LD expansion uses the
    authoritative property's declared object/literal kind and datatype.
    """
    context = dict(existing or {})
    context.update({
        "@vocab": SPECTRA_NAMESPACE,
        "tdoc": SPECTRA_NAMESPACE,
        "xsd": XSD_NAMESPACE,
        "tr": SPECTRA_NAMESPACE + "tr/",
        "trimpact": SPECTRA_NAMESPACE + "trimpact/",
        "impact": SPECTRA_NAMESPACE + "trimpact/",
        "spec": SPECTRA_NAMESPACE + "spec/",
        "rel": SPECTRA_NAMESPACE + "release/",
        "release": SPECTRA_NAMESPACE + "release/",
        "section": SPECTRA_NAMESPACE + "section/",
    })
    for name in sorted(schema_object_properties(schema_path)):
        definition = {"@id": SPECTRA_NAMESPACE + name, "@type": "@id"}
        context[name] = definition
        context["tdoc:" + name] = dict(definition)
    for name, datatype in sorted(schema_datatypes(schema_path).items()):
        definition = {"@id": SPECTRA_NAMESPACE + name, "@type": str(datatype)}
        context[name] = definition
        context["tdoc:" + name] = dict(definition)
    for alias, name in PROPERTY_ALIASES.items():
        definition = {"@id": SPECTRA_NAMESPACE + name, "@type": "@id"}
        context[alias] = definition
        context["tdoc:" + alias] = dict(definition)
    return context


def require_core_context(document: Mapping[str, Any]) -> None:
    """Reject the historical namespace split before structural validators run."""
    context = document.get("@context")
    if not isinstance(context, Mapping) or context.get("tdoc") != SPECTRA_NAMESPACE:
        raise ValueError("JSON-LD tdoc prefix must bind to the authoritative core namespace")
    if context.get("@vocab") != SPECTRA_NAMESPACE:
        raise ValueError("JSON-LD bare classes and properties must use the authoritative core @vocab")
    if not isinstance(document.get("@graph"), list):
        raise ValueError("JSON-LD must contain an explicit @graph list")


def require_core_rdf_targets(document: Mapping[str, Any]) -> Graph:
    """Parse with a standard RDF parser and reject zero-target namespace passes."""
    require_core_context(document)
    graph = Graph().parse(data=json.dumps(document), format="json-ld")
    expected = set()
    for node in document["@graph"]:
        types = node.get("@type", [])
        for value in [types] if isinstance(types, str) else types:
            if value.startswith("tdoc:"):
                expected.add(URIRef(SPECTRA_NAMESPACE + value[len("tdoc:"):]))
            elif ":" not in value:
                expected.add(URIRef(SPECTRA_NAMESPACE + value))
    absent = [str(cls) for cls in expected if not any(graph.subjects(RDF.type, cls))]
    if absent:
        raise ValueError(f"JSON-LD declares classes with zero canonical RDF targets: {absent}")
    return graph


def canonical_document(
    document: Mapping[str, Any], schema_path: str | Path | None = None,
    *, wg: str | None = None,
) -> dict[str, Any]:
    """Return core RDF bindings and references without changing literal content."""
    if "@graph" not in document:
        raise ValueError("An instance document must contain @graph")
    existing = document.get("@context", {})
    if not isinstance(existing, Mapping):
        raise ValueError("An instance document must use a local object @context")
    object_properties = schema_object_properties(schema_path)
    company_aliases = company_reference_aliases(wg) if wg else {}

    def reference(value: str, property_name: str | None = None):
        value = canonical_reference(value, property_name)
        if not value.startswith("tdoc:company/"):
            return value
        if wg:
            return _resolve_company_reference(value, company_aliases, property_name in {"moderatedBy", "chairedBy"})
        return value

    def normalize(value: Any, property_name: str | None = None) -> Any:
        if isinstance(value, list):
            result = []
            for item in value:
                normalized = normalize(item, property_name)
                result.extend(normalized if isinstance(normalized, list) else [normalized])
            return result
        if isinstance(value, Mapping):
            result = {}
            for key, item in value.items():
                local = key[len("tdoc:"):] if key.startswith("tdoc:") else key
                local = PROPERTY_ALIASES.get(local, local)
                if key == "@id":
                    result[key] = (reference(item, property_name) if property_name
                                   else canonical_reference(item))
                elif local in object_properties:
                    result[key] = normalize(item, local)
                else:
                    result[key] = item
            return result
        if isinstance(value, str) and property_name in object_properties:
            return reference(value, property_name)
        return value

    graph = [normalize(node) for node in document["@graph"]]
    result = {
        **document,
        "@context": canonical_context(existing, graph, schema_path),
        "@graph": graph,
    }
    require_core_context(result)
    return result
