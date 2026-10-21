"""Record ROOT's source-read semantic judgment; not a final admission."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
C = D.parent
R = next(p for p in D.parents if (p / 'CLAUDE.md').is_file())
PUBLIC = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/original_core_repair')
sys.path.insert(0, str(PUBLIC))

def pin(p):
    b = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

def module(name):
    spec = importlib.util.spec_from_file_location(name, PUBLIC / (name + '.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

definition_path = D / 'definition.json'
definition = json.loads(definition_path.read_text())
original = json.loads((C / 'original.json').read_text())
primary_path = D / 'primary_exact_seven_unit_review.json'
primary = json.loads(primary_path.read_text())
criteria_path = C / 'source_portable_v2/criteria.json'
criteria = json.loads(criteria_path.read_text())
authority_path = D / 'prospective_original_recorded_contract_and_authority.json'
authority = json.loads(authority_path.read_text())
source_path = R / authority['source_authority']['path']
source = source_path.read_text().splitlines()
replay_path = D / 'actual_ROOT_independent_reopened_original_frontier_v1.json'
replay = json.loads(replay_path.read_text())
verify, schema = module('verify_release'), module('review_schema')
identity = verify.digest(definition)
assert identity == 'bdf997f06492063fce39de80bca72378d557151ff81f0b1df846c9a9ec0e9a07'
assert pin(definition_path)['sha256'] == 'ad84ac8293386d13c8544e6eaf20841303c2f181e67b40ab77d7663d9d8d6d52'
assert pin(criteria_path)['sha256'] == 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
assert pin(source_path)['sha256'] == '7cfeb6a3802a7d0ce9193c19cf659dd03ee260177e2625eb3cb621fedb1b46a9'
assert pin(replay_path)['sha256'] == 'a4d5b1fafd469ec679432a3c3aa4b5c69cb3ac3e0b2daca7c8f28517eb872add'
assert original['question_en'] == definition['question_en']
assert original['cypher'] == definition['original_query'] == definition['reference_query']
assert set(definition) == set(verify.DEFINITION_KEYS)
assert '특정 기술(Work Item)에서 회사별 Resolution 기여도는?' in source[120]
assert 'Resolution, references' in source[499] and 'submittedBy' in source[870]
assert 'Count DESC' in source[168] and 'Company 이름 ASC' in source[168]
assert 'Limit은 쿼리 시 파라미터로 조정 가능' in source[181]
assert replay['immutable_database_unchanged'] is True
assert replay['first5_dependency']['role_failure_n'] == 0
assert replay['authored_7digit_reference_equivalence']['missing'] == []
assert replay['authored_7digit_reference_equivalence']['extra'] == []
question = original['question_en']

judgments = [
    (
        'Return the top companies by resolution contribution per work item',
        'The requested units are Work Item identities and each selected company with its Resolution contribution value. The prior Korean CQ asks how much company contribution exists for a technology; the authored objects name company and count. This source-specific evidence warrants count as a substantive answer value. No ordinal, approval flag or causal influence attribute is requested.',
        'RETURN wi.workItemCode, topCompanies; collect({company:c.companyName,count:cnt})',
        'The declared two outer roles and strict company/string,count/integer members match that original task. Extra helper projections are not scored.',
        ['original Korean CQ3-3 question and named count object', 'Phase2 L121,L500,L871'],
    ),
    (
        'resolution contribution per work item (technology leadership)',
        'The original phase scope is Resolution information recorded in Final Report bodies, including Agreement, Conclusion and WorkingAssumption, connected to original Phase1 Tdocs, companies and Work Items. The task is graph-relative documentary contribution in that explicit source context.',
        '(r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem); (t)-[:SUBMITTED_BY]->(c:Company)',
        'ROOT actually executed the reopened-original-frontier audit and obtained byte-identical source evidence: all twelve selected Resolution full contents and all294 Tdoc roles in eleven original registers. This covers the complete selected first-five dependency; it does not certify all3773 physical report bodies.',
        ['Phase2 L21,L28,L121,L500,L871', 'actual ROOT replay a4d5b1fafd469ec679432a3c3aa4b5c69cb3ac3e0b2daca7c8f28517eb872add'],
    ),
    (
        'by resolution contribution per work item (technology leadership)',
        'The original CQ3 required-term and property maps expressly operationalize company contribution through Resolution references to submitted Tdocs. The source rule extracts literal seven-digit R2 references in content and keeps existing Phase1 targets. That prior task-specific rule, rather than convenience of counting, supports this documentary proxy.',
        'REFERENCES to existing Tdoc; RELATED_TO WorkItem; SUBMITTED_BY Company',
        'All12995 existing-target pairs match all retained contents under the original operation. ROOT rejects an added first-Tdoc/header cutoff: it lacks original authority and conflicts with observed after-header references and plural Conclusion containers. The word leadership does not add an unmeasured causal, actual approval or normative incorporation criterion to this operational CQ.',
        ['Phase2 L500,L757,L871,L1121-L1135,L1219', 'retained reference equivalence and original source frontier'],
    ),
    (
        'resolution contribution per work item',
        'The author-selected unit is a distinct recorded Resolution for each WI/company pair. Repeated referenced documents or edge paths for that pair contribute once. Co-submitters retain their separate company incidences.',
        'WITH wi,c,count(DISTINCT r) AS cnt',
        'The immutable SQL projection has13654 paths and1939 grouped pairs across223 WIs. These counts are not distinct physical technical propositions, approvals or exclusive ownership. The full population remains eligibility evidence and is not replaced by a limited exemplar.',
        ['exact original English and Korean query', 'ROOT replay full_recorded_scope/full_group_population'],
    ),
    (
        'Return the top companies by resolution contribution per work item',
        'The instantiated original query fixes five lexical WI-code partitions and at most five highest-contribution company members per partition. Original generic limits are parameterizable and do not prohibit the explicit five-member instantiation.',
        'collect(...)[0..5]; ORDER BY wi.workItemCode LIMIT 5',
        'Five outer records are required, with min(5,eligible company count) members each. All36 grouped company values for these WIs are retained. The fifth WI has four mandatory count5 companies and five count4 companies competing for one slot. Each of the five lawful boundary alternatives must be accepted; source arithmetic is not itself native capture.',
        ['Phase2 L174-L182', 'unchanged exact query', 'ROOT replay full population and first5'],
    ),
    (
        'top companies by resolution contribution per work item',
        'The question explicitly requests a contribution-based selection. The authored inner query sorts count descending and supplies no company tiebreak; the instantiated outer query chooses the lexical first five WI codes. Generic Company ASC/default10 is genuine contrary context and is retained.',
        'ORDER BY cnt DESC before collect[..5]; outer ORDER BY wi.workItemCode LIMIT 5',
        'The task-specific concrete count-only slice establishes lawful boundary subsets; silently adding Company ASC would narrow unchanged original-query eligibility. Output order is not a requested ordinal role, so outer records and member pairs may be returned in any order while their selected membership/counts remain constrained. This does not transfer to a plain Which-specs CQ whose source supplies no grouped frequency selection: here BY contribution explicitly identifies the ranking metric.',
        ['Phase2 L169,L179,L182 and exact authored query', 'declared partitioned_top_k contract'],
    ),
    (
        'Return the top companies by resolution contribution per work item (technology leadership).',
        'No additional external or counterfactual leadership labels, approval states, semantic revisions or author-selected company exclusions are needed for the original documentary operation. The extra source files are verification inputs and not extra fields or facts silently given to evaluated models.',
        'reference_query == original_query byte-for-byte; repair_class=scorer_only',
        'The current INDEX code remains compatible-rule evidence, not proof of the historical frozen RDF generator. Six/eight-digit, Annex and prior header-truncation variants remain diagnostics. No model score, expert endorsement, final local admission or public completion follows from this semantic review.',
        ['fixed criterion source_context,query_repair,reference_evidence', 'ROOT independently replayed exact frozen operation'],
    ),
]
evidence = {}
for unit, (quote, derivation, clauses, assessment, locators) in zip(criteria['semantic_units'], judgments):
    assert quote in question
    evidence[unit] = {'status':'pass','original_quote':quote,'independent_derivation':derivation,'query_evidence':clauses,'assessment':assessment,'original_source_locators':locators}
review = {
    'status':'pass','id':definition['id'],'repair_sha256':identity,
    'criteria_sha256':pin(criteria_path)['sha256'],
    'reviewer_kind':'ROOT_AI','reviewer_identity':'/root',
    'nonblind_AI':True,'expert_validation_n':0,
    'exposure':'Original English/Korean/query, source contexts, previous held variants, primary judgment and gold/source diagnostics were visible. ROOT independently reopened source and reran the frontier audit. No new model predictions exist for this identity.',
    'semantic_evidence':evidence,'semantic_review_only':True,
    'primary_review_pin':pin(primary_path),'definition_pin':pin(definition_path),
    'authority_contract_pin':pin(authority_path),
    'evidence_pins':[pin(criteria_path),pin(source_path),pin(replay_path)],
    'remaining_execution_gates':['Fresh guarded native limited query and full1939 population capture','Exact native/immutable-SQL typed agreement','Declared per-WI production dispatch with all five lawful answers and adverse checks','Physically relocated fixed-inventory source/native/scorer proof and final ROOT seal'],
    'new_public_admissions':0,'API_calls':0,'native_calls':0,
}
schema.check_pass(primary,question,criteria['semantic_units'],criteria_sha=pin(criteria_path)['sha256'],identity_key='repair_sha256',identity_sha=identity)
schema.check_pass(review,question,criteria['semantic_units'],criteria_sha=pin(criteria_path)['sha256'],identity_key='repair_sha256',identity_sha=identity)
assert primary['reviewer_identity'] != review['reviewer_identity']
out = D / 'ROOT_secondary_exact_seven_unit_review_v1.json'
assert not out.exists()
out.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'PASS_PRE_NATIVE_SEMANTIC_REVIEW_ONLY','review':pin(out),'independent_reviewers':2,'human_expert_n':0,'new_admission':0},ensure_ascii=False))
