#!/usr/bin/env python3
"""Resume pinned readback checks after a fully inserted, interrupted fresh restore.

This administrative verifier accepts only the original serializer's complete
helper-bound population plus its unique contract-labeled, property-free initial seed. It preserves
all input/content/order/schema checks and cleanup from the pinned serializer.
"""
from __future__ import annotations
import argparse, ast, hashlib, inspect, os, sys
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import snapshot as adapter

REPLACEMENT = """
initial = None
recovery_population = counts(session, args.timeout)
expected_population = dict(manifest['before_counts'])
expected_population['nodes'] += 1
if recovery_population != expected_population:
    raise ValueError('Interrupted target population is incomplete or has unexpected records')
bound = session.run(f'MATCH (n:{ident(HELPER_LABEL)}) RETURN count(n) AS n').single()['n']
if bound != manifest['before_counts']['nodes']:
    raise ValueError('Interrupted target helper-bound node coverage differs')
seeds = session.run(f'MATCH (n) WHERE NOT n:{ident(HELPER_LABEL)} RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties').data()
if len(seeds) != 1 or seeds[0]['labels'] != label_contract['token_creation_order'] or seeds[0]['properties']:
    raise ValueError('Interrupted target lacks its unique contract-labeled, property-free initial seed')
order_seed_id = seeds[0]['id']
"""

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--working-group',choices=adapter.GROUPS,required=True)
    p.add_argument('--bolt',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();group=args.working_group
    helper=adapter.helper_directory();sys.path.insert(0,str(helper))
    gs=adapter.module('pinned_query_resume_serializer',helper/'graph_snapshot.py')
    guard=adapter.module('pinned_query_resume_syntax',helper/'cq_anchor_guard.py')
    directory=HERE/'source'/group;manifest=adapter.load(directory/'manifest.json');study=manifest['query_study']
    for file,key in (('graph_snapshot.py','serializerSha256'),('runner.py','runnerSha256')):
        if adapter.digest(helper/file)!=study[key]:raise ValueError('Pinned serializer/helper source differs')
    if adapter.digest(HERE/'snapshot.py')!=study['adapterSha256']:raise ValueError('Pinned adapter differs')
    dependency=adapter.query_inputs(guard)
    gs.dependencies=lambda *_:dependency;gs.token_probes=lambda *_:dependency['tokenProbes']
    _,_,gs.read_records=adapter.reuse_topology(gs,helper,group,dependency)
    original=inspect.getsource(gs.restore);tree=ast.parse(original)
    function=tree.body[0];function.name='resume_restored_verification'
    outer=next(node for node in function.body if isinstance(node,ast.With))
    inner=next(node for node in outer.body if isinstance(node,ast.With))
    def assignment(node,name):
        return isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets)
    start=next(i for i,node in enumerate(inner.body) if assignment(node,'initial'))
    end=next(i for i,node in enumerate(inner.body) if assignment(node,'actual_fingerprints'))
    # Replace only the already-completed creation stage. All following actual
    # content fingerprints, relative order, schema, cleanup and final counts
    # remain the original pinned implementation.
    inner.body[start:end]=ast.parse(REPLACEMENT).body
    tree=ast.fix_missing_locations(tree);code=ast.unparse(tree)
    exec(compile(tree,'<pinned-readback-resume>','exec'),gs.__dict__)
    contract={'definition_contract':study['definition_contract'],'graph_views':[{
        'working_group':group,'manifest_path':str((directory/'manifest.json').relative_to(HERE)),
        'manifest_sha256':adapter.digest(directory/'manifest.json'),
        'definition_binding_path':str((directory/'definition_binding.json').relative_to(HERE))}]}
    expected=args.output/(group+'-restore.json')
    if expected.exists():raise ValueError('Preserve an existing restore receipt')
    common=SimpleNamespace(working_group=group,timeout=1800,snapshot=directory,
        output=args.output.resolve(),confirm_empty_target=True)
    connection={'uri':args.bolt,'user':os.environ['NEO4J_USER'],'password_env':'NEO4J_PASSWORD','database':'neo4j'}
    gs.resume_restored_verification(HERE,contract,[],connection,common)
    receipt=adapter.load(expected)
    receipt['scope']='Actual complete-content, order and schema verification resumed after interruption of a fresh empty-target restore following its completed insertion stages.'
    receipt['recovery']={'initialFreshRestoreEmptyTargetGuardCompleted':True,
        'initialCountsMeasurement':'The original pinned fresh-restore empty-target guard completed before the observed full node and relationship insertion stages. This resumed process measures post-insertion state.',
        'interruptedProcessExitCode':143,'observedCompletedInsertionStages':manifest['before_counts'],
        'requiredRecoveryState':'Exactly the manifest node count under the source-ID helper label, all expected relationships, and one property-free initial seed with exactly the pinned token_creation_order label sequence.',
        'originalSerializerSha256':study['serializerSha256'],
        'resumedVerifierSha256':adapter.digest(Path(__file__)),
        'transformedReadbackFunctionSha256':hashlib.sha256(code.encode()).hexdigest(),
        'transformation':'Replace original creation block from initial-count assignment up to actual_fingerprints assignment with strict interrupted-helper-state checks. Preserve all following original readback/cleanup/schema verification.',
        'replacementSource':REPLACEMENT}
    receipt['finishedUtc']=datetime.now(timezone.utc).isoformat()
    adapter.save(expected,receipt)
if __name__=='__main__':main()
