#!/usr/bin/env python3
"""Reconstruct the exact enriched TTL from the preserved public base and patch.

No network is used unless --download-base is explicitly supplied. The base
file must match its recorded complete SHA256 before any output is created.
"""
import argparse,hashlib,json,urllib.request
from pathlib import Path
BASE_URL='https://raw.githubusercontent.com/spectra-ontology/spec-trace/71ff3b8be1093f093527520fb44f4554ce0850bb/release_package/kg/per_wg/RAN2-body.ttl'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--base-ttl',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--download-base',action='store_true');a.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parent);args=a.parse_args()
 m=json.loads((args.bundle/'provenance/snapshot_manifest.json').read_text())
 if args.output.exists():raise ValueError('refuse replacing output')
 if not args.base_ttl.exists():
  if not args.download_base:raise ValueError('supply preserved base TTL or --download-base')
  with urllib.request.urlopen(BASE_URL,timeout=120) as r,args.base_ttl.open('xb') as f:
   while b:=r.read(1024*1024):f.write(b)
 if sha(args.base_ttl)!=m['old_snapshot']['sha256']:raise ValueError('wrong preserved base TTL')
 patch=args.bundle/'source/CRPack_additions.ttl'
 if sha(patch)!=m['patch']['sha256']:raise ValueError('patch changed')
 with args.output.open('xb') as out:
  for p in (args.base_ttl,patch):
   with p.open('rb') as f:
    while b:=f.read(1024*1024):out.write(b)
 if sha(args.output)!=m['new_snapshot']['sha256'] or args.output.stat().st_size!=m['new_snapshot']['bytes']:raise ValueError('reconstructed source differs')
 print(json.dumps({'status':'PASS','new_snapshot_sha256':sha(args.output),'bytes':args.output.stat().st_size}))
if __name__=='__main__':main()
