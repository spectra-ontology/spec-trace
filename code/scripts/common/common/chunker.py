#!/usr/bin/env python3
"""5 WG 공통 chunker 라이브러리 (Phase-7 P7-V06~V12 정책 적용).

기존 5 WG 별도 chunker (`scripts/tsg/RAN/formal/RAN{1-5}/phase-7/ts-parser/01_parse_ts_sections.py`)에
중복된 split_giant_section 로직을 통합. paragraph 단위 split만 수행하던 결함을
hard_max 강제 + 거대 paragraph 행/문자 split으로 보강.

Spec 근거:
- [P7-V06] SPLIT_THRESHOLD = 10,000 토큰 (paragraph 단위 split 트리거)
- [P7-V07] SPLIT_TARGET = 2,000 토큰 (분할 목표)
- [P7-V08] SPLIT_OVERLAP = 100 토큰
- [P7-V11] HARD_MAX = 6,500 토큰 (임베딩 8,192 한계 - 안전 마진)
- [P7-V12] EMBEDDING_MODEL = 임베딩 인코더의 것을 그대로 쓴다 (`embedding_registry` 가 선언)

사용법 (5 WG 공통):
    sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "common"))
    from common.chunker import split_giant_section_v2

    chunks = split_giant_section_v2(paragraphs)
    # 또는 기존 정책 호환 (paragraph 단위만):
    chunks = split_giant_section_v2(paragraphs, hard_max=None)

발견 경로 (재발 방지):
    docs/tsg/build/standards/chunking_standards.md  (HARD_MAX 6,500 토큰 정책)
    docs/tsg/build/standards/reembedding_policy.md  (선별 재처리 Step 0)
"""

from __future__ import annotations

import json
from pathlib import Path

from .atomic_io import write_json_atomic
from .embedding_registry import ENCODERS
from .script_markup import ScriptMarkup

# ===========================================================================
# Spec P7-V06~V12 정책 상수
# ===========================================================================

# 기본 BGE-M3 경로의 토큰 수와 한도는 같은 인코더 선언에서 가져온다.
# 다른 토크나이저로 측정한 길이는 실제 임베딩 입력의 길이와 다를 수 있다.
_ENCODER = ENCODERS["bge-m3"]
EMBEDDING_MODEL = _ENCODER.model
EMBEDDING_MAX_TOKENS = _ENCODER.max_tokens
HARD_MAX_DEFAULT = 6_500  # 안전 마진 (8,192 의 ~80%). 정본 = docs/tsg/build/standards/chunking_standards.md
SPLIT_THRESHOLD = 10_000
SPLIT_TARGET = 2_000
SPLIT_OVERLAP = 100

# 토크나이저는 처음 토큰 수를 측정할 때 로컬 파일에서만 읽는다.
# 이 모듈을 import하는 것만으로 파일 다운로드나 모델 로딩을 시작하지 않는다.
_TOKENIZER = None
_TOKENIZER_ERR: Exception | None = None


def _tokenizer():
    """기본 인코더의 로컬 토크나이저를 반환하고, 로딩 실패 원인을 보관한다."""
    global _TOKENIZER, _TOKENIZER_ERR
    if _TOKENIZER is None and _TOKENIZER_ERR is None:
        try:
            from .embedding_registry import load_local_tokenizer

            _TOKENIZER = load_local_tokenizer(_ENCODER)
        except Exception as e:  # 토크나이저 파일 또는 transformers 등의 의존성 부재
            _TOKENIZER_ERR = e
    return _TOKENIZER


class TokenizerUnavailable(RuntimeError):
    """실제 토큰 수를 측정해야 하는 호출에서 토크나이저를 사용할 수 없다."""


def count_tokens(text: str, *, estimate_ok: bool = False) -> int:
    """임베딩 인코더(`EMBEDDING_MODEL`)의 토크나이저로 센 토큰 수.

    기본 호출은 토크나이저 로딩·인코딩 실패 시 TokenizerUnavailable을 발생시킨다.
    토큰 한도 검사에 문자 수의 추정값이 사용되는 것을 막기 위한 조건이다.
    대략적인 분포 보고처럼 추정값을 허용하는 호출만 estimate_ok=True를 지정한다.
    이 경우 실제 측정에 실패하면 문자 수를 2로 나눈 정수 추정값을 반환한다.
    """
    if not text:
        return 0
    tok = _tokenizer()
    if tok is not None:
        try:
            return len(tok(text, add_special_tokens=False)["input_ids"])
        except Exception as e:
            if not estimate_ok:
                raise TokenizerUnavailable(f"{EMBEDDING_MODEL} 인코딩 실패: {e}") from e
    elif not estimate_ok:
        raise TokenizerUnavailable(
            f"{EMBEDDING_MODEL} 토크나이저를 열지 못했다 — 토큰을 셀 수 없다"
            f" ({_TOKENIZER_ERR}). 어림으로 대신하려면 estimate_ok=True 를 명시하라"
            "(그 값은 토큰 수가 아니다)."
        )
    # 보고용 추정값이며, 실제 토큰 수나 한도 준수의 근거로 사용하지 않는다.
    return len(text) // 2


# ===========================================================================
# chunks.json의 지원 형식을 공통으로 정의한다.
# ===========================================================================

BODY_FIELDS = ("text", "content")


class ChunkShapeError(ValueError):
    """청크 파일 또는 본문 필드가 지원 형식과 다르다."""


def chunk_list(doc, where: str) -> list:
    """청크 목록을 꺼낸다. 최상위가 리스트인 파일과 `chunks` 를 가진 사전이 섞여 있다.

    지원하지 않는 형식에는 ChunkShapeError를 발생시킨다. 잘못된 입력을
    청크가 없는 정상 입력으로 집계하지 않도록 빈 목록으로 대체하지 않는다.
    """
    if isinstance(doc, list):
        return doc
    if isinstance(doc, dict) and isinstance(doc.get("chunks"), list):
        return doc["chunks"]
    raise ChunkShapeError(f"모르는 chunks.json 모양 — {where} ({type(doc).__name__})")


def chunk_body(chunk: dict, where: str) -> str:
    """본문을 꺼낸다. 본문 칸의 이름이 트리마다 다르다(`text` · `content`).

    본문 필드가 없으면 ChunkShapeError를 발생시킨다. 지원 필드가 존재하고
    값이 null 또는 빈 문자열이면 빈 본문으로 반환한다.
    """
    try:
        key = body_key(chunk)
    except ChunkShapeError as exc:
        raise ChunkShapeError(f"{exc} — {where}") from exc
    return (chunk.get(key) or "").strip()


def body_key(chunk: dict, text_keys: tuple[str, ...] = BODY_FIELDS) -> str:
    """비어 있지 않은 본문 필드를 우선 선택하고, 재작성 시 같은 키를 사용한다."""
    if not isinstance(chunk, dict):
        raise ChunkShapeError("청크는 사전이어야 합니다")
    if not text_keys:
        raise ChunkShapeError("본문 키 후보가 없습니다")
    present = [key for key in text_keys if key in chunk]
    if not present:
        raise ChunkShapeError("본문 칸(text | content)이 없습니다")
    if any(chunk[key] is not None and not isinstance(chunk[key], str) for key in present):
        raise ChunkShapeError("본문 칸은 문자열 또는 null이어야 합니다")
    return next((key for key in present if (chunk[key] or "").strip()), present[0])


def read_chunk_file(path) -> tuple[object, list]:
    """(원본 문서, 청크 목록) 을 돌려준다. 목록은 사전 모양일 때 문서 안의 그 객체다."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
        doc = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ChunkShapeError(f"못 읽음 {path}: {e}") from e
    return doc, chunk_list(doc, str(path))


def write_chunk_file(path, doc, chunks: list) -> None:
    """읽을 때의 모양을 보존하고, 완전히 쓴 임시 파일로 교체합니다."""
    path = Path(path)
    if isinstance(doc, list):
        out = chunks
    else:
        out = dict(doc, chunks=chunks)
    write_json_atomic(path, out)
    if isinstance(doc, dict):
        doc["chunks"] = chunks


# ===========================================================================
# 거대 paragraph 처리 (P7-V11)
# ===========================================================================

def is_table_text(text: str) -> bool:
    """파이프(|) 구분자가 다수 있고 행 비율이 높으면 표로 판별."""
    pipe_count = text.count("|")
    line_count = text.count("\n") + 1
    return (pipe_count > 50) and (pipe_count / max(1, line_count) > 2)


def split_huge_paragraph_by_rows(
    text: str, target_tokens: int = SPLIT_TARGET
) -> list[str]:
    """표 텍스트를 행(row) 단위 split. 첫 줄(헤더) 보존하여 각 chunk에 포함.

    예: 38.306 §4.2.7.2 BandNR parameters (100K 토큰 표) → 각 capability 행 단위.
    """
    if target_tokens < 1:
        raise ValueError("target_tokens must be positive")
    source = ScriptMarkup(text)
    # Each later range owns its original preceding newline. A generated role
    # can cross a newline, so splitting and parsing individual lines loses it.
    ends, cursor = [], 0
    for line in text.split("\n"):
        cursor += len(line)
        ends.append(cursor)
        cursor += 1
    header = source.slice(0, ends[0])
    chunks: list[str] = []
    start, end, current_lines = 0, ends[0], 1
    for next_end in ends[1:]:
        candidate = (header if start else "") + source.slice(start, next_end)
        if count_tokens(candidate) > target_tokens and current_lines > 1:
            chunks.append((header if start else "") + source.slice(start, end))
            start = end
            current_lines = 2  # repeated header plus the current source row
        else:
            current_lines += 1
        end = next_end
    chunks.append((header if start else "") + source.slice(start, end))
    return chunks


def split_huge_paragraph_by_chars(
    text: str,
    target_tokens: int = SPLIT_TARGET,
    overlap_tokens: int = SPLIT_OVERLAP,
) -> list[str]:
    """비표 텍스트를 문자 단위 sliding window split.

    예: 38.331 §5.x 거대 절차 본문 (한 문단이 수만자) → 일정 크기 윈도우.
    """
    if target_tokens < 1 or overlap_tokens < 0:
        raise ValueError("target_tokens must be positive and overlap nonnegative")
    source = ScriptMarkup(text)
    target_chars = target_tokens * 4
    overlap_chars = overlap_tokens * 4
    step = max(1, target_chars - overlap_chars)

    chunks: list[str] = []
    pos = 0
    while pos < len(text):
        candidate = source.slice(pos, pos + target_chars)
        if candidate:
            chunks.append(candidate)
        pos += step
    return chunks


def split_huge_paragraph(text: str, target_tokens: int = SPLIT_TARGET) -> list[str]:
    """긴 문단을 분할한다. 표는 행 단위로, 일반 문단은 문자 단위로 나눈다."""
    if is_table_text(text):
        return split_huge_paragraph_by_rows(text, target_tokens)
    return split_huge_paragraph_by_chars(text, target_tokens, SPLIT_OVERLAP)


def _fit_raw_slice(source: ScriptMarkup, start: int, end: int, budget: int):
    """Shrink raw offsets, measuring the independently balanced presentation."""
    candidate = source.slice(start, end)
    while count_tokens(candidate) > budget:
        if end - start <= 1:
            raise ValueError("한 문자의 토큰 수와 첨자 표시가 요청한 상한을 넘습니다")
        end = start + max(1, int((end - start) * 0.85))
        candidate = source.slice(start, end)
    return end, candidate


def _force_split_by_chars(
    text: str, hard_max: int = HARD_MAX_DEFAULT, safety_buffer: int = 200
) -> list[str]:
    """행·문자 분할 뒤에도 한도를 넘는 본문을 실제 토큰 수에 맞춰 재분할한다.

    문자 수로 초기 구간을 잡고 토크나이저로 측정해 구간을 조정한다.
    문장의 의미 경계보다 hard_max를 우선하며, 생성한 첨자 표시도 측정에 포함한다.
    """
    if hard_max < 1 or safety_buffer < 0:
        raise ValueError("hard_max must be positive and safety_buffer nonnegative")
    if count_tokens(text) <= hard_max:
        return [text]

    source = ScriptMarkup(text)
    target_tokens = hard_max - min(safety_buffer, hard_max // 4)
    chunks: list[str] = []
    pos = 0
    text_len = len(text)
    while pos < text_len:
        # 초기 추정: chars/token = 3
        estimate_chars = target_tokens * 3
        end = min(pos + estimate_chars, text_len)
        try:
            end, candidate = _fit_raw_slice(source, pos, end, target_tokens)
        except ValueError:
            # The safety margin is a target; a source character plus its role
            # wrappers may still fit the actual hard bound for tiny budgets.
            end, candidate = _fit_raw_slice(source, pos, end, hard_max)
        # Added closing/reopening markers participate in every measurement.
        while end < text_len:
            next_end = min(text_len, end + 200)
            expanded = source.slice(pos, next_end)
            if count_tokens(expanded) > target_tokens:
                break
            end, candidate = next_end, expanded
        if candidate:
            chunks.append(candidate)
        # Rendered wrappers change string length; source progress uses raw end.
        pos = end
    return chunks or [""]


# ===========================================================================
# 메인 chunker (5 WG 공통) — paragraph 단위 + hard_max 강제
# ===========================================================================

def split_giant_section_v2(
    paragraphs: list[str],
    target: int = SPLIT_TARGET,
    overlap: int = SPLIT_OVERLAP,
    hard_max: int | None = HARD_MAX_DEFAULT,
) -> list[str]:
    """초대형 섹션을 paragraph 경계 + hard_max 강제로 분할.

    기존 5 WG chunker는 paragraph 단위 split만 수행 → 거대 표 1 paragraph는 split 불가.
    본 함수는 다음 로직 추가:
      1. 단일 paragraph 토큰 > hard_max → 해당 paragraph를 행/문자 단위로 강제 split
      2. 그 후 일반 paragraph 단위 누적 split (기존 로직)
      3. 결과 chunk 모두 tokenCount <= hard_max 보장

    Args:
        paragraphs: 분할 대상 paragraph 리스트
        target: 청크 목표 토큰 (P7-V07)
        overlap: 청크 오버랩 토큰 (P7-V08)
        hard_max: 청크 절대 최대 토큰 (P7-V11). None이면 기존 동작 (paragraph 단위만).

    Returns:
        분할된 chunk text 리스트.
    """
    if not paragraphs:
        return []

    # Step 1: 거대 paragraph 사전 분해
    if hard_max is not None:
        normalized: list[str] = []
        for para in paragraphs:
            if count_tokens(para) > hard_max:
                normalized.extend(split_huge_paragraph(para, target))
            else:
                normalized.append(para)
        paragraphs = normalized

    # Step 2: 일반 paragraph 단위 누적 split
    chunks: list[str] = []
    current_paras: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        if current_tokens + para_tokens > target and current_paras:
            # 오버랩 처리 (기존 로직)
            overlap_paras: list[str] = []
            overlap_tokens = 0
            for p in reversed(current_paras):
                pt = count_tokens(p)
                if overlap_tokens + pt > overlap:
                    if not overlap_paras:
                        char_limit = overlap * 4
                        suffix = ScriptMarkup(p).slice(-char_limit) if char_limit else ""
                        overlap_paras = [suffix] if suffix else []
                        overlap_tokens = count_tokens(suffix)
                    break
                overlap_paras.insert(0, p)
                overlap_tokens += pt

            # 쌓인 글 전체가 다음 청크의 오버랩으로 그대로 다시 실리면, 여기서 내보내는 청크는 다음 청크에
            # 통째로 들어 있는 중복 조각이다(거대 표 앞의 표 제목 한 줄 · 짧은 도입 문장). 내보내지 않고
            # 다음 문단과 합친다. 합친 글이 hard_max 를 넘으면 오버랩도 버려지므로 그때는 그대로 내보낸다.
            if overlap_paras == current_paras and (hard_max is None or current_tokens + para_tokens <= hard_max):
                current_paras.append(para)
                current_tokens += para_tokens
                continue
            chunks.append("\n".join(current_paras))

            # 오버랩은 편의이고 hard_max 는 절대 한도다. 둘이 부딪치면 오버랩을 버린다.
            if hard_max is not None and overlap_tokens + para_tokens > hard_max:
                overlap_paras, overlap_tokens = [], 0
            current_paras = overlap_paras + [para]
            current_tokens = overlap_tokens + para_tokens
        else:
            current_paras.append(para)
            current_tokens += para_tokens

    if current_paras:
        chunks.append("\n".join(current_paras))

    # 최종 본문을 다시 측정한다. 행 하나가 길거나 여러 문단을 합친 경우에는
    # 앞 단계에서 측정한 부분별 토큰 수만으로 최종 한도 준수를 보장할 수 없다.
    if hard_max is not None:
        chunks = [piece for c in chunks
                  for piece in (_force_split_by_chars(c, hard_max) if count_tokens(c) > hard_max else [c])]
    return chunks


# ===========================================================================
# Chunks.json 후처리 (기존 적재본 보정용 — 재파싱 없이 v2 적용)
# ===========================================================================

def split_existing_chunk(chunk: dict, hard_max: int = HARD_MAX_DEFAULT) -> list[dict]:
    """기존 chunks.json 의 거대 chunk를 hard_max 기준으로 후처리 split.

    재파싱 없이 chunks.json 만 패치하여 Qdrant 재인덱싱하는 용도.
    RAN별 chunker가 'text' 또는 'content' 키 사용 — 둘 다 지원.

    저장된 tokenCount가 과거 추정값일 수 있으므로 본문을 토크나이저로 다시 측정한다.
    행·문자 분할 뒤에도 한도를 넘는 조각에는 _force_split_by_chars를 적용한다.
    """
    # RAN1/2/3/4는 'text', RAN5는 'content' 사용
    text_key = body_key(chunk)
    text = chunk.get(text_key, "") or ""
    token_count = count_tokens(text)  # always re-measure (stale tokenCount field 무시)

    if token_count <= hard_max:
        return [chunk]

    if is_table_text(text):
        split_texts = split_huge_paragraph_by_rows(text)
    else:
        split_texts = split_huge_paragraph_by_chars(text)

    # 안전장치: 행/문자 split 후에도 여전히 hard_max 초과인 sub-chunks가 있으면
    # 강제 char-split (last resort, 의미 단위 무시).
    final_texts: list[str] = []
    for sub in split_texts:
        if count_tokens(sub) > hard_max:
            final_texts.extend(_force_split_by_chars(sub, hard_max))
        else:
            final_texts.append(sub)
    split_texts = final_texts

    # split이 빈 리스트면 fallback (예: text가 비어있는 경우)
    if not split_texts:
        return [chunk]

    # 원본 chunkId 전체에 split 인덱스 suffix → 형제 청크 ID 충돌 방지
    # (마지막 세그먼트를 떼고 재번호하면 '...-005' split이 '...-001'을 만들어 충돌).
    # 주의: 이 함수는 청크 하나만 본다. 그래서 조각에 매기는 chunkIndex(1..k)가
    # 같은 문서의 다른 청크와 겹치는지 알 수 없다. 목록을 가진 호출부가
    # renumber_chunk_indices()로 문서 전체의 chunkIndex를 다시 매겨야 한다.
    base_id = chunk["chunkId"]
    new_chunks = []
    for idx, sub in enumerate(split_texts, 1):
        nc = dict(chunk)
        nc["chunkId"] = base_id if len(split_texts) == 1 else f"{base_id}-{idx:03d}"
        nc[text_key] = sub  # 원본 키 보존 (text 또는 content)
        nc["chunkIndex"] = idx
        nc["totalChunks"] = len(split_texts)
        nc["tokenCount"] = count_tokens(sub)
        nc["_v2Split"] = True
        nc["_originalTokenCount"] = token_count
        new_chunks.append(nc)
    return new_chunks


# ===========================================================================
# 검증 헬퍼
# ===========================================================================

def validate_chunk_size(
    chunks: list[dict], hard_max: int = HARD_MAX_DEFAULT
) -> dict:
    """본문을 직접 측정해 토큰 한도 위반과 최대 토큰 수를 반환한다.

    저장된 tokenCount 대신 토크나이저의 재측정값을 사용하며 text/content를 지원한다.

    Returns:
        {"pass": bool, "violations": list, "maxToken": int, "total": int, "hardMax": int}
    """
    violations = []
    max_t = 0
    for c in chunks:
        # 직접 측정 (stale payload tokenCount 무시)
        text = chunk_body(c, f"chunkId={c.get('chunkId')}" if isinstance(c, dict) else "chunk")
        tc = count_tokens(text)
        max_t = max(max_t, tc)
        if tc > hard_max:
            violations.append(
                {
                    "chunkId": c.get("chunkId"),
                    "tokenCount": tc,
                    "sectionNumber": c.get("sectionNumber"),
                    "sectionTitle": (c.get("sectionTitle") or "")[:50],
                }
            )

    return {
        "pass": len(violations) == 0,
        "violations": violations,
        "maxToken": max_t,
        "total": len(chunks),
        "hardMax": hard_max,
    }


def _index_base(chunks: list[dict]) -> int:
    """목록이 쓰는 chunkIndex 시작값. 정수 번호가 하나도 없으면 1."""
    return min((c["chunkIndex"] for c in chunks
                if isinstance(c.get("chunkIndex"), int)), default=1)


def renumber_chunk_indices(chunks: list[dict], base: int | None = None) -> list[dict]:
    """문서 안에서 chunkIndex 가 유일하도록 목록 전체에 번호를 다시 매긴다.

    쪼갠 조각에 1..k 를 다시 매기면 그 번호가 같은 문서의 원래 청크와 겹친다.
    적재는 (문서, chunkIndex) 로 포인트 신원을 만들기 때문에, 겹치는 순간 뒤엣것이
    앞엣것을 조용히 덮어쓴다 — 개수는 맞고 본문 하나가 사라진다. chunkId 는 이미
    부모 이름 전체에 조각 번호를 덧붙이므로, 여기서는 chunkId를 유지하고 순번만 바꾼다.

    번호의 시작값은 입력이 쓰던 것을 따른다(0-기반 목록을 1-기반으로 옮기지 않는다).
    `base` 를 주면 그 값에서 시작한다. 조각에 1..k 를 덮어쓴 목록에서는 원래 시작값이
    지워졌을 수 있으므로, 쪼개기 전 목록에서 시작값을 읽은 호출자가 넘긴다.

    받은 목록 **전체**를 한 줄로 매기므로, 번호의 단위를 고르는 것은 호출자다.
    tdoc 은 문서가 단위지만 TS 트리의 chunkIndex 는 절 안의 순번이라 절마다 나눠
    넘겨야 한다(신원은 md5(chunkId) 라 번호와 무관하다).
    """
    if not chunks:
        return chunks
    if base is None:
        base = _index_base(chunks)
    for i, c in enumerate(chunks, base):
        c["chunkIndex"] = i
        c["totalChunks"] = len(chunks)
    return chunks


def enforce_hard_max(
    chunks: list[dict],
    hard_max: int = HARD_MAX_DEFAULT,
    text_keys: tuple[str, ...] = ("text", "content"),
) -> list[dict]:
    """청크 목록의 본문을 측정·분할해 HARD_MAX를 적용한다.

    phase-6/8/9 parser가 자체 chunker로 청크 생성 후 본 함수를 마지막에 호출하면,
    어떤 chunker 정책이든 최종 chunk 크기가 hard_max를 초과하지 않도록 보장.

    동작:
    1. 각 chunk text를 인코더의 토크나이저로 정확 측정
    2. hard_max 초과 chunk를 `_force_split_by_chars`로 분해
    3. 새 sub-chunks의 `chunkId`/`tokenCount`/`chunkIndex`/`totalChunks` 필드 갱신
    4. chunk 순서 보존

    Args:
        chunks: chunk dict 리스트 (각 dict에 'text' 또는 'content' 키, 'chunkId' 키 가짐)
        hard_max: 최대 토큰 수 (기본 6,500)
        text_keys: 본문 텍스트 키 후보 (RAN별 chunker가 다른 키 사용 — 'text' 우선, 'content' fallback)

    Returns:
        HARD_MAX 보장된 chunk 리스트.
    """
    if not chunks:
        return chunks

    selected_keys = [body_key(chunk, text_keys) for chunk in chunks]
    # 시작값은 쪼개기 전에 읽는다. 첫 청크가 쪼개지면 그 자리에 조각 번호 1 이 들어가
    # 0-기반 목록이 1-기반으로 읽힌다.
    base = _index_base(chunks)
    reserved_ids = {c["chunkId"] for c in chunks if isinstance(c.get("chunkId"), str)}
    generated_ids: set[str] = set()
    final: list[dict] = []
    split_happened = False
    for chunk, text_key in zip(chunks, selected_keys):
        text = chunk.get(text_key, "") or ""
        actual_tok = count_tokens(text)

        if actual_tok <= hard_max:
            # 안전: tokenCount field 갱신 (stale 보정)
            new_chunk = dict(chunk)
            new_chunk["tokenCount"] = actual_tok
            final.append(new_chunk)
            continue

        # 초과 → 분해
        split_happened = True
        if is_table_text(text):
            split_texts = split_huge_paragraph_by_rows(text)
        else:
            split_texts = split_huge_paragraph_by_chars(text)

        # 행/문자 split 후에도 초과인 sub-chunks는 _force_split_by_chars
        normalized: list[str] = []
        for sub in split_texts:
            if count_tokens(sub) > hard_max:
                normalized.extend(_force_split_by_chars(sub, hard_max))
            else:
                normalized.append(sub)

        if not normalized:
            # 안전망: 비어 있으면 force-split 직접 호출
            normalized = _force_split_by_chars(text, hard_max)

        # sub-chunk ID: 원본 chunkId 전체에 split 인덱스를 덧붙여 고유성 보장.
        # 마지막 숫자 세그먼트를 떼고 1부터 재번호하면(이전 방식) 같은 부모의
        # 형제 청크(예: '...-body-005'를 split → '...-body-001')와 ID가 충돌하고,
        # Qdrant point_id = md5(chunkId) 가 겹쳐 silent 덮어쓰기(내용 소실)가 발생한다.
        # 단일 조각이면 원본 ID를 그대로 유지(분해 안 된 것과 동일 취급).
        chunk_id = chunk.get("chunkId", "") or "chunk"

        for idx, sub_text in enumerate(normalized, 1):
            sub_chunk = dict(chunk)
            sub_chunk[text_key] = sub_text
            new_id = chunk_id
            if len(normalized) > 1:
                suffix = idx
                new_id = f"{chunk_id}-{suffix:03d}"
                while new_id in reserved_ids or new_id in generated_ids:
                    suffix += 1
                    new_id = f"{chunk_id}-{suffix:03d}"
            generated_ids.add(new_id)
            sub_chunk["chunkId"] = new_id
            sub_chunk["chunkIndex"] = idx
            sub_chunk["totalChunks"] = len(normalized)
            sub_chunk["tokenCount"] = count_tokens(sub_text)
            sub_chunk["_hardMaxEnforced"] = True
            sub_chunk["_originalTokenCount"] = actual_tok
            final.append(sub_chunk)

    # 분할로 청크가 추가되면 목록 전체의 chunkIndex를 다시 매긴다.
    # 아무것도 쪼개지 않았으면 손대지 않는다(불필요한 신원 변경 = 재적재 유발).
    if split_happened:
        renumber_chunk_indices(final, base=base)
    return final


# ===========================================================================
# 임베딩 입력 한도 — 자르기
# ===========================================================================
# EMBEDDING_MAX_TOKENS는 기본 인코더 선언의 토큰 한도다.
# 문자 수로만 자른 본문은 한도를 넘을 수 있으므로 실제 토큰 수로 확인한다.


def truncate_to_token_budget(text: str, max_tokens: int = EMBEDDING_MAX_TOKENS) -> str:
    """토큰 한도 안으로 자른다. 한도 안이면 원문 그대로 돌려준다.

    count_tokens 의 추정은 estimate_ok=True 로 명시한 호출에만 허용한다. 여기서는
    추정을 쓰지 않는다 — 한도를 지켰다고 말하려면 같은 단위로 정확히 세야 한다.
    UTF-8 바이트 수가 한도 이하면 그대로 통과시킨다. 긴 본문은 원문의 문자
    prefix를 선택하고 생성된 첨자 역할을 닫은 뒤 실제 토큰 수를 잰다. 토큰을
    decode한 문자열로 원문을 대체하지 않는다.
    """
    if max_tokens < 0:
        raise ValueError("max_tokens must be nonnegative")
    if not text or max_tokens == 0:
        return "" if max_tokens == 0 else text
    if len(text.encode("utf-8")) <= max_tokens:
        return text
    tok = _tokenizer()
    if tok is None:
        raise TokenizerUnavailable(
            f"{EMBEDDING_MODEL} 토크나이저가 필요합니다 ({_TOKENIZER_ERR}). 임베딩 "
            "한도는 토큰 단위라서 글자 수로는 자른 뒤에도 한도 안임을 보장할 수 없습니다."
        )
    encode = lambda t: tok(t, add_special_tokens=False)["input_ids"]
    tokens = encode(text)
    if len(tokens) <= max_tokens:
        return text
    source = ScriptMarkup(text)
    end = max(1, len(text) * max_tokens // len(tokens))
    try:
        end, candidate = _fit_raw_slice(source, 0, end, max_tokens)
    except ValueError:
        return ""  # No complete first source character fits this prefix budget.
    # Find a fuller measured prefix without assuming a token-prefix decode has
    # the same characters as the original source. Every accepted result fits.
    low, high = end, len(text)
    while low + 1 < high:
        middle = (low + high) // 2
        expanded = source.slice(0, middle)
        if len(encode(expanded)) <= max_tokens:
            low, candidate = middle, expanded
        else:
            high = middle
    return candidate


__all__ = [
    "EMBEDDING_MODEL",
    "EMBEDDING_MAX_TOKENS",
    "HARD_MAX_DEFAULT",
    "SPLIT_THRESHOLD",
    "SPLIT_TARGET",
    "SPLIT_OVERLAP",
    "count_tokens",
    "truncate_to_token_budget",
    "split_giant_section_v2",
    "split_huge_paragraph",
    "split_huge_paragraph_by_rows",
    "split_huge_paragraph_by_chars",
    "split_existing_chunk",
    "renumber_chunk_indices",
    "validate_chunk_size",
    "is_table_text",
    "enforce_hard_max",
]
