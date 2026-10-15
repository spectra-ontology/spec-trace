"""Package the existing source6 gate and a small reproducible property delta."""
from pathlib import Path
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
B = HERE.parent
ROOT = Path('/home/sihyeon/workspace/spectra')
MAT = B/'source_enriched/RAN1_UL_formal_v2'
REG = B/'RAN1/source_variant_OpenRouter_registration/source6_UL_formal'
TARGET = HERE/'UL_formal_source6_portable_public_patch_v1'
REPAIR = B.parents[1]/'original_repair'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def canonical(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


def main():
    assert not TARGET.exists()
    TARGET.mkdir()
    def copy(source,relative,pin=None):
        source=Path(source);actual=sha(source)
        assert pin is None or actual==pin,(source,pin,actual)
        assert source.is_file() and source.suffix!='.pyc' and '__pycache__' not in source.parts
        dest=TARGET/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
        assert sha(dest)==actual
    def write(relative,value):
        dest=TARGET/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    gate=load(REG/'complete_actual_source6_question_gate.json')
    auth=load(REG/'raw_source_archive_authentication.json')
    graph=load(MAT/'native_import_manifest.json')
    sql=load(MAT/'relational/RAN1.manifest.json')
    mapping=B/'RAN1/UL_switching_formal_ontology_mapping_v2.json'
    mp=load(mapping)
    copy(auth['archive']['path'],'source/original_report.zip',auth['archive']['sha256'])
    copy(REG/'raw_source_archive_authentication.json','source/raw_source_archive_authentication.json')
    copy(ROOT/mp['whole_report_mapping']['path'],'source/whole_ordered_report_source.json',mp['whole_report_mapping']['sha256'])
    copy(ROOT/mp['source_blocks']['path'],'source/formal_source_blocks_v2.json',mp['source_blocks']['sha256'])
    copy(mapping,'patch/existing_resolution_property_mapping6.json')
    copy(ROOT/mp['patch']['path'],'patch/formal_source_content6_add.ttl',mp['patch']['sha256'])
    (TARGET/'patch/full_source6_query.sql').write_text(sql['full_formal_records']['sql']+'\n')
    (TARGET/'patch/formal_source_content6_property.md').write_text(
        '`formalSourceContentWithTables` is a string on existing Resolution/Agreement nodes. '
        'Its six values join complete formal source group records with newlines. Paragraphs '
        'use the declared existing visible w:t projection with tabs/breaks rendered as spaces and '
        'outer strip; Word table rows join cells with ` | ` and rows with newlines. '
        'Inline provisional/revisitable qualifications, Note, table and FFS remain literal. '
        'A separate neighboring WorkingAssumption stays optional. Original content is retained. '
        'No new entity, relationship, source alias or ratification claim is introduced.\n')
    for key,dest in [
        ('definition','contracts/original_canonical_candidate.json'),
        ('criteria','contracts/criteria.json'),
        ('controls','evaluation/controls.json'),
        ('native_queries','evidence/full_native_three_queries.json'),
        ('native_records','evidence/native_full6_records.jsonl'),
        ('independent_SQL_records','evidence/independent_SQL_full6_records.jsonl'),
        ('graph_import','evidence/original_native_import_manifest.json'),
        ('SQL_materialization','evidence/original_SQL_materialization_manifest.json'),
        ('source_integrity','evidence/retained_DOCX_whole_report_and_six_blocks_integrity.json'),
        ('temporal_context','evidence/named_meeting_temporal_context.json'),
        ('independent_temporal_context','evidence/independent_online_meeting_temporal_context.json')]:
        copy(gate[key]['path'],dest,gate[key]['sha256'])
    for name,review in zip(('primary','secondary'),gate['reviews']):
        copy(review['path'],'contracts/'+name+'_AI_review.json',review['sha256'])
    copy(REG/'complete_actual_source6_question_gate.json','evidence/complete_existing_actual_source6_gate.json')
    copy(B/'root_evidence/UL_source6_root_fresh_whole_report_prefreeze.json','evidence/root_fresh_whole6017_report_prefreeze.json')
    copy(B/'root_evidence/verify_UL_source6_whole_report_root.py','evidence/root_fresh_whole6017_report_reader.py')
    copy(B/'audit_UL_source_integrity.py','evidence/original_retained_report_integrity_reader.py')
    copy(B/'build_UL_source_sql.py','evidence/original_SQL_materializer.py')
    copy(MAT/'native_queries/full_property_source_witness.jsonl','evidence/native_all6_old_and_new_property_values.jsonl')
    copy(MAT/'native_queries/preserved_original_query.jsonl','evidence/native_preserved_original_query.jsonl')
    task=load(Path(gate['definition']['path']))
    task['validation_status']='validated'
    (TARGET/'evaluation/tasks.jsonl').write_text(canonical(task)+'\n')
    records=[json.loads(line) for line in Path(gate['native_records']['path']).read_text().splitlines() if line.strip()]
    gold=dict(id=task['id'],repair_sha256=task['repair_sha256'],records=records,order_groups=[])
    (TARGET/'evaluation/reference_gold.jsonl').write_text(canonical(gold)+'\n')
    kernel=HERE/'source5_portable_public_patch_v5/evaluation'
    for name in ('scorer.py','original_scorer.py','typed_values.py','source_pins.json','review_schema.py'):
        copy(kernel/name,'evaluation/'+name)
    copy(REPAIR/'contract_checks.py','evaluation/contract_checks.py')
    tools=B/'RAN1/UL_formal_source6_evaluation_tools_v1'
    for name in ('score_predictions.py','verify_controls.py'):
        copy(tools/name,'evaluation/'+name)
    copy(HERE/'UL_source6_portable_verify_rebuild_v1.py','verify_rebuild.py')
    (TARGET/'README.md').write_text('''# Separate RAN1 UL formal-source6 snapshot

This source patch adds `formalSourceContentWithTables` to six existing Agreement/Resolution nodes. Every original property, node and edge stays unchanged. The exact original report ZIP, member/XML authentication, complete 6,017-paragraph ordered source projection, six formal body boundaries, literal table and qualifiers are included. The old `content` values are preserved. Inline Work assumption, revisitable language, Note and FFS are part of their actual formal bodies; an adjacent standalone WorkingAssumption is optional.

Run `python3 -B -S verify_rebuild.py --package .` for complete original source verification. To reconstruct a private snapshot add `--base-sql /path/to/frozen/RAN1.sqlite --base-ttl /path/to/frozen/RAN1-body.ttl --out-dir /new/output`. The manifest pins frozen inputs. The reader checks all 89 original SQL tables and all original columns with two-way EXCEPT, allowing only the six new string values in Agreement/Resolution, `_node_record` and `node_property`. RDF is the exact original byte prefix plus six property triples, with no extra separator byte. No service, model or network is started.

Run `python3 -B -S evaluation/verify_controls.py --bundle evaluation` for the existing seven generic and twelve literal content controls. Run `python3 -B -S evaluation/score_predictions.py --predictions PATH` for supplied predictions. The self-contained pinned typed-value kernel scores the six requested complete content strings; it does not assess paraphrase equivalence or the truthfulness of unrequested optional commentary. No answer reroll or historical score transfer is performed.

Two exact nonblind AI semantic judgments, complete original native output and independent SQL records are preserved. Their earlier local candidate/manifest fields `admitted:false`, `gates_remaining` and `question_admissions:0` remain unchanged as historical bytes; the later consolidated actual gate explains their completed status. These are AI development diagnoses with human/expert validation0. The meeting label RAN1#100 and the actual #100-e source-report context are separately supported by retained temporal evidence. Formal report content does not certify normative TSG ratification, all-report semantic extraction completeness or causal adoption.

This separately measured source snapshot does not change the frozen original-question completion index, old source bytes or old model results. Local preparation, public push and fresh anonymous download verification are distinct states.
''')
    manifest=dict(kind='Separate RAN1 UL six formal-source content values portable additive patch',
        status='EXISTING_TWO_AI_NATIVE_SQL_7_PLUS12_CONTROLS_PACKAGED_REQUIRE_FRESH_REBUILD',
        question_id=task['id'],repair_sha256=task['repair_sha256'],source_variant_only=True,
        baseline=dict(SQLite=sql['base'],RDF=graph['base']),
        expected_rebuilt_RDF_sha256=graph['snapshot']['sha256'],reference_rebuilt_SQL_sha256=sql['db']['sha256'],
        original_tables_n=89,new_nodes_n=0,new_edges_n=0,new_property_values_n=6,
        raw_original_ZIP_n=1,authentic_DOCX_members_n=1,whole_report_paragraph_n=6017,
        answer_formal_groups_n=6,baseline_node_n=165418,baseline_edge_n=848228,
        exact_AI_review_n=2,human_expert_validation_n=0,frozen_original_index_changed=False,
        child_native_model_public_calls_n=0)
    manifest['files']=[dict(path=p.relative_to(TARGET).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
        for p in sorted(TARGET.rglob('*')) if p.is_file()]
    assert not any('__pycache__' in f['path'] or f['path'].endswith('.pyc') for f in manifest['files'])
    write('manifest.json',manifest)
    print(json.dumps(dict(status='PACKAGED_REQUIRE_FRESH_SOURCE_REBUILD_AND_CONTROL_CLI',path=str(TARGET),
        manifest_sha256=sha(TARGET/'manifest.json'),files_n=len(manifest['files']),bytes=sum(f['bytes'] for f in manifest['files']))))


if __name__=='__main__':main()
