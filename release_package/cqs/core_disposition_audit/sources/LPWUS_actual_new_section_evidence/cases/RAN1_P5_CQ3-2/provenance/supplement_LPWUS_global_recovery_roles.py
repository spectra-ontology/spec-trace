"""Preserve global literal recovery as candidates with complete incident roles."""
import hashlib,json,sqlite3
from reopen_LPWUS_original_source_and_frozen import R,F,DB,load,pin,save,sha
before=pin(DB)
c=sqlite3.connect(DB.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
fields="lower(coalesce(cr.title,'')||' '||coalesce(cr.reasonForChange,'')||' '||coalesce(cr.summaryOfChange,''))"
sql='SELECT cr.* FROM CR cr WHERE '+fields+" LIKE '%lp%wus%' OR "+fields+" LIKE '%lp%wur%' OR "+fields+" LIKE '%low%power%wake%' ORDER BY cr.tdocNumber,cr.node_id"
rows=[dict(x) for x in c.execute(sql)]
sql2='''SELECT cr.node_id AS CR_node,cr.tdocNumber,e.edge_id,e.src_id,e.rel_type,e.dst_id,n.labels FROM CR cr JOIN edge e ON e.src_id=cr.node_id OR e.dst_id=cr.node_id JOIN node n ON n.node_id=CASE WHEN e.src_id=cr.node_id THEN e.dst_id ELSE e.src_id END WHERE '''+fields+" LIKE '%lp%wus%' OR "+fields+" LIKE '%lp%wur%' OR "+fields+" LIKE '%low%power%wake%' ORDER BY cr.tdocNumber,e.edge_id"
rs=[dict(x) for x in c.execute(sql2)]
save('actual_global_literal_recovery_SQL.json',{'all_topic_CR_fields_without_required_Spec_or_WI_edge':{'sql':sql,'sql_sha256':sha(sql.encode()),'rows':rows,'row_count':len(rows)},'all_topic_CR_complete_incident_roles':{'sql':sql2,'sql_sha256':sha(sql2.encode()),'rows':rs,'row_count':len(rs)}})
frontier=load(F/'whole_decoded_LPWUS_literal_frontier.json');base=load(F/'complete_own_and_alternative_role_slice.json')
core=set(base['core_node_ids'])|{x['node_id'] for x in frontier['literal_values']}|{x['node_id'] for x in rows}
marks=','.join('?' for _ in core)
edges=[dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id IN ('+marks+') OR dst_id IN ('+marks+') ORDER BY edge_id',tuple(sorted(core))*2)]
nodes={x['node_id'] for x in base['records']}|core|{e[k] for e in edges for k in ['src_id','dst_id']}
records=[dict(x) for n in sorted(nodes) for x in c.execute('SELECT * FROM _node_record WHERE node_id=?',(n,))]
save('expanded_complete_literal_and_own_role_slice.json',{'core_node_ids':sorted(core),'records':records,'edges':edges,'scope':'Original 42 complete-incidence core plus every global LP-WUS/TR38.869/low-power-wake property-literal recovery node and every independently queried topic CR. Complete incidence is retained for these explicit recovery nodes; literal correspondence remains candidate evidence, not a causal oracle.'})
c.close();assert before==pin(DB)
save('actual_global_recovery_receipt.json',{'status':'PASS_GLOBAL_RECOVERY_ROLE_PRESERVATION','global_literal_nodes':len({x['node_id'] for x in frontier['literal_values']}),'topic_CR_nodes_without_Spec_WI_prerequisite':len(rows),'all_topic_CR_incident_edges':len(rs),'complete_incident_core_nodes':len(core),'records':len(records),'edges':len(edges),'sqlite_before':before,'sqlite_after':pin(DB),'API_calls':0,'native_calls':0,'public_writes':0})
print(json.dumps({'status':'PASS','topic_CR_nodes':len(rows),'core':len(core),'records':len(records),'edges':len(edges)}))
