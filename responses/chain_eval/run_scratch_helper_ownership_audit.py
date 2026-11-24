"""작업 폴더 공유 감사 두 가지를 `scratch_helper_ownership/agents.json` 의 모든 묶음에 돌린다 (모델 호출 없음).

- 묶음마다 `audit_scratch_helper_ownership.py` → `scratch_helper_ownership/{묶음}.json`
- 세션마다 그 세션의 모든 묶음을 한 시간축에 놓고 같은 검사 → `scratch_helper_ownership/session_{세션 앞 8자}_all_groups.json`
  (같은 작업 폴더를 쓴 서로 다른 묶음 사이의 겹침을 본다)
- 세션마다 그 세션 전체 시간축과 대화 기록으로 `audit_indirect_helper_execution.py` → `scratch_helper_ownership/indirect_{세션 앞 8자}.json`
  (실행된 스크립트가 안에서 다른 에이전트의 스크립트를 부른 후보. 명령 한 줄만 읽는 첫 검사가 못 보는 경우다)
- 폴더마다 `audit_scratch_file_mentions.py` → `scratch_helper_ownership/mentions/{이름}.json`

작업 폴더는 세션 임시 폴더이므로 폴더가 남아 있을 때만 두 번째 검사를 다시 돌릴 수 있다. 폴더가 없으면 그 검사는
건너뛰고 건너뛴 이름을 적는다. `--check` 를 주면 파일을 덮어쓰지 않고 저장된 결과와 JSON 값으로 비교한다.
폴더 검사의 파일 수(`files`)는 폴더에 그 뒤로 생긴 파일 때문에 달라질 수 있어 따로 적고(folderFileCountChanged),
나머지 칸이 하나라도 다르면 differ 에 넣고 끝 상태 1 로 끝난다.

사용: python3 run_scratch_helper_ownership_audit.py [--check]
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "scratch_helper_ownership"


def run(command: list[str], env: dict | None = None, given: str | None = None) -> str:
    return subprocess.run([sys.executable, *command], check=True, capture_output=True, text=True, input=given,
                          env={**os.environ, **(env or {})}).stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="저장된 결과와 비교만 한다")
    args = parser.parse_args()
    manifest = json.loads((OUT / "agents.json").read_text())
    outputs, skipped = {}, []
    by_session: dict[str, list[str]] = {}
    for name, group in manifest["groups"].items():
        outputs[OUT / f"{name}.json"] = run([str(HERE / "audit_scratch_helper_ownership.py"), group["session"],
                                             *group["agents"]])
        by_session.setdefault(group["session"], []).extend(group["agents"])
    for session, agents in by_session.items():
        whole = run([str(HERE / "audit_scratch_helper_ownership.py"), session, *dict.fromkeys(agents)])
        outputs[OUT / f"session_{session[:8]}_all_groups.json"] = whole
        outputs[OUT / f"indirect_{session[:8]}.json"] = run(
            [str(HERE / "audit_indirect_helper_execution.py"), session], given=whole)
    for scan in manifest["mentionScans"]:
        if not pathlib.Path(scan["root"]).is_dir():
            skipped.append(scan["name"])
            continue
        sessions = {manifest["groups"][group]["session"] for group in scan["groups"]}
        if len(sessions) != 1:
            raise SystemExit(f"한 폴더 검사에 세션이 둘 이상이다: {scan['name']}")
        agents = [agent for group in scan["groups"] for agent in manifest["groups"][group]["agents"]]
        outputs[OUT / "mentions" / f"{scan['name']}.json"] = run(
            [str(HERE / "audit_scratch_file_mentions.py"), sessions.pop(), scan["root"], *agents],
            {"FLAT": "1"} if scan["topLevelOnly"] else None)
    differ, file_count = [], {}
    for path, text in outputs.items():
        if args.check:
            name = str(path.relative_to(HERE))
            if not path.exists():
                differ.append(name)
                continue
            saved, now = json.loads(path.read_text()), json.loads(text)
            if path.parent.name == "mentions" and saved.get("files") != now.get("files"):
                # 폴더에 그 뒤로 파일이 더 생기면 파일 수만 바뀐다. 판정 대상은 나머지 칸이다.
                file_count[name] = [saved["files"], now["files"]]
                saved.pop("files"), now.pop("files")
            if saved != now:
                differ.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print(json.dumps({"written" if not args.check else "compared": len(outputs), "differ": differ,
                      "folderFileCountChanged": file_count, "skippedMissingFolder": skipped},
                     ensure_ascii=False, indent=1))
    if differ:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
