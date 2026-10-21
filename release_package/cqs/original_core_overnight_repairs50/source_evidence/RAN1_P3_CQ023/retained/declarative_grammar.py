"""Declarative current-amendment grammar over retained fields.

This compiler emits core Cypher Boolean expressions and evaluates the same
syntax tree for an immutable-input equivalence challenge. No record identity,
source label or expected population enters an expression.
"""
import json
import re


def var(name): return ('var', name)
def lit(value): return ('lit', value)
def rx(name, pattern): return ('rx', var(name), pattern)
def both(*xs): return ('and', *xs)
def either(*xs): return ('or', *xs)
def no(x): return ('not', x)
def anyof(items, name, predicate): return ('any', var(items), name, predicate)
def equal(a, b): return ('eq', a, b)
def inc(a, b): return ('in', a, b)
def prop(name, key): return ('prop', var(name), key)


def evaluate(expr, env):
    op, *args = expr
    if op == 'var': return env[args[0]]
    if op == 'lit': return args[0]
    if op == 'rx': return bool(re.search(args[1], evaluate(args[0], env)))
    if op == 'and': return all(evaluate(x, env) for x in args)
    if op == 'or': return any(evaluate(x, env) for x in args)
    if op == 'not': return not evaluate(args[0], env)
    if op == 'any':
        return any(evaluate(args[2], dict(env, **{args[1]: x})) for x in evaluate(args[0], env))
    if op == 'eq': return evaluate(args[0], env) == evaluate(args[1], env)
    if op == 'in': return evaluate(args[0], env) in evaluate(args[1], env)
    if op == 'prop': return evaluate(args[0], env).get(args[1], '') or ''
    if op == 'dynamic_rx': return bool(re.search(evaluate(args[1], env), evaluate(args[0], env)))
    if op == 'concat': return ''.join(str(evaluate(x, env)) for x in args)
    raise ValueError(op)


def java_search(pattern):
    flags = ''
    while pattern.startswith('(?'):
        m = re.match(r'^\(\?([ims]+)\)', pattern)
        if not m: break
        flags += m[1]
        pattern = pattern[m.end():]
    flags = ''.join(dict.fromkeys(flags))
    return ('(?' + flags + ')' if flags else '') + '(?s:.*?)(?:' + pattern + ')(?s:.*)'


def cypher(expr, names=None):
    names = names or {}
    render = lambda value: cypher(value, names)
    op, *args = expr
    if op == 'var': return names.get(args[0], args[0])
    if op == 'lit': return json.dumps(args[0], ensure_ascii=False)
    if op == 'rx': return '(' + render(args[0]) + ' =~ ' + json.dumps(java_search(args[1])) + ')'
    if op in ('and', 'or'):
        return '(' + (' AND ' if op == 'and' else ' OR ').join(render(x) for x in args) + ')'
    if op == 'not': return '(NOT ' + render(args[0]) + ')'
    if op == 'any': return 'any(' + args[1] + ' IN ' + render(args[0]) + ' WHERE ' + render(args[2]) + ')'
    if op == 'eq': return '(' + render(args[0]) + ' = ' + render(args[1]) + ')'
    if op == 'in': return '(' + render(args[0]) + ' IN ' + render(args[1]) + ')'
    if op == 'prop': return "coalesce(" + render(args[0]) + '.' + args[1] + ", '')"
    if op == 'dynamic_rx': return '(' + render(args[0]) + ' =~ ("(?is).*?" + ' + render(args[1]) + ' + ".*"))'
    if op == 'concat': return '(' + ' + '.join(render(x) for x in args) + ')'
    raise ValueError(op)


TS = r'(?i)(?:TS\s*)?38\s*\.\s*214(?!\d)'
SPEC = r'(?i)(?:TS\s*)?38\s*\.\s*\d{3}(?!\d)'
HEADER = r'^\s*R1-\d{7}(?!\d)\s*\t'
STATE = r'(?i)\b(?:is|are)\s+(?:endorsed|approved|agreed|adopted|agreeable)|\b(?:adopt|endorse|approve|accept|agree)\b'
BAD = r'(?i)\b(?:not|never)\s+(?:yet\s+)?(?:endorsed|approved|agreed|adopted)|\b(?:no consensus|no agreement|if agreed|if approved|previously agreed|earlier agreed|already agreed)\b|^\s*(?:Reason for change|Consequences if not approved):'
NEG = r'(?i)\b(?:no consensus|no agreement|not (?:yet )?(?:agreed|endorsed|approved|adopted)|for consideration|if (?:agreed|approved))\b'
HISTORY = r'(?i)\b(?:previously|earlier|already)\s+(?:agreed|endorsed|approved|adopted)\b'
NO_CURRENT = r'(?i)\bno consensus\b.{0,70}\b(?:TP|text proposal)\b|\b(?:TP|text proposal)\b.{0,70}\b(?:not agreed|not endorsed|not approved)\b'
NO_CHANGE = r'(?i)\bno\s+(?:spec(?:ification)?\s+)?change(?:s)?\s+(?:is|are)\s+(?:needed|required|necessary)\b'
TP = r'(?i)\b(?:(?:the\s*)?TPs?(?=\b|[0-9#_])|text proposals?\b|proposals?\s*\d)'
OBJECT = r'(?i)\b(?:TPs?(?=\b|\d|#)|text proposals?|text changes?)'
ADOPT = r'(?i)\b(?:adopt(?:ed|ing)?|endorse(?:d)?|approv(?:e|ed)|accept(?:ed)?|(?:is|are) agreed)\b'
CR = r'(?i)\b(?:draft\s*)?CRs?\b'
NORM = r'(?i)\b(?:shall|is expected to|is not expected to|are applied|is transmitted|can only be|clarif(?:y|ied)|fix|add|remove|replace|amend|correct|apply existing agreements|further revised as follows|support\s+\w+\s*=)\b'
NORM_FOLLOW = r'(?i)\b(?:shall|is expected to|are applied|is transmitted|is configured|the UE|a UE|UE determines|support|does not expect|can only)\b'
START = r'(?i)^\s*(?:[-*•\d.)]+\s*)?(?:(?:to|RAN1\s+(?:to|agrees?\s+to))\s+)?(?:add(?:ing)?|remov(?:e|ing)|replac(?:e|ing)|clarif(?:y|ication)|updat(?:e|ing)|chang(?:e|ing)|fix|captur(?:e|ing)|align(?:ment)?|scale|confirm|take|make|include|adop(?:t|ting)?)\b'
BODY_TARGET = r'(?i)^\s*(?:\|\s*)?[-_<>\s]*(?:(?:Start|Beginning|Begin|Text)\s*(?:of\s*)?(?:the\s*)?)?(?:(?:TPs?(?=\b|\d|#)|text proposals?|text change|new text|change)\b|(?:(?:in|to)\s+)?(?:section|clause|subclause)\s+\d)'
DECL = r'(?i)^\s*[-_<>\s]*(?:(?:the|and related)\s+)?(?:TPs?(?=\b|\d|#)|text proposals?|text change|new text|change|(?:in\s+)?(?:sub)?(?:clause|section))\b'
FUTURE_OPTIONS = r'(?i)\b(?:down[- ]select(?:ion)?(?:\s+one)?|one of (?:the )?following(?:s)?)\b'
SELECTED = r'(?i)\b(?:option|alt(?:ernative)?)\s*[\d\w\u2019\u2032\x27-]+.{0,30}\b(?:is adopted|is agreed|is endorsed)|\badopt\s+(?:option|alt)\b'
LS = r'(?i)^\s*(?:endorse|approve|adopt|agree|send|the (?:draft|final)).{0,90}\b(?:LS|liaison)\b'
ACTION = r'(?i)\b(?:add(?:ing)?|remov(?:e|ing)|replac(?:e|ing)|clarify|updat(?:e|ing)|chang(?:e|ing)|fix|captur(?:e|ing)|align|scale|confirm|take|make|include|adop(?:t|ting)?)\b'
CRSUBJECT = r'(?i)^\s*(?:Decision:\s*)?(?:The\s+|A\s+)?(?:(?:following|two|three|four|these|corresponding|alignment|final|draft|38\.214|TS\s*38\.214)\s+)*CRs?\b'
DIRECTIVE = r'(?i)\b(?:please\s+include|to\s+be\s+included\s+as\s+part|include\s+(?:it|them|this|the|following)|replace|remove|amend|correct|revision\s+from)\b'
ALIGN = r'(?i)(?:alignment.{0,25}\bCRs?\b|editor.{0,25}\bCRs?\b|\bCRs?\b.{0,25}alignment)'


def surface_rules():
    """Every family retains its scope and its own negative/target governors."""
    target = rx('l', TS)
    valid = no(rx('l', BAD))
    current = both(no(rx('full', NO_CURRENT)), no(rx('l', NEG)), no(rx('l', NO_CHANGE)), no(rx('l', HEADER)))
    not_options = no(both(rx('full', FUTURE_OPTIONS), no(rx('full', SELECTED))))
    not_ls = no(rx('firstContent', LS))
    approved = either(rx('l', STATE), rx('l', r'(?i)\b(?:endorsed|approved|adopted)\s+(?:(?:the\s*)?TPs?(?=\b|[0-9#_])|text proposals?)'), rx('l', r'(?i)\b(?:(?:the\s*)?TPs?(?=\b|[0-9#_])|text proposals?).*\b(?:endorsed|approved|adopted)\b'))
    rules = []
    def put(name, pred): rules.append({'name': name, 'predicate': pred})
    put('current_identified_TP_or_explicit_changes_214_amendment', both(valid, rx('subject', TS), approved, either(rx('l', TP), both(rx('l', r'(?i)\b(?:text|changes?|corrections?|revisions?|clarifications?)\b'),rx('l',r'(?i)\b(?:Adopt|Agree|Endorse|Approve|Accept)\b')))))
    put('explicit_current_CR_object_and_TS', both(valid, rx('l', STATE), rx('l', CRSUBJECT), either(target,both(rx('next',r'(?i)^\s*(?:For editors?:|To be included|Include (?:it|this)|For (?:the )?alignment)'),rx('next',TS)))))
    put('current_identified_CR_amendment_directive', both(valid,target,rx('l',CR),rx('l',DIRECTIVE)))
    put('approved_TS_component_explicit_alignment_CR',both(valid,target,rx('l',TP),rx('l',STATE),rx('l',ALIGN)))
    put('explicit_current_214_correction_directive',both(valid,target,rx('l',r'(?i)^\s*(?:Apply existing agreements|Fix the specification)')))
    put('current_explicit_target_directive_extended',both(current,target,rx('l',START),no(rx('l',r'(?i)for the description of.{0,40}\bFG\b')),no(rx('l',r'(?i)^\s*clarification\s+on\s+(?:the\s+)?relationship')),not_ls))
    put('explicit_current_target_amendment_passive',both(current,no(rx('l',HISTORY)),target,rx('l',r'(?i)\b(?:is|are|be|being)\s+(?:modified|revised|updated|replaced|removed|deleted|added|captured|clarified|implemented)\b'),no(rx('l',r'^\s*\||\?'))))
    put('specific_current_target_editor_instruction',both(current,no(rx('l',HISTORY)),target,rx('l',r'(?i)\beditor(?:s)?\b.{0,80}\b(?:capture|change|clarif|align|expand|define|describe|implement|correct)')))
    put('Agreement_owns_declared_target_amendment_text',both(current,no(rx('l',HISTORY)),target,rx('l',DECL),no(rx('l',r'(?i)\b(?:according to|defined in|as in|reference to|unchanged|for reference)\b')),either(rx('following20',NORM_FOLLOW),rx('following20',r'(?i)Start.{0,20}(?:TP|text proposal)'))))
    put('current_own_rule_explicit_target_application',both(current,no(rx('l',HISTORY)),not_options,target,rx('l',r'(?i)\b(?:appl(?:y|ies|ied).{0,30}(?:above|following)|above.{0,40}(?:appl|procedure)|this (?:affects|addresses|is for)|how (?:this|to describe).{0,40}(?:captured|specification)|total.{0,40}will be used)\b')))
    put('specific_current_amendment_editor_execution',both(current,target,rx('l',r'(?i)\b(?:example change|editorial corrections?|parameter name alignments?|detailed clarifications?)\b'),rx('l',r'(?i)\beditors?\b')))
    put('current_specific_target_clause_operation',both(current,target,not_options,rx('l',r'(?i)\b(?:requires? (?:the )?chang|is to be made|to be (?:implemented|captured)|will be added|is (?:modified|set)|reused with the following add-on|scale\s+\d|extend the definition|applies? (?:the )?(?:above|following) procedure|addresses the FFS|affects Tables|will be used in the.{0,30}equation)\b'),no(rx('l',r'^\s*\|')),either(no(rx('l',r'(?i)\bis set\b')),rx('l',r'(?i)^\s*In\s+(?:TS\s*)?38\s*\.\s*214'))))
    put('current_Agreement_declared_amendment_target',both(current,target,rx('l',BODY_TARGET),no(rx('l',r'(?i)\b(?:according to|as defined|reference to)\b')),either(rx('l',OBJECT),rx('l',r'(?i)\b(?:section|clause|subclause|new text|change)\b')),rx('firstTarget',r'^214$')))
    put('current_identified_target_proposal_act',both(current,target,rx('l',r'(?i)\b(?:TP|text proposal).{0,100}\b(?:adapted|supported|recommended|to be made|implemented)\b|\bsupport\s+(?:the\s+)?following\s+TP')))
    put('verb_governs_current_target_clause',both(current,target,not_ls,no(rx('l',r'^\s*\|')),rx('l',r'(?i)\b(?:clarify|capture|add|remove)\s*,?\s*(?:in|to|from)\s+(?:TS\s*)?38\s*\.\s*214')))
    put('specific_target_change_application',both(current,target,not_ls,no(rx('l',r'^\s*\|')),rx('l',r'(?i)\b(?:requires? (?:the )?changes?|scale\s+(?:the|\d)|should be specified|is to be made|in\s+TS38\.214,\s*remove)\b')))
    put('current_target_procedure_new_parameter_or_step',both(current,target,no(rx('l',r'^\s*\|')),rx('l',r'(?i)\b(?:excludes?.{0,170}after\s+Step|reports?.{0,30}after\s+Step|total number.{0,130}will be used|correspond to the SS/PBCH|\bj\s*=)')))
    put('own_current_amendment_editor_target_allocation',both(current,target,no(rx('l',r'^\s*\|')),rx('l',r'(?i)\b(?:spec impact is only|up to the editor|editor.{0,30}whether to create a new section|suggest to the editors to align)')))
    put('current_target_TP_or_table_amendment',both(current,target,no(rx('l',r'^\s*\|')),no(rx('l',r'(?i)\bsupport\s+of\b')),rx('l',r'(?i)\b(?:support\b.{0,80}\b(?:in|to)\s+(?:Table|TS)|beginning of TP|Start.{0,20}TP|adopting the TP)')))
    put('current_TP_start_declares_target_next_line',both(current,target,rx('l',r'(?i)^\s*(?:In\s+)?(?:TS\s*)?38\s*\.\s*214(?:\s+v\d|\s*,)'),rx('prev',r'(?i)Start.{0,20}(?:text proposal|TP)')))
    put('current_directive_adjacent_explicit_target_clause',both(current,rx('firstTarget',r'^214$'),no(rx('l',FUTURE_OPTIONS)),not_ls,either(rx('prev',ACTION),rx('next',ACTION)),rx('l',r'(?i)^\s*(?:For\s+(?:timing determination|the processing time formulas)|In\s+(?:TS\s*)?38\s*\.\s*214|(?:The\s+)?(?:[“\"])?(?:dedicated|shared) SL PRS resource pool)')))
    put('current_explicit_target_numeric_scale',both(current,target,rx('l',r'(?i)\bscale\s+\d+\b')))
    put('current_explicit_target_procedure_exclusion',both(current,target,rx('l',r'(?i)\bexcludes?\b.+\bafter\s+Step\b')))
    put('current_quoted_target_bracket_amendment',both(current,target,rx('l',r'(?i)^\s*Regarding\s+(?:the\s+)?following\s+text\s+in\s+brackets'),rx('following4',r'(?i)\b(?:keep|remove)\b.{0,60}\bbrackets?\b')))
    put('current_TP_start_section_target_declaration',both(current,target,rx('l',r'(?i)\b(?:section|clause)\s+\d'),rx('prev',r'(?i)\b(?:Start|Beginning)\b.{0,20}\bTP\b')))
    put('own_current_amendment_explicit_MAC_CE_target_impact',both(current,target,rx('prev',r'(?i)^\s*MAC[- ]?CE\s+Impact\s*:'),rx('beforePrev',r'(?im)^\s*(?:Modify|Introduce)\b')))
    put('current_adjacent_target_parameter_replacement',both(current,target,rx('l',r'(?i)^\s*(?:If|In|For)\b'),rx('next',r'(?i)\breplaces\b')))
    return rules


SURFACE_RULES = surface_rules()
SURFACE_RULES[0]['scope'] = 'uppercase_sentence_clause'
SURFACE_RULES.extend([
    dict(name='current_approved_text_explicitly_part_of_CR', predicate=both(no(rx('l',BAD)),rx('l',TS),rx('l',CR),rx('l',r'(?i)\b(?:is|are)\s+(?:agreed|endorsed|approved|adopted|agreeable)|^\s*(?:Agree\s+on|Adopt|Endorse|Approve|Accept)\b'),rx('l',ALIGN),rx('l',r'(?i)\b(?:TPs?|text\s+proposals?|text\s+change|corrections?|parameter\s+names?)\b'))),
    dict(name='Agreement_presented_current_inline_CR_component',predicate=both(no(rx('l',BAD)),rx('l',TS),rx('l',CR),var('firstThreeLines'),rx('l',r'(?i)^\s*(?:Text\s+Proposal\s+for|CR\s+to|TP#?\d*\s+for)'),either(rx('l',ALIGN),rx('l',r'(?i)\bis\s+as\s+follows')))),
    dict(name='explicit_Agreement_amendment_with_CR_coversheet',predicate=both(rx('fieldText',r'(?i)Agreement\s*\(further amended with CR coversheet'),rx('l',TS),rx('l',r'(?i)\bamend\b'))),
])


def contextual_rules():
    rules=[]
    def put(name,expr): rules.append(dict(name=name,predicate=expr))
    valid=no(rx('l',BAD));positive=both(valid,rx('l',STATE))
    direct=anyof('lineDocs','d',equal(prop('d','typed214'),lit(True)))
    put('direct_target_positive_statement',both(positive,direct))
    put('target_TS_CR_number_positive_tuple',both(positive,rx('l',TS),var('targetNumberTuple')))
    put('current_TDoc_header_CR_anaphor',both(positive,either(rx('l',CR),rx('l',TP)),var('noLineIDs'),var('headerTyped214')))
    put('following_CR_list',var('listedApproved214'))
    put('explicit_current_draft_CR_document_list',var('openedApprovedCRList214'))
    put('adopted_existing_CR_proposal_list',var('approvedTPList214'))
    put('approved_editor_CR_list_explicit_TS_component',var('editorListComponent214'))
    put('current_named_TP_existing_explicit_target_title',both(no(rx('full',NO_CURRENT)),valid,no(rx('l',NEG)),no(rx('l',HISTORY)),rx('l',OBJECT),rx('l',ADOPT),var('namedTargetTPTitle')))
    put('current_following_TP_list_target_binding',both(no(rx('full',NO_CURRENT)),valid,no(rx('l',NEG)),rx('l',r'(?i)\bfollowing\s+(?:TPs?|text proposals?)\b'),rx('l',ADOPT),var('followingTargetTPTitle')))
    put('current_above_TP_list_target_binding',both(no(rx('full',NO_CURRENT)),valid,no(rx('l',NEG)),rx('l',OBJECT),rx('l',ADOPT),rx('l',r'(?i)\babove\b'),var('aboveTargetTPTitle')))
    put('current_approved_named_TP_same_event_CR_summary_component',both(positive,rx('l',r'(?i)\b(?:TPs?|text proposals?|proposal\s*#?\s*\d+)\b'),var('reverseCompatibleComponent')))
    put('current_approved_header_TP_same_event_CR_summary_component',both(positive,rx('l',r'(?i)\b(?:TPs?|text proposals?)\b'),var('noLineIDs'),var('headerReverseCompatibleComponent')))
    put('current_approved_named_TP_explicit_CR_component_metadata',both(positive,rx('l',r'(?i)\b(?:TPs?|text proposals?)\b'),var('namedRemarksCompatibleComponent')))
    put('current_TP_FLS_unique_same_event_same_title_existing_CR_context',both(positive,rx('l',r'(?i)\b(?:TPs?|text proposals?)\b'),var('uniqueSameEventTitleCR')))
    put('own_current_normative_subject_explicitly_captured_in_same_event_214_CR',var('ownNormativeExactCapturedScope'))
    put('own_current_substantive_amendment_existing_214_CR_context',var('ownNormativeAdjacentTargetCR'))
    put('own_current_amendment_complete_existing_same_event_CR_title_phrase',var('ownNormativeCompleteSameEventTitle'))
    put('own_current_normative_amendment_same_event_combined_CR_individual_target',var('ownNormativeNamedCombinedEntry'))
    put('current_multiline_declared_214_TP_approval',var('selectedDeclaredTargetTP'))
    put('current_Agreement_marker_owns_identified_214_TP',var('firstOwnCompleteTargetTP'))
    put('approved_component_under_explicit_TS_CR_heading',var('scopedAlignmentCRApproval'))
    put('current_scale_governs_following_target_parameter_list',var('scaleFollowingTarget'))
    put('own_target_clause_decision_explicit_specification_update',var('explicitCurrentSpecificationUpdate'))
    return rules


CONTEXT_RULES = contextual_rules()
