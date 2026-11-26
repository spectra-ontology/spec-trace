#!/usr/bin/env python3
"""Verify, restore and replay one WG into a dedicated empty Neo4j 5.26.0."""
import argparse, json, os, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from snapshot import digest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--working-group",choices=[f"RAN{i}" for i in range(1,6)],required=True)
    p.add_argument("--bolt",required=True)
    p.add_argument("--matched-study",type=Path)
    p.add_argument("--output-directory",type=Path,required=True)
    args=p.parse_args();out=args.output_directory.resolve()
    if out.is_relative_to(HERE.parent): raise ValueError("Choose fresh receipts outside the preserved study")
    if out.exists() and any(out.iterdir()): raise ValueError("Choose an empty receipt output directory")
    out.mkdir(parents=True,exist_ok=True)
    group=args.working_group;common=["--working-group",group]
    run=lambda script,options: subprocess.run([sys.executable,"-B",str(HERE/script),*options],check=True)
    run("support.py",["verify",*common,"--output-directory",str(out)])
    run("snapshot.py",["restore",*common,"--bolt",args.bolt,"--output",str(out),"--confirm-empty-target"])
    run("support.py",["apply-indexes",*common,"--bolt",args.bolt,"--output-directory",str(out)])
    source_sha=digest(HERE/"source"/group/"manifest.json")
    matched_options=["--matched-study",str(args.matched_study)] if args.matched_study else []
    subprocess.run([sys.executable,"-B",str(HERE.parent/"replay_queries.py"),"--language","cypher",*common,
        "--bolt",group+"="+args.bolt,"--graph-identity","Fresh portable study input; "+group+" manifest SHA256 "+source_sha,
        "--out",str(out/(group+"-replay.json")),*matched_options],check=True)
    print(json.dumps({"workingGroup":group,"sourceManifestSha256":source_sha,"receiptDirectory":str(out)}))
if __name__=="__main__":main()
