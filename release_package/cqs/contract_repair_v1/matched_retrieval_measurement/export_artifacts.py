#!/usr/bin/env python3
"""Create a public allowlist copy from an explicitly supplied completed study.

No models, database queries or scoring. Host paths and transport logs are not
published. All original source hashes are retained in the build registry.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

BASE=Path(__file__).resolve().parent
USAGE_KEYS=('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens')
CALL_KEYS=('number','label','component','model_requested','effort','prompt','prompt_sha256','schema',
           'started_unix','finished_unix','seconds','output','system_prompt_visibility','internal_provider_retries')
EXEC_KEYS=('status','error_class','rows','columns','row_count_retained','truncated','started_utc','finished_utc','elapsed_s')
PRIVATE_PATTERN=re.compile(r'/home/[^\s"\x27]+|/mnt/[a-zA-Z]/|/root/|(?:sk-proj-|sk-ant-api\d+-)[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9_.-]{20,}')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def safe_check(raw,name):
    if PRIVATE_PATTERN.search(raw.decode('utf-8')):
        raise ValueError('Private path or credential-shaped material detected in '+name)


def write(path,raw):
    safe_check(raw,path.name)
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=raw:
            raise ValueError('Refusing to replace different existing public bytes: '+path.name)
        return
    with path.open('xb') as stream:
        stream.write(raw)


def encoded(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()


def failure(error):
    if not error:
        return None
    text=str(error).lower()
    for needles,category in ((('timeout','timed out'),'timeout'),(('tool action',),'tool_use'),
                             (('cap','budget'),'call_budget'),(('query execution',),'query_execution'),
                             (('helper',),'helper_failure')):
        if any(needle in text for needle in needles):
            return category
    return 'generation_or_prediction_failure'


def public_call(raw):
    result={k:raw.get(k) for k in CALL_KEYS}
    result['error_category']=failure(raw.get('error'))
    result['usage_events']=[{'type':'turn.completed','usage':{k:v for k,v in event.get('usage',{}).items()
                             if k in USAGE_KEYS and type(v) is int}}
                             for event in raw.get('usage_events',[]) if event.get('type')=='turn.completed']
    return result


def provenance_paths(value):
    if isinstance(value,list):
        return [provenance_paths(child) for child in value]
    if isinstance(value,dict):
        return {key:provenance_paths(child) for key,child in value.items() if key not in ('uri','server','password','credentials')}
    if isinstance(value,str) and value.startswith(('/home/','/tmp/','/root/','/mnt/')):
        return Path(value).name
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',type=Path,required=True)
    parser.add_argument('--primary-source',type=Path,required=True)
    args=parser.parse_args()
    registry=[]
    def copy(source,destination,transform=None,description='byte-identical allowlist copy'):
        raw=source.read_bytes()
        public=raw if transform is None else encoded(transform(json.loads(raw)))
        target=BASE/destination
        write(target,public)
        registry.append({'public_path':destination,'public_sha256':sha(target),
                         'original_source_sha256':hashlib.sha256(raw).hexdigest(),
                         'original_source_filename':source.name,'transformation':description})
    stage=args.study/'public_export_v1'
    manifest=read(stage/'export_manifest_v1.json')
    for row in manifest['files']:
        source=stage/row['path']
        if sha(source)!=row['sha256']:
            raise ValueError('Staged allowlist file hash mismatch')
        copy(source,row['path'])
    copy(stage/'export_manifest_v1.json','provenance/source_export_manifest_v1.json')
    for source in sorted((args.study/'calls').glob('*.reservation.json')):
        raw=read(source)
        if set(raw)!={'number','label','component','reserved_unix'}:
            raise ValueError('Unexpected reservation keys')
        copy(source,'calls/'+source.name)
    for source in sorted((args.study/'calls').glob('*_*.json')):
        raw=read(source)
        if raw['component']=='kg':
            copy(source,'calls/'+source.name,public_call,'Explicit caller/usage/error-category allowlist; transport/events/host command removed')
    for source in sorted((args.study/'predictions/structured').glob('*.json')):
        def receipt(raw):
            keys=('id','original_id','variant_id','wg','arm','call_number','generated_query','generation_abstain','prediction')
            result={k:raw[k] for k in keys if k in raw}
            result['error_category']=failure(raw.get('error'))
            execution=raw.get('execution') or {}
            result['execution']={k:execution[k] for k in EXEC_KEYS if k in execution}
            return result
        copy(source,'predictions/structured/'+source.name,receipt,'Structured receipt allowlist; raw errors/auth/server/host paths omitted')
    reader_source=args.study/'frozen_run_manifest.json'
    def reader(raw):
        result=provenance_paths(raw)
        result['original_manifest_sha256']=sha(reader_source)
        result['export_transformation']='Filesystem provenance paths reduced to filenames; scientific wording/contracts/flags/guards unchanged'
        return result
    copy(reader_source,'frozen_run_manifest.json',reader,'Filesystem provenance sanitization; original manifest SHA retained')
    structured_source=args.study/'frozen_structured_manifest.json'
    def structured(raw):
        result=provenance_paths(raw)
        result['public_directory']='..'
        result['original_manifest_sha256']=sha(structured_source)
        result['original_retrieval_manifest_sha256']=raw['retrieval_manifest_sha256']
        result['retrieval_manifest_sha256']=sha(BASE/'frozen_run_manifest.json')
        result['export_transformation']='Filesystem provenance sanitized; reader pointer reanchored to sanitized public file, original pointer retained'
        return result
    copy(structured_source,'frozen_structured_manifest.json',structured,'Sanitized public reader pointer with both original manifest SHA values preserved')
    for name in ('frozen_analysis_manifest.json','corpus_readiness_v1_attempt.json','corpus_readiness_v2.json','completed_retrieval_audit_v1.json'):
        source=args.study/name
        def audit(raw,source=source):
            result=provenance_paths(raw)
            result['original_source_sha256']=sha(source)
            result['export_transformation']='Host filesystem provenance reduced to filenames; actual observed results and bounds preserved'
            return result
        copy(source,'provenance/'+name,audit,'Host provenance sanitized; actual audit data and original source SHA preserved')
    for name in ('scientific_analysis_protocol.json','protocol_matched_structured.json'):
        copy(args.primary_source/name,name)
    copy(args.primary_source/'protocol_matched_retrieval.json','implementation/protocol_matched_retrieval.json')
    code_source=args.primary_source/'matched_retrieval.py'
    original=code_source.read_text()
    old="ROOT = next(p for p in BASE.parents if (p / '.git').exists())\nOUT = ROOT / 'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/baseline-runs/_matched_retrieval_v1'"
    new="OUT = Path(os.environ.get('KDD_MATCHED_OUTPUT', str(BASE.parent / 'local_run')))"
    if original.count(old)!=1:
        raise ValueError('Portable code replacement guard failed')
    target=BASE/'implementation/matched_retrieval.py'
    write(target,original.replace(old,new).encode())
    registry.append({'public_path':'implementation/matched_retrieval.py','public_sha256':sha(target),
                     'original_source_sha256':sha(code_source),'original_source_filename':code_source.name,
                     'transformation':'Replace project/.git-dependent output location with explicit KDD_MATCHED_OUTPUT or local_run; retrieval/prompt/schema/caller algorithms unchanged'})
    copy(args.primary_source/'test_matched_retrieval.py','implementation/test_matched_retrieval.py')
    write(BASE/'publication_build_registry_v1.json',encoded({'classification':'Public artifact transformation registry; not a new measurement',
              'export_tool_sha256':sha(__file__),'source_manifest_sha256':sha(stage/'export_manifest_v1.json'),
              'files':registry,'public_release_completed':False,
              'bounds':['Primary private source/fixtures/results were not changed.',
                        'Published transformed code is not byte-identical to the original generation runner.',
                        'Full 19.78GB/18.42GiB SQLite ranking corpus is not included.']}))
    print(json.dumps({'copied_files':len(registry),'registry_sha256':sha(BASE/'publication_build_registry_v1.json')}))


if __name__=='__main__':
    main()
