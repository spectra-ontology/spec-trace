"""하위 에이전트 대화 기록에서 시작·종료 시각, 응답 모델, 응답 메시지 수, 작업 지시에 적힌 출력 경로를 읽는다.

사용: python3 collect_subagent_model_provenance.py SESSION_ID AGENT_ID... > out.json
모델은 각 assistant 메시지의 model 필드에서 읽는다(과금 API 호출 없음).
model 이 `<synthetic>` 인 메시지는 모델의 응답이 아니라 실행 환경이 끼워 넣은 안내(예: 사용량 한도)이므로
models · assistantMessages 에서 빼고 harnessNotices 에 시각과 첫 글자들을 적는다.
뒤따른 사용자 메시지는 followupInstructions 에 적고 kind 로 나눈다: coordinator(작업을 맡긴 쪽의 지시),
contextSummary(대화가 길어져 실행 환경이 앞부분을 요약해 이어 붙인 것), handbackReminder(보고를 넘기라는 실행 환경 안내),
harnessReminder(실행 환경이 `<system-reminder>` 로 끼운 안내. 예: 보고를 SubagentHandback 으로 넘기라는 시작 안내),
streamRetry(응답 전송이 중간에 끊겨 실행 환경이 같은 응답을 처음부터 다시 쓰게 한 안내).
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path.home() / ".claude/projects/<project-dir>" / sys.argv[1] / "subagents"
OUTPUT = re.compile(r"(/home/[^\s'\"]+\.jsonl)")
SYNTHETIC = "<synthetic>"
HARNESS_USER = (("contextSummary", "This session is being continued from a previous conversation"),
                ("handbackReminder", "[handback-send-enforce]"),
                ("harnessReminder", "<system-reminder>"),
                ("streamRetry", "Your response above was cut off mid-stream"))


def text_of(content) -> str:
    if isinstance(content, list):
        return " ".join(c.get("text", "") for c in content if isinstance(c, dict))
    return content or ""


out = {}
for agent in sys.argv[2:]:
    records = [json.loads(line) for line in (ROOT / f"agent-{agent}.jsonl").read_text().splitlines()]
    stamps = [r["timestamp"] for r in records if r.get("timestamp")]
    models, assistant, notices = set(), 0, []
    for record in records:
        message = record.get("message") or {}
        if record.get("type") != "assistant":
            continue
        if message.get("model") == SYNTHETIC:
            notices.append({"time": record.get("timestamp"), "text": text_of(message.get("content"))[:120]})
            continue
        assistant += 1
        if message.get("model"):
            models.add(message["model"])
    prompt = text_of((records[0].get("message") or {}).get("content", ""))
    followups = []
    for record in records[1:]:
        message = record.get("message") or {}
        if record.get("type") == "user" and isinstance(message.get("content"), str):
            kind = next((k for k, prefix in HARNESS_USER if message["content"].startswith(prefix)), "coordinator")
            followups.append({"time": record.get("timestamp"), "kind": kind,
                              "outputsNamed": sorted(set(OUTPUT.findall(message["content"])))})
    out[agent] = {"started": min(stamps), "ended": max(stamps), "models": sorted(models), "assistantMessages": assistant,
                  "harnessNotices": notices, "outputsNamedInPrompt": sorted(set(OUTPUT.findall(prompt))),
                  "followupInstructions": followups}
json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
