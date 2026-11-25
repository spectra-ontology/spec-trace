#!/usr/bin/env python3
"""build_decision_dispositions.py — 모든 parsed 결정의 대상별 원문 처분을 산출한다.

Spec: docs/tsg/build/standards/decision_disposition_contract.md.
Ontology: DecisionDisposition preserves ambiguous targets and qualified approval evidence.
Cycle: five-WG parsed reports + accepted DOCX → JSON-LD and complete coverage ledger.
배경: REFERENCES를 보존하면서 승인 질문을 원문 대상별 처분으로 계산한다.
사용: python3 build_decision_dispositions.py --wg RAN1 --out /tmp/dispositions.
LLM 호출: 없음. 원문 기반 판독 규칙은 decision_disposition.py에 있다.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from decision_disposition import ROOT, write_dispositions, coverage_for_wg
from common.atomic_io import write_text_atomic


def build(wg, out):
    directory = ROOT / f'ontology/output/tsg/RAN/formal/parsed_reports/{wg}'
    paths = sorted(p for p in directory.glob('*.json') if not p.name.startswith('_'))
    reports = [json.loads(p.read_text()) for p in paths]
    reports = [r for r in reports if r.get('meeting_id') and r.get('docx_path')]
    result = write_dispositions(reports, out, ROOT)
    rows = json.loads((out / 'decision_dispositions.jsonld').read_text())['@graph']
    result.update(coverage_for_wg(wg, rows))
    result['sourceFiles'] = [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
    write_text_atomic(out / 'decision_disposition_coverage.json', json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('pending', 'sourceFiles')}, ensure_ascii=False), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wg', choices=[f'RAN{x}' for x in range(1, 6)], required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.wg, args.out)


if __name__ == '__main__':
    main()
