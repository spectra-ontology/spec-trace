#!/usr/bin/env python3
"""Source-bound native index support and complete portable-input preflight."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, sys
from datetime import datetime, timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import snapshot as adapter

def credentials(args):
    return os.environ[args.user_env],os.environ[args.password_env]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("capture-indexes","apply-indexes","verify"))
    parser.add_argument("--working-group",choices=adapter.GROUPS,required=True)
    parser.add_argument("--bolt")
    parser.add_argument("--user-env",default="NEO4J_USER")
    parser.add_argument("--password-env",default="NEO4J_PASSWORD")
    parser.add_argument("--cq-tools",type=Path)
    parser.add_argument("--output-directory",type=Path)
    args=parser.parse_args()
    group=args.working_group; directory=HERE/"source"/group
    helper=adapter.helper_directory(args.cq_tools)
    if args.mode=="verify":
        manifest=adapter.load(directory/"manifest.json"); study=manifest["query_study"]
        for filename,key in (("graph_snapshot.py","serializerSha256"),("runner.py","runnerSha256")):
            if adapter.digest(helper/filename)!=study[key]: raise ValueError("Helper source digest differs: "+filename)
        if adapter.digest(HERE/"snapshot.py")!=study["adapterSha256"]:
            raise ValueError("Adapter source differs from captured adapter")
        binding=adapter.load(directory/"definition_binding.json")
        if binding["definition_contract"]!=study["definition_contract"]: raise ValueError("Definition binding differs")
        observation=(HERE/binding["schema_token_observations"]["path"]).resolve()
        if not observation.is_relative_to(directory.resolve()) or adapter.digest(observation)!=binding["schema_token_observations"]["sha256"]:
            raise ValueError("Schema observation path or digest differs")
        label=(directory/manifest["label_order"]["path"]).resolve()
        if not label.is_relative_to(directory.resolve()) or adapter.digest(label)!=manifest["label_order"]["sha256"]:
            raise ValueError("Label observation path or digest differs")
        for kind,record in manifest["records"].items():
            comparison=study["topologyComparison"][kind]
            if not comparison["allTopologyRecordsEqual"] or comparison["recordsCompared"]!=manifest["before_counts"][kind]:
                raise ValueError("Topology coverage differs")
        receipt={"workingGroup":group,"sourceManifestSha256":adapter.digest(directory/"manifest.json"),
            "definitionBindingSha256":adapter.digest(directory/"definition_binding.json"),
            "indexSupportSha256":adapter.digest(HERE/"index_support"/(group+".json")),
            "helperSourcesVerified":True,"schemaAndLabelSidecarDigestsVerified":True,
            "allSourceTopologyRowsCompared":True,"checkedUtc":datetime.now(timezone.utc).isoformat()}
        if args.output_directory is not None:
            target=args.output_directory/(group+"-source-verification.json")
            if target.exists(): raise ValueError("Preserve an existing input verification receipt")
            adapter.save(target,receipt)
        print(json.dumps(receipt)); return
    if not args.bolt: parser.error("Supply --bolt")
    from neo4j import GraphDatabase,READ_ACCESS
    with GraphDatabase.driver(args.bolt,auth=credentials(args)) as driver:
        with driver.session(default_access_mode=READ_ACCESS if args.mode=="capture-indexes" else "WRITE") as session:
            version=session.run("CALL dbms.components() YIELD name,versions RETURN name,versions").data()
            if not any(row["name"]=="Neo4j Kernel" and row["versions"]==["5.26.0"] for row in version):
                raise ValueError("Use the study's Neo4j 5.26.0")
            if args.mode=="capture-indexes":
                target=HERE/"index_support"/(group+".json")
                if target.exists(): raise ValueError("Preserve existing index source capture")
                rows=session.run("SHOW INDEXES YIELD name,type,entityType,labelsOrTypes,properties RETURN name,type,entityType,labelsOrTypes,properties ORDER BY name").data()
                adapter.save(target,{"format":"spectra-native-query-index-support-1","workingGroup":group,
                    "capturedUtc":datetime.now(timezone.utc).isoformat(),"components":version,"indexes":rows,
                    "scope":"Read-only source index inventory; range indexes over preserved properties can support replay performance."})
                print(json.dumps({"capturedIndexes":group,"count":len(rows)})); return
            source=adapter.load(HERE/"index_support"/(group+".json"))
            manifest=adapter.load(directory/"manifest.json")
            actual={"nodes":session.run("MATCH (n) RETURN count(n) AS n").single()["n"],
                    "relationships":session.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"]}
            if actual!=manifest["before_counts"]: raise ValueError("Index target population differs from restored study input")
            quote=lambda value:"`"+value.replace("`","``")+"`"
            applied=[]; whitelist=set(manifest["dependency"]["properties"])
            for index in source["indexes"]:
                if index["type"]!="RANGE" or not index["properties"] or not set(index["properties"]).issubset(whitelist): continue
                labels=index["labelsOrTypes"]
                if len(labels)!=1: raise ValueError("Review non-single-token range index")
                pattern="(n:"+quote(labels[0])+")" if index["entityType"]=="NODE" else "()-[n:"+quote(labels[0])+"]-()"
                query="CREATE RANGE INDEX "+quote(index["name"])+" IF NOT EXISTS FOR "+pattern+" ON ("+", ".join("n."+quote(prop) for prop in index["properties"])+")"
                session.run(query).consume(); applied.append({"name":index["name"],"statement":query})
            session.run("CALL db.awaitIndexes(1800)").consume()
            receipt={"workingGroup":group,"indexSourceSha256":adapter.digest(HERE/"index_support"/(group+".json")),
                "sourceManifestSha256":adapter.digest(directory/"manifest.json"),"components":version,
                "appliedProjectedPropertyIndexes":applied,"finishedUtc":datetime.now(timezone.utc).isoformat()}
            target=(args.output_directory or HERE/"receipts")/(group+"-index-restore.json")
            if target.exists(): raise ValueError("Preserve existing index restore receipt")
            adapter.save(target,receipt); print(json.dumps({"appliedIndexes":group,"count":len(applied)}))
if __name__=="__main__": main()
