#!/usr/bin/env python3
"""Exercise source identity rejection and pinned native conversion acceptance."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--exact-source', type=Path, required=True)
    parser.add_argument('--native-source', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    runner = args.bundle / 'restore_cr_probe.py'
    spec = importlib.util.spec_from_file_location('cr_source_guard_runner', runner)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    exact = json.loads((args.bundle / 'network_pilot/R3-233526/recipe.json').read_text())
    native = json.loads((args.bundle / 'network_pilot/R3-180694/recipe.json').read_text())
    cases = []
    with tempfile.TemporaryDirectory(prefix='spectra-cr-source-guards-') as temporary:
        target = Path(temporary) / 'source.docx'
        target.write_bytes(args.exact_source.read_bytes() + b'\n')
        sidecar = target.with_name(target.name + '.conversion.json')
        sidecar.write_text(json.dumps({'output_sha256': module.sha(target)}))
        try:
            module.execute_recipe(args.repository.resolve(), exact, target)
            cases.append({'case': 'forged_sidecar_for_exact_member_source', 'rejected': False})
        except ValueError as error:
            cases.append({'case': 'forged_sidecar_for_exact_member_source', 'rejected': str(error) == 'Source DOCX digest differs without a pinned native conversion', 'error': str(error)})
        shutil.copyfile(args.native_source, target)
        shutil.copyfile(args.native_source.with_name(args.native_source.name + '.conversion.json'), sidecar)
        result = module.execute_recipe(args.repository.resolve(), native, target)
        cases.append({'case': 'genuine_pinned_native_conversion', 'accepted': result['supported_replay_exact'], 'chunks': result['actual_chunk_count'], 'raw_field_sha_equal': result['raw_field_sha_equal'], 'snapshot_source_container_sha_equal': result['snapshot_source_container_sha_equal']})
        proof = json.loads(sidecar.read_text())
        proof['native_sha256'] = '0' * 64
        sidecar.write_text(json.dumps(proof))
        try:
            module.execute_recipe(args.repository.resolve(), native, target)
            cases.append({'case': 'wrong_native_digest_in_sidecar', 'rejected': False})
        except ValueError as error:
            cases.append({'case': 'wrong_native_digest_in_sidecar', 'rejected': str(error) == 'Converted native source digest differs', 'error': str(error)})
    report = {'runner_sha256': module.sha(runner), 'control_script_sha256': module.sha(Path(__file__)), 'controls': cases, 'all_gates_as_expected': all(x.get('rejected', x.get('accepted', False)) for x in cases), 'runtime': module.runtime()}
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    raise SystemExit(0 if report['all_gates_as_expected'] else 1)


if __name__ == '__main__':
    main()
