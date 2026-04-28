#!/usr/bin/env python3
"""Reproduce structural_metrics.json from spectra.ttl using rdflib.

Run:
    pip install rdflib
    python3 reproduce_structural_metrics.py

Compares the recomputed metrics with validation/structural_metrics.json
and exits with non-zero status if any field disagrees. This is the simplest
third-party reproducibility check for paper §6.2 / Table 4 numbers.
"""
import json
import sys
from pathlib import Path

import rdflib

ROOT = Path(__file__).resolve().parents[1]
TTL = ROOT / 'ontology' / 'spectra.ttl'
EXPECTED = ROOT / 'validation' / 'structural_metrics.json'

OWL = rdflib.Namespace('http://www.w3.org/2002/07/owl#')
RDFS = rdflib.RDFS
RDF = rdflib.RDF


def main():
    g = rdflib.Graph()
    g.parse(TTL, format='turtle')

    classes = set(g.subjects(RDF.type, OWL.Class))
    obj_props = set(g.subjects(RDF.type, OWL.ObjectProperty))
    data_props = set(g.subjects(RDF.type, OWL.DatatypeProperty))
    func_props = set(g.subjects(RDF.type, OWL.FunctionalProperty))
    inv_func_props = set(g.subjects(RDF.type, OWL.InverseFunctionalProperty))
    irr_props = set(g.subjects(RDF.type, OWL.IrreflexiveProperty))
    asym_props = set(g.subjects(RDF.type, OWL.AsymmetricProperty))
    inverse_pairs = set()
    for s, _, o in g.triples((None, OWL.inverseOf, None)):
        pair = tuple(sorted((str(s), str(o))))
        inverse_pairs.add(pair)
    subclass_axioms = sum(1 for _ in g.triples((None, RDFS.subClassOf, None)))

    # Filter to classes/properties under the spectra namespace (drop FOAF/PROV-O reuse)
    SPECTRA_PREFIX = 'https://w3id.org/spectra#'
    spectra_classes = sum(1 for c in classes if str(c).startswith(SPECTRA_PREFIX))
    spectra_obj = sum(1 for p in obj_props if str(p).startswith(SPECTRA_PREFIX))
    spectra_dp  = sum(1 for p in data_props if str(p).startswith(SPECTRA_PREFIX))

    computed = {
        'classes_total':                  spectra_classes,
        'object_properties':              spectra_obj,
        'data_properties':                spectra_dp,
        'properties_total':               spectra_obj + spectra_dp,
        'functional_properties':          len(func_props),
        'inverse_functional_properties':  len(inv_func_props),
        'inverse_property_pairs':         len(inverse_pairs),
        'irreflexive_properties':         len(irr_props),
        'asymmetric_properties':          len(asym_props),
        'subclass_axioms':                subclass_axioms,
        'triples_total':                  len(g),
    }

    with open(EXPECTED) as f:
        expected = json.load(f)

    print(f'{"Metric":<35} {"Expected":>10} {"Computed":>10} {"OK":>4}')
    print('-' * 65)
    ok = True
    for k, v in computed.items():
        e = expected.get(k)
        if e is None:
            print(f'{k:<35} {"(missing)":>10} {v:>10} {"-":>4}')
            continue
        match = '✓' if e == v else '✗'
        if e != v:
            ok = False
        print(f'{k:<35} {e:>10} {v:>10} {match:>4}')

    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
