"""Phase-3 TS 구조 적재기가 소유한 KG 부분을 입력과 같게 맞춘다.

적재기는 MERGE 만 하므로, 재파싱으로 사라진 절·표·그림과 거짓으로 해소됐던 참조 간선이
그래프에 그대로 남는다. 이 모듈은 적재 직전에 불러, 입력이 다루는 spec 의 구조 간선을 걷고
입력에 없는 노드를 지운다. 이어지는 적재가 입력대로 다시 세운다.

- 범위: 입력에 나오는 specNumber 의 release-키 Spec 에 매달린 Section, 그리고 ID 가 그 spec 의
  것인 Section·TSTable·TSFigure (`{spec}-Rel-NN-…`). 추상 허브 Spec 과 그 문서 간선은 건드리지 않는다.
- 소유 간선 타입은 적재기마다 다르므로 부르는 쪽이 넘긴다(자기가 MERGE 하는 타입만).
- 입력에 없는 Section 에 다른 생성 코드의 간선(Tdoc/CR→Section, Email ANCHORS, ConformanceTest
  definedInSection 등)이 붙어 있으면 그 노드는 그 생성 코드의 것이기도 하므로 지우지 않고 센다.
  소유 간선은 걷혔으므로 구조에서는 빠진다. 그 생성 코드를 다시 돌리면 간선이 옮겨 가고,
  이 적재기를 다시 돌리면 그때 지워진다.

LLM 호출: 없음
"""

from __future__ import annotations

NODE_LABELS = ("Section", "TSTable", "TSFigure")
_ID_KEY = {"Section": "sectionId", "TSTable": "tableId", "TSFigure": "figureId"}


def _spec_of(node_id: str) -> str:
    return node_id.split("-Rel-", 1)[0] if "-Rel-" in node_id else ""


def _batched(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def reconcile_structure(session, specs: set[str], desired: dict[str, set[str]],
                        owned_rel_types: list[str], dry_run: bool,
                        batch_size: int = 500) -> tuple[dict[str, int], dict[str, list[str]]]:
    """specs = 입력의 specNumber 집합, desired = {라벨: 입력의 ID 집합}.

    (지운 — dry_run 이면 지울 — 수, 남긴 노드의 ID 목록)을 돌려준다.
    """
    out: dict[str, int] = {}
    kept_ids: dict[str, list[str]] = {}
    scoped: dict[str, set[str]] = {}
    for label in NODE_LABELS:
        key = _ID_KEY[label]
        ids = {r["id"] for r in session.run(f"MATCH (n:{label}) RETURN n.{key} AS id")
               if r["id"] and _spec_of(r["id"]) in specs}
        if label == "Section":
            ids |= {r["id"] for r in session.run(
                "MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) "
                "WHERE sp.specRelease IS NOT NULL AND sp.specNumber IN $specs "
                "RETURN s.sectionId AS id", specs=sorted(specs))}
        scoped[label] = ids

    # 소유 간선: 범위 안 노드에 닿은 것은 방향과 상대를 가리지 않고 전부 걷는다.
    # 양 끝이 모두 범위 안인 간선은 두 노드에서 다 보이므로 ID 로 모아 한 번씩만 센다.
    rel_ids: set[str] = set()
    for label in NODE_LABELS:
        key = _ID_KEY[label]
        for batch in _batched(sorted(scoped[label]), batch_size):
            rel_ids |= {r["rid"] for r in session.run(
                f"UNWIND $ids AS nid MATCH (n:{label} {{{key}: nid}})-[r]-() "
                "WHERE type(r) IN $owned RETURN DISTINCT elementId(r) AS rid",
                ids=batch, owned=owned_rel_types)}
    if not dry_run:
        for batch in _batched(sorted(rel_ids), batch_size):
            session.run("UNWIND $ids AS rid MATCH ()-[r]->() WHERE elementId(r) = rid DELETE r",
                        ids=batch)
    out["소유 구조 간선 (걷고 다시 세움)"] = len(rel_ids)

    # 입력에 없는 노드.
    for label in NODE_LABELS:
        key = _ID_KEY[label]
        stale = sorted(scoped[label] - desired.get(label, set()))
        gone, kept = [], []
        for batch in _batched(stale, batch_size):
            for r in session.run(
                    f"UNWIND $ids AS nid MATCH (n:{label} {{{key}: nid}}) "
                    "OPTIONAL MATCH (n)-[x]-() WHERE NOT type(x) IN $owned "
                    "RETURN nid AS id, count(x) AS foreign",
                    ids=batch, owned=owned_rel_types):
                (kept if r["foreign"] else gone).append(r["id"])
        if gone and not dry_run:
            for batch in _batched(gone, batch_size):
                session.run(f"UNWIND $ids AS nid MATCH (n:{label} {{{key}: nid}}) DETACH DELETE n",
                            ids=batch)
        out[f"{label} (입력 밖)"] = len(gone)
        out[f"{label} kept (다른 생산자 간선)"] = len(kept)
        if kept:
            kept_ids[label] = kept
    return out, kept_ids


def _missing_section_snapshot(session, repairs):
    """Exact properties and incident edges of the small approved repair footprint."""
    import json
    nodes = {}
    for row in repairs:
        sec = row['section']
        keys = [('Section', 'sectionId', sec['sectionId']),
                ('Section', 'sectionId', sec['parentSectionId']),
                ('Section', 'sectionId', row['previousSectionId']),
                ('Spec', 'specNumber', row['specNumber'], row['release'])]
        keys += [('TSTable', 'tableId', t['tableId']) for t in row['tableMoves']]
        keys += [('Section', 'sectionId', sid) for sid in sec['references']]
        keys += [('Spec', 'specNumber', sn, None) for sn in sec['referencesSpec']]
        for key in keys:
            token = json.dumps(key)
            if token in nodes:
                continue
            label, prop, value, *release = key
            query = f'MATCH (n:{label} {{{prop}: $value}})'
            if release:
                query += ' WHERE n.specRelease IS NULL' if release[0] is None else ' WHERE n.specRelease = $release'
            found = [r.data() for r in session.run(
                query + ' RETURN elementId(n) AS eid, labels(n) AS labels, properties(n) AS properties',
                value=value, release=release[0] if release else None)]
            for item in found:
                item['labels'].sort()
            nodes[token] = found
    ids = sorted({n['eid'] for values in nodes.values() for n in values})
    edges = [r.data() for r in session.run(
        'MATCH (n)-[r]-(m) WHERE elementId(n) IN $ids '
        'RETURN DISTINCT elementId(r) AS eid, elementId(startNode(r)) AS start, '
        'elementId(endNode(r)) AS end, type(r) AS type, properties(r) AS properties', ids=ids)]
    return {'nodes': nodes, 'edges': sorted(edges, key=lambda x: x['eid'])}


def _missing_section_inputs(manifest_path):
    """Require parsed facts and accepted raw DOCX paragraphs, pinned by SHA256."""
    import hashlib
    import json
    from pathlib import Path
    import zipfile
    from xml.etree import ElementTree as ET
    import docx_text
    root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
    import sys
    sys.path.insert(0, str(root / 'scripts/common'))
    from common import review_artifacts
    manifest_path = Path(manifest_path).resolve()
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    repairs = manifest['repairs']
    if not repairs or len({r['section']['sectionId'] for r in repairs}) != len(repairs):
        raise ValueError('empty or duplicate missing-section repair')
    pins = {str(manifest_path): hashlib.sha256(manifest_bytes).hexdigest(),
            str(Path(__file__).resolve()): hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            str(Path(review_artifacts.__file__).resolve()): hashlib.sha256(Path(review_artifacts.__file__).read_bytes()).hexdigest()}
    for file_pin in manifest['artifactPins']:
        try:
            path = review_artifacts.resolve_recorded_path(root, file_pin['path'], file_pin['sha256'])
        except (OSError, ValueError) as error:
            raise ValueError(f'artifact generation changed: {file_pin["path"]}') from error
        pins[str(path)] = file_pin['sha256']
    for row in repairs:
        sec = row['section']
        if row['specNumber'] not in {'38.508-1', '38.508-2', '38.509', '38.521-1', '38.521-2',
                                     '38.521-3', '38.521-4', '38.523-1', '38.523-3', '38.533'}:
            raise ValueError('missing-section repair is limited to RAN5 conformance specifications')
        if str((root / row['parsedPath']).resolve()) not in pins:
            raise ValueError('canonical parsed input is not SHA-pinned')
        if (not sec['parentSectionId'] or sec['childSectionIds']
                or sec['isVoid'] or sec['sectionId'] != f'{row["specNumber"]}-{row["release"]}-{sec["sectionNumber"]}'):
            raise ValueError('repair supports only non-void leaf sections with an existing parent')
        parsed = json.loads((root / row['parsedPath']).read_text())
        matches = [s for s in parsed['sections'] if s['sectionId'] == sec['sectionId']]
        if matches != [sec]:
            raise ValueError('repair does not match canonical parsed section')
        previous = [s for s in parsed['sections'] if s['sectionId'] == row['previousSectionId']]
        if previous != [row['previousAfter']]:
            raise ValueError('previous section does not match canonical parsed projection')
        if (set(row['previousBefore']['references']) - set(row['previousAfter']['references']) != set(sec['references'])
                or set(row['previousAfter']['references']) - set(row['previousBefore']['references'])
                or not set(sec['referencesSpec']) <= set(row['previousBefore']['referencesSpec'])):
            raise ValueError('references must move from previous section or retain its explicit TS-only target')
        for move in row['tableMoves']:
            matches = [t for t in parsed['tables'] if t['tableId'] == move['tableId']]
            if len(matches) != 1 or matches[0]['sectionId'] != sec['sectionId']:
                raise ValueError('table repair does not match canonical parsed ownership')
        source = (root / row['sourcePath']).resolve()
        source.relative_to(root)
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != row['sourceSHA256']:
            raise ValueError('raw source generation changed')
        pins[str(source)] = actual
        with zipfile.ZipFile(source) as archive:
            xml = ET.fromstring(archive.read('word/document.xml'))
        paras = xml.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')
        quote = docx_text.final_text(paras[row['paragraphIndex']])
        if quote != row['sourceQuote'] or sec['sectionNumber'] + '\t' + sec['sectionTitle'] not in quote:
            raise ValueError('raw source paragraph/heading mismatch')
    return repairs, pins


def _missing_section_verify(before, after, repairs):
    """Permit new leaf nodes, exact structure edges, and source-backed ownership moves."""
    from collections import Counter
    import json
    def key(*parts):
        return json.dumps(parts)
    def node(snapshot, *parts):
        values = snapshot['nodes'][key(*parts)]
        if len(values) != 1:
            raise ValueError(f'expected one node: {parts}')
        return values[0]
    additions, deletions = Counter(), Counter()
    for row in repairs:
        sec = row['section']; sid = sec['sectionId']
        if before['nodes'][key('Section', 'sectionId', sid)]:
            raise ValueError('repair target already exists')
        fresh = node(after, 'Section', 'sectionId', sid)
        expected = {k: sec[k] for k in ('sectionId', 'sectionNumber', 'sectionTitle', 'level', 'isVoid')}
        expected.update(specNumber=row['specNumber'], granularity='section')
        if fresh['properties'] != expected or fresh['labels'] != ['ConformanceTest', 'Section']:
            raise ValueError('new section properties/labels differ from producer contract')
        parent = node(before, 'Section', 'sectionId', sec['parentSectionId'])
        spec = node(before, 'Spec', 'specNumber', row['specNumber'], row['release'])
        if expected['level'] != parent['properties']['level'] + 1:
            raise ValueError('new section hierarchy level differs from its parent')
        additions.update([(fresh['eid'], 'BELONGS_TO_SPEC', spec['eid']),
                          (fresh['eid'], 'PARENT_SECTION', parent['eid']),
                          (parent['eid'], 'HAS_SUB_SECTION', fresh['eid'])])
        previous = node(before, 'Section', 'sectionId', row['previousSectionId'])
        for sid in sec['references']:
            referred = node(before, 'Section', 'sectionId', sid)
            deletions.update([(previous['eid'], 'REFERENCES_SECTION', referred['eid']),
                              (referred['eid'], 'REFERENCED_BY_SECTION', previous['eid'])])
            additions.update([(fresh['eid'], 'REFERENCES_SECTION', referred['eid']),
                              (referred['eid'], 'REFERENCED_BY_SECTION', fresh['eid'])])
        for sn in sec['referencesSpec']:
            hub = node(before, 'Spec', 'specNumber', sn, None)
            additions.update([(fresh['eid'], 'REFERENCES_SPEC', hub['eid'])])
        for move in row['tableMoves']:
            table = node(before, 'TSTable', 'tableId', move['tableId'])
            previous = node(before, 'Section', 'sectionId', row['previousSectionId'])
            deletions.update([(previous['eid'], 'CONTAINS_TABLE', table['eid']),
                              (table['eid'], 'TABLE_IN_SECTION', previous['eid'])])
            additions.update([(fresh['eid'], 'CONTAINS_TABLE', table['eid']),
                              (table['eid'], 'TABLE_IN_SECTION', fresh['eid'])])
    for token, values in before['nodes'].items():
        if values and values != after['nodes'][token]:
            raise ValueError('existing node changed during missing-section repair')
    old = {e['eid']: e for e in before['edges']}; new = {e['eid']: e for e in after['edges']}
    removed, created = Counter(), Counter()
    for eid in old.keys() & new.keys():
        if old[eid] != new[eid]:
            raise ValueError('existing edge properties changed')
    for eid in old.keys() - new.keys():
        edge = old[eid]
        if edge['properties']:
            raise ValueError('table ownership edge has foreign properties')
        removed.update([(edge['start'], edge['type'], edge['end'])])
    for eid in new.keys() - old.keys():
        edge = new[eid]
        if edge['properties']:
            raise ValueError('unexpected new edge properties')
        created.update([(edge['start'], edge['type'], edge['end'])])
    if removed != deletions or created != additions:
        raise ValueError('graph delta exceeds approved missing-section repair')


def repair_missing_sections(session, manifest_path, receipt_path, *, expected_plan=None):
    """Plan by default; apply one source-pinned transaction against that exact plan.

    No broad reconcile, label pass, source mutation, or vector writes occur here.
    Existing nodes and all incident relationships are recorded in the plan.
    """
    import hashlib
    import json
    from pathlib import Path
    def publish(path, value):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    def recheck(pins):
        for path, digest in pins.items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
                raise ValueError('source/artifact changed after preflight')
    repairs, pins = _missing_section_inputs(manifest_path)
    before = _missing_section_snapshot(session, repairs)
    plan = {'status': 'planned', 'pins': pins, 'repairs': repairs, 'preimage': before}
    # Require all old footprint nodes and no target nodes before publishing a plan.
    targets = {json.dumps(('Section', 'sectionId', r['section']['sectionId'])) for r in repairs}
    for key, values in before['nodes'].items():
        if len(values) != (0 if key in targets else 1):
            raise ValueError('missing/duplicate existing node or non-missing repair target')
    if expected_plan is None:
        recheck(pins)
        publish(receipt_path, plan)
        return plan
    if json.loads(Path(expected_plan).read_text()) != plan:
        raise ValueError('source or graph differs from approved missing-section plan')
    tx = session.begin_transaction(timeout=180)
    try:
        if _missing_section_snapshot(tx, repairs) != before:
            raise ValueError('graph changed before missing-section transaction')
        recheck(pins)
        for row in repairs:
            sec = row['section']
            properties = {k: sec[k] for k in ('sectionId', 'sectionNumber', 'sectionTitle', 'level', 'isVoid')}
            properties.update(specNumber=row['specNumber'], granularity='section')
            tx.run('MATCH (p:Section {sectionId:$parent}), (sp:Spec {specNumber:$spec,specRelease:$release}) '
                   'CREATE (n:Section:ConformanceTest) SET n = $properties '
                   'CREATE (n)-[:BELONGS_TO_SPEC]->(sp), (n)-[:PARENT_SECTION]->(p), (p)-[:HAS_SUB_SECTION]->(n)',
                   parent=sec['parentSectionId'], spec=row['specNumber'], release=row['release'], properties=properties).consume()
            for sid in sec['references']:
                tx.run('MATCH (p:Section {sectionId:$previous})-[a:REFERENCES_SECTION]->(r:Section {sectionId:$referred}), '
                       '(r)-[b:REFERENCED_BY_SECTION]->(p), (n:Section {sectionId:$target}) '
                       'DELETE a,b CREATE (n)-[:REFERENCES_SECTION]->(r), (r)-[:REFERENCED_BY_SECTION]->(n)',
                       previous=row['previousSectionId'], referred=sid, target=sec['sectionId']).consume()
            for sn in sec['referencesSpec']:
                tx.run('MATCH (n:Section {sectionId:$target}), (sp:Spec {specNumber:$spec}) '
                       'WHERE sp.specRelease IS NULL CREATE (n)-[:REFERENCES_SPEC]->(sp)',
                       target=sec['sectionId'], spec=sn).consume()
            for move in row['tableMoves']:
                tx.run('MATCH (p:Section {sectionId:$previous})-[a:CONTAINS_TABLE]->(t:TSTable {tableId:$table}), '
                       '(t)-[b:TABLE_IN_SECTION]->(p), (n:Section {sectionId:$target}) '
                       'DELETE a,b CREATE (n)-[:CONTAINS_TABLE]->(t), (t)-[:TABLE_IN_SECTION]->(n)',
                       previous=row['previousSectionId'], table=move['tableId'], target=sec['sectionId']).consume()
        after = _missing_section_snapshot(tx, repairs)
        _missing_section_verify(before, after, repairs)
        recheck(pins)
        tx.commit()
    except BaseException:
        tx.rollback()
        raise
    finally:
        tx.close()
    observed = _missing_section_snapshot(session, repairs)
    _missing_section_verify(before, observed, repairs)
    receipt = dict(plan, status='committed', postimage=observed,
                   createdSections=len(repairs), movedTables=sum(len(r['tableMoves']) for r in repairs))
    publish(receipt_path, receipt)
    return receipt


if __name__ == '__main__':
    import argparse
    import sys
    from pathlib import Path
    root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
    sys.path.insert(0, str(root / 'scripts/common'))
    from common import credentials, axis
    from neo4j import GraphDatabase, READ_ACCESS
    parser = argparse.ArgumentParser(description='Source-pinned missing RAN5 leaf Section repair')
    parser.add_argument('--repair-missing-sections', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--expected-plan', type=Path)
    args = parser.parse_args()
    with GraphDatabase.driver(axis.bolt_uri('RAN5'), auth=credentials.neo4j_auth()) as driver:
        with driver.session(**({} if args.expected_plan else {'default_access_mode': READ_ACCESS})) as session:
            result = repair_missing_sections(session, args.repair_missing_sections, args.receipt,
                                             expected_plan=args.expected_plan)
    print(result['status'], 'sections=', len(result['repairs']))


def validate_ts_inputs(config, root) -> bool:
    """WG 전체의 Phase-3 구조·SHACL을 기존 KG 삭제 전에 검사합니다.

    RAN1~3은 생성된 JSON-LD와 파싱 통계를, RAN4/5는 직접 적재할 parsed
    JSON을 검사합니다. TS-1이 전체 WG를 재파싱하므로 검사 범위도 같습니다.
    """
    import subprocess
    import sys
    if config.wg_name in ("RAN1", "RAN2", "RAN3"):
        structure_validator = "validate_ts_jsonld.py"
    elif config.wg_name in ("RAN4", "RAN5"):
        structure_validator = "validate_release_integrity.py"
    else:
        raise ValueError("TS 구조 검사 대상은 RAN1~RAN5입니다")
    commands = [
        [sys.executable, str(config.phase_script(3, "ts-parser", structure_validator)),
         "--wg", config.wg_name],
        [sys.executable, str(root / "scripts/common/bootstrap/validate_formal_shacl.py"),
         "--wg", config.wg_name, "--phase", "3"],
    ]
    for command in commands:
        try:
            result = subprocess.run(command, cwd=str(root), capture_output=True, text=True, timeout=1800)
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"  ERROR: TS 적재 전 검사 실행 실패: {type(error).__name__}")
            return False
        if result.returncode != 0:
            print(f"  ERROR: TS 적재 전 검사 실패: {command[1]}\n{result.stdout[-1000:]}\n{result.stderr[-1000:]}")
            return False
    return True


def validate_direct_ts_inputs(config, root) -> bool:
    """RAN4/5의 직접 JSON 적재용 공개 검사 진입점을 유지합니다."""
    if config.wg_name not in ("RAN4", "RAN5"):
        raise ValueError("직접 TS 구조 검사 대상은 RAN4/RAN5입니다")
    return validate_ts_inputs(config, root)
