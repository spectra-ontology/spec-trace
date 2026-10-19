"""Extract pinned saved evidence and run its offline verifier in isolation."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile

ARCHIVE_SHA256 = 'ce57bae4d744c5a5c380348e46519e1adc4873dc898ce99f1c3368283e891591'
VERIFIER_SHA256 = '96ae9cf7807be40d8609080c1a31de2f9a8c94ecc855c8daa10d36888d345ba8'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--source-evidence', type=Path)
    args = parser.parse_args()
    home = Path(__file__).resolve().parent
    source_evidence = (args.source_evidence or home.parent/'original_core_source_RAN1_common3176').resolve(strict=True)
    archive = home/'evidence.tar.gz'
    if sha(archive) != ARCHIVE_SHA256:
        raise ValueError('Saved evidence archive changed')
    manifest = json.loads((home/'manifest.json').read_text())
    for entry in manifest['files']:
        relative = PurePosixPath(entry['path'])
        if relative.is_absolute() or any(x in {'.', '..'} for x in relative.parts):
            raise ValueError('Manifest path must be relative and contained')
        path = home/relative
        if path.is_symlink() or not path.resolve().is_relative_to(home):
            raise ValueError('Manifest path escapes bundle')
        if sha(path) != entry['sha256'] or path.stat().st_size != entry['bytes']:
            raise ValueError('Package file changed: '+entry['path'])
    output = args.output.resolve()
    if output.is_relative_to(home):
        raise ValueError('Unpack outside the immutable package')
    if output.exists():
        raise FileExistsError('Choose a new output directory')
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        names = set()
        for member in members:
            path = PurePosixPath(member.name)
            if (not member.isfile() or path.is_absolute() or not path.parts or
                    any(x in {'.', '..'} for x in path.parts) or member.name in names):
                raise ValueError('Unsafe or duplicate archive member')
            names.add(member.name)
        if len(members) != 199:
            raise ValueError('Unexpected included evidence inventory')
        output.mkdir(parents=True)
        for member in members:
            path = output/member.name
            path.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as source, path.open('xb') as dest:
                dest.write(source.read())
    if sha(output/'verify_saved_outputs.py') != VERIFIER_SHA256:
        raise ValueError('Saved-output verifier changed')
    result = subprocess.run([sys.executable, '-B', '-I', str(output/'verify_saved_outputs.py'), '--source-evidence', str(source_evidence)],
                            capture_output=True, text=True, timeout=60)
    receipt = {'archive_sha256': ARCHIVE_SHA256, 'included_files': len(names),
               'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr,
               'new_API_calls': 0, 'native_operations': 0, 'generated_query_executions': 0}
    (output.parent/(output.name+'.verification.json')).write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    if result.returncode:
        raise RuntimeError(result.stderr)
    print(result.stdout.strip())


if __name__ == '__main__':
    main()
