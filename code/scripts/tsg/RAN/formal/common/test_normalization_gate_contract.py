#!/usr/bin/env python3
"""Spec: email E0 C2/C4; Ontology: frozen email schema; Cycle: 9.
배경: 스레드 경계와 리포트 재측정 계약을 격리 입력으로 검증한다.
사용: python3 -m unittest discover -s scripts/tsg/RAN/formal/common -p test_normalization_gate_contract.py
LLM/DB/실제 데이터 호출 없이 scratch JSON만 사용한다.
"""
import ast
from collections import Counter
import contextlib
import io
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import re
from types import SimpleNamespace as NS
import unittest
from test_audit_safety_contracts import function, ROOT

class NormalizationGate(unittest.TestCase):
    def test_thread_and_report_mismatches_fail(self):
        path=ROOT/"scripts/tsg/RAN/email/common/phase-0/verify_normalization.py"
        keys={}
        for n in ast.parse(path.read_text()).body:
            if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ("FROZEN_KEYS","ADDED_KEYS","MSG_BASE_KEYS"):
                keys[n.targets[0].id]=ast.literal_eval(n.value)
        for duplicated,wrong_empty,expected in ((False,False,0),(True,False,1),(False,True,1)):
            with tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp);derived=base/"derived";tdir=base/"unit";threads=derived/"threads"
                threads.mkdir(parents=True);tdir.mkdir()
                records=[]
                for index,key in enumerate(("A","B")):
                    msg={k:"" for k in keys["MSG_BASE_KEYS"]};msg.update(body_original="body",msg_id=key,index=0,body_original_len=4,date_parsed=None,round_num=None)
                    rec={k:None for k in keys["FROZEN_KEYS"]+keys["ADDED_KEYS"]}
                    rec.update(thread_key=key,wg="RAN1",subject="synthetic",total_messages=1,messages_in=1,dedup_removed=0,overmerge_suspect=False,overmerge_signals={},messages=[msg],participants=[],participant_count=0,archive_codes=[],bracket_ids=[],spec_refs=[],meeting_anchors=[],spec_anchors=[],participant_keys=[])
                    (threads/f"{key}.json").write_text(json.dumps(rec))
                    if duplicated: rec['thread_key']='A'
                    records.append(rec)
                (tdir/"threads.jsonl").write_text("".join(json.dumps(r)+"\n" for r in records))
                (tdir/"manifest.json").write_text(json.dumps({"wg":"RAN1","counts":{"messages_out":2,"messages_in":2,"dedup_removed":0,"threads":2,"overmerge_suspect_threads":0,"parse_failures":0}}))
                (tdir/"masking_missing_report.json").write_text(json.dumps({"wg":"RAN1","email_plaintext_leaks":0,"messages_in":2,"messages_out":2,"dedup_removed":0,"participant_instances":0,"empty_body_messages":999 if wrong_empty else 0,"empty_body_pct":0.0,"email_masked_pct":None}))
                class Parser:
                    def add_argument(self,*a,**kw):pass
                    def parse_args(self):return NS(wg="RAN1")
                atomic_path=ROOT/'scripts/common/common/atomic_io.py'
                spec=importlib.util.spec_from_file_location('normalization_atomic_fixture',atomic_path)
                atomic=importlib.util.module_from_spec(spec);spec.loader.exec_module(atomic)
                reader=function(path.parent/'common.py','load_draft_thread',{'re':re,'json':json,'Path':Path})
                env={**keys,"Counter":Counter,"json":json,"hashlib":hashlib,"load_draft_thread":reader,"write_json_atomic":atomic.write_json_atomic,"argparse":NS(ArgumentParser=Parser),"WG_LIST_NAMES":{"RAN1":"RAN1"},"unit_path":lambda _:tdir,"derived_path":lambda _:derived,"audit_log_path":lambda:base/"audit","WORKSPACE_ROOT":base}
                for name in ('_record_errors','_frozen_signature','_expected_frozen','_verify'):
                    function(path,name,env)
                with contextlib.redirect_stdout(io.StringIO()): result=function(path,"main",env)()
                self.assertEqual(result,expected)
                checks=json.loads((base/"audit/normalization_integrity_RAN1.json").read_text())["checks"]
                self.assertEqual(checks[1]["pass"],not duplicated)
                self.assertEqual(checks[3]["pass"],not wrong_empty)

if __name__ == "__main__":unittest.main()
