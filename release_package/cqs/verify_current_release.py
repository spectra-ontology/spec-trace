#!/usr/bin/env python3
"""Run the current saved-artifact verifiers with Python assertions enabled."""
import sys

if sys.flags.optimize != 0:
    raise SystemExit("Verification requires assertions; Python -O and -OO are refused.")

import json
import os
from pathlib import Path
import subprocess


def main():
    if len(sys.argv) != 1:
        raise SystemExit("Usage: python3 -B -I verify_current_release.py")
    package = Path(__file__).resolve().parent
    specifications = [
        ("current_core", ["current_core/verify_index.py"]),
        ("core_disposition", ["core_disposition_audit/verify_package.py"]),
        ("AUTH23_saved_evaluation", [
            "original_core_overnight_evaluation23/runtime/verify_authorized_incremental23_evaluation.py",
            "--evidence", "original_core_overnight_evaluation23",
            "--bundle", "original_core_overnight_repairs23",
        ]),
        ("AUTH24_saved_evaluation", [
            "original_core_overnight_evaluation24/runtime/verify_authorized_incremental24_evaluation.py",
            "--evidence", "original_core_overnight_evaluation24",
            "--bundle", "original_core_overnight_repairs24",
        ]),
        ("AUTH25_saved_evaluation", [
            "original_core_overnight_evaluation25/runtime/verify_authorized_incremental25_evaluation.py",
            "--evidence", "original_core_overnight_evaluation25",
            "--bundle", "original_core_overnight_repairs25",
        ]),
        ("AUTH26_saved_evaluation", [
            "original_core_overnight_evaluation26/runtime/verify_authorized_incremental26_evaluation.py",
            "--evidence", "original_core_overnight_evaluation26",
            "--bundle", "original_core_overnight_repairs26",
        ]),
        ("AUTH27_saved_evaluation", [
            "original_core_overnight_evaluation27/runtime/verify_authorized_incremental27_evaluation.py",
            "--evidence", "original_core_overnight_evaluation27",
            "--bundle", "original_core_overnight_repairs27",
        ]),
        ("AUTH28_saved_evaluation", [
            "original_core_overnight_evaluation28/runtime/verify_authorized_incremental28_evaluation.py",
            "--evidence", "original_core_overnight_evaluation28",
            "--bundle", "original_core_overnight_repairs28",
        ]),
        ("AUTH29_saved_evaluation", [
            "original_core_overnight_evaluation29/runtime/verify_authorized_incremental29_evaluation.py",
            "--evidence", "original_core_overnight_evaluation29",
            "--bundle", "original_core_overnight_repairs29",
        ]),
        ("AUTH30_saved_evaluation", [
            "original_core_overnight_evaluation30/runtime/verify_authorized_incremental30_evaluation.py",
            "--evidence", "original_core_overnight_evaluation30",
            "--bundle", "original_core_overnight_repairs30",
        ]),
        ("AUTH31_saved_evaluation", [
            "original_core_overnight_evaluation31/runtime/verify_authorized_incremental31_evaluation.py",
            "--evidence", "original_core_overnight_evaluation31",
            "--bundle", "original_core_overnight_repairs31",
        ]),
        ("AUTH32_saved_evaluation", [
            "original_core_overnight_evaluation32/runtime/verify_authorized_incremental32_evaluation.py",
            "--evidence", "original_core_overnight_evaluation32",
            "--bundle", "original_core_overnight_repairs32",
        ]),
        ("AUTH33_saved_evaluation", [
            "original_core_overnight_evaluation33/runtime/verify_authorized_incremental33_evaluation.py",
            "--evidence", "original_core_overnight_evaluation33",
            "--bundle", "original_core_overnight_repairs33",
        ]),
        ("AUTH34_saved_evaluation", [
            "original_core_overnight_evaluation34/runtime/verify_authorized_incremental34_evaluation.py",
            "--evidence", "original_core_overnight_evaluation34",
            "--bundle", "original_core_overnight_repairs34",
        ]),
        ("AUTH35_saved_evaluation", [
            "original_core_overnight_evaluation35/runtime/verify_authorized_incremental35_evaluation.py",
            "--evidence", "original_core_overnight_evaluation35",
            "--bundle", "original_core_overnight_repairs35",
        ]),
        ("AUTH36_saved_evaluation", [
            "original_core_overnight_evaluation36/runtime/verify_authorized_incremental36_evaluation.py",
            "--evidence", "original_core_overnight_evaluation36",
            "--bundle", "original_core_overnight_repairs36",
        ]),
        ("AUTH37_saved_evaluation", [
            "original_core_overnight_evaluation_auth37/runtime/verify_authorized_incremental37_evaluation.py",
            "--evidence", "original_core_overnight_evaluation_auth37",
            "--bundle", "original_core_overnight_repairs_auth37",
        ]),
        ("AUTH38_saved_evaluation", [
            "original_core_overnight_evaluation38/runtime/verify_authorized_incremental38_evaluation.py",
            "--evidence", "original_core_overnight_evaluation38",
            "--bundle", "original_core_overnight_repairs38",
        ]),
        ("AUTH39_saved_evaluation", [
            "original_core_overnight_evaluation39/runtime/verify_authorized_incremental39_evaluation.py",
            "--evidence", "original_core_overnight_evaluation39",
            "--bundle", "original_core_overnight_repairs39",
        ]),
        ("AUTH40_saved_evaluation", [
            "original_core_overnight_evaluation40/runtime/verify_authorized_incremental40_evaluation.py",
            "--evidence", "original_core_overnight_evaluation40",
            "--bundle", "original_core_overnight_repairs40",
        ]),
        ("AUTH41_saved_evaluation", [
            "original_core_overnight_evaluation41/runtime/verify_authorized_incremental41_evaluation.py",
            "--evidence", "original_core_overnight_evaluation41",
            "--bundle", "original_core_overnight_repairs41",
        ]),
        ("AUTH42_saved_evaluation", [
            "original_core_overnight_evaluation42/runtime/verify_authorized_incremental42_evaluation.py",
            "--evidence", "original_core_overnight_evaluation42",
            "--bundle", "original_core_overnight_repairs42",
        ]),
        ("AUTH43_saved_evaluation", [
            "original_core_overnight_evaluation43/runtime/verify_authorized_incremental43_evaluation.py",
            "--evidence", "original_core_overnight_evaluation43",
            "--bundle", "original_core_overnight_repairs43",
        ]),
        ("AUTH44_saved_evaluation", [
            "original_core_overnight_evaluation44/runtime/verify_authorized_incremental44_evaluation.py",
            "--evidence", "original_core_overnight_evaluation44",
            "--bundle", "original_core_overnight_repairs44",
        ]),
        ("AUTH45_saved_evaluation", [
            "original_core_overnight_evaluation45/runtime/verify_authorized_incremental45_evaluation.py",
            "--evidence", "original_core_overnight_evaluation45",
            "--bundle", "original_core_overnight_repairs45",
        ]),
        ("AUTH46_saved_evaluation", [
            "original_core_overnight_evaluation46/runtime/verify_authorized_incremental46_evaluation.py",
            "--evidence", "original_core_overnight_evaluation46",
            "--bundle", "original_core_overnight_repairs46",
        ]),
    ]
    # Child interpreters use a clean environment and disable site packages; the explicit parent guard runs before package files open.
    environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                   "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
    completed = []
    for name, arguments in specifications:
        command = [sys.executable, "-B", "-S", *arguments]
        result = subprocess.run(command, cwd=package, env=environment,
                                text=True, capture_output=True, timeout=600)
        record = {"verifier": name, "argv": command,
                  "exit_code": result.returncode,
                  "stdout": result.stdout, "stderr": result.stderr}
        completed.append(record)
        if result.returncode != 0:
            print(json.dumps({"status": "FAIL", "commands": completed}, sort_keys=True))
            raise SystemExit(result.returncode if result.returncode > 0 else 1)
    print(json.dumps({"status": "PASS", "commands": completed,
                      "scope": "Included bytes, contract partition and saved AUTH23, AUTH24, AUTH25, AUTH26, AUTH27, AUTH28, AUTH29, AUTH30, AUTH31, AUTH32, AUTH33, AUTH34, AUTH35, AUTH36, AUTH37, AUTH38, AUTH39, AUTH40, AUTH41, AUTH42, AUTH43, AUTH44, AUTH45 and AUTH46 output replay only.",
                      "fresh_source_extraction": False,
                      "new_model_calls": 0, "new_database_executions": 0,
                      "human_expert_validation": False}, sort_keys=True))


if __name__ == "__main__":
    main()
