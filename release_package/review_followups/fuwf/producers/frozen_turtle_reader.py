#!/usr/bin/env python3
"""Recount the S2 and S3 scenario figures on the released per-WG graphs.

S2 (cross-WG liaison statements) and S3 (change requests on TS 38.300) are
counted here on the five body-text graphs of the deposit, not on the
deployed per-WG KGs that `validation/cross_wg_use_evidence.json` was
measured on. Every count of that file is recounted, and the two sets of
figures are set side by side.

Run from release_package/ with the five RAN{1..5}-body.ttl files of the
Zenodo deposit in kg/per_wg/, or name their directory:
    python3 tests/reproduce_scenario_counts.py
    python3 tests/reproduce_scenario_counts.py --ttl-dir /path/to/deposit

Standard library only. Each file is read once as text and split into
subject blocks, one block per instance IRI, so that a type list wrapping
over several lines is read whole. Quoted literals and comments cannot
introduce predicates or subject blocks; escaped literal values are decoded.
The lexer follows the bundled export format, not arbitrary Turtle. Counted:

  ls_per_wg                instances typed spectra:LS, per graph
  ls_distinct_tdoc_number  distinct spectra:tdocNumber values over the LS
                           instances of all five graphs
  s2_ran1_ls_sent_to_ran2  distinct LS instances of the RAN1 graph with a
                           spectra:sentTo WorkingGroup whose spectra:wgName
                           is "RAN2"
  s2_ran1_ls_by_recipient  the same count for each recipient name listed in
                           queries[0] of the evidence file, and how many
                           unlisted recipient names reach the lowest listed
                           count
  ran2_ls_originated_from_ran1
                           distinct LS instances of the RAN2 graph with a
                           spectra:originatedFrom WorkingGroup whose
                           spectra:wgName is "RAN1", in total and for each
                           meeting listed in queries[1] (spectra:presentedAt,
                           matched on spectra:meetingNumber), with the same
                           unlisted count
  s3_ts_38_300             per RAN2 and RAN3 graph, distinct instances typed
                           spectra:CR with a spectra:modifies target Spec
                           whose spectra:specNumber is "38.300", split by
                           their spectra:type value

compared_with_deployed lists each count of the evidence file next to its
recount here. A count that differs there is a finding about the two
graphs, not a failure of this script.

The result is compared with validation/released_graph_scenario_counts.json
and the exit status is 1 on any difference; --write rewrites that file
instead. Exit status 2 means the graph files were not found.
"""
import argparse
import collections
from functools import lru_cache
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / 'validation' / 'released_graph_scenario_counts.json'
EVIDENCE = ROOT / 'validation' / 'cross_wg_use_evidence.json'
WGS = ['RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5']
SUBJ = '<https://w3id.org/spectra/inst/'
PREFIX = '@prefix spectra: <https://w3id.org/spectra#>'
IRI = re.compile(r'<([^>]*)>')
SPEC_NUMBER = '38.300'
TOKEN = re.compile(
    r'"""(?:\\.|(?!""")[^\\])*"""'
    r"|'''(?:\\.|(?!''')[^\\])*'''"
    r'|"(?:\\.|[^"\\])*"'
    r"|'(?:\\.|[^'\\])*'"
    r'|<(?:\\.|[^<>\\])*>'
    r'|\#[^\r\n]*'
    r'''|[^\s<>"'\#;,]+|[;,]''',
    re.DOTALL,
)
ESCAPE = re.compile(r'''\\(?:[tbnrf"'\\]|u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8})''')
QUOTE_START = re.compile(r'<[^<>]*>|#[^\r\n]*|"""|' + r"'''|\"|'")
QUOTE_END = {quote: re.compile(r'\\.|' + re.escape(quote))
             for quote in ('"', "'", '"""', "'''")}


@lru_cache(maxsize=1)
def export_tokens(text):
    """Keep literals and IRIs atomic in the export's subject-block format.

    This is a lexer for the bundled rdflib export, not a general Turtle
    parser. Comments cannot supply predicates, and literal content cannot
    become relationships. Cache only the current block for large graphs.
    """
    tokens, position = [], 0
    for match in TOKEN.finditer(text):
        if text[position:match.start()].strip():
            raise ValueError('Unsupported or malformed exported Turtle token')
        token = match.group()
        if not token.startswith('#'):
            tokens.append(token)
        position = match.end()
    if text[position:].strip():
        raise ValueError('Unsupported or malformed exported Turtle token')
    return tuple(tokens)


def decode_literal(token):
    width = 3 if token.startswith(('"""', "'''")) else 1
    value = token[width:-width]
    escapes = {'t': '\t', 'b': '\b', 'n': '\n', 'r': '\r', 'f': '\f',
               '"': '"', "'": "'", '\\': '\\'}

    def replace(match):
        escape = match.group()[1:]
        return chr(int(escape[1:], 16)) if escape[0] in ('u', 'U') else escapes[escape]

    return ESCAPE.sub(replace, value)


def quote_state(line, quote):
    """Track quoted literals across lines before recognizing a new subject."""
    position = 0
    while position < len(line):
        pattern = QUOTE_END[quote] if quote is not None else QUOTE_START
        match = pattern.search(line, position)
        if match is None:
            break
        token, position = match.group(), match.end()
        if quote is not None:
            if not token.startswith('\\'):
                quote = None
        elif token.startswith('#'):
            break
        elif not token.startswith('<'):
            quote = token
    return quote


def digests(path):
    md5, sha = hashlib.md5(), hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            md5.update(chunk)
            sha.update(chunk)
    return md5.hexdigest(), sha.hexdigest()


def blocks(path):
    """Yield (subject IRI, set of types, block text) for each instance."""
    cur, prefix_seen, quote = [], False, None
    with open(path, encoding='utf-8') as f:
        for line in f:
            if quote is None and line.startswith('@prefix') and line.split()[:3] == PREFIX.split()[:3]:
                prefix_seen = True
            if quote is None and line.startswith(SUBJ):
                if cur:
                    yield parse(cur)
                cur = [line]
            elif cur:
                cur.append(line)
            quote = quote_state(line, quote)
    if quote is not None:
        raise ValueError(f'{path.name}: unterminated Turtle literal')
    if not prefix_seen:
        raise SystemExit(f'{path.name}: no "{PREFIX}" declaration')
    if cur:
        yield parse(cur)


def parse(lines):
    text = ''.join(lines)
    subj = IRI.match(text).group(1)
    head = text.split(' ;', 1)[0]
    types = set()
    if ' a ' in head:
        types = {t.strip(' .\r\n\t') for t in head.split(' a ', 1)[1].split(',')}
    return subj, types, text


def objects(text, pred):
    tokens, found = export_tokens(text), []
    for index, token in enumerate(tokens):
        if token != pred:
            continue
        index += 1
        while index < len(tokens) and tokens[index].startswith('<'):
            found.append(tokens[index][1:-1])
            if index + 1 >= len(tokens) or tokens[index + 1] != ',':
                break
            index += 2
    return found


def literal(text, pred):
    tokens = export_tokens(text)
    for index, token in enumerate(tokens[:-1]):
        if token == pred and tokens[index + 1].startswith(('"', "'")):
            return decode_literal(tokens[index + 1])
    return None


def listed_and_rest(per_name, listed):
    """Counts for the listed names, and how many other names reach the lowest."""
    got = {name: len(per_name.get(name, ())) for name in listed}
    floor = min(got.values())
    rest = sum(1 for name, subjects in per_name.items()
               if name not in got and len(subjects) >= floor)
    return {'listed': got, 'unlisted_at_or_above_lowest_listed': rest}


def count(ttl_dir, evidence):
    q_sent, q_from, q_spec = evidence['queries']
    recipients = [row['wg'] for row in q_sent['result']]
    meetings = [row['mtg'] for row in q_from['top_meetings']]
    inputs, ls_per_wg, tdoc_numbers, s3 = {}, {}, set(), {}
    s2 = by_recipient = from_ran1 = None
    for wg in WGS:
        path = ttl_dir / f'{wg}-body.ttl'
        md5, sha = digests(path)
        inputs[wg] = {'file': path.name, 'bytes': path.stat().st_size, 'md5': md5, 'sha256': sha}
        n_ls, wg_name, spec_no, ls_sent, cr_mod = 0, {}, {}, [], []
        meeting_no, ls_from = {}, []
        for subj, types, text in blocks(path):
            if 'spectra:LS' in types:
                n_ls += 1
                number = literal(text, 'spectra:tdocNumber')
                tdoc_numbers.add(number if number is not None else subj)
                if wg == 'RAN1':
                    ls_sent.append((subj, objects(text, 'spectra:sentTo')))
                if wg == 'RAN2':
                    ls_from.append((subj, objects(text, 'spectra:originatedFrom'),
                                    objects(text, 'spectra:presentedAt')))
            if 'spectra:CR' in types and wg in ('RAN2', 'RAN3'):
                targets = objects(text, 'spectra:modifies')
                if targets:
                    cr_mod.append((subj, targets, literal(text, 'spectra:type')))
            if 'spectra:WorkingGroup' in types:
                wg_name[subj] = literal(text, 'spectra:wgName')
            if 'spectra:Spec' in types:
                spec_no[subj] = literal(text, 'spectra:specNumber')
            if 'spectra:Meeting' in types:
                meeting_no[subj] = literal(text, 'spectra:meetingNumber')
        ls_per_wg[wg] = n_ls
        if wg == 'RAN1':
            per_name = collections.defaultdict(set)
            for subj, targets in ls_sent:
                for t in targets:
                    if wg_name.get(t) is not None:
                        per_name[wg_name[t]].add(subj)
            s2 = len(per_name.get('RAN2', ()))
            by_recipient = listed_and_rest(per_name, recipients)
        if wg == 'RAN2':
            hit = [(subj, held) for subj, origins, held in ls_from
                   if any(wg_name.get(t) == 'RAN1' for t in origins)]
            per_meeting = collections.defaultdict(set)
            for subj, held in hit:
                for m in held:
                    if meeting_no.get(m) is not None:
                        per_meeting[meeting_no[m]].add(subj)
            from_ran1 = {'total': len({subj for subj, _ in hit}),
                         **listed_and_rest(per_meeting, meetings)}
        if wg in ('RAN2', 'RAN3'):
            specs = {s for s, n in spec_no.items() if n == SPEC_NUMBER}
            hit = {}
            for subj, targets, kind in cr_mod:
                if specs.intersection(targets):
                    hit[subj] = kind if kind is not None else '(no spectra:type)'
            s3[wg] = {'cr_instances': len(hit),
                      'spec_instances_with_number': len(specs),
                      'by_type': dict(sorted(collections.Counter(hit.values()).items()))}
    pairs = [(f'queries[0].result {row["wg"]}', row['n'], by_recipient['listed'][row['wg']])
             for row in q_sent['result']]
    pairs.append(('queries[1].total', q_from['total'], from_ran1['total']))
    pairs += [(f'queries[1].top_meetings {row["mtg"]}', row['n'], from_ran1['listed'][row['mtg']])
              for row in q_from['top_meetings']]
    pairs += [(f'queries[2].result {wg}', n, s3[wg]['cr_instances'])
              for wg, n in q_spec['result'].items()]
    return {
        'inputs': inputs,
        'ls_per_wg': ls_per_wg,
        'ls_total': sum(ls_per_wg.values()),
        'ls_distinct_tdoc_number': len(tdoc_numbers),
        's2_ran1_ls_sent_to_ran2': s2,
        's2_ran1_ls_by_recipient': by_recipient,
        'ran2_ls_originated_from_ran1': from_ran1,
        's3_ts_38_300': s3,
        'compared_with_deployed': [
            {'field': field, 'deployed': dep, 'released': rel, 'same': dep == rel}
            for field, dep, rel in pairs],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n', 1)[0])
    ap.add_argument('--ttl-dir', type=Path, default=ROOT / 'kg' / 'per_wg',
                    help='directory holding RAN{1..5}-body.ttl (default: kg/per_wg/)')
    ap.add_argument('--write', action='store_true',
                    help='rewrite validation/released_graph_scenario_counts.json')
    args = ap.parse_args()
    missing = [wg for wg in WGS if not (args.ttl_dir / f'{wg}-body.ttl').is_file()]
    if missing:
        print(f'graph files not found in {args.ttl_dir}: {missing}; '
              'they are in the Zenodo deposit, see kg/per_wg/README.md')
        return 2
    result = count(args.ttl_dir, json.loads(EVIDENCE.read_text()))
    if args.write:
        EXPECTED.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
        print(f'wrote {EXPECTED.relative_to(ROOT)}')
        return 0
    expected = json.loads(EXPECTED.read_text())
    bad = 0
    for key in sorted(set(expected) | set(result)):
        same = expected.get(key) == result.get(key)
        bad += not same
        print(f"[{'OK' if same else 'DIFF'}] {key}")
    print(f'=== {len(set(expected) | set(result)) - bad} of {len(set(expected) | set(result))} fields agree ===')
    rows = result['compared_with_deployed']
    print(f'compared with {EVIDENCE.relative_to(ROOT)} (deployed KGs):')
    for row in rows:
        mark = 'SAME' if row['same'] else 'DIFFERS'
        print(f"  [{mark}] {row['field']}: deployed {row['deployed']}, released {row['released']}")
    print(f"  {sum(r['same'] for r in rows)} of {len(rows)} counts are the same")
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
