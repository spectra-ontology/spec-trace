"""Read frozen TTL for separate followup semantic evidence; never query a DB."""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[5]
BASE = Path(__file__).resolve().parent
LOADER = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/pipeline/load_released_kg.py')
spec = importlib.util.spec_from_file_location('frozen_loader', LOADER)
loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loader)


def hash_file(path):
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def audit(wg):
    start = time.monotonic()
    source = ROOT / 'release_package/kg/per_wg' / (wg + '-body.ttl')
    nodes = {}
    relations = set()
    wanted = {'belongsToSpec', 'referencesSection', 'referencesTr', 'resolutionBelongsTo',
              'belongsTo', 'moderatedBy', 'hasSubSection', 'containsTable', 'containsFigure'}
    statements = 0
    with source.open() as fh:
        for statement in loader.StatementReader(fh):
            parsed = loader.parse_statement(statement)
            if parsed is None:
                continue
            iri, predicates = parsed
            match = loader.INST_RE.match(iri)
            if not match:
                continue
            statements += 1
            key = (match.group('cls'), match.group('nid'))
            node = nodes.setdefault(key, {'labels': set(), 'props': {}, 'raw': iri})
            for (prefix, local), objects in predicates:
                if prefix == 'rdf' and local == 'type':
                    node['labels'].update(v[1] for t, v in objects if t == 'pname' and v[0] == 'spectra')
                if prefix != 'spectra':
                    continue
                if local in {'id', 'sectionId', 'tableId', 'figureId', 'trNumber', 'specNumber', 'specRelease',
                             'sectionNumber', 'companyName', 'summaryId'}:
                    values = [v for t, v in objects if t == 'lit']
                    if values:
                        node['props'][local] = values[0] if len(values) == 1 else sorted(map(str, values))
                if local in wanted:
                    for kind, value in objects:
                        if kind == 'iri':
                            target = loader.INST_RE.match(value)
                            if target:
                                relations.add((key, local, (target.group('cls'), target.group('nid'))))
    def label_keys(label):
        return {key for key, node in nodes.items() if label in node['labels']}
    def identity_audit(label, field):
        population = label_keys(label)
        values = []
        absent = []
        for key in population:
            value = nodes[key]['props'].get(field)
            if value is None:
                absent.append(nodes[key]['raw'])
                value = 'https://w3id.org/spectra/inst/_/' + key[0] + '/' + key[1]
            values.append(value)
        count = collections.Counter(values)
        return {'population': len(population), 'missing_property': len(absent),
                'missing_property_source_examples': sorted(absent)[:5],
                'effective_identity_duplicates': {str(k): v for k, v in count.items() if v > 1}}
    result = {'kind': 'Direct full frozen-TTL read for separate AI secondary evidence; no DB/model execution',
              'wg': wg, 'graph_source_path': str(source.relative_to(ROOT)),
              'graph_source_sha256': hash_file(source), 'parser_sha256': hash_file(LOADER),
              'source_statements': statements, 'identity_audits': {
                  label: identity_audit(label, field) for label, field in
                  [('AgendaItem', 'id'), ('Section', 'sectionId'), ('TechnicalReport', 'trNumber'), ('Spec', 'specNumber')]}}
    by_target = collections.defaultdict(set)
    section_pairs = collections.Counter()
    for source_key, relationship, target_key in relations:
        if relationship == 'belongsToSpec':
            by_target[source_key].add(target_key)
        if relationship == 'referencesSection':
            section_pairs[(source_key, target_key)] += 1
    result['reference_unit_equivalence'] = {
        'distinct_section_reference_source_target_pairs': len(section_pairs),
        'duplicate_section_reference_source_target_pairs': sum(v - 1 for v in section_pairs.values()),
        'section_membership_maximum_spec_nodes': max(map(len, by_target.values()), default=0),
        'loader_relation_set_deduplicates': True,
        'incoming_reference_unit': 'one recorded directed REFERENCES_SECTION source-target edge, identical to one referencing Section per target on this deduplicated relation'}
    agenda = label_keys('AgendaItem')
    resolution = label_keys('Resolution')
    tdocs = label_keys('Tdoc')
    result['agenda_role_checks'] = {}
    for relation, expected in [('resolutionBelongsTo', resolution), ('belongsTo', tdocs)]:
        edges = [(a, b) for a, r, b in relations if r == relation and b in agenda]
        result['agenda_role_checks'][relation] = {
            'edges_to_agenda': len(edges),
            'unexpected_source_label': sum(a not in expected for a, b in edges),
            'zero_agenda_items': len(agenda - {b for a, b in edges if a in expected})}
    tr = label_keys('TechnicalReport')
    tr_numbers = collections.defaultdict(list)
    for key in tr:
        tr_numbers[str(nodes[key]['props'].get('trNumber'))].append(key)
    result['technical_report_number_groups'] = {k: len(v) for k, v in sorted(tr_numbers.items())}
    if wg == 'RAN3':
        zte = {k for k, n in nodes.items() if n['props'].get('companyName') == 'ZTE' and 'Company' in n['labels']}
        moderated = {a for a, r, b in relations if r == 'moderatedBy' and b in zte and 'Summary' in nodes[a]['labels']}
        agendas = {b for a, r, b in relations if r == 'resolutionBelongsTo' and a in moderated and b in agenda}
        result['zte_moderation_lookup'] = {'canonical_company_nodes': len(zte), 'moderated_summary_nodes': len(moderated),
                                           'distinct_agenda_nodes': len(agendas)}
    if wg == 'RAN5':
        lookups = [('CQ1-2', '38.533', '5', 'hasSubSection', 'sectionId'),
                   ('CQ1-12', '38.523-1', '7', 'hasSubSection', 'sectionId'),
                   ('CQ1-5', '38.521-1', '6.2.3', 'containsTable', 'tableId'),
                   ('CQ1-6', '38.509', '5.3.4.1', 'containsFigure', 'figureId'),
                   ('CQ2-1', '38.521-1', '6.5D.3.3.5', 'referencesSection', 'sectionId')]
        lookup_evidence = {}
        for identifier, number, section, relation, field in lookups:
            parents = {k for k, n in nodes.items() if 'Section' in n['labels'] and n['props'].get('sectionNumber') == section}
            matching = {p: {s for s in by_target[p] if nodes[s]['props'].get('specNumber') == number} for p in parents}
            matching = {p: owners for p, owners in matching.items() if owners}
            release = {p: max((int(str(nodes[s]['props']['specRelease']).replace('Rel-', '')) for s in owners
                              if nodes[s]['props'].get('specRelease')), default=-1) for p, owners in matching.items()}
            max_release = max(release.values(), default=-1)
            output = collections.defaultdict(set)
            for p, r, target in relations:
                if p in matching and r == relation:
                    output[release[p]].add(nodes[target]['props'].get(field))
            all_values = set().union(*output.values()) if output else set()
            latest_values = output[max_release]
            lookup_evidence['RAN5_P3_' + identifier] = {
                'matching_parent_nodes': len(matching), 'parent_release_counts': dict(collections.Counter(release.values())),
                'maximum_recorded_release': max_release,
                'all_release_output_count': len(all_values), 'latest_release_output_count': len(latest_values),
                'extra_all_release_identity_count': len(all_values - latest_values),
                'all_release_null_identity_count': int(None in all_values),
                'all_release_output_examples': sorted(str(v) for v in all_values)[:4]}
        result['lookup_population_difference'] = lookup_evidence
    result['elapsed_seconds'] = round(time.monotonic() - start, 2)
    target = BASE / ('secondary_source_audit_' + wg + '.json')
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'wg': wg, 'path': str(target.relative_to(ROOT)), 'sha256': hash_file(target),
                      'elapsed_seconds': result['elapsed_seconds'],
                      'identities': result['identity_audits'], 'lookup_population_difference': result.get('lookup_population_difference')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    for group in ['RAN3', 'RAN4', 'RAN5']:
        audit(group)
