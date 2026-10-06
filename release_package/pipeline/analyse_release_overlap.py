#!/usr/bin/env python3
"""Reproduce release-overlap statistics from the deposited SPECTRA body graphs.

Offline, standard library only; no model calls or database connection.
Both a subject-block parser and a separate line-state parser must produce
identical (working group, upload year, release, CR category) counts.

Run from any directory:
    python3 release_package/pipeline/analyse_release_overlap.py --ttl-dir /path/to/deposit
    python3 release_package/pipeline/analyse_release_overlap.py --ttl-dir /path/to/deposit --output /tmp/release_overlap.json

The five input SHA-256 values are fixed to the deposited snapshot. Missing
files or a hash mismatch exit with status 2 without writing a result.
The feature-CR leader is a descriptive, data-defined comparator, not a
release freeze date. See examples/PROCESS_REQUIREMENTS.md for interpretation.
"""
import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
TTL_DIR = PKG / 'kg' / 'per_wg'
WGS = ['RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5']
SUBJ = '<https://w3id.org/spectra/inst/'
IRI = re.compile(r'<([^>]*)>')
REL = re.compile(r'Rel_(\d+)$')
YEARS = range(2016, 2027)
EXPECTED_SHA256 = {'RAN1': '9540683df5407bb3f8978ad4d05ddc7f7880f10c94f21273f588d737f145e231', 'RAN2': 'f0997bbfb5fd5844837514cd29cfe943b8cb2d0240f0ea5579c5e69b4e547d6c', 'RAN3': 'd9791c08773a0e38b89869b3882d3098d879a37ddd7109630c346200d6776e95', 'RAN4': '90c6bf7d4420949b7395e8a0b5700a07f8866ddd461699d4516fe4e4f5deec5d', 'RAN5': '1ab414b785a155b58218a209be71ed9d1dacc1ea86ae13abbacfbaea27808f5e'}


def stream_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def blocks(path):
    cur = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            if line.startswith(SUBJ):
                if cur:
                    yield parse(cur)
                cur = [line]
            elif cur:
                cur.append(line)
    if cur:
        yield parse(cur)


def parse(lines):
    text = ' '.join(x.strip() for x in lines)
    subj = IRI.match(text).group(1)
    head = text.split(' ;', 1)[0]
    types = {t.strip(' .') for t in head.split(' a ', 1)[1].split(',')} if ' a ' in head else set()
    return subj, types, text


def objects(text, pred):
    m = re.search(re.escape(pred) + r' ((?:<[^>]*>(?:, )?)+)', text)
    return IRI.findall(m.group(1)) if m else []


def literal(text, pred):
    m = re.search(re.escape(pred) + r' "([^"]*)"', text)
    return m.group(1) if m else None


def classify(is_cr, ctype, rels, up):
    """One record -> (year, release) or an exclusion reason."""
    if not is_cr:
        return None
    if ctype != 'CR':
        return 'not_formal'
    nums = [int(REL.search(r).group(1)) for r in rels if REL.search(r)]
    if len(nums) != 1:
        return 'release_missing_or_multiple'
    if not up or not up[:4].isdigit() or int(up[:4]) not in YEARS:
        return 'date_missing_or_outside_window'
    return int(up[:4]), nums[0]


def first_pass(wg):
    agg, excl = collections.Counter(), collections.Counter()
    for subj, types, text in blocks(TTL_DIR / f'{wg}-body.ttl'):
        ctype, rels, up = literal(text, 'spectra:type'), objects(text, 'spectra:targetRelease'), literal(text, 'spectra:uploadedDate')
        if ctype == 'CR' and 'spectra:CR' not in types:
            excl['type_literal_CR_without_CR_class'] += 1
            if not isinstance(classify(True, ctype, rels, up), str):
                excl['type_literal_CR_without_CR_class_but_usable'] += 1
        r = classify('spectra:CR' in types, ctype, rels, up)
        if r is None:
            continue
        if isinstance(r, str):
            excl[r] += 1
            continue
        agg[(r[0], r[1], literal(text, 'spectra:crCategory'))] += 1
    return agg, excl


def second_pass(wg):
    """Line state machine: subject lines start a record; property lines are matched individually (no block join)."""
    type_line = re.compile(r'^\s+a\s+(.*?)\s*[;.]\s*$')
    lit_line = re.compile(r'^\s+spectra:(type|uploadedDate|crCategory)\s+"([^"]*)"')
    rel_line = re.compile(r'^\s+spectra:targetRelease\s+(.*?)\s*[;.]\s*$')
    agg = collections.Counter()

    def flush(rec):
        if rec is None:
            return
        r = classify(rec['cr'], rec.get('type'), rec['rels'], rec.get('uploadedDate'))
        if r is not None and not isinstance(r, str):
            agg[(r[0], r[1], rec.get('crCategory'))] += 1

    def take_types(rec, part):
        part = part.strip()
        rec['in_types'] = part.endswith(',')
        rec['cr'] = rec['cr'] or 'spectra:CR' in [t.strip(' ;.') for t in part.split(',')]

    rec = None
    with open(TTL_DIR / f'{wg}-body.ttl', encoding='utf-8') as f:
        for line in f:
            if line.startswith(SUBJ):
                flush(rec)
                rest = line.split('>', 1)[1]
                rec = {'cr': False, 'rels': [], 'in_types': False}
                m = re.match(r'\s+a\s+(.*)$', rest)
                if m:
                    take_types(rec, m.group(1))
                continue
            if rec is None:
                continue
            if rec['in_types']:
                take_types(rec, line)
                continue
            m = type_line.match(line)
            if m:
                take_types(rec, m.group(1))
                continue
            m = lit_line.match(line)
            if m:
                rec.setdefault(m.group(1), m.group(2))
                continue
            m = rel_line.match(line)
            if m:
                rec['rels'] += IRI.findall(m.group(1))
    flush(rec)
    return agg


def stats(agg):
    feat = collections.defaultdict(collections.Counter)
    for (y, r, c), n in agg.items():
        if c == 'B':
            feat[y][r] += n
    lead = {y: max(cnt.items(), key=lambda kv: (kv[1], kv[0]))[0] for y, cnt in feat.items()}
    used = older = newer = 0
    by_cat = collections.defaultdict(lambda: [0, 0])
    by_year = {}
    for (y, r, c), n in agg.items():
        if y not in lead:
            continue
        used += n
        o = r < lead[y]
        older += n * o
        newer += n * (r > lead[y])
        by_cat[c or 'none'][0] += n * o
        by_cat[c or 'none'][1] += n
        by_year.setdefault(y, [0, 0])
        by_year[y][0] += n * o
        by_year[y][1] += n
    total = sum(agg.values())
    return {
        'formal_crs_dated': total,
        'formal_crs_in_years_with_a_lead': used,
        'older_than_lead': older,
        'years_without_a_lead': sorted({y for (y, r, c) in agg} - set(lead)),
        'lead_release_by_year': {str(y): f'Rel-{lead[y]}' for y in sorted(lead)},
        'older_than_lead_share': round(older / used, 4) if used else None,
        'newer_than_lead_share': round(newer / used, 4) if used else None,
        'older_than_lead_share_by_category': {c: {'n': v[1], 'share': round(v[0] / v[1], 4)} for c, v in sorted(by_cat.items())},
        'older_than_lead_share_by_year': {str(y): {'n': v[1], 'share': round(v[0] / v[1], 4)} for y, v in sorted(by_year.items())},
    }


DEFINITIONS = {'formal_cr': 'subject typed spectra:CR whose spectra:type literal is CR (draftCR and pCR excluded)', 'lead_release': 'per working group and upload year, the target release with the most category B (feature) formal CRs; ties go to the newer release', 'older_than_lead_share': "formal CRs whose target release is older than that year's lead, over formal CRs in years that have a lead"}

INTERPRETATION_LIMITS = ['the same change-request fields exist in the 3GPP CR database; the finding shows what the released graph supports, not something only its links can compute', 'the lead release is inferred from feature change requests in the data, not from release freeze dates', 'RAN5 has many formal CRs without an upload date and too few feature CRs to set a lead in some years', 'subjects whose type literal is CR but that lack the spectra:CR class carry no single target release, so a class-free definition gives the same records (asserted)']


def analyse(ttl_dir):
    global TTL_DIR
    TTL_DIR = ttl_dir
    missing = [f'{wg}-body.ttl' for wg in WGS if not (TTL_DIR / f'{wg}-body.ttl').is_file()]
    if missing:
        raise ValueError('Missing deposited body-text files: ' + ', '.join(missing)
                         + '. See release_package/kg/per_wg/README.md.')
    inputs, per_wg, coverage = {}, {}, {}
    for wg in WGS:
        path = TTL_DIR / f'{wg}-body.ttl'
        sha = stream_sha256(path)
        if sha != EXPECTED_SHA256[wg]:
            raise ValueError(f'{wg}: SHA-256 mismatch; expected {EXPECTED_SHA256[wg]}, got {sha}')
        inputs[wg] = {'file': path.name, 'sha256': sha}
        first, excluded = first_pass(wg)
        second = second_pass(wg)
        if first != second:
            raise ValueError(f'{wg}: the two parsers disagree')
        if excluded.get('type_literal_CR_without_CR_class_but_usable'):
            raise ValueError(f'{wg}: omitting the CR class condition would add usable records')
        per_wg[wg] = stats(first)
        coverage[wg] = {'excluded': dict(sorted(excluded.items())),
                        'used_dated_formal': sum(first.values())}
    used = sum(per_wg[wg]['formal_crs_in_years_with_a_lead'] for wg in WGS[:4])
    older = sum(per_wg[wg]['older_than_lead'] for wg in WGS[:4])
    return {
        'purpose': 'Descriptive release-overlap analysis of formal change requests in the deposited snapshot.',
        'manifest': {
            'type': 're-analysis',
            'llm_calls': 0,
            'database_calls': 0,
            'snapshot': 'SpectraCQ v2.0 / snapshot v2.0.0',
            'version_doi': '10.5281/zenodo.21504833',
            'method': 'Independent subject-block and line-state parsers, with fixed input SHA-256 checks.',
            'ttl_inputs': inputs,
        },
        'definitions': DEFINITIONS,
        'second_parser_agrees': True,
        'per_wg': per_wg,
        'coverage': coverage,
        'pooled_ran1_to_ran4': {'formal_crs': used, 'older_than_lead': older,
                               'share': round(older / used, 4)},
        'interpretation_limits': INTERPRETATION_LIMITS,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ttl-dir', type=Path, default=PKG / 'kg' / 'per_wg',
                        help='directory containing the five deposited RAN{1..5}-body.ttl files')
    parser.add_argument('--output', type=Path,
                        help='write the result to this path; otherwise print JSON to stdout')
    args = parser.parse_args()
    try:
        payload = analyse(args.ttl_dir)
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    output = json.dumps(payload, indent=2, ensure_ascii=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding='utf-8')
        print(f'Wrote {args.output}')
        print(json.dumps(payload['pooled_ran1_to_ran4']))
    else:
        print(output, end='')
    return 0


if __name__ == '__main__':
    sys.exit(main())
