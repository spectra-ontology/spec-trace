#!/usr/bin/python3
"""Replay frozen first responses and recompute answers from table relations."""

import argparse
import ast
import gzip
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time


RELEASE = None
STUDY = None


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def label(path):
    try:
        return str(Path(path).resolve().relative_to(RELEASE))
    except ValueError:
        return str(Path(path).resolve())


def load(path):
    return json.loads(Path(path).read_text())


def normalized(rows):
    """Canonical textual row set; raw rows retain multiplicity and NULLs."""
    return [list(row) for row in sorted({tuple('' if cell is None else str(cell) for cell in row) for row in rows})]


def open_readonly(path):
    connection = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    connection.execute('PRAGMA query_only=ON')
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}

    def authorize(action, arg1, arg2, database, source):
        if action not in allowed:
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION and (arg2 or '').lower() in {'load_extension', 'writefile', 'readfile', 'eval'}:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    connection.set_authorizer(authorize)
    return connection


def execute(connection, sql, cap):
    start = time.monotonic()
    deadline = start + cap
    expired = False

    def progress():
        nonlocal expired
        expired = time.monotonic() >= deadline
        return int(expired)

    connection.set_progress_handler(progress, 1000)
    try:
        cursor = connection.execute(sql)
        raw = [list(row) for row in cursor.fetchall()]
        return {'status': 'returned', 'actual': normalized(raw), 'raw_rows': raw,
                'columns': [entry[0] for entry in cursor.description],
                'raw_row_count': len(raw), 'normalized_row_count': len(normalized(raw)),
                'null_cells': sum(cell is None for row in raw for cell in row),
                'seconds': time.monotonic() - start}
    except sqlite3.Error as error:
        return {'status': 'timeout' if expired else 'error', 'actual': [], 'raw_rows': [],
                'error_type': type(error).__name__, 'error': str(error),
                'seconds': time.monotonic() - start}
    finally:
        connection.set_progress_handler(None, 0)


def read_relations(connection, cap):
    requests = {
        'membership': 'SELECT cr,pack_id FROM cr_in_pack',
        'section': 'SELECT id,spec,release,clause FROM section',
        'link': 'SELECT cr,section_id FROM cr_modifies_section',
        'disposition': 'SELECT resolution_id,target,code,evidence_status,scope FROM disposition',
        'resolution': 'SELECT id,meeting_id FROM resolution',
    }
    raw = {}
    receipts = {}
    for name, sql in requests.items():
        result = execute(connection, sql, cap)
        if result['status'] != 'returned':
            raise RuntimeError('Independent relation read failed: ' + name + ' ' + repr(result))
        raw[name] = result['raw_rows']
        receipts[name] = {'sql': sql, 'raw_row_count': len(raw[name]), 'seconds': result['seconds']}
    packs = defaultdict(set)
    for cr, pack in raw['membership']:
        packs[pack].add(cr)
    sections = {row[0]: tuple(row[1:]) for row in raw['section']}
    typed_links = defaultdict(set)
    linked_documents = set()
    for cr, section_id in raw['link']:
        linked_documents.add(cr)
        if section_id in sections:
            typed_links[cr].add(sections[section_id])
    return {'packs': packs, 'typed_links': typed_links, 'linked_documents': linked_documents,
            'dispositions': raw['disposition'], 'resolution_meeting': dict(raw['resolution'])}, receipts


def relational_gold(item, relations):
    """Implement question operations as Python sets, without reference SQL."""
    anchor = item['anchor']
    family = item['family']
    packs = relations['packs']
    links = relations['typed_links']

    def count_codes(eligible=None, meeting=None):
        targets_by_code = defaultdict(set)
        for resolution, target, code, evidence, scope in relations['dispositions']:
            if evidence != 'source_verified' or scope != 'whole_target':
                continue
            if eligible is not None and target not in eligible:
                continue
            if meeting is not None and relations['resolution_meeting'].get(resolution) != meeting:
                continue
            targets_by_code[code].add(target)
        return [(code, len(targets)) for code, targets in targets_by_code.items()]

    if family == 'pack_disposition_counts':
        rows = count_codes(eligible=packs[anchor[1]]) if anchor[0] == 'pack' else count_codes(meeting=anchor[1])
    elif family == 'shared_clauses':
        rows = links[anchor[1]] & links[anchor[2]]
    elif family == 'exclusive_clauses':
        rows = links[anchor[1]] - links[anchor[2]]
    elif family in {'both_clause_documents', 'conjunction_disposition_counts'}:
        needed = {tuple(anchor[1]), tuple(anchor[2])}
        eligible = {document for document in packs[anchor[0]] if needed <= links[document]}
        rows = count_codes(eligible=eligible) if family == 'conjunction_disposition_counts' else [(document.removeprefix('tdoc:'),) for document in eligible]
    elif family == 'largest_clause_footprint':
        counts = {document: len(links[document]) for document in packs[anchor[0]]}
        largest = max(counts.values(), default=None)
        rows = [(document.removeprefix('tdoc:'), count) for document, count in counts.items() if count == largest]
    elif family == 'members_without_clause_records':
        rows = [(document.removeprefix('tdoc:'),) for document in packs[anchor[0]] if document not in relations['linked_documents']]
    else:
        raise ValueError('Unimplemented frozen family: ' + family)
    return normalized(rows)


def group_summary(results, field):
    groups = {}
    for value in sorted({row[field] for row in results}):
        subset = [row for row in results if row[field] == value]
        groups[value] = {'n': len(subset), 'exact': sum(row['exact'] for row in subset),
                         'statuses': dict(sorted(Counter(row['status'] for row in subset).items()))}
    return groups


def compare_original_independent_checks(independent_dir, checks, hashes):
    """Describe relocation differences; prior receipts never supply test answers."""
    original_receipt = independent_dir / 'receipt.json'
    original_code = independent_dir / 'check.py'
    if not original_receipt.exists() or not original_code.exists():
        return {'available': False, 'role': 'Optional provenance comparison; all replay checks run independently'}
    original = load(original_receipt)
    old_by_name = {entry['check']: entry for entry in original['checks']}
    new_by_name = {entry['check']: entry for entry in checks}
    differences = []
    for name in sorted(set(old_by_name) | set(new_by_name)):
        old = old_by_name.get(name)
        new = new_by_name.get(name)
        if old != new:
            differences.append({'check': name, 'original': old, 'portable': new,
                                'interpretation': 'Input-byte and database-byte invariance uses relocated public and scratch labels; the tracked-byte correspondence table records the actual SHA-256 matches.' if name == 'all tracked sources and execution databases unchanged' else 'Inspect the actual values; no equivalence is assumed.'})
    scientific_functions = ['normalized', 'open_readonly', 'execute', 'read_relations', 'relational_gold', 'group_summary']
    def function_trees(path):
        module = ast.parse(path.read_text())
        return {node.name: ast.dump(node, include_attributes=False) for node in module.body if isinstance(node, ast.FunctionDef)}
    old_functions = function_trees(original_code)
    new_functions = function_trees(Path(__file__))
    original_hash_to_labels = defaultdict(list)
    for path, sha256 in original['hashes_before'].items():
        original_hash_to_labels[sha256].append(path)
    relocation = [{'portable': path, 'sha256': sha256,
                   'matching_original_labels': original_hash_to_labels.get(sha256, [])} for path, sha256 in hashes.items()]
    return {'available': True, 'role': 'Provenance comparison after independent execution; prior outputs never supply answers',
            'original_receipt_sha256': digest(original_receipt), 'original_checker_sha256': digest(original_code),
            'original_checks_total': len(original['checks']), 'portable_checks_total': len(checks),
            'same_check_name_order': [entry['check'] for entry in original['checks']] == [entry['check'] for entry in checks],
            'same_pass_flags': [entry['pass'] for entry in original['checks']] == [entry['pass'] for entry in checks],
            'identical_check_payloads': sum(old_by_name.get(entry['check']) == entry for entry in checks),
            'actual_check_payload_differences': differences,
            'scientific_function_AST_identity': {name: old_functions.get(name) == new_functions.get(name) for name in scientific_functions},
            'tracked_byte_correspondence': relocation}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True, help='Root of the unpacked public artifact')
    parser.add_argument('--database-dir', type=Path, required=True, help='Scratch directory for materialized SQLite databases')
    parser.add_argument('--output', type=Path, required=True, help='New receipt path; existing files are preserved')
    args = parser.parse_args()
    global RELEASE, STUDY
    RELEASE = args.release.resolve()
    STUDY = RELEASE / 'studies/semantic_witnesses/first_queries'
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError('Choose a new receipt path: ' + str(output))
    started = datetime.now(timezone.utc).isoformat()
    protocol = load(STUDY / 'protocol.json')
    freeze = load(STUDY / 'frozen/freeze.json')
    response_freeze = load(STUDY / 'first_response_freeze.json')
    selection = load(STUDY / 'frozen/selection_and_gold.json')
    questions = load(STUDY / 'frozen/writer_questions.json')
    schema = load(STUDY / 'frozen/writer_schema.json')
    response = load(STUDY / 'first_response.json')
    recorded = load(STUDY / 'first_response_execution.json')
    source_selection_path = RELEASE / 'studies/semantic_witnesses/measurement/selection_and_gold.json'
    source_freeze_path = source_selection_path.with_name('freeze.json')
    source_selection = load(source_selection_path)
    source_freeze = load(source_freeze_path)
    pilot_evaluator = RELEASE / 'studies/operator_pilot/evaluate_first_response.py'
    pilot_schema = RELEASE / 'studies/operator_pilot/frozen/writer_schema.json'
    pilot_pin = load(RELEASE / 'studies/operator_pilot/evaluation_pre_writer_pin.json')
    checks = []

    def check(name, observed, expected=True):
        checks.append({'check': name, 'pass': observed == expected, 'observed': observed, 'expected': expected})

    check('runtime SQLite version', sqlite3.sqlite_version, '3.37.2')
    check('protocol engine', protocol['execution']['engine'], 'SQLite3.37.2')
    check('per-statement time cap', protocol['execution']['cap_seconds'], 60)
    for name, expected in freeze['files'].items():
        check('frozen file hash ' + name, digest(STUDY / 'frozen' / name), expected)
    check('protocol hash in freeze', digest(STUDY / 'protocol.json'), freeze['protocol_sha256'])
    for name, expected in response_freeze['files'].items():
        check('first-response freeze hash ' + name, digest(STUDY / name), expected)
    evaluator_hash = digest(STUDY / 'evaluate_first_response.py')
    for name, expected in [('protocol', protocol['execution']['evaluator_sha256']),
                           ('freeze', freeze['evaluator_sha256']), ('original30 bytes', digest(pilot_evaluator)),
                           ('original30 pre-writer pin', pilot_pin['evaluator_sha256']),
                           ('recorded execution', recorded['evaluator_sha256'])]:
        check('evaluator hash ' + name, evaluator_hash, expected)
    check('source selection protocol hash', digest(source_selection_path), protocol['provenance']['original_selection_sha256'])
    check('source selection freeze hash', digest(source_selection_path), source_freeze['files']['selection_and_gold.json'])
    check('writer schema original30 byte reuse', digest(STUDY / 'frozen/writer_schema.json'), digest(pilot_schema))
    check('writer schema protocol source hash', digest(pilot_schema), protocol['provenance']['schema_source_sha256'])
    check('freeze declaration before first writer response', freeze['before_first_writer_response'])
    check('protocol declaration output absent at registration', protocol['model_output_exists_before_registration'], False)
    check('response freeze feedback declaration', response_freeze['feedback_before_freeze'], False)
    check('protocol timestamp precedes response freeze timestamp', datetime.fromisoformat(protocol['createdUtc']) < datetime.fromisoformat(response_freeze['recorded_at_utc']))
    check('writer service', response['writer']['service'], 'Codex session')
    check('provider model ID remains unknown', response['writer']['provider_model_id'], None)
    check('writer execution feedback declaration', response['writer']['execution_feedback'], False)
    check('writer metadata frozen', response['writer'], response_freeze['writer'])
    check('recorded response hash', recorded['response_sha256'], digest(STUDY / 'first_response.json'))
    check('recorded freeze hash', recorded['freeze_sha256'], digest(STUDY / 'frozen/freeze.json'))
    check('one planned writer session', freeze['writer_sessions'], 1)
    check('freeze item count', freeze['items'], 66)
    ids = ['W%03d' % number for number in range(1, 67)]
    for name, rows in [('selection', selection['items']), ('questions', questions['questions']),
                       ('responses', response['responses']), ('recorded execution', recorded['results'])]:
        check(name + ' complete ordered IDs', [row['id'] for row in rows], ids)
    check('source selection complete count', len(source_selection['items']), 66)
    mapping = []
    for item, original, question in zip(selection['items'], source_selection['items'], questions['questions']):
        restored = {key: value for key, value in item.items() if key != 'source_item_id'}
        restored['id'] = item['source_item_id']
        check(item['id'] + ' source selection exact item mapping', restored == original)
        check(item['id'] + ' exact question projection', question, {key: item[key] for key in ['id', 'wg', 'question', 'fields']})
        mapping.append({key: item[key] for key in ['id', 'source_item_id', 'wg', 'stratum', 'family', 'anchor']})
    identities = defaultdict(list)
    for item in selection['items']:
        identities[json.dumps([item['wg'], item['family'], item['anchor']], separators=(',', ':'))].append(item['id'])
    check('unique family-anchor count', len(identities), 65)

    databases = {}
    materialization = []
    path_resolution = []
    independent_dir = STUDY / 'independent'
    tracked = [path for path in STUDY.rglob('*') if path.is_file() and independent_dir not in path.parents]
    tracked += [source_selection_path, source_freeze_path, pilot_evaluator, pilot_schema,
                RELEASE / 'studies/operator_pilot/evaluation_pre_writer_pin.json']
    for item in selection['inputs']:
        source = RELEASE / 'sqlite' / Path(item['source']).name
        database = source if source.suffix == '.sqlite' else args.database_dir.resolve() / (item['wg'] + '.sqlite')
        if source.suffix == '.gz' and not database.exists():
            if digest(source) != item['source_sha256']:
                raise ValueError('Pinned compressed source hash mismatch: ' + label(source))
            database.parent.mkdir(parents=True, exist_ok=True)
            created = False
            try:
                with database.open('xb') as outgoing:
                    created = True
                    with gzip.open(source, 'rb') as incoming:
                        for block in iter(lambda: incoming.read(1024 * 1024), b''):
                            outgoing.write(block)
                if digest(database) != item['database_sha256']:
                    raise ValueError('Pinned materialized database hash mismatch: ' + label(database))
            except BaseException:
                if created:
                    database.unlink(missing_ok=True)
                raise
            materialization.append({'wg': item['wg'], 'action': 'decompressed pinned public gzip into new scratch file'})
        else:
            materialization.append({'wg': item['wg'], 'action': 'used existing pinned SQLite file'})
        databases[item['wg']] = database
        path_resolution.append({'wg': item['wg'], 'frozen_source_record': item['source'],
                                'public_source': label(source), 'source_bytes_match_frozen_pin': digest(source) == item['source_sha256'],
                                'frozen_database_record': item['database'], 'execution_database': label(database),
                                'database_bytes_match_frozen_pin': digest(database) == item['database_sha256']})
        tracked.extend([source, database])
    tracked = sorted(set(tracked), key=str)
    hashes_before = {label(path): digest(path) for path in tracked}
    database_receipts = []
    for inp, original in zip(selection['inputs'], source_selection['inputs']):
        database = databases[inp['wg']]
        source = RELEASE / 'sqlite' / Path(inp['source']).name
        check(inp['wg'] + ' source hash', digest(source), inp['source_sha256'])
        check(inp['wg'] + ' materialized database hash', digest(database), inp['database_sha256'])
        check(inp['wg'] + ' source-selection source hash', inp['source_sha256'], original['source_sha256'])
        check(inp['wg'] + ' source-selection database hash', inp['database_sha256'], original['database_sha256'])
        database_receipts.append({'wg': inp['wg'], 'source': label(source), 'database': label(database),
                                  'source_sha256_before': digest(source), 'database_sha256_before': digest(database)})

    connections = {wg: open_readonly(path) for wg, path in databases.items()}
    relations = {}
    relation_receipts = {}
    try:
        for wg, connection in connections.items():
            relations[wg], relation_receipts[wg] = read_relations(connection, 60)
            actual_schema = [row[0] for row in connection.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND type IN ('table','index')")]
            check(wg + ' complete writer SQL schema', sorted(actual_schema), sorted(schema[wg]['sql']))
            for field, declared in schema[wg]['disposition_value_domains'].items():
                actual_domain = [row[0] for row in connection.execute('SELECT DISTINCT ' + field + ' FROM disposition ORDER BY ' + field)]
                check(wg + ' complete disposition domain ' + field, actual_domain, declared)

        results = []
        for item, submitted, earlier in zip(selection['items'], response['responses'], recorded['results']):
            result = execute(connections[item['wg']], submitted['sql'], 60)
            expected = normalized(item['gold'])
            recomputed = relational_gold(item, relations[item['wg']])
            reference = execute(connections[item['wg']], item['reference_sql'], 60)
            result.update({key: item[key] for key in ['id', 'wg', 'stratum', 'family', 'anchor']})
            result.update({'sql': submitted['sql'], 'sql_utf8_sha256': hashlib.sha256(submitted['sql'].encode('utf-8')).hexdigest(),
                           'frozen_gold': expected, 'relational_gold': recomputed,
                           'reference_execution': reference,
                           'exact': result['status'] == 'returned' and result['actual'] == expected})
            expected_set = {tuple(row) for row in expected}
            actual_set = {tuple(row) for row in result['actual']}
            result['missing'] = [list(row) for row in sorted(expected_set - actual_set)]
            result['extra'] = [list(row) for row in sorted(actual_set - expected_set)]
            result['recorded_comparison'] = {
                'sql_bytes_match': earlier['sql'] == submitted['sql'],
                'status_matches': earlier['status'] == result['status'],
                'full_normalized_rows_match': earlier['actual'] == result['actual'],
                'exact_matches': earlier['exact'] == result['exact'],
                'missing_matches': earlier['missing'] == result['missing'],
                'extra_matches': earlier['extra'] == result['extra'],
                'wg_matches': earlier['wg'] == item['wg'],
                'family_matches': earlier['family'] == item['family'],
            }
            check(item['id'] + ' independent relational gold', recomputed, expected)
            check(item['id'] + ' reference SQL gold', reference['status'] == 'returned' and reference['actual'] == expected)
            for name, matched in result['recorded_comparison'].items():
                check(item['id'] + ' recorded ' + name, matched)
            results.append(result)
    finally:
        for connection in connections.values():
            connection.close()

    groups = {field: group_summary(results, field) for field in ['family', 'wg']}
    check('recorded n', recorded['n'], len(results))
    check('recorded aggregate exact', recorded['exact'], sum(result['exact'] for result in results))
    check('recorded operation and WG summaries', recorded['groups'], groups)
    check('recorded source unchanged declaration', recorded['source_inputs_unchanged'])
    hashes_after = {label(path): digest(path) for path in tracked}
    check('all tracked sources and execution databases unchanged', hashes_after, hashes_before)
    for item in database_receipts:
        item['source_sha256_after'] = hashes_after[item['source']]
        item['database_sha256_after'] = hashes_after[item['database']]
    unique_results = [next(result for result in results if result['id'] == members[0]) for members in identities.values()]
    correspondence = compare_original_independent_checks(independent_dir, checks, hashes_before)
    receipt = {
        'study': 'portable_independent_witness_first_query_replay', 'started_utc': started,
        'finished_utc': datetime.now(timezone.utc).isoformat(),
        'classification': 'Author-side independent execution and artifact validation; no review judgement',
        'runtime': {'python': sys.version, 'executable': sys.executable, 'sqlite': sqlite3.sqlite_version,
                    'cap_seconds_per_statement': 60, 'database_open': 'mode=ro&immutable=1; query_only; SELECT/READ/FUNCTION/RECURSIVE authorizer'},
        'independence': {'original_evaluator_imported_or_executed': False,
                         'original_evaluator_content_read_for_implementation': False,
                         'original_evaluators_hashed_only': [label(STUDY / 'evaluate_first_response.py'), label(pilot_evaluator)],
                         'gold_method': 'Independent Python relation sets from five flat table projections; frozen reference SQL additionally replayed',
                         'review_scores_or_memory_read': False, 'paid_api_calls': 0, 'new_model_generations': 0,
                         'human_evaluation': False},
        'writer': response['writer'],
        'freeze_timing_evidence': 'Manifest declarations and recorded UTC ordering; hashes verify present artifact consistency',
        'normalization': 'Full textual row sets, sorted and deduplicated; NULL becomes empty text. Raw rows, multiplicity, columns and NULL counts retained separately.',
        'summary': {'n': len(results), 'exact': sum(result['exact'] for result in results),
                    'statuses': dict(sorted(Counter(result['status'] for result in results).items())),
                    'distinct_wg_family_anchor_n': len(identities),
                    'distinct_wg_family_anchor_exact': sum(result['exact'] for result in unique_results),
                    'duplicate_anchor_groups': [members for members in identities.values() if len(members) > 1],
                    'raw_rows_total': sum(result['raw_row_count'] for result in results if result['status'] == 'returned'),
                    'normalized_rows_total': sum(len(result['actual']) for result in results),
                    'null_cells_total': sum(result.get('null_cells', 0) for result in results),
                    'independent_relational_gold_matches': sum(result['relational_gold'] == result['frozen_gold'] for result in results),
                    'reference_sql_gold_matches': sum(result['reference_execution']['status'] == 'returned' and result['reference_execution']['actual'] == result['frozen_gold'] for result in results),
                    'recorded_full_result_matches': sum(all(result['recorded_comparison'].values()) for result in results),
                    'groups': groups},
        'checks_passed': sum(check['pass'] for check in checks), 'checks_total': len(checks),
        'all_checks_pass': all(check['pass'] for check in checks), 'checks': checks,
        'source_mask_mapping': mapping, 'database_hashes': database_receipts,
        'hashes_before': hashes_before, 'hashes_after': hashes_after,
        'relation_read_receipts': relation_receipts, 'results': results,
        'checker_sha256': digest(Path(__file__)),
        'portability': {
            'release': str(RELEASE), 'study_relative_to_release': str(STUDY.relative_to(RELEASE)),
            'invocation': [sys.executable, str(Path(__file__).resolve()), '--release', str(RELEASE),
                           '--database-dir', str(args.database_dir.resolve()), '--output', str(output)],
            'public_reference_paths': {
                'operator_pilot_evaluator': label(pilot_evaluator),
                'operator_pilot_pre_writer_pin': label(RELEASE / 'studies/operator_pilot/evaluation_pre_writer_pin.json'),
                'operator_pilot_writer_schema': label(pilot_schema),
                'semantic_witness_selection': label(source_selection_path),
                'semantic_witness_selection_freeze': label(source_freeze_path),
            },
            'path_resolution': path_resolution, 'database_materialization': materialization,
            'comparison_to_original_independent_receipt': correspondence,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as destination:
        destination.write(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: receipt[key] for key in ['summary', 'checks_passed', 'checks_total', 'all_checks_pass']}, indent=2))
    if not receipt['all_checks_pass']:
        print(json.dumps([check for check in checks if not check['pass']], ensure_ascii=False, indent=2))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
