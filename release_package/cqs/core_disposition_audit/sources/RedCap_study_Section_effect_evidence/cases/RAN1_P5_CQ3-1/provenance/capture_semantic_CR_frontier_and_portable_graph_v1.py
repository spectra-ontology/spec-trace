"""Complete source-record slice for every observed RedCap CR recovery candidate."""
import hashlib,json,sqlite3,sys
from pathlib import Path
if sys.flags.optimize:raise SystemExit('Enabled checks required')
L=Path(__file__).resolve().parent;R=next(p for p in L.parents if (p/'CLAUDE.md').is_file())
D=L/'actual_original_and_frozen_v2';A=L/'actual_amendment_frontier_v1';O=L/'actual_complete_recovery_frontier_v1'
DB=R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/authorized_incremental48_OpenRouter_release/evaluation/runtime/relational/RAN1.sqlite'
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def save(n,x):
 p=O/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');return pin(p)
def main():
 assert not O.exists();O.mkdir(parents=True)
 before=pin(DB);c=sqlite3.connect(DB.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
 frontier=json.loads((D/'whole_decoded_frozen_TR_and_RedCap_literal_frontier.json').read_text())
 sem={x['node_id'] for x in frontier['hits']['RedCap_semantic'] if 'CR' in x['labels']}
 base=json.loads((D/'complete_own_TR_impacts_RedCap_workitems_and_CR_incident_slice.json').read_text())
 literal=json.loads((A/'complete_TR_number_study_item_and_RP_literal_frontier_incident_slice.json').read_text())
 core=set(base['core_node_ids'])|set(literal['core_node_ids'])|sem
 marks=','.join('?' for _ in core);args=tuple(sorted(core))*2
 edges=[dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id IN ('+marks+') OR dst_id IN ('+marks+') ORDER BY edge_id',args)]
 identity_only={x[0] for x in c.execute('SELECT node_id FROM WorkItem')}
 identity_only|={r['node_id'] for r in json.loads((D/'actual_immutable_SQL_diagnostics.json').read_text())['own_affected_sections_same_number_all_spec_releases']['rows']}
 ids=core|identity_only|{e[k] for e in edges for k in ['src_id','dst_id']}
 records=[dict(x) for n in sorted(ids) for x in c.execute('SELECT * FROM _node_record WHERE node_id=?',(n,))]
 source=save('source_records_and_edges.json',{'complete_incident_core_node_ids':sorted(core),'identity_only_additional_node_ids':sorted(identity_only-core),'records':records,'edges':edges,'scope':'Every incident edge for the named TR/impact/number/RP/study-item frontier, every RedCap-named WI and incident CR, and every full-corpus RedCap/reduced-capability semantic CR candidate. All WorkItem identities and same-number Section candidates are retained as identity-only additions. Endpoints are original _node_record records; diagnostic SQL outputs do not supply graph properties.'})
 qs={'all_semantic_CR_candidates':'''SELECT cr.*,w.workItemCode,sp.specNumber,s.sectionId,s.sectionTitle FROM CR cr LEFT JOIN rel_RELATED_TO r ON r.src_id=cr.node_id LEFT JOIN WorkItem w ON w.node_id=r.dst_id LEFT JOIN rel_MODIFIES m ON m.src_id=cr.node_id LEFT JOIN Spec sp ON sp.node_id=m.dst_id LEFT JOIN rel_MODIFIES_SECTION k ON k.src_id=cr.node_id LEFT JOIN Section s ON s.node_id=k.dst_id WHERE cr.node_id IN ('''+','.join(str(n) for n in sorted(sem))+''') ORDER BY cr.id,w.workItemCode,sp.specNumber,s.sectionId'''}
 out={}
 for name,sql in qs.items():
  rows=[dict(x) for x in c.execute(sql)];out[name]={'sql':sql,'sql_sha256':sha(sql.encode()),'rows':rows,'row_count':len(rows),'candidate_node_ids_from_original_full_property_scan':sorted(sem)}
 save('actual_additional_SQL_diagnostics.json',out)
 named_ids={r['node_id'] for r in json.loads((D/'actual_immutable_SQL_diagnostics.json').read_text())['all_RedCap_named_workitem_CR_TS_Section_candidates']['rows'] if r['id']}
 extra=sem-named_ids
 save('additional_semantic_CR_frozen_fields.json',{'all_semantic_CR_n':len(sem),'additional_to_all_named_WI_CR_n':len(extra),'rows':[dict(x) for n in sorted(extra) for x in c.execute('SELECT * FROM CR WHERE node_id=?',(n,))],'meaning':'Exhausts observed full-property semantic CR recovery candidates beyond named work items; these are additional candidates rather than an attributed study-effect oracle.'})
 c.close();after=pin(DB);assert before==after
 save('actual_complete_recovery_frontier_receipt.json',{'status':'COMPLETE_OBSERVED_RECOVERY_CANDIDATE_CAPTURE','all_semantic_CR_n':len(sem),'additional_to_named_WI_CR_n':len(extra),'complete_incident_core_n':len(core),'original_record_n':len(records),'incident_edge_n':len(edges),'source_graph':source,'SQLite_before':before,'SQLite_after':after,'API_calls':0,'native_calls':0,'public_mutations':0,'queue_mutations':0})
 print(json.dumps({'all_semantic_CR_n':len(sem),'additional_CR_n':len(extra),'core_n':len(core),'records_n':len(records),'edges_n':len(edges)}))
if __name__=='__main__':main()
