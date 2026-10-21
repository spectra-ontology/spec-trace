"""Compare literal Cypher regex semantics and complete-record scoring controls."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def unquote(value):
    out, index = [], 0
    translations = {'\\': '\\', 'n': '\n', 'r': '\r', 't': '\t', 'b': '\b', 'f': '\f', "'": "'", '"': '"'}
    while index < len(value):
        if value[index] == '\\':
            index += 1
            if index == len(value) or value[index] not in translations:
                raise ValueError('unexpected Cypher escape')
            out.append(translations[value[index]])
        else:
            out.append(value[index])
        index += 1
    return ''.join(out)

def captured_cypher_regex(query, target):
    patterns = []
    for line in query.splitlines():
        if 'line =~ ' not in line:
            continue
        expr = line.split('line =~ ', 1)[1]
        fragments = []
        for match in re.finditer(r"'((?:\\.|[^'])*)'|c\.tdocNumber", expr):
            fragments.append(target if match.group(0) == 'c.tdocNumber' else unquote(match.group(1)))
        patterns.append(''.join(fragments))
    if len(patterns) != 6:
        raise ValueError('unexpected actual query predicate layout')
    return patterns

def literal_cypher_approves(query, content, target):
    transition, direct, post, previous, negative, conditional = captured_cypher_regex(query, target)
    for line in (content or '').split('\n'):
        if re.fullmatch(transition, line):
            break
        if ((re.fullmatch(direct, line) or re.fullmatch(post, line))
                and not re.fullmatch(previous, line)
                and not re.fullmatch(negative, line)
                and not re.fullmatch(conditional, line)):
            return True
    return False

def run():
    rule = load('technical_approval_rule_frozen', HERE / 'technical_approval_rule_v4.py')
    query = (HERE / 'reference_technical_approval_v5.cypher').read_text()
    x = json.loads(gzip.decompress((HERE / 'actual_frozen_full_input_v1.json.gz').read_bytes()))
    a = {row['node_id']: row for row in x['Agreement']}
    c = {row['node_id']: row for row in x['CR']}
    checks = []
    for u, v in x['REFERENCES']:
        if u not in a or v not in c:
            continue
        wanted = bool(rule.approves(a[u]['content'], c[v]['tdocNumber']))
        actual = literal_cypher_approves(query, a[u]['content'], c[v]['tdocNumber'])
        if wanted != actual:
            raise ValueError(('literal query regex differs', a[u]['resolutionId'], c[v]['tdocNumber']))
        checks.append({'resolutionId': a[u]['resolutionId'], 'tdocNumber': c[v]['tdocNumber'], 'approval_object': wanted})
    cases = [
        ('current_CR_object', 'Agree the stage 2 CR in R3-900001.', 'R3-900001', True),
        ('direct_CR_list_first', 'Agree the XnAP CR R3-900001 and R3-900002 to support the update.', 'R3-900001', True),
        ('direct_CR_list_second', 'Agree the XnAP CR R3-900001 and R3-900002 to support the update.', 'R3-900002', True),
        ('current_revision', 'Agree the Rel-16 F1AP CR (R3-900002 revision of R3-900001), taking comments into account.', 'R3-900002', True),
        ('old_revision', 'Agree the Rel-16 F1AP CR (R3-900002 revision of R3-900001), taking comments into account.', 'R3-900001', False),
        ('separate_semicolon_clause', 'Agree the CR R3-900001; R3-900002 is discussed.', 'R3-900002', False),
        ('separate_sentence', 'Agree the CR R3-900001. R3-900002 is discussed.', 'R3-900002', False),
        ('different_object_with_note', 'Agree the CR R3-900001 and note the CR R3-900002.', 'R3-900002', False),
        ('different_object_with_revision', 'Agree the CR R3-900001, revise the CR R3-900002.', 'R3-900002', False),
        ('future_preparation', 'Agree to prepare the CR R3-900001.', 'R3-900001', False),
        ('affirmative_provision_not_CR_object', 'Agree Option 1 and report the CR R3-900001.', 'R3-900001', False),
        ('postposed_CR_object', 'The CR R3-900001 is agreed.', 'R3-900001', True),
        ('postposed_current_list_first', 'Add the current information. R3-900001 and R3-900002 (was R3-900003 and R3-900004 respectively) are agreed.', 'R3-900001', True),
        ('postposed_current_list_second', 'Add the current information. R3-900001 and R3-900002 (was R3-900003 and R3-900004 respectively) are agreed.', 'R3-900002', True),
        ('postposed_old_object', 'The current CR was R3-900003 agreed', 'R3-900003', False),
        ('previous_object_grouping', 'R3-900001 was R3-900002 are agreed', 'R3-900002', False),
        ('different_postposed_clause', 'R3-900001 is mentioned; the CR is agreed.', 'R3-900001', False),
        ('explicit_no_CR', 'No CR is agreed at this meeting. R3-900001 may be considered in future.', 'R3-900001', False),
        ('explicit_not_agreed', 'The CR R3-900001 is not agreed.', 'R3-900001', False),
        ('never_endorsed', 'The CR R3-900001 was never endorsed.', 'R3-900001', False),
        ('conditional_proposal', 'If we agree the CR R3-900001, work will continue.', 'R3-900001', False),
        ('conditional_comment_after_approval', 'Agree the XnAP CR R3-900001, avoiding “an IE is ignored if another IE is ignored”.', 'R3-900001', True),
        ('later_document_status', 'Choose Option 2.\nR3-900001\tCorrection CR\nDecision: Agreed', 'R3-900001', False),
        ('later_document_content', 'Choose Option 2.\nR3-900002\tSeparate discussion\nAgree the CR R3-900001.', 'R3-900001', False),
        ('after_document_Decision', 'Choose Option 2.\nDecision: Noted\nAgree the CR R3-900001.', 'R3-900001', False),
    ]
    grammar = []
    for name, content, target, wanted in cases:
        actual = bool(rule.approves(content, target))
        cypher_actual = literal_cypher_approves(query, content, target)
        if actual != wanted or cypher_actual != wanted:
            raise ValueError((name, wanted, actual, cypher_actual))
        grammar.append({'check': name, 'content': content, 'target': target, 'expected': wanted, 'pass': True})

    sys.path.insert(0, str(HERE / 'scoring'))
    import original_scorer as scorer
    import contract_checks
    task = json.loads((HERE / 'repair_technical_approval_v5.json').read_bytes())
    rows = json.loads((HERE / 'fresh_SQL_technical_approval_full8_requested_fields_v5.json').read_bytes())
    groups = scorer.make_order_groups(task, rows, rows)
    generic = contract_checks.checks(task, rows, groups)
    if not all(case['pass'] for case in generic):
        raise ValueError('generic complete-record control failed')
    prediction = scorer.reference_prediction(task, rows)
    if len(prediction) != 5 or len(groups) != 8:
        raise ValueError('wrong full or selected cardinality')
    requested = []
    def require(name, records, wanted):
        outcome = scorer.score(task, rows, records, diagnostic=True, order_groups=groups)
        if outcome['exact'] is not wanted:
            raise ValueError((name, outcome))
        requested.append({'check': name, 'expected_exact': wanted, 'pass': True, 'outcome': outcome})
    require('same_complete_five_in_reverse_order', prediction[::-1], True)
    require('later_CR_displaces_first', prediction[1:] + [rows[5]], False)
    require('duplicate_displaces_required_CR', prediction[:-1] + prediction[:1], False)
    for field in ['reason', 'summary']:
        altered = copy.deepcopy(prediction)
        altered[0][field] = altered[1][field]
        require(field + '_cross_CR_swap', altered, False)
        altered = copy.deepcopy(prediction)
        altered[0][field] = altered[0][field][:20]
        require(field + '_fragment', altered, False)
        altered = copy.deepcopy(prediction)
        altered[0][field] = None
        require('actual_nonempty_' + field + '_changed_to_null', altered, False)
        altered = copy.deepcopy(prediction)
        altered[0].pop(field)
        require(field + '_key_omitted', altered, False)
    altered = copy.deepcopy(prediction)
    altered[0]['summary'] = ''
    require('actual_nonempty_summary_changed_to_empty', altered, False)
    altered = copy.deepcopy(prediction)
    altered[0]['tdocNumber'] = 900001
    require('CR_identity_changed_to_number', altered, False)
    require('unrequested_source_context_ignored', [dict(row, Agreement_content=None) for row in prediction], True)
    null_record = dict(prediction[0], summary=None)
    scorer.typed.record_token(null_record, task['required_fields'])
    requested.append({'check': 'unchanged_nullable_summary_schema_accepts_explicit_null', 'pass': True,
                      'actual_selected_summary_empty_claim': False})
    return {'status': 'PASS_LITERAL_CYPHER_GRAMMAR_AND_UNCHANGED_TYPED_CONTROLS',
            'literal_query_reference_path_checks': checks, 'literal_query_reference_path_n': len(checks),
            'grammar': grammar, 'grammar_n': len(grammar), 'generic_typed': generic,
            'requested_typed': requested, 'typed_n': len(generic) + len(requested),
            'actual_Cypher_engine_execution': False, 'native_API_calls': 0,
            'outside_frontier_global_source_classifier_certified': False}

if __name__ == '__main__':
    if sys.flags.optimize:
        raise SystemExit('optimized mode is not accepted')
    result = run()
    output = HERE / 'actual_technical_approval_query_and_typed_controls_v5.json'
    with output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'paths': result['literal_query_reference_path_n'],
                      'grammar': result['grammar_n'], 'typed': result['typed_n'],
                      'receipt_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))
