"""결정 처분 기록(DecisionDisposition)을 원문 DOCX와 다시 대조한다.

구축 코드와 독립으로 작성한 검사다. WG별로 `source_verified` 기록을 무작위 추출해
① 근거 파일의 SHA-256 ② 인용문의 원문 존재 ③ 인용문 안의 대상 문서 번호
④ `Decision:` 줄을 별도 키워드 순서로 다시 읽은 처분 코드의 일치를 센다.

인용문은 공백을 제거한 뒤 비교한다. 표 행 인용(`| 셀 | 셀 |`)은 `|`와 줄바꿈으로
나눈 조각(공백 제거 후 4자 이상) 단위로 원문 존재를 확인한다.
원문 글은 word/document.xml 의 w:t 에 더해 글자를 그리는 요소를 함께 읽는다. 줄바꿈 없는 하이픈(w:noBreakHyphen)은
`-` 다. 기호 글꼴 글자(회의록의 `ZTE 🡪 …` 화살표 따위)는 유니코드로 옮기는 표가 글꼴마다 달라 엄격한 비교에서는
원문 글에서 뺀다. 이 글자는 w:sym 요소로도, 기호 글꼴 런의 w:t 안 사용자 정의 영역 글자(U+F000~U+F0FF)로도 온다.
그리고 원문의 기호 자리 하나가 인용문 글자 하나와 맞는다고 본 비교(`all_fragments_in_source_with_symbol_positions`)로
따로 센다.
`Decision:` 줄이 없는 인용(본문 합의문·부속서 표 행)은 ④에서 제외하고 건수를 따로 적는다.

사용: python3 audit_decision_disposition.py --sample 500 --seed 20261111 --out <json>
저장소 루트에서 실행한다(근거 경로가 루트 상대 경로다).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import re
import xml.etree.ElementTree as ET
import zipfile
from functools import lru_cache
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
INSTANCES = Path("ontology/output/tsg/RAN/formal/instances/phase-2")
# 앞에 놓인 표현이 먼저 판정된다. 부정형과 후속 조치(revised 등)를 긍정형보다 앞에 둔다.
READ_ORDER = [
    ("not_treated", r"not\s+treated"), ("not_pursued", r"not\s+pursued"),
    ("not_concluded", r"not\s+concluded"), ("not_agreed", r"not\s+agreed"),
    ("withdrawn", r"withdrawn"), ("postponed", r"postponed"), ("merged", r"merged"),
    ("revised", r"revised"), ("rejected", r"rejected"), ("replied_to", r"replied"),
    ("endorsed", r"endorsed"), ("agreed", r"agreed|approved"), ("noted", r"noted"),
]


def squeeze(text: str) -> str:
    return re.sub(r"\s+", "", text)


SYMBOL = "\x00"


@lru_cache(maxsize=8)
def load_docx(path: str) -> tuple[str, str, str]:
    """(파일 SHA-256, 공백을 제거한 본문 텍스트, 기호 자리를 SYMBOL 로 남긴 같은 텍스트)를 돌려준다."""
    raw = Path(path).read_bytes()
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    parts: list[str] = []
    for element in root.iter():
        if element.tag == W + "t":
            parts.append(element.text or "")
        elif element.tag in (W + "tab", W + "p", W + "br"):
            parts.append(" ")
        elif element.tag == W + "noBreakHyphen":
            parts.append("-")
        elif element.tag == W + "sym":
            parts.append(SYMBOL)
    joined = squeeze("".join(parts))
    with_symbols = re.sub("[\uf000-\uf0ff]", SYMBOL, joined)
    return hashlib.sha256(raw).hexdigest(), joined.replace(SYMBOL, ""), with_symbols


def in_source_with_symbol_positions(fragment: str, with_symbols: str) -> bool:
    if SYMBOL not in with_symbols:
        return False
    pattern = "".join(f"(?:{re.escape(c)}|{SYMBOL})" for c in fragment)
    return re.search(pattern, with_symbols) is not None


def reread_code(quote: str) -> str | None:
    lines = re.findall(r"Decision:\s*(.+)", quote)
    if not lines:
        return None
    last = lines[-1].lower()
    for code, pattern in READ_ORDER:
        if re.search(pattern, last):
            return code
    return "unread"


def audit_wg(wg: str, sample: int, rng: random.Random) -> dict:
    graph = json.loads((INSTANCES / f"RAN{wg}" / "decision_dispositions.jsonld").read_text())["@graph"]
    verified = [r for r in graph if r.get("evidenceStatus") == "source_verified"]
    drawn = sorted(rng.sample(verified, min(sample, len(verified))), key=lambda r: r["evidencePath"])
    count: collections.Counter[str] = collections.Counter()
    code_differences, fragment_misses = [], []
    for record in drawn:
        sha, text, with_symbols = load_docx(record["evidencePath"])
        quote = record["evidenceQuote"]
        fragments = [squeeze(f) for f in re.split(r"[|\n]", quote) if len(squeeze(f)) >= 4]
        found = [f in text for f in fragments]
        count["all_fragments_in_source_with_symbol_positions"] += all(
            hit or in_source_with_symbol_positions(f, with_symbols) for f, hit in zip(fragments, found))
        count["sampled"] += 1
        count["sha_match"] += sha == record["evidenceSha256"]
        count["whole_quote_in_source"] += squeeze(quote) in text
        count["all_fragments_in_source"] += all(found)
        count["fragments"] += len(fragments)
        count["fragments_in_source"] += sum(found)
        count["target_number_in_quote"] += record["targetTdocNumber"] in quote
        if not all(found):
            fragment_misses.append({"dispositionId": record["dispositionId"],
                                    "missingFragment": fragments[found.index(False)][:160]})
        reread = reread_code(quote)
        if reread is None:
            count["without_decision_line"] += 1
        else:
            count["with_decision_line"] += 1
            if reread == record["dispositionCode"]:
                count["code_match"] += 1
            else:
                code_differences.append({"dispositionId": record["dispositionId"],
                                         "recorded": record["dispositionCode"], "reread": reread,
                                         "decisionLine": re.findall(r"Decision:\s*(.+)", quote)[-1][:200]})
    return {"wg": f"RAN{wg}", "records": len(graph), "sourceVerified": len(verified),
            "counts": dict(count), "codeDifferences": code_differences, "fragmentMisses": fragment_misses}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sample", type=int, required=True, help="WG별 추출 건수")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    result = {"samplePerWg": args.sample, "seed": args.seed,
              "workingGroups": [audit_wg(wg, args.sample, rng) for wg in "12345"]}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    for row in result["workingGroups"]:
        print(row["wg"], row["records"], row["sourceVerified"], row["counts"])


if __name__ == "__main__":
    main()
