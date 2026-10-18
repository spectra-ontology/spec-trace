#!/usr/bin/env python3
"""Build an isolated graph with source-authored CR summaries on preserved existing nodes.

Spec: KDD D&B source investigation; no question is admitted by this build.
Ontology: sourceAuthoredSummary string on existing CR/Tdoc; old properties preserved.
Cycle: overnight audit ending 2026-10-15 10:00 KST.
배경: Verify actual additive-source graph restoration without changing base.
사용: .venv/bin/python build_CR_summary_graph.py --config PATH
LLM 호출: 없음; no prediction or external model API calls.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import socket
import subprocess
import time
import uuid

BASE = Path(__file__).resolve().parent
ROOT = next(p for p in BASE.parents if (p / 'CLAUDE.md').exists())
ARGS = argparse.ArgumentParser()
ARGS.add_argument('--config', type=Path, required=True)
CONFIG_PATH = ARGS.parse_args().config.resolve()
CONFIG = json.loads(CONFIG_PATH.read_text())
WORK = BASE / CONFIG['work']
LOADER = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/pipeline/load_released_kg.py')
GIB = 1024 ** 3


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def pin(path):
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.pending')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def command(*args):
    return subprocess.check_output(list(args), text=True).strip()


def inspect(name):
    return json.loads(command('docker', 'inspect', name))[0]


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    with (BASE / 'native_capture.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        manifest_path = WORK / 'native_import_manifest.json'
        assert not manifest_path.exists(), 'Refuse overwrite or adoption of a prior import'
        windows = int(command('powershell.exe', '-NoProfile', '-Command',
                              '(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory')) * 1024
        available = next(int(s.split()[1]) * 1024 for s in Path('/proc/meminfo').read_text().splitlines()
                         if s.startswith('MemAvailable:'))
        guard = {'checked_utc': now(), 'linux_available_bytes': available,
                 'windows_available_bytes': windows, 'reserve_bytes': 16 * GIB,
                 'parser_budget_bytes': 8 * GIB, 'container_budget_bytes': 2 * GIB}
        save(WORK / 'host_resource_guard.json', guard)
        assert min(available, windows) >= 26 * GIB, 'Preserve host memory reserve'
        active = command('docker', 'ps', '--format', '{{.Names}}').splitlines()
        assert not any(n.startswith('kdd-db-') for n in active), 'Another audit database is active'
        mapping_path = BASE / CONFIG['mapping']
        mapping = json.loads(mapping_path.read_text())
        base = ROOT / mapping['base']['path']
        delta = ROOT / mapping['patch']['path']
        assert sha(base) == mapping['base']['sha256']
        assert sha(delta) == mapping['patch']['sha256']
        integrity_path = BASE / CONFIG['integrity']
        integrity = json.loads(integrity_path.read_text())
        assert integrity['status'] == 'all_primary_cells_and_stage_context_reread'
        assert sha(integrity_path) == CONFIG['integrity_sha256']
        assert integrity['source_rows_sha256'] == sha(Path(integrity['source_rows_path']))
        assert integrity['rows'] == mapping['new_property_values_n'] == CONFIG['values_n']
        assert len(mapping['fills']) == CONFIG['values_n']
        assert mapping['property_mapping']['native'] == 'CR.sourceAuthoredSummary'
        assert mapping['old_property_edits_n'] == 0 and mapping['new_edges_n'] == 0
        base_manifest_path = BASE.parent / ('relational/' + CONFIG['wg'] + '.manifest.json')
        base_manifest = json.loads(base_manifest_path.read_text())
        assert base_manifest['source']['sha256'] == sha(base)
        expected_nodes = base_manifest['nodes']
        expected_rels = base_manifest['relationships']
        snapshot = WORK / (CONFIG['wg'] + '-CR-summary-source-enriched.ttl')
        with snapshot.open('xb') as output:
            for path in (base, delta):
                with path.open('rb') as source:
                    shutil.copyfileobj(source, output)
        # Compare prefix incrementally, without allocating two full TTL copies.
        with base.open('rb') as original, snapshot.open('rb') as enriched:
            for block in iter(lambda: original.read(1024 * 1024), b''):
                assert block == enriched.read(len(block))
        assert sha(base) == mapping['base']['sha256']
        name, port = CONFIG['container'], CONFIG['port']
        all_names = command('docker', 'ps', '-a', '--format', '{{.Names}}').splitlines()
        assert name not in all_names, 'Refuse existing container adoption'
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', port))
        run_id = str(uuid.uuid4())
        image = json.loads(command('docker', 'image', 'inspect', 'neo4j:5.26.0'))[0]
        manifest = {'status': 'starting', 'created_utc': now(), 'working_group': CONFIG['wg'],
                    'snapshot_kind': 'separate additive CR source-authored summary graph',
                    'base': pin(base), 'delta': pin(delta), 'snapshot': pin(snapshot),
                    'base_bytes_preserved_as_exact_prefix': True,
                    'mapping': pin(mapping_path), 'root_raw_witness_integrity': pin(integrity_path),
                    'base_relational_manifest': pin(base_manifest_path), 'loader': pin(LOADER),
                    'wrapper': pin(Path(__file__)), 'config': pin(CONFIG_PATH), 'run_uuid': run_id,
                    'expected_nodes': expected_nodes, 'expected_relationships': expected_rels,
                    'image_id': image['Id'], 'host_guard': guard,
                    'target': {'container': name, 'bolt': f'bolt://127.0.0.1:{port}',
                               'cpu': 1, 'memory_bytes': 2 * GIB, 'loopback_only': True},
                    'question_admissions': 0, 'new_model_api_calls': 0,
                    'limit': 'Complete source-authored Summary of change values on a named WG meeting population. Original fields, status labels, nodes and edges preserved. No formal TSG approval or semantic paraphrase performance certification.'}
        save(manifest_path, manifest)
        started = time.monotonic()
        created = False
        try:
            data_dir = WORK / 'neo4j_data'
            data_dir.mkdir()
            command('docker', 'run', '--detach', '--pull=never', '--name', name,
                    '--cpus=1', '--memory=2g', '--memory-swap=2g',
                    '--publish', f'127.0.0.1:{port}:7687',
                    '--label', 'spectra.frozen.owner=contract_repair_v1',
                    '--label', f'spectra.frozen.run_uuid={run_id}',
                    '--label', f"spectra.frozen.source_sha256={manifest['snapshot']['sha256']}",
                    '--env', 'NEO4J_AUTH=none',
                    '--env', 'NEO4J_server_memory_heap_initial__size=512m',
                    '--env', 'NEO4J_server_memory_heap_max__size=512m',
                    '--env', 'NEO4J_server_memory_pagecache_size=256m',
                    '--volume', f'{data_dir}:/data', 'neo4j:5.26.0')
            created = True
            helper_path = BASE.parent / 'pending_recheck/RAN2_pack110_enriched/load_enriched_ttl_neo4j.py'
            spec = importlib.util.spec_from_file_location('preserved_source_guard', helper_path)
            helper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(helper)
            helper.guard_container(inspect(name), name, port, run_id, manifest['snapshot']['sha256'])
            helper.wait_empty_database(manifest['target']['bolt'])
            resource.setrlimit(resource.RLIMIT_AS, (8 * GIB, 8 * GIB))
            os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
            spec = importlib.util.spec_from_file_location('shipped_graph_loader', LOADER)
            loader = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(loader)
            manifest['status'] = 'parsing'
            save(manifest_path, manifest)
            nodes, relations, stats = loader.parse_ttl(snapshot)
            assert len(nodes) == expected_nodes and len(relations) == expected_rels
            assert not stats['prop_conflicts'], 'Additive source property conflict'
            manifest['parse_inventory'] = {'nodes': len(nodes), 'relationships': len(relations),
                                           'property_conflicts': stats['prop_conflicts']}
            manifest['status'] = 'loading'
            save(manifest_path, manifest)
            helper.guard_container(inspect(name), name, port, run_id, manifest['snapshot']['sha256'])
            helper.wait_empty_database(manifest['target']['bolt'])
            counts = loader.load_neo4j(manifest['target']['bolt'], 'neo4j', '', nodes, relations, 2000)
            expected_types = {loader.decode_rel_type(k): v for k, v in stats['rel_pred_camel'].items()}
            assert counts['total_nodes'] == expected_nodes
            assert counts['label_counts'] == dict(stats['class_subjects'])
            assert counts['rel_counts'] == expected_types
            assert sum(counts['rel_counts'].values()) == expected_rels
            manifest['measured_counts'] = counts
            manifest['status'] = 'restored_inventory_match'
            assert sha(base) == mapping['base']['sha256']
            print(json.dumps({'status': manifest['status'], 'nodes': expected_nodes,
                              'relationships': expected_rels, 'question_admissions': 0}), flush=True)
        except BaseException as exc:
            manifest['status'] = 'failed_preserved_for_diagnosis'
            manifest['error_type'] = type(exc).__name__
            manifest['error'] = str(exc)[:1000]
            raise
        finally:
            if created:
                info = inspect(name)
                labels = info['Config']['Labels'] or {}
                if labels.get('spectra.frozen.run_uuid') == run_id:
                    command('docker', 'stop', '--time', '20', name)
                    manifest['owned_container_stopped'] = True
            manifest['updated_utc'] = now()
            manifest['elapsed_seconds'] = time.monotonic() - started
            manifest['max_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            save(manifest_path, manifest)


if __name__ == '__main__':
    main()
