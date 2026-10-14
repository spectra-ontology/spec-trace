#!/usr/bin/env python3
"""Verify and replay the compact complete SQL experiment without credentials."""
import hashlib
import json
from pathlib import Path,PurePosixPath
import subprocess
import sys
import tarfile
import tempfile

BASE=Path(__file__).resolve().parent


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    manifest=json.loads((BASE/'manifest.json').read_text())
    for name,expected in manifest['files'].items():
        if Path(name).name!=name or sha(BASE/name)!=expected:
            raise ValueError('Public archive membership or hashes differ')
    with tempfile.TemporaryDirectory(prefix='spectra-sql-replay-') as temporary:
        root=Path(temporary)
        with tarfile.open(BASE/'evidence.tar.gz','r:gz') as archive:
            names=set()
            for member in archive.getmembers():
                parts=PurePosixPath(member.name).parts
                if (not member.isfile() or member.name in names or not parts or parts[0]!='evidence'
                        or '..' in parts or '\\' in member.name or member.name.startswith('/')):
                    raise ValueError('Unsafe or duplicate archived evidence member')
                names.add(member.name)
                target=root/member.name
                target.parent.mkdir(parents=True,exist_ok=True)
                source=archive.extractfile(member)
                with target.open('xb') as stream:
                    while chunk:=source.read(1024*1024):
                        stream.write(chunk)
        evidence=root/'evidence'
        if sha(evidence/'portable_manifest.json')!=manifest['expanded_manifest_sha256']:
            raise ValueError('Expanded frozen evidence manifest differs')
        result=subprocess.run([sys.executable,'-B','-S',str(evidence/'verify_portable.py'),
                               '--evidence',str(evidence)],capture_output=True,text=True)
        if result.returncode:
            raise ValueError(result.stderr)
        report=json.loads(result.stdout)
        if report['status']!='PASS' or report['cohort_n']!=378:
            raise ValueError('Strict replay did not pass full cohort')
        print(json.dumps({'status':'PASS','archive_sha256':manifest['archive_sha256'],
                          'expanded_manifest_sha256':manifest['expanded_manifest_sha256'],
                          'strict_replay':report,'new_model_calls':0,'new_database_executions':0}))


if __name__=='__main__':
    main()
