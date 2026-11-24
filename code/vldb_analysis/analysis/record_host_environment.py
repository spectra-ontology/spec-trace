"""측정 호스트의 CPU 모델 · 논리 CPU 수 · 메모리 총량 · 커널 판본을 기록한다(재현 절의 환경 문장 근거).
usage: record_host_environment.py <out-json>"""
import json, os, platform, subprocess, sys
from pathlib import Path

lscpu = subprocess.run(["lscpu"], capture_output=True, text=True, check=True).stdout
model = next(l.split(":", 1)[1].strip() for l in lscpu.splitlines() if l.startswith("Model name"))
mem_kib = next(int(l.split()[1]) for l in Path("/proc/meminfo").read_text().splitlines() if l.startswith("MemTotal:"))
out = {"cpuModel": model, "logicalCpus": os.cpu_count(), "memTotalKiB": mem_kib,
       "memTotalGiB": round(mem_kib / 1024 ** 2, 1), "kernel": platform.release(),
       "wsl": "microsoft" in platform.release().lower()}
Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out))
