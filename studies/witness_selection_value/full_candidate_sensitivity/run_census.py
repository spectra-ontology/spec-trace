#!/usr/bin/env python3
"""Gated, exact finite census of known controls on frozen source candidates.

No measurement runs without a separate parent-created hash-bound authorization.
Only --out is written. The original enumerator is used for raw relation reading
and candidate/gate regeneration, never for the new control-rowset interpreter.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
from fractions import Fraction
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import resource
import shutil
import sqlite3
import sys
import time
import traceback

from exact_stats import aggregate, contrast, fraction, summarize_pmf
from symbolic import RawInterpreter, canonical, normalized, ordered, signature


HERE = Path(__file__).resolve().parent
SUBSETS = ('all', 'direct', 'other')
POLICIES = ('U', 'E')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def write_line(handle, value):
    handle.write(canonical(value) + '\n')


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def authorize(args):
    protocol, approval = load(args.protocol), load(args.approval)
    if approval.get('approved') is not True or approval.get('approved_by') != 'parent':
        raise ValueError('Parent execution approval absent')
    if approval.get('authorization') != 'run_frozen_full_candidate_census':
        raise ValueError('Wrong authorization scope')
    if approval.get('protocol_sha256') != sha(args.protocol):
        raise ValueError('Protocol is not the approved byte sequence')
    manifest_path = HERE / 'implementation_manifest.json'
    manifest_hash = sha(manifest_path)
    if approval.get('implementation_sha256') != manifest_hash:
        raise ValueError('Implementation manifest is not approved')
    if protocol['implementation_plan']['implementation_sha256'] != manifest_hash:
        raise ValueError('Protocol implementation pin differs')
    manifest = load(manifest_path)
    for name, expected in manifest['sha256'].items():
        if sha(HERE / name) != expected:
            raise ValueError(('Code differs from approved implementation', name))
    if sha(args.enumerator) != protocol['enumerator_sha256']:
        raise ValueError('Frozen raw/enumeration module differs')
    for name, expected in protocol['design_document_sha256'].items():
        if sha(HERE / name) != expected:
            raise ValueError(('Design document differs', name))
    return protocol, manifest_hash


def raw_input_checks(connection):
    """Fail closed on affinities/NULL/collations outside literal-set semantics."""
    fields = {'cr_in_pack': ['cr', 'pack_id'], 'section': ['id', 'spec', 'release', 'clause'],
              'cr_modifies_section': ['cr', 'section_id'], 'resolution': ['id', 'meeting_id'],
              'disposition': ['target', 'code', 'resolution_id']}
    for table, columns in fields.items():
        schema = connection.execute('SELECT sql FROM sqlite_master WHERE name=?', (table,)).fetchone()[0]
        collations = re.findall(r'\bCOLLATE\s+["`\[]?([A-Za-z0-9_]+)', schema, re.I)
        if any(value.lower() != 'binary' for value in collations):
            raise ValueError(('Non-binary source collation', table, collations))
        predicate = ' OR '.join('typeof(' + column + ")<>'text'" for column in columns)
        if table == 'disposition':
            predicate = '(' + predicate + ") AND evidence_status='source_verified' AND scope='whole_target'"
        row = connection.execute('SELECT ' + ','.join(columns) + ' FROM ' + table +
                                 ' WHERE ' + predicate + ' LIMIT 1').fetchone()
        if row is not None:
            raise ValueError(('Unsupported source NULL/type', table, row))
    # The original builder's removeprefix gold must coincide with SQL REPLACE.
    # Census itself uses exact SQL REPLACE semantics; preflight records any issue
    # rather than silently treating the builder's Python gold as the reference.
    return {'all_interpreted_fields_nonnull_text': True,
            'interpreted_table_collations_binary': True,
            'display_semantics': "SQLite REPLACE(value,'tdoc:','')"}


def open_database(args, selection, wg, out):
    pin = next(row for row in selection['inputs'] if row['wg'] == wg)
    plain = args.release / 'sqlite' / (wg + '.sqlite')
    source = plain if plain.exists() else plain.with_suffix('.sqlite.gz')
    if sha(source) != pin['source_sha256']:
        raise ValueError(('Database source hash mismatch', wg))
    if source.suffix != '.gz':
        database = source
    elif args.materialized_db_dir:
        database = args.materialized_db_dir / (wg + '.sqlite')
    else:
        directory = out / '.databases'
        directory.mkdir(exist_ok=True)
        database = directory / (wg + '.sqlite')
        if not database.exists():
            with gzip.open(source, 'rb') as src, database.open('xb') as dest:
                shutil.copyfileobj(src, dest)
    if sha(database) != pin['database_sha256']:
        raise ValueError(('Materialized database hash mismatch', wg))
    connection = sqlite3.connect('file:' + str(database.resolve()) + '?mode=ro&immutable=1', uri=True)
    connection.execute('PRAGMA query_only=ON')
    connection.execute('PRAGMA cache_size=-16384')
    return connection, database, pin


def initial_cells(catalog):
    result = {}
    for row in catalog['cells']:
        names = row['control_names']
        result[row['wg'], row['stratum']] = {
            'cell_id': row['wg'] + '/' + row['stratum'], 'wg': row['wg'],
            'stratum': row['stratum'], 'family': row['family'],
            'primary_available': row['primary_available'], 'role': row['role'],
            'subsets': {'all': names, 'direct': row['direct_controls'], 'other': row['other_controls']},
            'policy_sizes': {'U': 0, 'E': 0},
            'histograms': {p: {s: Counter() for s in SUBSETS} for p in POLICIES},
            'control_detected_counts': {p: Counter() for p in POLICIES},
            'expected_U': row['candidate_universe_count'], 'expected_E': row['eligible_candidates']}
    return result


def evaluate(interpreter, cell, anchor):
    outcomes, branches = interpreter.evaluate(cell['family'], anchor)
    names = ['reference'] + sorted(cell['subsets']['all'])
    value, detected = signature(outcomes, names, branches)
    encoded = canonical(value)
    return outcomes, value, detected, hashlib.sha256(encoded.encode()).hexdigest()


def census(args, protocol, selection, cells, enumerator, out):
    representatives, signatures, wg_receipts = {}, {}, []
    for pin in selection['inputs']:
        wg = pin['wg']
        connection, database, _ = open_database(args, selection, wg, out)
        input_check = raw_input_checks(connection)
        raw = enumerator.raw(connection)
        connection.close()
        interpreter = RawInterpreter(raw)
        archive = args.release / 'studies/witness_selection_value/measurement' / pin['candidate_file']
        uncompressed = hashlib.sha256()
        rows = 0
        with gzip.open(archive, 'rb') as frozen, gzip.open(out / ('candidates_' + wg + '.jsonl.gz'),
                                                         'wt', encoding='utf-8') as annotations:
            for stratum, anchor, properties, flags, raw_override in enumerator.generated(raw, Counter()):
                line = frozen.readline()
                if not line:
                    raise ValueError(('Frozen archive ended early', wg, rows))
                uncompressed.update(line)
                actual = {'stratum': stratum, 'candidate': anchor, 'properties': properties,
                          'original_predicate_results': flags}
                old = json.loads(line)
                if canonical(actual) != canonical(old):
                    save(out / 'candidate_mismatch.json', {'wg': wg, 'row': rows, 'old': old, 'raw': actual})
                    raise ValueError(('Raw candidate regeneration mismatch', wg, rows))
                cell = cells[wg, stratum]
                eligible = all(flags.values())
                outcomes, value, detected, signature_id = evaluate(interpreter, cell, anchor)
                if signature_id in signatures and signatures[signature_id] != value:
                    raise ValueError('Signature hash collision')
                signatures[signature_id] = value
                for policy in ('U', 'E') if eligible else ('U',):
                    cell['policy_sizes'][policy] += 1
                    cell['control_detected_counts'][policy].update(detected)
                    for subset in SUBSETS:
                        j = sum(detected[name] for name in cell['subsets'][subset])
                        cell['histograms'][policy][subset][j] += 1
                key = (wg, stratum, eligible, signature_id)
                if key not in representatives or canonical(anchor) < canonical(representatives[key]['anchor']):
                    representatives[key] = {'wg': wg, 'stratum': stratum, 'family': cell['family'],
                                            'eligible': eligible, 'signature_id': signature_id,
                                            'anchor': anchor, 'predicates': flags,
                                            'detected': detected,
                                            'allowed_full_rowsets': {name: outcomes[name].to_json()
                                                                     for name in value['names']}}
                write_line(annotations, {'index': rows, 'stratum': stratum, 'candidate': anchor,
                                         'eligible': eligible, 'signature_id': signature_id,
                                         'control_names': value['names'][1:],
                                         'detection_vector': [detected[name] for name in value['names'][1:]]})
                rows += 1
            if frozen.readline():
                raise ValueError(('Frozen archive has extra rows', wg))
        if uncompressed.hexdigest() != pin['candidate_uncompressed_sha256']:
            raise ValueError(('Uncompressed frozen archive hash mismatch', wg))
        if sha(archive) != pin['candidate_file_sha256'] or sha(database) != pin['database_sha256']:
            raise ValueError(('Input changed during census', wg))
        for (group, stratum), cell in cells.items():
            if group == wg and (cell['policy_sizes']['U'] != cell['expected_U'] or
                                cell['policy_sizes']['E'] != cell['expected_E']):
                raise ValueError(('Cell census denominator mismatch', cell['cell_id']))
        wg_receipts.append({'wg': wg, 'raw_candidate_rows': rows,
                            'all_properties_and_frozen_flags_equal_archive': True,
                            'input_checks': input_check})
        print(canonical({'phase': 'symbolic_census', 'wg': wg, 'rows': rows}), flush=True)
    if sum(c['policy_sizes']['U'] for c in cells.values()) != 2269290:
        raise ValueError('Wrong total candidate population')
    ordered_representatives = [representatives[key] for key in sorted(representatives)]
    inventory = {'definition': protocol['sql_validation']['signature'],
                 'representative_rule': protocol['sql_validation']['representatives'],
                 'signatures': signatures, 'representatives': ordered_representatives,
                 'all95_cells': True, 'all2269290_candidates_evaluated': True,
                 'sql_audit_started': False}
    save(out / 'signature_inventory.json', inventory)
    freeze = {'signature_inventory_sha256': sha(out / 'signature_inventory.json'),
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'representatives': len(ordered_representatives),
              'new_sql_audit_slots_executed_before_freeze': 0}
    save(out / 'signature_inventory_freeze.json', freeze)
    save(out / 'census_cells_unvalidated.json', list(cells.values()))
    return ordered_representatives, signatures, wg_receipts, freeze


def render(builder, data, cell, anchor, selection_sha256='diagnostic_no_reselection'):
    if cell['family'] == 'pack_disposition_counts' and anchor[0] == 'meeting':
        # Exact original metadata fallback; SQL does not use the label.
        if anchor[1] not in data['meetings']:
            data['meetings'][anchor[1]] = ('metadata label unavailable', None, cell['wg'])
    item = builder.task(data, {'wg': cell['wg'], 'stratum': cell['stratum'],
                               'family': cell['family'], 'selected': {'candidate': anchor, 'witness': {}},
                               'selection_sha256': selection_sha256})
    queries = {'reference': item['reference_sql']}
    queries.update({name: item['mutations'][name] for name in cell['subsets']['all']})
    return item, queries


def execute(connection, sql):
    started = time.monotonic()
    connection.set_progress_handler(lambda: time.monotonic() - started >= 60, 10000)
    try:
        rows = ordered(normalized(connection.execute(sql).fetchall()))
        return {'status': 'ok', 'rows': rows, 'seconds': time.monotonic() - started,
                'output_sha256': hashlib.sha256(canonical(rows).encode()).hexdigest()}
    except sqlite3.Error as error:
        return {'status': 'timeout' if 'interrupted' in str(error) else 'error',
                'error': str(error), 'seconds': time.monotonic() - started}
    finally:
        connection.set_progress_handler(None, 0)


def renderer_preflight(args, selection, cells, builder, old, out):
    """Check every original SQL literal before any SQL audit/cache reuse."""
    rows, failures = [], []
    for pin in selection['inputs']:
        wg = pin['wg']
        connection, database, _ = open_database(args, selection, wg, out)
        raw_input_checks(connection)
        data = builder.data_from_connection(connection)
        for arm, items in old['arms'].items():
            for item in items:
                if item['wg'] != wg:
                    continue
                cell = cells[wg, item['stratum']]
                _, rendered = render(builder, data, cell, item['anchor'], item['selection_sha256'])
                frozen = {'reference': item['reference_sql']}
                frozen.update({c['name']: c['sql'] for c in item['controls']})
                required = {c['name'] for c in item['controls'] if c['required']}
                passed = rendered == frozen and required == set(cell['subsets']['direct'])
                row = {'arm': arm, 'cell_id': cell['cell_id'], 'anchor': item['anchor'],
                       'all_sql_strings_equal': rendered == frozen,
                       'direct_control_names_equal': required == set(cell['subsets']['direct']),
                       'controls': len(item['controls']), 'passed': passed}
                rows.append(row)
                if not passed:
                    failures.append(dict(row, rendered=rendered, frozen=frozen))
        connection.close()
        if sha(database) != pin['database_sha256']:
            failures.append({'wg': wg, 'error': 'Database changed during renderer preflight'})
    result = {'status': 'passed' if not failures else 'failed', 'task_slots': len(rows),
              'control_slots': sum(r['controls'] for r in rows), 'rows': rows, 'failures': failures,
              'new_control_sql_executions': 0}
    save(out / 'renderer_preflight.json', result)
    if failures or len(rows) != 132 or result['control_slots'] != 400:
        raise ValueError('Original132 task/400 control SQL render preflight failed')
    return result


def audit(args, selection, cells, builder, enumerator, reps, signatures, inventory_freeze, old, out):
    # No SQL audit begins until the complete census/representative inventory exists.
    if sha(out / 'signature_inventory.json') != inventory_freeze['signature_inventory_sha256']:
        raise ValueError('Representative inventory changed after freeze')
    failures, receipts, counts = [], [], Counter()
    with gzip.open(out / 'sql_audit.jsonl.gz', 'wt', encoding='utf-8') as log:
        for pin in selection['inputs']:
            wg = pin['wg']
            connection, database, _ = open_database(args, selection, wg, out)
            raw_input_checks(connection)
            interpreter = RawInterpreter(enumerator.raw(connection))
            data = builder.data_from_connection(connection)
            cache = {}
            slots = [('signature', row) for row in reps if row['wg'] == wg]
            for arm, items in old['arms'].items():
                slots += [('frozen', {'wg': wg, 'stratum': row['stratum'], 'anchor': row['anchor'],
                                      'arm': arm, 'old': row}) for row in items if row['wg'] == wg]
            for kind, row in slots:
                cell, anchor = cells[wg, row['stratum']], row['anchor']
                outcomes, value, detected, signature_id = evaluate(interpreter, cell, anchor)
                _, queries = render(builder, data, cell, anchor,
                                    row['old']['selection_sha256'] if kind == 'frozen'
                                    else 'diagnostic_no_reselection')
                slot_errors, executions = [], {}
                if kind == 'signature':
                    if signature_id != row['signature_id'] or signatures[signature_id] != value:
                        slot_errors.append('Representative signature changed on reread')
                    if {name: outcomes[name].to_json() for name in value['names']} != row['allowed_full_rowsets']:
                        slot_errors.append('Representative full rowset family changed on reread')
                else:
                    counts['frozen_task_slots'] += 1
                    old_queries = {'reference': row['old']['reference_sql']}
                    old_queries.update({c['name']: c['sql'] for c in row['old']['controls']})
                    if queries != old_queries:
                        slot_errors.append('Original renderer SQL differs from frozen SQL')
                    if set(cell['subsets']['all']) != {c['name'] for c in row['old']['controls']}:
                        slot_errors.append('Frozen control names differ from catalog')
                    if not outcomes['reference'].contains(row['old']['gold']):
                        slot_errors.append('Independent raw reference differs from frozen gold full rowset')
                actual_outcomes = {}
                for name in value['names']:
                    sql = queries[name]
                    query_hash = hashlib.sha256(sql.encode()).hexdigest()
                    reused = query_hash in cache
                    if reused and cache[query_hash]['sql'] != sql:
                        raise ValueError('SQL hash collision')
                    if not reused:
                        cache[query_hash] = {'sql': sql, 'result': execute(connection, sql)}
                        counts['unique_sql_executions'] += 1
                    result = cache[query_hash]['result']
                    executions[name] = {'sql': sql, 'sql_sha256': query_hash,
                                         'cache_reused_exact_wg_sql': reused, 'execution': result}
                    counts['audit_query_slots'] += 1
                    if kind == 'frozen' and name != 'reference':
                        counts['frozen_control_slots'] += 1
                    if result['status'] != 'ok':
                        slot_errors.append(name + ':' + result['status'])
                        continue
                    if not outcomes[name].contains(result['rows']):
                        slot_errors.append(name + ':SQL full rowset outside symbolic admitted family')
                    actual_outcomes[name] = normalized(result['rows'])
                    if kind == 'frozen':
                        archived = row['old']['reference'] if name == 'reference' else next(
                            c['execution'] for c in row['old']['controls'] if c['name'] == name)
                        if archived['status'] != 'ok' or normalized(archived['rows']) != normalized(result['rows']):
                            slot_errors.append(name + ':SQL full rowset differs from frozen execution')
                if len(actual_outcomes) == len(value['names']):
                    actual_partition, group_rows = [], []
                    for name in value['names']:
                        answer = actual_outcomes[name]
                        if answer not in group_rows:
                            group_rows.append(answer)
                        actual_partition.append(group_rows.index(answer))
                    actual_detected = {name: int(actual_outcomes[name] != actual_outcomes['reference'])
                                       for name in value['names'][1:]}
                    if actual_partition != value['partition'] or actual_detected != detected:
                        slot_errors.append('SQL equality partition/detection vector differs')
                    if kind == 'frozen':
                        archived_detected = {c['name']: int(c['discriminating']) for c in row['old']['controls']}
                        if actual_detected != archived_detected:
                            slot_errors.append('Frozen detection vector differs')
                        receipts.append({'arm': row['arm'], 'cell_id': cell['cell_id'], 'anchor': anchor,
                                         'signature_id': signature_id, 'detected': detected,
                                         'all_frozen_sql_strings_and_rows_equal': not slot_errors})
                item = {'kind': kind, 'wg': wg, 'cell_id': cell['cell_id'], 'anchor': anchor,
                        'arm': row.get('arm'), 'eligible': row.get('eligible'),
                        'signature_id': signature_id, 'symbolic_signature': value,
                        'symbolic_detection': detected,
                        'allowed_full_rowsets': {name: outcomes[name].to_json() for name in value['names']},
                        'queries': executions, 'errors': slot_errors, 'passed': not slot_errors}
                write_line(log, item)
                counts[kind + '_audit_slots'] += 1
                if slot_errors:
                    failures.append({key: item[key] for key in ('kind', 'wg', 'cell_id', 'anchor', 'arm', 'errors')})
            connection.close()
            if sha(database) != pin['database_sha256']:
                failures.append({'wg': wg, 'errors': ['Database changed during SQL audit']})
            print(canonical({'phase': 'sql_audit', 'wg': wg, 'cumulative_slots': dict(counts),
                             'failures': len(failures)}), flush=True)
    if counts['frozen_task_slots'] != 132 or counts['frozen_control_slots'] != 400:
        failures.append({'errors': ['Expected all132 frozen tasks and400 controls audited'],
                         'counts': dict(counts)})
    if counts['signature_audit_slots'] != len(reps):
        failures.append({'errors': ['Representative audit incomplete']})
    result = {'status': 'passed' if not failures else 'validation_incomplete_or_failed',
              'counts': dict(counts), 'failures': failures, 'frozen_anchor_replay': receipts,
              'signature_inventory_sha256': inventory_freeze['signature_inventory_sha256']}
    save(out / 'sql_validation.json', result)
    return result


def analyze(cells, validation, out):
    rows = sorted(cells.values(), key=lambda c: c['cell_id'])
    per_cell = []
    for cell in rows:
        result = {k: cell[k] for k in ('cell_id', 'wg', 'stratum', 'family', 'role',
                                      'primary_available', 'policy_sizes', 'subsets')}
        result['policies'] = {}
        for policy in POLICIES:
            n = cell['policy_sizes'][policy]
            if not n:
                result['policies'][policy] = {'status': 'NA_empty_population'}
                continue
            result['policies'][policy] = {
                'population': n,
                'control_probabilities': {name: fraction(Fraction(
                    cell['control_detected_counts'][policy][name], n)) for name in cell['subsets']['all']},
                'subset_joint_count_pmf': {
                    subset: summarize_pmf(cell['histograms'][policy][subset], n, len(names))
                    if names else {'status': 'NA_category_empty'}
                    for subset, names in cell['subsets'].items()}}
        per_cell.append(result)
    aggregates = {}
    for subset in SUBSETS:
        aggregates[subset] = {}
        for weight in ('control', 'equal_cell'):
            eligible = aggregate(rows, subset, 'E', weight)
            universe = aggregate(rows, subset, 'U', weight)
            aggregates[subset][weight] = {'U': universe, 'E': eligible,
                                          'contrast': contrast(eligible, universe)}
    # Locate both unchanged arms in the policy distributions and list cell scores.
    old_arms = {}
    for arm in sorted({r['arm'] for r in validation['frozen_anchor_replay']}):
        arm_rows = [r for r in validation['frozen_anchor_replay'] if r['arm'] == arm]
        if len(arm_rows) != 66:
            raise ValueError('Original arm replay missing primary cells')
        scores = {}
        for subset in SUBSETS:
            selected = [cells[tuple(r['cell_id'].split('/'))] for r in arm_rows]
            nonempty = [(r, c) for r, c in zip(arm_rows, selected) if c['subsets'][subset]]
            count = sum(sum(r['detected'][k] for k in c['subsets'][subset]) for r, c in nonempty)
            slots = sum(len(c['subsets'][subset]) for _, c in nonempty)
            values = {'control': Fraction(count, slots),
                      'equal_cell': sum((Fraction(sum(r['detected'][k] for k in c['subsets'][subset]),
                                                          len(c['subsets'][subset]))
                                         for r, c in nonempty), Fraction()) / len(nonempty)}
            scores[subset] = {}
            for weight, score in values.items():
                locations = {}
                for policy in POLICIES:
                    pmf = aggregates[subset][weight][policy]
                    lattice_value = score * pmf['score_index_denominator']
                    if lattice_value.denominator != 1:
                        raise ValueError('Original score is not on policy score lattice')
                    index = lattice_value.numerator
                    coefficients = {int(k): v for k, v in pmf['pmf_integer_coefficients'].items()}
                    population = pmf['pmf_integer_denominator']
                    locations[policy] = {
                        'probability_score_less': fraction(Fraction(sum(v for k, v in coefficients.items() if k < index), population)),
                        'probability_score_equal': fraction(Fraction(coefficients.get(index, 0), population)),
                        'probability_score_less_or_equal': fraction(Fraction(sum(v for k, v in coefficients.items() if k <= index), population)),
                        'note': 'A score location only; this does not assert the original anchor tuple belongs to E.'}
                scores[subset][weight] = {'score': fraction(score), 'policy_score_locations': locations}
        old_arms[arm] = {'fixed_task_slots': len(arm_rows), 'scores': scores, 'cell_replay': arm_rows}
    result = {'role': 'Posthoc AUTHOR exact census of known controls and fixed source candidates',
              'validation': 'All representative and frozen-anchor SQL checks passed',
              'scope': 'Uniform finite-anchor policies, known operations, current fixed source relations; no unseen/model-success claim.',
              'cells': per_cell, 'primary_aggregates': aggregates, 'unchanged_original_arms': old_arms,
              'unavailable_policy': 'All29 retained with U-only family diagnostics, empty E=NA, primary weight zero.',
              'pooling': 'Each cell divided by its own candidate population before either stated weighting.'}
    save(out / 'analysis.json', result)
    with (out / 'per_control_probabilities.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['cell_id', 'primary_available', 'role', 'policy', 'population',
                                                    'control', 'direct', 'detected', 'probability_numerator',
                                                    'probability_denominator', 'probability_rational'])
        writer.writeheader()
        for cell in rows:
            for policy in POLICIES:
                n = cell['policy_sizes'][policy]
                for name in cell['subsets']['all']:
                    value = Fraction(cell['control_detected_counts'][policy][name], n) if n else None
                    writer.writerow({'cell_id': cell['cell_id'], 'primary_available': cell['primary_available'],
                                     'role': cell['role'], 'policy': policy, 'population': n, 'control': name,
                                     'direct': name in cell['subsets']['direct'],
                                     'detected': cell['control_detected_counts'][policy][name] if n else 'NA',
                                     'probability_numerator': value.numerator if value is not None else 'NA',
                                     'probability_denominator': value.denominator if value is not None else 'NA',
                                     'probability_rational': str(value) if value is not None else 'NA'})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--enumerator', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, default=HERE / 'protocol.json')
    parser.add_argument('--approval', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--materialized-db-dir', type=Path)
    args = parser.parse_args()
    # Authorization precedes imports, source reads, candidate evaluation and output creation.
    protocol, manifest_hash = authorize(args)
    if sqlite3.sqlite_version != '3.37.2':
        raise ValueError('SQLite3.37.2 required; use /usr/bin/python3')
    args.release = args.release.resolve()
    args.out = args.out.resolve()
    if not args.out.is_relative_to(HERE) or args.out == HERE:
        raise ValueError('--out must be a fresh child directory of this authorized analysis bundle')
    if args.out.is_relative_to(args.release):
        raise ValueError('Output must not modify the public release')
    args.out.mkdir(parents=True, exist_ok=False)
    resource.setrlimit(resource.RLIMIT_AS, (4 << 30, 4 << 30))
    started, phase = time.monotonic(), 'input_verification'
    receipt = {'status': 'started', 'role': 'AUTHOR new measurement; original review preserved',
               'protocol_sha256': sha(args.protocol), 'implementation_sha256': manifest_hash,
               'approval_sha256': sha(args.approval), 'enumerator_sha256': sha(args.enumerator),
               'python': sys.version, 'sqlite': sqlite3.sqlite_version, 'model_or_paid_api_calls': 0,
               'release': str(args.release), 'out': str(args.out),
               'write_scope': 'Fresh --out child only; immutable review/manuscript/release untouched',
               'single_process': True, 'memory_limit_bytes': 4 << 30,
               'started_utc': datetime.now(timezone.utc).isoformat()}
    save(args.out / 'receipt.json', receipt)
    try:
        for relative, expected in protocol['input_sha256'].items():
            if sha(args.release / relative) != expected:
                raise ValueError(('Pinned input differs', relative))
        enumerator = import_file('frozen_raw_candidate_enumerator', args.enumerator)
        enumerator.P = args.release
        # SQL builder is used only to render exact frozen operations, not symbolic gold.
        builder = import_file('pinned_sql_renderer', args.release /
                              'studies/semantic_witnesses/build_semantic_witnesses.py')
        selection = load(args.release / 'studies/witness_selection_value/measurement/selection.json')
        old = load(args.release / 'studies/witness_selection_value/measurement/execution.json')
        catalog = load(HERE / 'control_catalog.json')
        cells = initial_cells(catalog)
        if len(cells) != 95 or sum(c['primary_available'] for c in cells.values()) != 66:
            raise ValueError('Cell contract differs')
        if [sum(len(c['subsets'][s]) for c in cells.values() if c['primary_available']) for s in SUBSETS] != [200, 113, 87]:
            raise ValueError('Frozen control-slot contract differs')
        phase = 'all132_renderer_preflight'
        preflight = renderer_preflight(args, selection, cells, builder, old, args.out)
        receipt['renderer_preflight_task_slots'] = preflight['task_slots']
        receipt['renderer_preflight_control_slots'] = preflight['control_slots']
        phase = 'symbolic_census'
        reps, signatures, wg_receipts, inventory_freeze = census(args, protocol, selection, cells, enumerator, args.out)
        receipt.update(census_working_groups=wg_receipts, candidate_rows=2269290,
                       signature_inventory_freeze=inventory_freeze)
        save(args.out / 'receipt.json', receipt)
        phase = 'sql_audit'
        validation = audit(args, selection, cells, builder, enumerator, reps, signatures,
                           inventory_freeze, old, args.out)
        receipt['sql_validation_status'] = validation['status']
        if validation['status'] != 'passed':
            raise ValueError('SQL validation incomplete/failed; all unvalidated results retained')
        phase = 'exact_aggregation'
        analyze(cells, validation, args.out)
        for relative, expected in protocol['input_sha256'].items():
            if sha(args.release / relative) != expected:
                raise ValueError(('Pinned input changed after execution', relative))
        if sha(args.enumerator) != protocol['enumerator_sha256']:
            raise ValueError('Frozen enumerator changed after execution')
        authorize(args)  # Recheck every code/protocol/design pin at completion.
        receipt.update(status='complete', all_candidate_rows_recomputed=True,
                       all95_cells_preserved=True, primary_available=66, unavailable=29,
                       frozen_controls=200, direct_controls=113, other_controls=87,
                       all_input_hashes_unchanged=True, original_review_rerated=False,
                       manuscript_or_release_modified=False)
    except BaseException as error:
        receipt.update(status='validation_incomplete_or_failed', failure_phase=phase,
                       error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc(),
                       policy='All partial/adverse outputs retained; no successful-subset headline.')
        if 'cells' in locals():
            save(args.out / 'census_cells_partial_unvalidated.json', list(cells.values()))
        raise
    finally:
        receipt.update(elapsed_seconds=time.monotonic() - started,
                       maximum_resident_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                       ended_utc=datetime.now(timezone.utc).isoformat())
        save(args.out / 'receipt.json', receipt)
        files = {str(path.relative_to(args.out)): sha(path) for path in args.out.rglob('*')
                 if path.is_file() and '.databases' not in path.parts and path.name != 'output_sha256.json'}
        save(args.out / 'output_sha256.json', files)
        print(canonical({'status': receipt['status'], 'phase': phase,
                         'seconds': receipt['elapsed_seconds']}), flush=True)


if __name__ == '__main__':
    main()
