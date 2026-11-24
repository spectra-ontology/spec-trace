#!/usr/bin/env python3
"""bounded_scope.py — 선택 구축과 갱신에서 같은 자료 신원 계약을 검사한다.

Spec: docs/common/process/internal_install_guide.md 범위 고르기.
Ontology: 선택한 규격·Release와 원문·생성 자료의 식별자 대조.
Cycle: 범위 준비·원문 검증·파싱·적재·범위 CQ.
배경: 원문 선택만 줄인 뒤 기존 전체 자료를 소비하는 실행을 차단한다.
사용: prepare_scope.py·run_bootstrap.py와 갱신 실행기가 import한다.
LLM 호출: 없음. 네트워크·DB·모델 접근 없음.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from bootstrap_runtime import Refused, file_manifest, relative_file

KINDS = ('TS', 'TR', 'CR', 'tdoc', 'meetings', 'email')
SELECTION_KEYS = {'data_kinds', 'specs', 'releases', 'mail'}
SPEC_RE = re.compile(r'\d{2}\.\d{3}(?:-\d+)*')
TDOC_WGS = tuple(f'RAN{number}' for number in range(1, 6))
BUILD_MODE_REQUIRED_MESSAGE = (
    '새 범위에는 구축 모드를 명시한다. 소량 업무 구축은 --build-mode bounded --scope RAN1 '
    '--data-kind TS --spec RAN1:38.214 --release 18로 선택한다. '
    '회의·TDoc 구축은 --build-mode bounded --scope RAN1:115-116 --data-kind tdoc로 선택한다. '
    '선택 WG의 전체 구축 경로가 필요하면 --build-mode full을 명시한다. '
    'full의 회의 조건은 TS·TR·CR·메일 범위를 줄이지 않는다.'
)


def is_bounded(scope: dict | None) -> bool:
    return isinstance(scope, dict) and scope.get('build_mode') == 'bounded'


def is_tdoc_scope(scope: dict | None) -> bool:
    return (is_bounded(scope) and isinstance(scope.get('selection'), dict)
            and scope['selection'].get('data_kinds') == ['tdoc'])


def _validate_meeting_selection(scope: dict, selected: dict) -> None:
    wgs, requested = scope.get('wgs'), scope.get('requested')
    if (not isinstance(wgs, list) or not wgs
            or any(not isinstance(wg, str) or wg not in TDOC_WGS for wg in wgs)
            or len(wgs) != len(set(wgs)) or not isinstance(requested, dict)
            or set(requested) != set(wgs)):
        raise Refused('제한 회의·TDoc 구축은 RAN1~5의 WG와 각 회의 조건을 명시한다')
    if selected['specs'] != {} or selected['releases'] != [] or selected['mail'] is not None:
        raise Refused('회의·TDoc 전용 구축에는 규격·Release·메일 조건을 함께 지정하지 않는다')
    filters = scope.get('meeting_filters', {})
    if not isinstance(filters, dict) or set(filters) - set(wgs):
        raise Refused('회의 폴더 조건은 선택한 WG 안에서 지정한다')
    for wg in wgs:
        bounds = requested[wg]
        if bounds is not None and (not isinstance(bounds, list) or len(bounds) != 2
                or any(value is not None and (type(value) is not int or value < 0) for value in bounds)
                or (all(value is not None for value in bounds) and bounds[0] > bounds[1])):
            raise Refused(f'{wg}: 회의 범위 형식이 다르다')
        group = filters.get(wg, {})
        if not isinstance(group, dict) or set(group) - {'include', 'exclude'}:
            raise Refused(f'{wg}: 회의 폴더 조건은 include·exclude 목록을 사용한다')
        for values in group.values():
            if (not isinstance(values, list)
                    or any(not isinstance(name, str) or re.fullmatch(rf'TSGR{wg[-1]}_+\d+[A-Za-z0-9_-]*', name) is None
                           for name in values)
                    or len(values) != len(set(values))):
                raise Refused(f'{wg}: 회의 폴더 이름 또는 중복 조건을 확인한다')
        if set(group.get('include', [])) & set(group.get('exclude', [])):
            raise Refused(f'{wg}: 같은 회의 폴더를 포함·제외 조건에 함께 지정했다')
        if not group.get('include') and (bounds is None or any(value is None for value in bounds)):
            raise Refused(f'{wg}: 제한 회의·TDoc 구축은 양끝 회의 번호 또는 포함할 정확한 폴더를 지정한다')


def release_number(value: str | int) -> int:
    if type(value) is int:
        number = value
    elif isinstance(value, str) and re.fullmatch(r'Rel-[1-9][0-9]*', value):
        number = int(value[4:])
    else:
        raise Refused('Release는 정수 번호 또는 Rel-번호로 지정한다')
    if not 1 <= number <= 35:
        raise Refused('Release 번호는 원문 판 코드가 표현하는 1~35에서 지정한다')
    return number


def validate_selection(scope: dict, *, check_namespace: bool = True) -> dict:
    """실제로 연결된 제한 DAG의 입력만 수락한다. full 계약은 여기서 바꾸지 않는다."""
    if not is_bounded(scope):
        raise Refused('제한 구축의 build_mode는 bounded여야 한다')
    selected = scope.get('selection')
    if not isinstance(selected, dict) or set(selected) != SELECTION_KEYS:
        raise Refused('제한 자료 선택 계약의 필드가 다르다')
    kinds, specs, releases = (selected.get(key) for key in ('data_kinds', 'specs', 'releases'))
    if kinds == ['tdoc']:
        _validate_meeting_selection(scope, selected)
    elif kinds != ['TS'] or scope.get('wgs') != ['RAN1']:
        raise Refused('제한 구축은 RAN1 TS 또는 RAN1~5 회의·TDoc 전용 DAG를 선택한다')
    elif (not isinstance(specs, dict) or set(specs) != {'RAN1'}
            or not isinstance(specs['RAN1'], list) or not specs['RAN1']
            or any(not isinstance(number, str) or SPEC_RE.fullmatch(number) is None for number in specs['RAN1'])
            or specs['RAN1'] != sorted(set(specs['RAN1']))):
        raise Refused('제한 TS 구축은 선택한 WG의 서로 다른 규격 번호를 --spec WG:번호로 명시한다')
    if kinds == ['TS']:
        if (not isinstance(releases, list) or len(releases) != 1
                or type(releases[0]) is not int):
            raise Refused('현재 제한 TS 구축은 --release로 정확한 Release 한 개를 선택한다')
        release_number(releases[0])
        if selected['mail'] is not None:
            raise Refused('메일 기간 선택에는 메일 전용 제한 DAG가 필요하다')
        if scope.get('meeting_filters') or scope.get('requested') != {'RAN1': None}:
            raise Refused('TS 전용 제한 구축에는 회의 조건을 함께 지정하지 않는다')
    if scope.get('full') is not False:
        raise Refused('제한 구축을 전체 구축 상태로 기록하지 않는다')
    minimum = scope.get('company_min_tdocs', 10)
    if type(minimum) is not int or minimum < 1:
        raise Refused('Company 생성 기준은 양의 정수로 지정한다')
    if check_namespace and scope.get('namespace') != selection_digest(scope)[:16]:
        raise Refused('제한 구축 namespace와 선택 조건의 SHA가 다르다')
    return selected


def selection_digest(scope: dict) -> str:
    payload = {key: scope.get(key) for key in ('build_mode', 'wgs', 'requested', 'meeting_filters',
                                             'company_min_tdocs', 'selection')}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def selection_from_options(*, build_mode: str | None = None, data_kinds=(), specs=(),
                           releases=(), mail_from: str | None = None,
                           mail_until: str | None = None, previous: dict | None = None,
                           wgs: list[str], requested: dict, meeting_filters: dict | None = None,
                           company_min_tdocs: int = 10) -> dict:
    """설치·미리보기에서 같은 stdlib 선택 검사를 사용한다. 파일을 읽거나 쓰지 않는다.

    반환값은 기존 scope에 합칠 build_mode/selection/namespace 필드이다.
    규격의 초기 WG 매핑 검사는 호출자가 별도로 수행한다.
    """
    changed = any((data_kinds, specs, releases, mail_from, mail_until))
    mode = build_mode or (previous or {}).get('build_mode', 'full')
    if mode not in {'full', 'bounded'}:
        raise Refused('build_mode는 full 또는 bounded로 지정한다')
    if mode == 'full':
        # Legacy scopes retain their full DAG only when resuming the same contract.
        # A new WG/meeting selection must not silently opt into every other source.
        if build_mode is None and (
                previous is None or previous.get('wgs') != wgs
                or previous.get('requested') != requested
                or previous.get('meeting_filters', {}) != (meeting_filters or {})
                or previous.get('company_min_tdocs', 10) != company_min_tdocs):
            raise Refused(BUILD_MODE_REQUIRED_MESSAGE)
        if changed:
            raise Refused('--data-kind·--spec·--release·메일 기간은 --build-mode bounded와 함께 사용한다')
        return {'build_mode': 'full'} if build_mode or 'build_mode' in (previous or {}) else {}
    if not changed and is_bounded(previous):
        validate_selection(previous)
        selected = previous['selection']
    else:
        numbers: dict[str, list[str]] = {}
        for value in specs:
            wg, separator, number = value.partition(':')
            if not separator or wg not in wgs or SPEC_RE.fullmatch(number) is None:
                raise Refused(f'{value!r}: 선택한 WG의 규격 번호를 WG:번호로 지정한다')
            group = numbers.setdefault(wg, [])
            if number in group:
                raise Refused('같은 규격 선택을 두 번 지정했다')
            group.append(number)
        if len(releases) != len(set(releases)):
            raise Refused('같은 Release 선택을 두 번 지정했다')
        if len(data_kinds) != len(set(data_kinds)):
            raise Refused('같은 자료 종류를 두 번 지정했다')
        selected = {'data_kinds': sorted(data_kinds),
                    'specs': {wg: sorted(values) for wg, values in numbers.items()},
                    'releases': sorted(releases),
                    'mail': {'from': mail_from, 'until': mail_until} if mail_from or mail_until else None}
    candidate = {'build_mode': 'bounded', 'selection': selected, 'wgs': wgs,
                 'requested': requested, 'company_min_tdocs': company_min_tdocs, 'full': False}
    if meeting_filters:
        candidate['meeting_filters'] = meeting_filters
    validate_selection(candidate, check_namespace=False)
    return {'build_mode': 'bounded', 'selection': selected,
            'namespace': selection_digest(candidate)[:16]}


def load_contract(root: Path) -> dict | None:
    path = root / 'logs/common/bootstrap/scope.json'
    relative_file(root, path)
    if not path.exists():
        return None
    scope = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(scope, dict):
        raise Refused('scope.json은 JSON 객체여야 한다')
    mode = scope.get('build_mode', 'full')
    if mode not in {'full', 'bounded'}:
        raise Refused('저장된 build_mode를 확인하지 못했다')
    if mode == 'full':
        if scope.get('selection') is not None or scope.get('namespace') is not None:
            raise Refused('full 범위에 제한 구축 선택 조건이 섞여 있다')
        return None
    validate_selection(scope)
    return scope


def require_allowed_spec(scope: dict, wg: str, kind: str, spec: str, release: str | int) -> None:
    selected = validate_selection(scope)
    if (wg not in scope['wgs'] or kind not in selected['data_kinds']
            or spec not in selected['specs'].get(wg, [])
            or release_number(release) not in selected['releases']):
        raise Refused(f'선택 구축 범위 밖의 자료이다: {wg}/{kind}/{spec}/{release}')


def work_dir(root: Path, scope: dict, wg: str) -> Path:
    validate_selection(scope)
    if wg not in scope['wgs']:
        raise Refused('제한 구축 WG가 선택 범위 밖이다')
    path = root / 'logs/common/bootstrap/bounded' / scope['namespace'] / wg
    relative_file(root, path)
    return path


def validate_manifest(root: Path, scope: dict, path: Path) -> dict:
    """자료별 manifest 신원과 공통 파일 SHA 계약을 함께 검사한다."""
    validate_selection(scope)
    relative_file(root, path)
    document = json.loads(path.read_text(encoding='utf-8'))
    if (not isinstance(document, dict) or document.get('schema') != 1
            or document.get('scope_digest') != selection_digest(scope)
            or not isinstance(document.get('files'), dict) or not document['files']):
        raise Refused('제한 구축의 검증 입력 manifest 신원이 다르다')
    if is_tdoc_scope(scope):
        wg = document.get('wg')
        if not isinstance(wg, str) or wg not in scope['wgs'] or path.parent != work_dir(root, scope, wg):
            raise Refused('회의 manifest의 WG와 선택 namespace의 저장 위치가 다르다')
        if 'meetings' in document and document['meetings'] != scope.get('meetings', {}).get(wg):
            raise Refused('회의 manifest의 실제 폴더 목록과 고정 범위가 다르다')
    elif not isinstance(document.get('pairs'), list) or not document['pairs']:
        raise Refused('제한 구축의 검증 입력 manifest 신원이 다르다')
    paths = []
    for name, checksum in document['files'].items():
        if (not isinstance(name, str) or Path(name).is_absolute() or '..' in Path(name).parts
                or not isinstance(checksum, str) or re.fullmatch(r'[a-f0-9]{64}', checksum) is None):
            raise Refused('manifest는 저장소 상대경로와 SHA-256을 사용한다')
        paths.append(root / name)
    if file_manifest(root, paths) != document['files']:
        raise Refused('검증 입력 manifest 이후 원문 또는 본문 파일이 바뀌었다')
    if is_tdoc_scope(scope):
        return document
    expected = {(spec, f'Rel-{number}') for spec in scope['selection']['specs']['RAN1']
                for number in scope['selection']['releases']}
    seen = set()
    for row in document['pairs']:
        if not isinstance(row, dict) or (row.get('spec'), row.get('release')) in seen:
            raise Refused('manifest 규격·Release 신원이 비었거나 중복되었다')
        require_allowed_spec(scope, 'RAN1', 'TS', row.get('spec'), row.get('release'))
        seen.add((row['spec'], row['release']))
    if seen != expected:
        raise Refused('검증 입력 manifest의 규격·Release가 선택 조건과 다르다')
    return document
