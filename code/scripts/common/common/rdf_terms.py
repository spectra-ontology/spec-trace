"""Canonical RDF literal terms shared by build and full SHACL checks."""
from rdflib import Graph, Literal, XSD


def normalize_string_literals(graph: Graph) -> Graph:
    """Canonicalize RDF 1.1 simple/xsd:string terms for SHACL term equality.

    RDFLib distinguishes their syntactic forms in sh:in/hasValue membership.
    Language-tagged strings and all other datatypes retain their exact terms.
    """
    for subject, predicate, value in list(graph):
        if isinstance(value, Literal) and value.datatype == XSD.string:
            graph.remove((subject, predicate, value))
            graph.add((subject, predicate, Literal(str(value))))
    return graph
