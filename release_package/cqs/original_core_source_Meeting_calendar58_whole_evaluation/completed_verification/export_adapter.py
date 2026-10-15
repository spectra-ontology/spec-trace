#!/usr/bin/env python3
"""Spec: publishable retained Source58 whole-body original-question evaluation with lossless raw shards.
Ontology: separate source snapshots and exact output contracts.
Cycle: KDD Datasets and Benchmarks Cycle1.
배경: no score regeneration or frozen-core aggregation.
사용: --kind source58_fullbody_v2 --out-dir NEW_DIRECTORY after root completes the fixed model run.
LLM 호출: none; copies already completed root-authorized calls.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B = HERE.parent
RAN1 = B / 'RAN1'
REG = RAN1 / 'source_variant_OpenRouter_registration'
TOOLS = RAN1 / 'source_variant_evaluation_exports'
METHODS = ('text2cypher', 'text2sql', 'single_retrieval', 'iterative_retrieval')
PATCHES = {'source58_fullbody_v2': HERE / 'source58_portable_public_patch_v2'}
def load(p): return json.loads(Path(p).read_text())
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()
def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')
def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)


def export(kind, out):
    if out.exists(): raise ValueError('new export directory required; prior outputs are preserved')
    run = REG / kind / 'run'; protocol = load(run / 'protocol.json'); config = load(run / 'source_config.json')
    if load(run / 'generation_complete.json') != {'completed_method_items': 4, 'required': 4}: raise ValueError('incomplete methods')
    for method in METHODS:
        if not (run / method / 'predictions.jsonl').is_file() or not (run / method / 'statuses.jsonl').is_file(): raise ValueError('missing assembled method')
    source_before = {str(p): sha(p) for p in run.rglob('*') if p.is_file()}
    out.mkdir(parents=True)
    shutil.copytree(run, out / 'results', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(PATCHES[kind], out / 'source_patch', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    contract_subdir = 'source_patch/evaluation'
    write(out / 'evaluation_contract_location.json', {'evaluation_contract_subdir': contract_subdir, 'single_question_per_runtime_registration': True})
    locations = {}
    shard_locations = {}
    for key, pin in protocol['source_pins'].items():
        if key in {'sql_db_path', 'graph_ttl_path'}: continue
        if key == 'raw_records_path':
            whole = load(out / 'source_patch/source/full_authored_raw_v2/whole_authored_raw_inventory.json')
            if whole['raw_inputs_pin'] != pin: raise ValueError('raw input pin differs')
            parts, offset = [], 0
            for row in whole['raw_inputs_ordered_bin_shards']:
                rel = 'source_patch/source/full_authored_raw_v2/' + row['relative_path']
                path = out / rel
                if sha(path) != row['sha256'] or path.stat().st_size != row['bytes']: raise ValueError('raw shard differs')
                parts.append({'path': rel, 'offset_bytes': offset, 'bytes': row['bytes'], 'sha256': row['sha256']})
                offset += row['bytes']
            if offset != pin['bytes']: raise ValueError('raw shard total differs')
            descriptor = {'format': 'ordered_exact_byte_contiguous_shards_v1',
                'original_local_file': pin['path'], 'sha256': pin['sha256'], 'bytes': pin['bytes'],
                'max_shard_bytes': 64 * 1024 ** 2, 'parts': parts,
                'lossless_reconstruction': 'Concatenate binary parts in list order without added separators; boundaries can split UTF-8 and JSONL records.',
                'original_local_input_unchanged': True, 'no_source_abridgement_or_filtering': True}
            write(out / 'raw_records_shard_descriptor.json', descriptor)
            shard_locations[key] = 'raw_records_shard_descriptor.json'
            continue
        filename = key + Path(pin['path']).suffix
        rel = 'inputs/frozen_source_pins/' + filename
        copy(Path(pin['path']), out / rel)
        if sha(out / rel) != pin['sha256']: raise ValueError('source input differs: ' + key)
        locations[key] = rel
    copy(Path(config['actual_gate_pin']['path']), out / 'inputs/actual_gate.json')
    for rel, pin in protocol['code_pins'].items():
        copy(REG / rel, out / 'runtime/registration' / rel)
        if sha(out / 'runtime/registration' / rel) != pin: raise ValueError('runtime changed')
    for name in ('score_retained_four_methods.py', 'verify_retained_four_methods.py'):
        version = '_v4.py' if name.startswith('verify_') else '_v2.py'
        copy(TOOLS / name.replace('.py', version), out / 'tools' / name)
    for original, relative in [
        (HERE / 'source58_whole_input_population_count_closure.json', 'completed_verification/whole_population_and_count_closure.json'),
        (HERE / 'source58_whole_portable_actual_source_read_v2.json', 'completed_verification/actual_whole_portable_raw_source_replay.json'),
        (HERE / 'source58_whole_portable_actual23controls_v2.json', 'completed_verification/actual23_scorer_control_replay.json'),
        (B / 'root_evidence/RAN4_root_fresh_whole342_and4_raw_replay_v1/receipt.json', 'completed_verification/root_fresh_whole342_and4_raw_prefirst_model_call.json'),
        (B / 'root_evidence/verify_RAN4_whole342_and4_raw_sources_root_v1.py', 'completed_verification/root_fresh_source_reader.py'),
        (HERE / 'source58_actual_generated_recency_predicate_limits.json', 'completed_verification/retained_generated_recency_predicate_limits.json'),
        (HERE / 'source58_actual_structured20_uploadedDate_NULL_order_diagnostic.json', 'completed_verification/actual20_uploadedDate_NULL_order_diagnostic.json'),
        (HERE / 'diagnose_source58_retained_structured_uploadedDate_order.py', 'completed_verification/actual20_uploadedDate_NULL_order_reader.py'),
        (Path(__file__), 'completed_verification/export_adapter.py'),
    ]:
        copy(original, out / relative)
    requests_n, responses_n, cost, unknown = 0, 0, 0.0, 0
    for f in (run / 'calls').glob('*.request.json'):
        requests_n += 1
        request = load(f)
        if request['authorization_header_omitted'] is not True: raise ValueError('authorization must be omitted')
    for f in (run / 'calls').glob('*.attempt*.response.json'):
        responses_n += 1; response = load(f)
        charge = response.get('response', {}).get('usage', {}).get('cost')
        if type(charge) in (int, float): cost += charge
        else: unknown += 1
    write(out / 'actual_call_usage.json', {'requests_n': requests_n, 'actual_http_responses_n': responses_n,
          'known_cost_usd': cost, 'unknown_cost_responses_n': unknown, 'quality_regeneration_n': 0,
          'model': protocol['model'], 'provider': protocol['provider'],
          'scope': 'Retained actual transport receipts for this separate source cohort only.'})
    subprocess.run([sys.executable, '-B', str(out / 'tools/score_retained_four_methods.py'), '--evidence', str(out), '--write'], check=True, stdout=subprocess.DEVNULL)
    analysis = load(out / 'results/analysis.json')
    lines = ['# Separate source snapshot: retained four-method evaluation', '',
             'This is one original question evaluated on an additive source snapshot. It is separate from the original 560-question frozen-index accounting and does not change that index or inherit historical scores.', '',
             '| Method | N | Requested-record F1 | Exact | Retained status |',
             '| --- | ---: | ---: | ---: | --- |']
    for method in METHODS:
        row = analysis['tables'][method]
        lines.append(f"| {method} | {row['n']} | {row['requested_complete_record_macro_f1']:.6f} | {row['exact_outputs']}/{row['n']} | {', '.join(row['execution_status_counts'])} |")
    lines += ['', f"The five first-call requests cost ${cost:.6f}; unknown-cost responses: {unknown}. Original responses, generated queries, parse errors, abstentions and execution receipts are retained. No answer-quality regeneration occurred.", '',
              'The strict scorer measures only the requested typed output records. It does not establish generated-query semantics, source-predicate validity, documentary provenance or causality. No human/expert validation is claimed. Base graph/text cutoff and complete coverage equality are unestablished; lexical retrieval remains bounded.', '']
    if kind == 'source58_fullbody_v2':
        lines += ['The unchanged question requests ten recent CR document identities for TS 38.133. The source-calendar reference retains the full 16,017-record native population and complete date groups; any ten identities from the latest 563-record date group satisfy the cutoff. Source-reported meeting end dates define meeting-presentation recency, not upload, approval or normative enactment time. All 342 retained Word report bodies and four complete PPTX XML-text packages enter the frozen lexical corpus: 6,755,948 Word-body paragraphs plus 1,686 PPTX XML paragraphs are represented by 61,730 consecutive raw chunks. All original member packages and the exact 376,969,857-byte raw model input are retained in ordered binary shards below the repository file limit. Raw projection preserves w:t/m:t/a:t and tabs/breaks, including empty paragraphs; OCR, embedded binary-object semantics, deleted-text decoding, font-symbol decoding and final-visible document interpretation are not established. The 23 legacy DOC access derivatives are explicitly pinned and were not freshly reconverted.', '']
    lines += ['Both retained structured queries order CR.uploadedDate and do not use the added source-reported Meeting calendar dates. Text2SQL attains requested-record F1=1 for this saved output, while Text2Cypher attains 0; this does not validate calendar-recency semantics for either generated query. The explicit source-predicate limitation receipt is retained under completed_verification. A separate read-only diagnostic joins all twenty actually returned document identities to the immutable source SQL properties: all ten Cypher output values have NULL uploadedDate, while all ten SQL output values are non-NULL and equal the full non-NULL population\'s descending top ten. The complete relevant population has 1,734 NULL and 14,283 non-NULL uploadedDate values. This directly corroborates the different NULL placement in these retained outputs; ordering within the Cypher NULL tie group is unspecified. See [actual 20-output diagnostic](completed_verification/actual20_uploadedDate_NULL_order_diagnostic.json) and its packaged reader. No generated query, response, score or reference was repaired or rerolled.', '']
    if kind.startswith('source5_'):
        lines += ['The five added actual source tables are supported by two complete authored source members. CQ008 retains four required fields (TS identity and three integer counts); CQ041 requires the complete uncapped set of Section identities passing the inclusive five-table direct-containment threshold. This is a graph-relative recorded-snapshot contract, not a claim that every physical table in every authored source has been extracted. Four mathematical captions retain OMML/XML provenance; their W:t-only tableCaption strings remain explicitly partial.', '']
    if kind == 'source17':
        lines += ['The generated Text2SQL query returned the three requested TS-family identities using the retained REFERENCES and MODIFIES path. It did not use the added approved normative-incorporation observations. Its output-record score therefore must not be presented as verification that the query implemented approval/incorporation or that references alone prove decisions entered the standard.', '']
    lines += ['Run offline prompt, parse and score replay with:', '',
              '```bash', 'python -B tools/verify_retained_four_methods.py --evidence .', '```', '',
              'This command checks packaged hashes, reconstructs all five prompts, reproduces retained retrieval parsing (including failures), and recomputes all four strict scores. It does not call a provider, execute graph/SQL queries, or rerun full-text retrieval. The source_patch subdirectory contains separate authentic-source materialization and native/SQL/scorer validation evidence. Rebuilding that graph requires its documented baseline files; it is a separate operation.', '',
              'Historical absolute source paths in receipts are preserved as provenance. Packaged pin locations are declared in evaluation_manifest.json; offline replay resolves only package-relative copies.', '']
    (out / 'README.md').write_text('\n'.join(lines))
    files = {str(p.relative_to(out)): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()}
    if any(p.stat().st_size >= 100_000_000 for p in out.rglob('*') if p.is_file()): raise ValueError('oversized tracked file')
    manifest = {'kind': 'Portable retained separate-source four-method evaluation', 'source_variant': kind,
                'cohort_ids': protocol['cohort_ids'], 'cohort_n': 1, 'method_items': 4,
                'source_protocol_sha256': sha(run / 'protocol.json'), 'source_patch_manifest_sha256': sha(PATCHES[kind] / 'manifest.json'),
                'packaged_source_pin_locations': locations, 'packaged_source_pin_shards': shard_locations, 'external_large_source_pins': {key: protocol['source_pins'][key] for key in ('sql_db_path', 'graph_ttl_path')},
                'existing_frozen_core_modified_or_merged': False, 'quality_regeneration_n': 0,
                'files': files}
    write(out / 'evaluation_manifest.json', manifest)
    if source_before != {str(p): sha(p) for p in run.rglob('*') if p.is_file()}: raise ValueError('original run changed during export')
    result = json.loads(subprocess.check_output([sys.executable, '-B', str(out / 'tools/verify_retained_four_methods.py'), '--evidence', str(out)], text=True))
    write(out.parent / (out.name + '_offline_replay_receipt.json'), result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--kind', choices=tuple(PATCHES), required=True)
    parser.add_argument('--out-dir', type=Path, required=True); args = parser.parse_args()
    print(json.dumps(export(args.kind, args.out_dir.resolve()), ensure_ascii=False))
