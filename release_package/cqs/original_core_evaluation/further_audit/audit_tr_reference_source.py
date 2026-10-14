"""Read every frozen RAN4 TR-reference role and compare the saved native pool."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
parser_path = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/pipeline/load_released_kg.py')
spec = importlib.util.spec_from_file_location('source_parser', parser_path)
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)
source_path = ROOT / 'release_package/kg/per_wg/RAN4-body.ttl'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


reports = {}
edges = set()
edge_source_labels = {}
with source_path.open() as stream:
    for statement in parser.StatementReader(stream):
        if 'spectra:TechnicalReport' not in statement and 'spectra:referencesTr' not in statement:
            continue
        parsed = parser.parse_statement(statement)
        if parsed is None:
            continue
        iri, predicates = parsed
        labels = {value[1] for (prefix, name), objects in predicates if (prefix, name) == ('rdf', 'type')
                  for kind, value in objects if kind == 'pname' and value[0] == 'spectra'}
        if 'TechnicalReport' in labels:
            reports[iri] = next((value for (prefix, name), objects in predicates
                                if (prefix, name) == ('spectra', 'trNumber')
                                for kind, value in objects if kind == 'lit'), None)
        for (prefix, name), objects in predicates:
            if (prefix, name) == ('spectra', 'referencesTr'):
                edge_source_labels[iri] = sorted(labels)
                edges.update((iri, value) for kind, value in objects if kind == 'iri')
unexpected = [{'source':source, 'target':target, 'source_labels':edge_source_labels[source]}
              for source, target in edges if source not in reports or target not in reports]
counts = Counter(target for source, target in edges if source in reports and target in reports)
pool = [{'trNumber':number, 'referenceCount':counts[iri]} for iri, number in sorted(reports.items())]
tasks = [json.loads(line) for line in (BASE / 'native_capture/tasks.jsonl').read_text().splitlines()]
task = next(task for task in tasks if task['id'] == 'RAN4_P5_CQ5-3')
receipt = task['reference_evidence']
rows_path = BASE / 'native_capture' / receipt['rows_file']
rows = [json.loads(line) for line in rows_path.read_text().splitlines()]
native = [dict(zip(receipt['columns'], row)) for row in rows]
equivalent = sorted(pool, key=lambda row:row['trNumber']) == sorted(native, key=lambda row:row['trNumber'])
report = {'kind':'Separate full frozen-source TR-reference role/count audit; no DB/model execution',
          'id':task['id'],'repair_sha256':task['repair_sha256'],
          'graph_source_path':str(source_path.relative_to(ROOT)),'graph_source_sha256':sha(source_path),
          'parser_sha256':sha(parser_path),'actual_TTL_predicate':'spectra:referencesTr',
          'actual_loader_relation':'REFERENCES_TR','all_reference_edges_n':len(edges),
          'unexpected_source_or_target_role_n':len(unexpected),'unexpected_roles':unexpected,
          'TR_population_n':len(reports),'TR_number_missing_n':sum(value is None for value in reports.values()),
          'TR_number_duplicate_n':len(reports)-len(set(reports.values())),
          'zero_reference_TR_n':sum(row['referenceCount']==0 for row in pool),
          'complete_source_pool':pool,'actual_native_rows_sha256':sha(rows_path),
          'actual_native_rows_n':len(native),'full_native_counts_equal_independent_source_counts':equivalent,
          'source_graph_equals_native_receipt':sha(source_path)==receipt['provenance']['graph_source_sha256'],
          'status':'pass' if equivalent and not unexpected else 'fail',
          'expert_validation_n':0,'human_author_review_completed':False}
out = BASE / 'TR_reference_source_witness_RAN4.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:report[key] for key in ['status','all_reference_edges_n','unexpected_source_or_target_role_n',
                                            'TR_population_n','zero_reference_TR_n',
                                            'full_native_counts_equal_independent_source_counts']}))
print(json.dumps({'path':str(out),'sha256':sha(out)}))
