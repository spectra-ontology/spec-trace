"""Offline replay of complete frozen-source maximum-frequency witnesses.

The complete pool is retained evidence derived from the pinned frozen graph.
This replay checks the retained derivation and native answer equivalence; it does
not parse an external archive or certify graph facts or domain expertise.
"""
import hashlib
import json
from pathlib import Path

import scorer

REQUIRED_IDS = {'RAN5_P3_CQ2-4', 'RAN3_P3_CQ2-3'}
SOURCE_DOCUMENT_SHA = 'de154879dbc9f2c9f50ae5ad5153e22ec988b764963a9ce603a1cea6c61b94d9'
DERIVATION_SHA = 'bb15122f9480a822e3a91e654bfb56095bd16c4131a3952fadf4f118ffc86cb7'
PARSER_SHA = '9499ac120ea4fcf1c2707f6e3151e399530d9b4f43f5aec9d2d93040792d6e25'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(scorer.get_kernel().json_exact(value).encode()).hexdigest()


def pinned_file(base, manifest, item, prefix):
    relative, expected = item[prefix + '_file'], item[prefix + '_sha256']
    path = (base / relative).resolve()
    if (not path.is_relative_to(base.resolve()) or relative not in manifest['files']
            or manifest['files'][relative] != expected or sha(path) != expected):
        raise ValueError('maximum-pool portable file pin differs: ' + prefix)
    return path


def verify(base, task, native_records, manifest):
    base = Path(base)
    witness = task.get('completeness_witness')
    if (task['id'] not in REQUIRED_IDS or not witness
            or witness.get('kind') != 'full_frozen_source_frequency_pool'):
        raise ValueError('required complete maximum-frequency pool witness absent')
    if (task['collection']['kind'] != 'set' or task['cardinality_policy']['mode'] != 'all'
            or witness['id'] != task['id'] or witness['repair_sha256'] != task['repair_sha256']
            or witness['original_question_sha256'] != task['original_question_sha256']
            or witness['query_sha256'] != task['reference_query_sha256']
            or witness['expert_validation_n'] != 0
            or witness['human_author_review_completed'] is not False
            or witness['native_argmax_matches_complete_source_pool'] is not True):
        raise ValueError('maximum-frequency witness task identity or scope differs')
    files = witness['portable_source_evidence']
    document_path = pinned_file(base, manifest, files, 'source_witness')
    code_path = pinned_file(base, manifest, files, 'derivation_script')
    parser_path = pinned_file(base, manifest, files, 'parser')
    if (sha(document_path) != SOURCE_DOCUMENT_SHA or sha(code_path) != DERIVATION_SHA
            or sha(parser_path) != PARSER_SHA
            or witness['source_witness_sha256'] != SOURCE_DOCUMENT_SHA
            or witness['derivation_script_sha256'] != DERIVATION_SHA
            or witness['parser_sha256'] != PARSER_SHA):
        raise ValueError('maximum-frequency derivation source identity differs')
    document = json.loads(document_path.read_text())
    if document['parser_sha256'] != PARSER_SHA:
        raise ValueError('maximum-frequency parser identity differs')
    matches = [row for row in document['results'] if row['id'] == task['id']]
    if len(matches) != 1:
        raise ValueError('maximum-frequency source pool missing or duplicated')
    source = matches[0]
    graph_sha = manifest['graph_sources'][task['id'].split('_')[0]]['source']['sha256']
    evidence = task['portable_native_evidence']
    native_run = json.loads((base / evidence['run_report_file']).read_text())
    if (source['graph_source_sha256'] != graph_sha
            or witness['graph_source_sha256'] != graph_sha
            or witness['graph_source_path'] != source['graph_source_path']
            or native_run['source_before']['source']['sha256'] != graph_sha
            or native_run['source_after'] != native_run['source_before']
            or task['reference_evidence']['provenance']['graph_source_sha256'] != graph_sha
            or witness['native_receipt_sha256'] != evidence['receipt_sha256']
            or witness['native_rows_sha256'] != evidence['rows_sha256']):
        raise ValueError('maximum-frequency pool and native source pins differ')
    if 'pool_path' in source:
        pool_path = pinned_file(base, manifest, files, 'source_pool')
        if (sha(pool_path) != source['pool_sha256']
                or witness['source_pool_sha256'] != source['pool_sha256']):
            raise ValueError('complete maximum-frequency pool rows changed')
        pool = [scorer.get_kernel().loads_exact(line)
                for line in pool_path.read_text().splitlines() if line.strip()]
        if (len(pool) != source['pool_count']
                or sum(row['referenceCount'] == 0 for row in pool) != source['zero_count']):
            raise ValueError('maximum-frequency full-pool cardinality differs')
    else:
        pool = source['pool']
    fields = task['required_fields']
    names = [field['name'] for field in fields]
    if (not fields or len(names) != len(set(names)) or 'referenceCount' in names
            or any(field['type'] != 'string' or field['nullable'] is not False for field in fields)
            or not pool):
        raise ValueError('maximum-frequency requested identity schema differs')
    identities = []
    for row in pool:
        if (set(row) != set(names) | {'referenceCount'}
                or type(row['referenceCount']) is not int or row['referenceCount'] < 0
                or any(type(row[name]) is not str or not row[name] for name in names)):
            raise ValueError('maximum-frequency complete pool contains invalid values')
        identities.append(digest({name: row[name] for name in names}))
    if len(identities) != len(set(identities)):
        raise ValueError('maximum-frequency pool duplicates requested identities')
    maximum = max(row['referenceCount'] for row in pool)
    expected = [{name: row[name] for name in names}
                for row in pool if row['referenceCount'] == maximum]
    expected_tokens = sorted(map(digest, expected))
    if (maximum != source['maximum'] or maximum != witness['maximum_frequency']
            or len(pool) != witness['source_pool_n']
            or sum(row['referenceCount'] == 0 for row in pool) != witness['source_zero_n']
            or len(expected) != witness['maximum_tie_n']
            or expected_tokens != sorted(map(digest, source['maximal_requested_records']))
            or expected_tokens != sorted(map(digest, native_records))
            or digest(sorted(expected, key=digest)) != witness['expected_maximum_records_sha256']
            or digest(native_records) != witness['actual_native_projected_records_sha256']):
        raise ValueError('actual native answers differ from complete-pool maximum ties')
