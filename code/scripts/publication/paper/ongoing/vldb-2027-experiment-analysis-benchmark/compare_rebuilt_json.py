"""다시 만든 JSON 원장 파일이 저장된 파일과 같은지 맨 위 키 단위로 본다 (모델 호출 없음).

처분 단계의 `decision_disposition_coverage.json` 처럼 수 MB 크기의 원장 파일을 위한 도구다. 두 파일을 읽어
맨 위 키마다 정규화한 JSON 이 같은지 견준다. 200 MB 를 넘는 파일은 읽지 않고 멈춘다.
결과: 양쪽에 다 있는 키의 수와 그중 값이 다른 키, 한쪽에만 있는 키와 그 값의 요약(형식, 길이, 정수·문자열 값).
문자열 값이 저장소 루트 아래 경로이면 루트에서 시작하는 상대경로로 적는다.
`identical` 은 키 집합과 값이 모두 같을 때 참이고, `commonKeysIdentical` 은 양쪽에 다 있는 키의 값이 모두 같을 때 참이다.
`--indent N` 을 주면 다시 만든 객체에서 양쪽에 다 있는 키만 저장 파일의 키 차례대로 남겨
`json.dumps(indent=N, ensure_ascii=False)` 에 줄바꿈 하나를 붙여 쓴 바이트가 저장 파일과 같은지(`commonKeysBytesIdentical`)도
본다. 값 안의 키 차례와 표기까지 견주는 검사다. 맨 위에서 양쪽에 다 있는 키가 두 파일에서 같은 차례로 놓였는지는
`commonKeysOrderIdentical` 로 따로 적는다.

사용: python3 compare_rebuilt_json.py --rebuilt <json> --stored <json> --out <json> [--indent N]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
LIMIT_BYTES = 200 * 1000 * 1000


def load(path: Path) -> dict:
    if path.stat().st_size > LIMIT_BYTES:
        raise SystemExit(f"{path} 가 {LIMIT_BYTES} 바이트를 넘어 읽지 않는다")
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def describe(value) -> dict:
    out = {"type": type(value).__name__}
    if isinstance(value, (list, dict)):
        out["length"] = len(value)
    elif isinstance(value, str):
        out["value"] = value.replace(f"{ROOT}/", "")
    else:
        out["value"] = value
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuilt", required=True, type=Path)
    ap.add_argument("--stored", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--indent", type=int)
    args = ap.parse_args()
    a, b = load(args.rebuilt), load(args.stored)
    common = a.keys() & b.keys()
    differ = sorted(k for k in common if canonical(a[k]) != canonical(b[k]))
    report = {"rebuilt": str(args.rebuilt), "stored": str(args.stored),
              "keysCompared": len(common), "keysDiffering": differ,
              "keysOnlyRebuilt": {k: describe(a[k]) for k in sorted(a.keys() - b.keys())},
              "keysOnlyStored": {k: describe(b[k]) for k in sorted(b.keys() - a.keys())}}
    report["commonKeysIdentical"] = not differ
    report["identical"] = not (differ or report["keysOnlyRebuilt"] or report["keysOnlyStored"])
    if args.indent is not None:
        shared = {k: a[k] for k in b if k in a}
        text = json.dumps(shared, ensure_ascii=False, indent=args.indent) + "\n"
        report["commonKeysBytesIdentical"] = text.encode("utf-8") == args.stored.read_bytes()
        report["commonKeysOrderIdentical"] = [k for k in a if k in b] == list(shared)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
