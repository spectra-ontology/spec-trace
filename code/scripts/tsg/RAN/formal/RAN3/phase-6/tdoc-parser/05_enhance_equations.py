#!/usr/bin/env python3
"""
Phase-6 OMML→LaTeX 수식 변환 Enhancement
기존 파싱 결과에 LaTeX 수식 추가

구현 계획: docs/tsg/RAN/formal/RAN3/phase-6/

사용법:
    python 05_enhance_equations.py --workers 4 --resume
    python 05_enhance_equations.py --meeting RAN3#123-bis --limit 10
"""

import json
import logging
import os
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
import time
from xml.etree import ElementTree as ET
from lxml import etree

sys.path.insert(0, str(Path(__file__).parent))
from parse_tdoc_lib import meeting_id_to_folder, DEFAULT_WG, _equation_infos, tdoc_dir_for, tdoc_documents, bundle_equation_sites
import docx_text  # noqa: E402  문단 글 읽기 규칙의 정본. 경로는 parse_tdoc_lib 가 건다
import pool_run  # noqa: E402  워커가 죽어도 문서를 잃지 않는 RAN 공용 풀. 경로는 parse_tdoc_lib 가 건다
import tdoc_copy_owner  # noqa: E402  03 이 제 문서를 되찾아 읽은 번호의 기록. 경로는 parse_tdoc_lib 가 건다
import tdoc_selection  # noqa: E402

# docx 모듈은 워커에서 import


# =============================================================================
# 설정
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[7]
LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal"

# 풀 하나가 맡는 문서 수. 묶음 끝에서는 가장 느린 문서를 기다리므로 너무 작으면 그 기다림이 잦고,
# 너무 크면 풀이 깨졌을 때 줄어든 워커로 도는 몫이 커진다. Phase-4 CR 파서의 묶음 크기와 같게 둔다.
POOL_SLICE = 2000
log = logging.getLogger(__name__)

def get_data_base(wg: str) -> Path:
    return PROJECT_ROOT / "data" / "corpus" / "tsg" / "RAN" / "formal" / "meetings" / wg / "derived"

def get_parsed_base(wg: str) -> Path:
    return PROJECT_ROOT / "vectordb" / "parsed" / "tdocs" / wg

# OMML 네임스페이스
OMML_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
NSMAP = {'m': OMML_NS}


@dataclass
class EquationInfo:
    """수식 정보"""
    equationId: str
    index: int
    latex: str
    mathml: str
    context: str
    paragraph_index: int
    source: str = "omml"  # "omml" = OMML 수식 · "ole" = 수식 개체(`w:object`) — parse_tdoc_lib.EquationInfo 와 같다
    text: str = ""  # 청크 본문이 수식 자리에 넣는 선형 글


# =============================================================================
# Meeting ID 매핑 — parse_tdoc_lib.meeting_id_to_folder() 사용
# =============================================================================

def get_source_docs(meeting_id: str, tdoc_number: str, data_base: Path = None, wg: str = DEFAULT_WG,
                    parsed_dir: Path = None) -> list[Path]:
    """본문과 함께 읽는 표지의 경로 목록을 반환한다. TDoc 폴더가 없으면 빈 목록이다."""
    if data_base is None:
        data_base = get_data_base(wg)
    folder_name = meeting_id_to_folder(meeting_id, wg, base_dir=data_base)
    # 번호→폴더와 폴더→문서 둘 다 파싱(03)과 같은 규칙이어야 같은 문서를 보강한다.
    tdoc_dir = tdoc_dir_for(data_base / folder_name / "Docs", tdoc_number)
    if not tdoc_dir:
        return []
    # 03이 기본 후보 대신 해당 TDoc의 본문을 선택했다면 산출 폴더에 기록한 경로를 사용한다.
    # 수식 보강에서도 03과 같은 문서를 읽어야 한다.
    if parsed_dir is not None:
        recorded = tdoc_copy_owner.recorded_documents(parsed_dir, tdoc_dir)
        if recorded is not None:
            return recorded
    return tdoc_documents(tdoc_dir)


# =============================================================================
# OMML → LaTeX 변환
# =============================================================================

def omml_to_latex_simple(omml_element) -> str:
    """
    평평한 기호열만 LaTeX로 변환한다. 구조 수식은 원문 OMML을 보존하고 빈 LaTeX를 반환한다.
    """
    try:
        # m:t는 문단과 같은 문자 변환 규칙으로 읽어 기호 글꼴 문자를 실제 표시 문자로 변환한다.
        flat_tags = {"oMath", "oMathPara", "r", "t", "rPr", "sty", "scr", "nor", "ctrlPr"}
        if any(node.tag.rsplit("}", 1)[-1] not in flat_tags for node in omml_element.iter()):
            return ""
        raw_text = docx_text.math_text(omml_element)
        if any(ch in raw_text for ch in "\\{}_^$%&#"):
            return ""
        if not raw_text:
            return ""

        # 간단한 LaTeX 변환 규칙
        latex = raw_text

        # 그리스 문자 변환
        greek_map = {
            'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta',
            'ε': r'\epsilon', 'ζ': r'\zeta', 'η': r'\eta', 'θ': r'\theta',
            'λ': r'\lambda', 'μ': r'\mu', 'π': r'\pi', 'ρ': r'\rho',
            'σ': r'\sigma', 'τ': r'\tau', 'φ': r'\phi', 'ω': r'\omega',
            'Σ': r'\Sigma', 'Π': r'\Pi', 'Ω': r'\Omega', 'Δ': r'\Delta',
        }
        for char, latex_cmd in greek_map.items():
            latex = latex.replace(char, latex_cmd + ' ')

        # 수학 기호 변환
        symbol_map = {
            '×': r'\times', '÷': r'\div', '±': r'\pm', '≤': r'\leq',
            '≥': r'\geq', '≠': r'\neq', '∞': r'\infty', '∑': r'\sum',
            '∏': r'\prod', '∫': r'\int', '√': r'\sqrt', '∂': r'\partial',
        }
        for char, latex_cmd in symbol_map.items():
            latex = latex.replace(char, latex_cmd + ' ')

        # 첨자·분수 등은 위 구조 검사에서 별도로 보존한다.

        return latex.strip()

    except Exception:
        return ""


def omml_to_mathml(omml_element) -> str:
    """OMML 원문을 MathML 이름공간 래퍼에 보존한다(XSLT 변환 전)."""
    # 설계 결정: Microsoft OMML2MML.xsl 미적용 — 기본 MathML 래퍼 사용
    # 현재는 간단한 래핑만 수행
    try:
        # 문서를 zipfile 로 읽은 경로(XML 손상 문서)의 수식은 ElementTree 요소다 — lxml 로 쓰면 예외로 빈 글이 된다.
        if isinstance(omml_element, etree._Element):
            omml_str = etree.tostring(omml_element, encoding='unicode')
        else:
            omml_str = ET.tostring(omml_element, encoding='unicode')
        # 기본 MathML 래퍼
        return f"<math xmlns='http://www.w3.org/1998/Math/MathML'>{omml_str}</math>"
    except Exception:
        return ""


def extract_equations_enhanced(docx_paths: list[Path], tdoc_number: str = "") -> list[EquationInfo]:
    """문서 묶음(`tdoc_documents`)의 수식 목록에 LaTeX · MathML 을 더한다.

    목록은 파서(03)가 equations.json 에 쓰는 것과 같다 — 같은 규칙(`bundle_equation_sites` — 묶음 문서마다 `TdocParser.document_equation_sites`)으로 같은
    차례 · equationId · 종류(source) · 선형 글(text) · 주변 글(context)을 얻는다. LaTeX · MathML 은 OMML 수식에만
    만든다. 수식 개체(source "ole")는 OMML 이 없어 둘 다 빈 글이다.
    문서를 읽지 못하면 예외를 그대로 올린다 — 빈 목록을 돌려주면 부르는 쪽이 03 의 목록을 빈 목록으로 덮어쓴다.
    """
    sites = bundle_equation_sites(docx_paths, tdoc_number)
    equations = []
    for info, (eq, _owner, at, kind) in zip(_equation_infos(tdoc_number, sites), sites):
        omml = kind == "omml"
        equations.append(EquationInfo(
            equationId=info.equationId,
            index=info.index,
            latex=omml_to_latex_simple(eq) if omml else "",
            mathml=omml_to_mathml(eq) if omml else "",
            context=info.context,
            paragraph_index=at,  # 결합한 문서의 문단 인덱스(03의 start_idx 기준), 표 내부이면 -1
            source=kind,
            text=info.text,
        ))
    return equations


def enhance_single_tdoc(args: tuple) -> dict:
    """단일 Tdoc 수식 Enhancement"""
    parsed_dir, meeting_id, tdoc_number, data_base, wg = args

    try:
        # 원본 DOCX 찾기
        docx_paths = get_source_docs(meeting_id, tdoc_number, data_base, wg, parsed_dir)
        if not docx_paths:
            return {
                'status': 'error',
                'tdocNumber': tdoc_number,
                'reason': 'no_source_docx'
            }

        # 수식 추출 및 변환 (Spec §3.6: equationId 포함). 문서를 읽지 못하면 예외가 올라와 아래 except 가
        # 오류로 돌려준다 — 03 이 쓴 equations.json 은 그대로 둔다.
        equations = extract_equations_enhanced(docx_paths, tdoc_number)

        # equations.json 저장 (기존 파일 덮어쓰기)
        eq_file = parsed_dir / 'equations.json'

        # JSON 전체를 임시 파일에 쓴 다음 equations.json 경로를 교체한다.
        tmp = eq_file.with_name(eq_file.name + '.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump({
                'tdocNumber': tdoc_number,
                'meetingId': meeting_id,
                'enhanced': True,
                'equations': [asdict(eq) for eq in equations],
                'total_count': len(equations),
                'omml_count': sum(1 for eq in equations if eq.source == "omml"),
                'ole_count': sum(1 for eq in equations if eq.source == "ole"),
                'with_latex': sum(1 for eq in equations if eq.latex)
            }, f, indent=2, ensure_ascii=False)
        os.replace(tmp, eq_file)

        return {
            'status': 'success',
            'tdocNumber': tdoc_number,
            'meetingId': meeting_id,
            'equation_count': len(equations),
            'ole_count': sum(1 for eq in equations if eq.source == "ole"),
            'with_latex': sum(1 for eq in equations if eq.latex)
        }

    except Exception as e:
        return {
            'status': 'error',
            'tdocNumber': tdoc_number,
            'error': str(e)
        }


# =============================================================================
# 메인 로직
# =============================================================================

def collect_tasks(parsed_base: Path, data_base: Path, wg: str = DEFAULT_WG,
                   meeting_filter: str = None, resume: bool = False, tdoc_filter: str | None = None) -> list[tuple]:
    """Enhancement 대상 수집"""
    selected = tdoc_selection.parsed_target(parsed_base, wg, meeting_filter, tdoc_filter)
    tasks = []
    skipped = 0

    for meeting_dir in sorted(parsed_base.iterdir()):
        if not meeting_dir.is_dir() or not meeting_dir.name.startswith(f"{wg}#"):
            continue

        meeting_id = meeting_dir.name

        if meeting_filter and meeting_id != meeting_filter:
            continue

        for tdoc_dir in sorted(meeting_dir.iterdir()):
            if not tdoc_dir.is_dir():
                continue

            tdoc_number = tdoc_dir.name
            if selected is not None and tdoc_number != selected:
                continue

            # Resume 모드: enhanced=true인 파일 건너뛰기
            if resume:
                eq_file = tdoc_dir / 'equations.json'
                if eq_file.exists():
                    try:
                        with open(eq_file) as f:
                            data = json.load(f)
                        if data.get('enhanced'):
                            skipped += 1
                            continue
                    except json.JSONDecodeError:
                        pass

            tasks.append((tdoc_dir, meeting_id, tdoc_number, data_base, wg))

    return tasks, skipped


def main():
    parser = argparse.ArgumentParser(description="Phase-6 OMML→LaTeX 수식 변환")
    parser.add_argument("--workers", type=int, default=4, help="병렬 워커 수")
    parser.add_argument("--resume", action="store_true", help="이미 처리된 문서 건너뛰기")
    parser.add_argument("--meeting", type=str, help="특정 회의만 처리")
    parser.add_argument("--limit", type=int, default=0, help="처리할 최대 문서 수")
    parser.add_argument(
        "--wg",
        type=str,
        default=DEFAULT_WG,
        choices=[DEFAULT_WG],
        help=f"Working Group (기본: {DEFAULT_WG})"
    )

    tdoc_selection.add_argument(parser)
    args = parser.parse_args()
    tdoc_selection.validate_arguments(parser, args, wg=DEFAULT_WG)
    if args.workers < 1:
        parser.error("--workers는 1 이상의 정수여야 합니다")
    if args.limit < 0:
        parser.error("--limit는 0 이상의 정수여야 합니다")

    DATA_BASE = get_data_base(args.wg)
    PARSED_BASE = get_parsed_base(args.wg)

    print("=" * 70)
    print(f"Phase-6 OMML→LaTeX 수식 변환 Enhancement (WG: {args.wg})")
    print("=" * 70)
    print(f"워커: {args.workers}")
    print(f"Resume: {args.resume}")
    if args.meeting:
        print(f"회의 필터: {args.meeting}")
    print("=" * 70)

    # 작업 수집
    print("\n[작업 수집]")
    tasks, skipped = tdoc_selection.collect_or_error(parser, collect_tasks, PARSED_BASE, DATA_BASE, wg=args.wg, meeting_filter=args.meeting, resume=args.resume, tdoc_filter=args.tdoc)

    print(f"처리 대상: {len(tasks)}")
    if skipped > 0:
        print(f"건너뛴 문서: {skipped}")

    if args.limit > 0:
        tasks = tasks[:args.limit]
        print(f"제한 적용: {len(tasks)} 문서만 처리")

    if not tasks:
        print("처리할 문서가 없습니다.")
        return

    # 병렬 처리
    print("\n[수식 변환 시작]")
    start_time = time.time()

    results = []
    errors = []

    completed = 0
    total_equations = 0
    total_with_latex = 0

    # 묶음마다 새 풀을 띄워 RAN 공용 풀(pool_run)로 돈다 — 워커가 죽어도(메모리 상한 등) 끝나지 못한
    # 문서를 워커를 줄여 다시 돌리고, 문서마다 순환 GC 를 돌려 python-docx · lxml 트리가 워커에 쌓이지 않게 한다.
    for i in range(0, len(tasks), POOL_SLICE):
        for result in pool_run.run_all(enhance_single_tdoc, [(t,) for t in tasks[i:i + POOL_SLICE]],
                                       args.workers, log):
            completed += 1

            if result['status'] == 'success':
                results.append(result)
                total_equations += result.get('equation_count', 0)
                total_with_latex += result.get('with_latex', 0)
            elif result['status'] == 'error':
                errors.append(result)

            if completed % 100 == 0 or completed == len(tasks):
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                latex_pct = total_with_latex / total_equations * 100 if total_equations > 0 else 0
                print(f"  진행: {completed}/{len(tasks)} ({completed*100/len(tasks):.1f}%) "
                      f"| 속도: {rate:.1f} docs/s | 수식: {total_equations} | LaTeX: {latex_pct:.1f}%")

    elapsed = time.time() - start_time

    # 결과 요약
    print("\n" + "=" * 70)
    print("결과 요약")
    print("=" * 70)
    print(f"총 처리: {len(tasks)}")
    print(f"성공: {len(results)}")
    print(f"오류: {len(errors)}")
    print(f"소요 시간: {elapsed:.1f}초")

    if results:
        total_equations = sum(r.get('equation_count', 0) for r in results)
        total_with_latex = sum(r.get('with_latex', 0) for r in results)
        docs_with_equations = sum(1 for r in results if r.get('equation_count', 0) > 0)
        latex_pct = total_with_latex / total_equations * 100 if total_equations > 0 else 0

        print("\n[수식 통계]")
        print(f"  수식 포함 문서: {docs_with_equations}")
        print(f"  총 수식: {total_equations}")
        print(f"  LaTeX 변환 성공: {total_with_latex} ({latex_pct:.1f}%)")

    if errors:
        print("\n[오류 목록 (처음 5개)]")
        for err in errors[:5]:
            print(f"  {err['tdocNumber']}: {err.get('error', 'unknown')[:60]}")

    # 리포트 저장
    log_dir = LOG_DIR / args.wg / "phase-6"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_path = log_dir / f"enhance_equations_{timestamp}.json"

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'summary': {
                'total': len(tasks),
                'success': len(results),
                'errors': len(errors),
                'elapsed_seconds': elapsed
            },
            'stats': {
                'total_equations': sum(r.get('equation_count', 0) for r in results),
                'with_latex': sum(r.get('with_latex', 0) for r in results),
                'docs_with_equations': sum(1 for r in results if r.get('equation_count', 0) > 0)
            },
            'errors': errors  # 누락 문서를 식별할 수 있도록 전체 실패 목록을 보존한다.
        }, f, indent=2, ensure_ascii=False)

    print(f"\n리포트 저장: {report_path}")

    # 오류가 하나라도 있으면 종료 코드 1 — 파이프라인(set -e · pipefail)이 이 단계를 실패로 받는다.
    # 원본 문서를 읽지 못한 문서(부품 부재 · 손상)는 워커가 오류로 돌려주므로 여기서 실패가 된다.
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
