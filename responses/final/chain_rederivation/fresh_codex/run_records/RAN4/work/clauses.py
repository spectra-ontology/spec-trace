"""Extract small clause and CR-side relations from the supplied record files."""
import json


def values(value):
    return value if isinstance(value, list) else [value]


TRACE = {
    'RAN4-q4cc856ebbcdb': ('R4-2400632', '38.101-1'),
    'RAN4-q5564f8be249d': ('R4-2313080', '38.101-1'),
    'RAN4-q89cd953bf6e9': ('R4-2102876', '38.133'),
    'RAN4-qd52324c426b0': ('R4-2309870', '38.108'),
}
QUERIES = {
    'RAN4-q110ba8383702': ('38.151', 'Rel-17', 'B.2.3'),
    'RAN4-q1fe3755d6b40': ('38.133', 'Rel-16', 'A.4.6.1.4.2'),
    'RAN4-q8bd430fcdab9': ('38.133', 'Rel-17', '12'),
    'RAN4-qefd2278270e5': ('38.101-1', 'Rel-19', '6.3A.3.3.7'),
}


def extract():
    output = {'trace': {}, 'queries': {}, 'cr_extensions': {}}
    with open('records/phase-4/section_extensions.jsonld') as stream:
        graph = json.load(stream)['@graph']
    for qid, (document, spec) in TRACE.items():
        sections = []
        for record in graph:
            section = record['@id']
            if ('tdoc:' + document) in values(record.get('modifiedByCR', [])):
                prefix = 'tdoc:section/' + spec + '-'
                if section.startswith(prefix):
                    sections.append(section.split('-Rel-', 1)[1].split('-', 1)[1])
        output['trace'][qid] = {'document': document, 'clauses': sorted(set(sections))}
    for qid, (spec, release, clause) in QUERIES.items():
        section_id = 'tdoc:section/' + '-'.join((spec, release, clause))
        exact, descendant = set(), set()
        for record in graph:
            documents = {value.removeprefix('tdoc:') for value in values(record.get('modifiedByCR', []))}
            if record['@id'] == section_id:
                exact.update(documents)
            elif record['@id'].startswith(section_id + '.'):
                descendant.update(documents)
        output['queries'][qid] = {
            'exact': sorted(exact),
            'descendants_only': sorted(descendant - exact),
            'inclusive': sorted(exact | descendant),
        }
    del graph
    targets = {entry['document'] for entry in output['trace'].values()}
    targets.update(document for entry in output['queries'].values() for document in entry['inclusive'])
    with open('records/phase-4/cr_extensions.jsonld') as stream:
        graph = json.load(stream)['@graph']
    for record in graph:
        document = record['@id'].removeprefix('tdoc:')
        if document in targets:
            output['cr_extensions'][document] = {
                'packs': [value.removeprefix('tdoc:crpack/') for value in values(record.get('belongsToCRPack', []))],
                'modifiesSection': values(record.get('modifiesSection', [])),
            }
    return output


if __name__ == '__main__':
    print(json.dumps(extract(), ensure_ascii=False))
