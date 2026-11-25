#!/usr/bin/env python3
"""Prepare and verify the pinned local tokenizer used by original chunkers."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    pins_path = args.repository / 'scripts/common/common/local_model.py'
    spec = importlib.util.spec_from_file_location('retrieval_tokenizer_pins', pins_path)
    pins = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pins)
    files = ['config.json', 'tokenizer.json', 'tokenizer_config.json',
             'special_tokens_map.json', 'sentencepiece.bpe.model']
    os.environ['HF_HUB_OFFLINE'] = '0' if args.download else '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '0' if args.download else '1'
    from huggingface_hub import snapshot_download
    snapshot = Path(snapshot_download(pins.BGE_M3_REPO, revision=pins.BGE_M3_REVISION,
        allow_patterns=files, cache_dir=args.cache, local_files_only=not args.download))
    outcomes = []
    for name in files:
        data = (snapshot / name).read_bytes()
        expected = pins.BGE_M3_FILES[name]
        actual = (hashlib.sha256(data).hexdigest() if len(expected) == 64 else
                  hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest())
        if actual != expected:
            raise ValueError('Pinned tokenizer file differs: ' + name)
        outcomes.append({'path': name, 'bytes': len(data), 'pinned_digest': actual})
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    probe = tokenizer('SPECTRA source-bound retrieval', add_special_tokens=False)['input_ids']
    receipt = {'repository': pins.BGE_M3_REPO, 'revision': pins.BGE_M3_REVISION,
               'files': outcomes, 'all_pinned_files_matched': True,
               'local_tokenizer_probe_ids': probe, 'network_download_enabled': args.download,
               'scope': 'Five tokenizer/configuration files; original chunkers load this local cache without model inference.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
