"""Compare actually returned tool text with every assigned packet field."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
decoder = json.JSONDecoder()

def strings(value):
    if isinstance(value, str):
        yield value
        try:
            decoded = json.loads(value)
        except (ValueError, TypeError):
            decoded = None
        if decoded is not None and decoded != value:
            yield from strings(decoded)
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from strings(v)

def leaves(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from leaves(v)
    elif isinstance(value, list):
        for v in value:
            yield from leaves(v)
    elif isinstance(value, str):
        yield value

reports = []
for p in sorted((HERE / 'provenance').glob('*.json')):
    provenance = json.loads(p.read_text())
    run = next(r for r in json.loads((HERE / 'schedule.json').read_text()) if r['runId'] == provenance['runId'])
    packet_path = HERE / run['packet']
    header, body = packet_path.read_text().split('\n\n', 1)
    groups = json.loads(body)
    returned = []
    for line in Path(provenance['traceFile']).read_text().splitlines():
        record = json.loads(line)
        payload = record.get('payload', {})
        if payload.get('type') in {'function_call_output', 'custom_tool_call_output'}:
            returned.extend(strings(payload.get('output')))
    # Also parse JSON substrings embedded in returned shell output. Escaped schema
    # newlines and Unicode must be decoded before exact leaf matching.
    decoded_strings = list(returned)
    for text in returned:
        for start, char in enumerate(text):
            if char not in '[{':
                continue
            try:
                value, _ = decoder.raw_decode(text[start:])
            except ValueError:
                continue
            decoded_strings.extend(strings(value))
    visible = '\n'.join(decoded_strings)
    groups_report = []
    for group in groups:
        missing = [x for x in leaves(group) if x not in visible]
        missing_items = [i['id'] for i in group['items'] if any(x not in visible for x in leaves(i))]
        missing_schema_lines = [line for line in group['schema'].splitlines() if line not in visible]
        groups_report.append({'wg': group['wg'], 'missingExactLeafCount': len(missing),
                              'missingItemFields': missing_items, 'missingLeaves': missing,
                              'missingNonSchemaLeaves': [x for x in missing if x != group['schema']],
                              'missingSchemaLines': missing_schema_lines,
                              'schemaLineCoverage': 'Each exact schema line searched across actual returned text; may span separate readings or shared schemas.'})
    reports.append({'runId': run['runId'], 'traceSha256': provenance['traceSha256'],
                    'packetSha256': hashlib.sha256(packet_path.read_bytes()).hexdigest(),
                    'groups': groups_report,
                    'allAssignedPacketLeavesObserved': all(not g['missingLeaves'] for g in groups_report),
                    'allItemsAndSchemaLinesObserved': all(not g['missingNonSchemaLeaves'] and not g['missingSchemaLines'] for g in groups_report),
                    'scope': 'Exact packet string leaves in actual returned tool outputs; separate from comprehension or OS isolation.'})
(HERE / 'input_exposure_audit.json').write_text(json.dumps({'runs': reports}, indent=2) + '\n')
print(json.dumps({'runs': len(reports), 'complete': sum(r['allAssignedPacketLeavesObserved'] for r in reports),
                  'flagged': [r['runId'] for r in reports if not r['allAssignedPacketLeavesObserved']]}))
