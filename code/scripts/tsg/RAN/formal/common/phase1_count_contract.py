#!/usr/bin/env python3
"""phase1_count_contract.py — 선택한 회의 원본 자료에서 Phase-1 기대 건수와 식별정보를 저장한다.

Spec: 각 WG tdoc_ontology_specs(Tdoc_list) Step 7 §6·§11; 기존 snapshot은 legacy 기준이다.
Ontology: Meeting~WorkingGroup 및 Tdoc/CR/LS의 기존 정규화·신원·Contact 범위.
Cycle: 회의 입력 확인 → 회사 정규화 → 원본 자료 기준의 예상 건수 저장 → JSON-LD 생성·기존 검증.
배경: 새 설치는 선택한 원본 자료의 기대수를 사용하고, 생성된 JSON-LD에서 기대수를 복사하지 않는다.
사용: bootstrap prepare_phase1_counts.py; 검증기는 fresh 환경에서 load_expected_counts를 호출한다.
LLM 호출: 없음. XLSX·설정·설치 검증 기록만 읽으며 DB·네트워크 접근 없음.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/common/bootstrap'))
from bootstrap_runtime import Refused, file_hash, file_manifest, relative_file  # noqa: E402

ENV = 'SPECTRA_FORMAL_P1_CONTRACT_ROOT'
CONTRACT_ROOT = Path('logs/common/bootstrap/formal-p1-contracts')
SCOPE = Path('logs/common/bootstrap/scope.json')
STATE = Path('logs/common/bootstrap/state.json')
CLASSES = ('Meeting', 'Release', 'Company', 'Contact', 'WorkItem', 'AgendaItem',
           'Spec', 'WorkingGroup', 'Tdoc', 'CR', 'LS')


def canonical(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()


def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def read(root: Path, path: Path):
    relative_file(root, path)
    if any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root)):
        raise Refused('Phase-1 계약 입력의 symlink를 지원하지 않는다')
    return json.loads(path.read_text(encoding='utf-8'))


def contract_path(root: Path, wg: str) -> Path:
    if wg not in {f'RAN{i}' for i in range(1, 6)}:
        raise Refused('Phase-1 count 계약의 WG가 다르다')
    configured = os.environ.get(ENV)
    if configured:
        supplied = Path(configured)
        supplied = supplied if supplied.is_absolute() else root / supplied
        if supplied.resolve() != (root / CONTRACT_ROOT).resolve():
            raise Refused('Phase-1 최초 계약 루트가 설치기의 고정 경로와 다르다')
    path = root / CONTRACT_ROOT / wg / 'expected-counts.json'
    relative_file(root, path)
    if any(p.is_symlink() for p in path.parents if p.is_relative_to(root)):
        raise Refused('Phase-1 계약 루트의 symlink를 지원하지 않는다')
    return path


def source_identity(root: Path, wg: str, scope_path: Path) -> tuple[dict, list[Path]]:
    scope = read(root, scope_path)
    if wg not in scope.get('wgs', []):
        raise Refused('Phase-1 count 계약이 선택 WG 범위 밖이다')
    manifest_path = root / f'logs/common/bootstrap/inputs/meetings-{wg}.json'
    manifest = read(root, manifest_path)
    meetings = manifest.get('meetings', [])
    excluded = manifest.get('excluded', [])
    folders = [r['folder'] for r in meetings + excluded]
    if (manifest.get('kind') != 'meeting-inputs' or manifest.get('wg') != wg or not meetings
            or len(folders) != len(set(folders))
            or set(folders) != set(scope.get('meetings', {}).get(wg, []))):
        raise Refused('Phase-1 선택 회의와 입력 준비 기록의 범위가 다르다')
    target = root / f'ontology/input/tsg/RAN/formal/meetings/{wg}/TDoc_List'
    files = sorted(p for p in target.iterdir() if p.suffix.lower() in ('.xlsx', '.xlsm'))
    expected = {r['path']: r['sha256'] for r in manifest.get('outputs', [])
                if Path(r['path']).parent == target.relative_to(root)}
    if not files or file_manifest(root, files) != expected:
        raise Refused('Phase-1 TDoc 원본 입력의 누락·추가·내용 변경을 확인했다')
    records = [r for m in meetings for r in m.get('selected_sources', [])] + manifest.get('outputs', [])
    claimed = {}
    for record in records:
        path = root / record['path']
        read_name = relative_file(root, path)
        if any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root)):
            raise Refused('Phase-1 선택 원본 자료의 symlink를 지원하지 않는다')
        if file_hash(path) != record['sha256'] or path.stat().st_size != record['size_bytes']:
            raise Refused('Phase-1 선택 원본 자료의 SHA·크기가 입력 준비 기록과 다르다')
        if read_name in claimed and claimed[read_name] != record['sha256']:
            raise Refused('Phase-1 원본 자료 검증 기록에 서로 다른 SHA가 있다')
        claimed[read_name] = record['sha256']
    if not records or any(not m.get('selected_sources') for m in meetings):
        raise Refused('Phase-1 선택 원문 근거가 없다')
    additional = [scope_path, manifest_path, root / 'ontology/input/spec_titles.json']
    aliases = root / f'ontology/intermediate/tsg/RAN/formal/{wg}/phase-1'
    additional += [aliases / name for name in ('company_aliases.json', 'company_aliases_significant.json')]
    optional_company_sources = []
    base_aliases = root / 'ontology/intermediate/tsg/RAN/formal/RAN1/phase-1/company_aliases_significant.json'
    if wg != 'RAN1' and base_aliases.exists():
        additional.append(base_aliases)
        if 'RAN1' not in scope.get('wgs', []):
            optional_company_sources.append(relative_file(root, base_aliases))
    claimed.update(file_manifest(root, additional))
    from tdoc_source_supplements import source_inputs
    supplements = source_inputs(root, wg, {m['meeting_id'] for m in meetings})
    from tdoc_source_identity_corrections import source_inputs as correction_inputs
    supplements.update(correction_inputs(root, wg, {m['meeting_id'] for m in meetings}))
    from tdoc_source_classification import source_inputs as classification_inputs
    supplements.update(classification_inputs(root, wg, {m['meeting_id'] for m in meetings}))
    from agenda_source_supplements import source_inputs as agenda_inputs
    supplements.update(agenda_inputs(root, wg, {m['meeting_id'] for m in meetings}))
    from tdoc_revision_evidence import source_inputs as revision_inputs
    supplements.update(revision_inputs(root, wg))
    authored = sorted(set(supplements) - set(claimed))
    claimed.update(supplements)
    return {'scope_path': relative_file(root, scope_path), 'scope': scope,
            'sources': dict(sorted(claimed.items())),
            'authored_supplement_sources': authored,
            'optional_company_sources': optional_company_sources}, files


def build_identity(root: Path, wg: str, identity: dict) -> dict:
    state = read(root, root / STATE)
    context = state.get('context', {})
    if state.get('schema') != 2 or not state.get('started') or context.get('scope') != identity['scope']:
        raise Refused('Phase-1 최초 설치의 build·scope 신원을 확인하지 못했다')
    if bounded_tdoc_scope(identity['scope']):
        # 선택 회의 단계는 입력 승격과 회사 정규화를 함께 완료한 뒤 같은 SHA 계약을 확정한다.
        keys = [f'bounded.meetings.inputs@{wg}']
        if wg != 'RAN1' and 'RAN1' in identity['scope'].get('wgs', []):
            keys.append('bounded.meetings.inputs@RAN1')
    else:
        keys = [f'p0.prepare.meetings@{wg}', f'p1.jsonld.company@{wg}']
        if wg != 'RAN1' and 'RAN1' in identity['scope'].get('wgs', []):
            keys.append('p1.jsonld.company@RAN1')
    for key in keys:
        prior = state.get('steps', {}).get(key, {})
        if prior.get('status') != 'done' or prior.get('exit') != 0:
            raise Refused('Phase-1 선행 입력·회사 정규화 완료 상태·원문 식별 검증 기록이 없다: ' + key)
    for name, sha in identity['sources'].items():
        if (name.startswith(('ontology/input/', 'ontology/intermediate/'))
                and name not in identity.get('authored_supplement_sources', [])
                and name not in identity.get('optional_company_sources', [])):
            if state.get('artifacts', {}).get(name) != sha:
                raise Refused('Phase-1 원본 자료·정규화 SHA가 설치기 산출물 검증 기록과 다르다: ' + name)
    return {'started': state['started'], 'context_sha256': digest(context)}


def bounded_tdoc_scope(scope: dict) -> bool:
    """별도 회의 DAG의 단계 키는 검증된 TDoc 제한 범위에서만 인정한다."""
    if scope.get('build_mode') != 'bounded' or scope.get('selection', {}).get('data_kinds') != ['tdoc']:
        return False
    from bounded_scope import validate_selection
    validate_selection(scope)
    return True


@contextmanager
def wg_modules(root: Path, wg: str):
    """WG별 기존 문법의 import 이름을 격리한다. 데이터 산출 파일은 열지 않는다."""
    directory = root / f'scripts/tsg/RAN/formal/{wg}/phase-1/jsonld'
    names = ('tdoc_list_binding', 'meeting_id', 'date_swap', 'submitter_roles', 'contact_scope')
    old = {name: sys.modules.pop(name) for name in names if name in sys.modules}
    old_path = sys.path[:]
    try:
        modules = []
        for index, filename in enumerate(('01_company_normalization.py', '02_reference_classes.py',
                                          '03_tdoc_instances.py', '04_validation.py')):
            spec = importlib.util.spec_from_file_location(f'_p1_counts_{wg}_{index}', directory / filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            modules.append(module)
        yield modules
    finally:
        sys.path[:] = old_path
        for name in names:
            sys.modules.pop(name, None)
        sys.modules.update(old)


def normalization_rules(root: Path, wg: str) -> dict:
    paths = list((root / f'scripts/tsg/RAN/formal/{wg}/phase-1/jsonld').glob('*.py'))
    paths += [root / 'scripts/tsg/RAN/formal/common/contact_scope.py',
              root / 'scripts/tsg/RAN/formal/common/phase1_count_contract.py',
              root / 'scripts/common/common/atomic_io.py',
              root / 'scripts/tsg/RAN/formal/common/phase-1/date_columns.py',
              root / 'scripts/tsg/RAN/formal/common/phase-1/submitter_role_rules.py',
              root / 'scripts/tsg/RAN/formal/common/tdoc_source_supplements.py',
              root / 'scripts/tsg/RAN/formal/common/tdoc_source_identity_corrections.py',
              root / 'scripts/tsg/RAN/formal/common/tdoc_source_classification.py',
              root / 'scripts/tsg/RAN/formal/common/agenda_source_supplements.py',
              root / 'scripts/tsg/RAN/formal/common/tdoc_revision_evidence.py']
    # When retained Word evidence is selected, bind its maintained accepted-view
    # readers as well as the identity overlay. Fixtures without ledgers stay XLSX-only.
    from tdoc_source_supplements import ledger_path
    from tdoc_source_classification import ledger_path as classification_ledger
    from tdoc_source_identity_corrections import ledger_path as correction_ledger
    if any(p.exists() for p in (ledger_path(root, wg), classification_ledger(root, wg), correction_ledger(root, wg))):
        paths += [root / 'scripts/tsg/RAN/formal/common' / name for name in
                  ('cr_form.py', 'decision_disposition.py', 'document_decision_source.py', 'docx_text.py')]
    return file_manifest(root, paths)


def predict_from_sources(root: Path, wg: str, files: list[Path], *, min_company_tdocs=10) -> dict:
    """선택 XLSX의 정규화 신원을 예측한다. 기존 output/*.jsonld는 읽지 않는다.

    선택한 회사 최소 기고 수, 같은 문서의 열 병합, placeholder 제거, 신원 병합, Contact 교집합은
    기존 producer의 규칙을 그대로 사용한다. 검사 대상 파일과 독립된 메모리에서 계산한다.
    """
    with wg_modules(root, wg) as (company, reference, tdoc, validator):
        unique, frequency = company.load_all_companies(company.INPUT_DIR)
        args = (unique, frequency) if wg == 'RAN1' else (unique, frequency, company.load_ran1_aliases())
        aliases = company.merge_uri_colliding_canonicals(company.build_company_aliases(*args), frequency)
        minimum = company.positive_company_count(min_company_tdocs)
        # 실제 저장 함수의 계약으로 예측하되 운영 중간 산출물은 덮어쓰지 않는다.
        with tempfile.TemporaryDirectory(prefix='spectra-p1-company-') as directory:
            temporary_root = Path(directory)
            original_intermediate = company.INTERMEDIATE_DIR
            try:
                company.INTERMEDIATE_DIR = temporary_root
                if wg == 'RAN1':
                    all_path = temporary_root / 'company_aliases.json'
                    significant_path = temporary_root / 'company_aliases_significant.json'
                    company.save_results(aliases, all_path, significant_path,
                                         temporary_root / 'company_raw.json', unique, frequency, minimum)
                else:
                    company.save_results(aliases, frequency, minimum)
                    all_path = temporary_root / wg / 'phase-1/company_aliases.json'
                    significant_path = all_path.with_name('company_aliases_significant.json')
                normalized = json.loads(all_path.read_text(encoding='utf-8'))
                significant = json.loads(significant_path.read_text(encoding='utf-8'))
                company_records = reference.generate_companies(significant_path)
            finally:
                company.INTERMEDIATE_DIR = original_intermediate
        intermediate = root / f'ontology/intermediate/tsg/RAN/formal/{wg}/phase-1'
        if (read(root, intermediate / 'company_aliases.json') != normalized
                or read(root, intermediate / 'company_aliases_significant.json') != significant):
            raise Refused('Phase-1 회사 정규화 입력이 선택 원본 자료의 빈도·별칭 규칙과 다르다')
        pairs = [(path, reference.load_excel_file(path)) for path in files]
        data = [frame for _, frame in pairs if not frame.empty]
        pairs = [(path, frame) for path, frame in pairs if not frame.empty]
        graphs = {}
        filenames = {'Meeting': 'meetings', 'Release': 'releases', 'Company': 'companies',
                     'Contact': 'contacts', 'WorkItem': 'work_items', 'AgendaItem': 'agenda_items',
                     'Spec': 'specs', 'WorkingGroup': 'working_groups'}
        def ids(records, name):
            records = reference.drop_placeholder_nodes(records, name)
            nodes = reference.merge_by_identity(records, name)
            graphs[filenames[name] + '.jsonld'] = nodes
            return {node['@id'] for node in nodes}
        predicted = {
            'Meeting': ids(reference.generate_meetings(files), 'Meeting'),
            'Release': ids(reference.generate_releases(data), 'Release'),
            'Company': ids(company_records, 'Company'),
            'Contact': ids(reference.generate_contacts(data), 'Contact'),
            'WorkItem': ids(reference.generate_work_items(data), 'WorkItem'),
            'AgendaItem': ids(reference.generate_agenda_items(pairs), 'AgendaItem'),
            'Spec': ids(reference.generate_specs(data), 'Spec'),
            'WorkingGroup': ids(reference.generate_working_groups(data), 'WorkingGroup'),
            'Tdoc': set(), 'CR': set(), 'LS': set()}
        company_map = tdoc.load_company_aliases()
        instances = []
        seen_tdocs = set()
        for path in files:
            args = (path, company_map) if wg == 'RAN1' else (path, company_map, seen_tdocs)
            records = tdoc.process_file(*args)[0]
            instances.extend(records)
        from tdoc_source_supplements import supplement_instances
        instances.extend(supplement_instances(root, wg, instances,
            {name.removesuffix('.jsonld'): nodes for name, nodes in graphs.items()},
            {tdoc.extract_meeting_from_filename(path.name) for path in files} - {None}))
        from tdoc_source_identity_corrections import overlay_identity_corrections
        overlay_identity_corrections(root, wg, instances,
            {name.removesuffix('.jsonld'): nodes for name, nodes in graphs.items()},
            {tdoc.extract_meeting_from_filename(path.name) for path in files} - {None})
        from tdoc_source_classification import apply_source_classifications
        apply_source_classifications(root, wg, instances,
            {name.removesuffix('.jsonld'): nodes for name, nodes in graphs.items()},
            {tdoc.extract_meeting_from_filename(path.name) for path in files} - {None})
        tdoc.drop_placeholder_references(instances)
        referenced = set()
        for item in instances:
            predicted[item['@type'].split(':', 1)[1]].add(item['@id'])
            contacts = item.get('hasContact', [])
            contacts = contacts if isinstance(contacts, list) else [contacts]
            kept = [target for target in contacts if target in predicted['Contact']]
            referenced.update(kept)
            if 'hasContact' in item:
                if not kept:
                    del item['hasContact']
                elif isinstance(item['hasContact'], list):
                    item['hasContact'] = kept
                else:
                    item['hasContact'] = kept[0]
        predicted['Contact'] &= referenced
        graphs['contacts.jsonld'] = [c for c in graphs['contacts.jsonld'] if c['@id'] in referenced]
        graphs['tdocs.jsonld'] = instances
        def memory_graph(path):
            if path.name not in graphs:
                raise Refused('Phase-1 원본 자료 예측에 선언되지 않은 JSON-LD 읽기: ' + path.name)
            return graphs[path.name]
        validator.load_jsonld = memory_graph
        checks = {'props': validator.validate_required_properties(),
                  'refs': validator.validate_internal_references(),
                  'enum': validator.validate_enum_values()}
        failed = {name for name, result in checks.items() if not result[0]}
        if failed - validator.KNOWN_WARN_AXES:
            raise Refused('Phase-1 선택 원본 자료에 authored 허용 범위 밖 검증 오류가 있다: '
                          + ','.join(sorted(failed - validator.KNOWN_WARN_AXES)))
        return {'expected_counts': {name: len(predicted[name]) for name in CLASSES},
                'expected_identity_sha256': {name: digest(sorted(predicted[name])) for name in CLASSES},
                'expected_warning_axes': sorted(failed),
                'authored_allowed_warning_axes': sorted(validator.KNOWN_WARN_AXES),
                'source_validation_sha256': {name: digest(result) for name, result in checks.items()},
                'method': 'selected-source-normalization-identity-sets-before-jsonld'}


def immutable(root: Path, path: Path, value) -> None:
    relative_file(root, path)
    if path.exists():
        if read(root, path) != value:
            raise Refused('Phase-1 저장된 최초 기대수 계약과 달라 덮어쓰기를 거절한다')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.p1-counts-', dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(canonical(value)); stream.flush(); os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if read(root, path) != value:
                raise Refused('Phase-1 최초 기대수 계약의 동시 생성 값이 다르다')
    finally:
        os.unlink(temporary)


def prepare(root: Path, wg: str, scope_path: Path, *, predictor=None) -> dict:
    path = contract_path(root, wg)
    identity, files = source_identity(root, wg, scope_path)
    build = build_identity(root, wg, identity)
    rules = normalization_rules(root, wg)
    state_sha = file_hash(root / STATE)
    if path.exists():
        sealed = read(root, path)
        if (sealed.get('source_identity') != identity
                or sealed.get('build_identity') != build
                or sealed.get('normalization_rules') != rules):
            raise Refused('Phase-1 저장된 최초 기대수 계약의 원본 자료·범위·build·규칙이 달라 덮어쓰기를 거절한다')
    else:
        state = read(root, root / STATE)
        if (any(f'p1.jsonld.{step}@{wg}' in state.get('steps', {})
                for step in ('reference', 'tdoc', 'validate'))
                or f'bounded.meetings.jsonld@{wg}' in state.get('steps', {})
                or any((root / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}').glob('*.jsonld'))):
            raise Refused('Phase-1 JSON-LD 생성·검증이 시작되어 최초 기대수 계약을 새로 저장할 수 없다')
    if predictor is not None:
        prediction = predictor(root, wg, files)
    else:
        minimum = identity['scope'].get('company_min_tdocs', 10)
        if type(minimum) is not int or minimum < 1:
            raise Refused('Phase-1 회사 최소 기고 수는 양의 정수여야 한다')
        prediction = predict_from_sources(root, wg, files, min_company_tdocs=minimum)
    if (source_identity(root, wg, scope_path)[0] != identity
            or normalization_rules(root, wg) != rules or file_hash(root / STATE) != state_sha):
        raise Refused('Phase-1 기대수 계산 중 원본 자료·범위·규칙·설치 상태가 바뀌었다')
    value = {'schema': 1, 'wg': wg, 'source_identity': identity, 'build_identity': build,
             'normalization_rules': rules, **prediction}
    if (set(value['expected_counts']) != set(CLASSES)
            or any(type(n) is not int or n < 0 for n in value['expected_counts'].values())
            or set(value['expected_identity_sha256']) != set(CLASSES)):
        raise Refused('Phase-1 기대수 계약의 클래스·계수 형식이 다르다')
    immutable(root, path, value)
    return value


def validated_contract(root: Path, wg: str) -> dict:
    value = read(root, contract_path(root, wg))
    identity, _ = source_identity(root, wg, root / SCOPE)
    if (value.get('schema') != 1 or value.get('wg') != wg
            or value.get('source_identity') != identity
            or value.get('build_identity') != build_identity(root, wg, identity)
            or value.get('normalization_rules') != normalization_rules(root, wg)
            or value.get('method') != 'selected-source-normalization-identity-sets-before-jsonld'
            or set(value.get('expected_counts', {})) != set(CLASSES)
            or any(type(n) is not int or n < 0 for n in value['expected_counts'].values())):
        raise Refused('Phase-1 저장된 기대수 계약의 원본 자료·규칙·build 신원이 다르다')
    state = read(root, root / STATE)
    path = contract_path(root, wg)
    stage = 'bounded.meetings.counts' if bounded_tdoc_scope(identity['scope']) else 'p1.prepare.counts'
    prior = state.get('steps', {}).get(f'{stage}@{wg}', {})
    if (prior.get('status') != 'done' or prior.get('exit') != 0
            or state.get('artifacts', {}).get(relative_file(root, path)) != file_hash(path)):
        raise Refused('Phase-1 최초 기대수 계약 저장의 완료 상태·SHA 검증 기록이 없다')
    return value


def load_expected_counts(root: Path, wg: str, legacy: dict) -> dict:
    if not os.environ.get(ENV):
        from tdoc_source_supplements import legacy_expected_counts
        from tdoc_source_classification import ledger_path, legacy_expected_counts as classified_counts
        from agenda_source_supplements import legacy_expected_counts as agenda_counts
        supplemented = legacy_expected_counts(root, wg, legacy)
        classified = classified_counts(root, wg, supplemented) if ledger_path(root, wg).exists() else supplemented
        return agenda_counts(root, wg, classified)
    return validated_contract(root, wg)['expected_counts']


def load_warning_axes(root: Path, wg: str, legacy: set) -> set:
    if not os.environ.get(ENV):
        return legacy
    value = validated_contract(root, wg)
    axes = value.get('expected_warning_axes')
    if (not isinstance(axes, list) or len(axes) != len(set(axes))
            or not set(axes) <= legacy or value.get('authored_allowed_warning_axes') != sorted(legacy)):
        raise Refused('Phase-1 원본 자료의 예상 경고 축 형식이 다르다')
    return set(axes)


def verify_source_validation_results(root: Path, wg: str, results: dict) -> None:
    """속성·참조·열거값 검사 결과의 해시가 원본 입력에서 먼저 저장한 결과와 다르면 거부한다."""
    if not os.environ.get(ENV):
        return
    value = validated_contract(root, wg)
    checks = {'props': (results['props_passed'], results['required_properties']),
              'refs': (results['refs_passed'], results['reference_stats'],
                       results['reference_errors'], results['reference_notes']),
              'enum': (results['enum_passed'], results['enum_errors'])}
    if {name: digest(result) for name, result in checks.items()} != value.get('source_validation_sha256'):
        raise Refused('Phase-1 실제 속성·참조·enum 검증 근거가 원본 입력에서 먼저 저장한 검사 결과와 다르다')


def verify_jsonld_identities(root: Path, wg: str, output: Path) -> None:
    """JSON-LD의 클래스별 ID와 중복 여부를 원본 입력에서 먼저 저장한 식별정보와 대조한다."""
    if not os.environ.get(ENV):
        return
    value = validated_contract(root, wg)
    filenames = {'Meeting': 'meetings', 'Release': 'releases', 'Company': 'companies',
                 'Contact': 'contacts', 'WorkItem': 'work_items', 'AgendaItem': 'agenda_items',
                 'Spec': 'specs', 'WorkingGroup': 'working_groups'}
    observed = {name: [] for name in CLASSES}
    for name, filename in filenames.items():
        document = read(root, output / (filename + '.jsonld'))
        if not isinstance(document.get('@graph'), list):
            raise Refused('Phase-1 실제 JSON-LD @graph 목록이 없다')
        for node in document['@graph']:
            types = node.get('@type', [])
            types = types if isinstance(types, list) else [types]
            if 'tdoc:' + name not in types or not isinstance(node.get('@id'), str):
                raise Refused('Phase-1 실제 참조 노드의 클래스·신원이 다르다')
            observed[name].append(node['@id'])
    document = read(root, output / 'tdocs.jsonld')
    if not isinstance(document.get('@graph'), list):
        raise Refused('Phase-1 실제 TDoc JSON-LD @graph 목록이 없다')
    for node in document['@graph']:
        if node.get('@type') not in ('tdoc:Tdoc', 'tdoc:CR', 'tdoc:LS') or not isinstance(node.get('@id'), str):
            raise Refused('Phase-1 실제 문서 노드의 클래스·신원이 다르다')
        observed[node['@type'].split(':', 1)[1]].append(node['@id'])
    if (any(len(nodes) != len(set(nodes)) for nodes in observed.values())
            or {name: digest(sorted(nodes)) for name, nodes in observed.items()}
            != value.get('expected_identity_sha256')):
        raise Refused('Phase-1 실제 JSON-LD의 클래스별 신원이 원본 입력에서 먼저 저장한 클래스별 ID 목록과 다르다')


def jsonld_checkpoint(root: Path, output: Path) -> dict | None:
    """아홉 JSON-LD 파일의 SHA를 기록한다. 종료 시 verify_jsonld_checkpoint가 재검사한다."""
    if not os.environ.get(ENV):
        return None
    names = ('meetings', 'releases', 'companies', 'contacts', 'work_items',
             'agenda_items', 'specs', 'working_groups', 'tdocs')
    paths = [output / (name + '.jsonld') for name in names]
    for path in paths:
        if any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root)):
            raise Refused('Phase-1 검증 산출의 symlink를 지원하지 않는다')
    return file_manifest(root, paths)


def verify_jsonld_checkpoint(root: Path, output: Path, before: dict | None) -> None:
    if before is not None and jsonld_checkpoint(root, output) != before:
        raise Refused('Phase-1 검증 중 실제 JSON-LD 산출 내용이 바뀌었다')
