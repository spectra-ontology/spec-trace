"""스키마만 받은 Codex 질의 작성 조건이 Claude 서브에이전트와 같은 묶음 파일을 읽었는지 본다(읽기 전용).

Codex 실행 기록(events.jsonl)의 명령 출력 가운데 묶음 파일 전체를 찍은 출력을 찾아, 저장된 서브에이전트
묶음 파일과 JSON 객체로 같은지 견준다. 사용: python3 -B check_codex_packet_identity.py --out <json>
저장소 루트에서 실행한다.
"""
import argparse
import hashlib
import json
from pathlib import Path

CHAIN = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/chain_eval")
PACKETS = {"sql": "subagent_packets_sql", "cy": "subagent_packets"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for lang, folder in PACKETS.items():
        for n in range(1, 6):
            packet_path = CHAIN / folder / f"RAN{n}_schema.json"
            text = packet_path.read_text(encoding="utf-8")
            packet = json.loads(text)
            record = CHAIN / "codex/run_records" / f"chain_{lang}_RAN{n}" / "events.jsonl"
            same_object = same_bytes = False
            outputs = 0
            with open(record, encoding="utf-8") as handle:
                for line in handle:
                    item = json.loads(line).get("item", {})
                    out = item.get("aggregated_output") if item.get("type") == "command_execution" else None
                    if not out:
                        continue
                    outputs += 1
                    same_bytes = same_bytes or out.strip() == text.strip()
                    try:
                        same_object = same_object or json.loads(out) == packet
                    except json.JSONDecodeError:
                        pass
            rows.append({"language": lang, "wg": f"RAN{n}", "packet": str(packet_path),
                         "packetSha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                         "packetKeys": sorted(packet), "items": len(packet["items"]), "taskChars": len(packet["task"]),
                         "runRecord": str(record), "commandOutputs": outputs,
                         "printedPacketEqualsStoredObject": same_object, "printedPacketEqualsStoredText": same_bytes})
    report = {"check": "Codex 가 명령으로 찍은 packet.json 전체가 저장된 서브에이전트 묶음과 같은 JSON 객체인가",
              "runs": rows, "sameObject": sum(r["printedPacketEqualsStoredObject"] for r in rows), "of": len(rows)}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for r in rows:
        print(r["language"], r["wg"], r["items"], r["taskChars"], r["printedPacketEqualsStoredObject"], r["printedPacketEqualsStoredText"])
    print("same object:", report["sameObject"], "of", report["of"])


if __name__ == "__main__":
    main()
