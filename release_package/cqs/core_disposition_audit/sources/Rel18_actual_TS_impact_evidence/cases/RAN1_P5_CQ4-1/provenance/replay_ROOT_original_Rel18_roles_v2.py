"""ROOT actual immutable Rel18 source-role diagnostics, with original requested extent."""
import sqlite3,json,hashlib,gzip,datetime
from pathlib import Path
D=Path(__file__).resolve().parent
R=next(p for p in D.parents if (p/'CLAUDE.md').is_file())
B=next(p for p in D.parents if p.name=='overnight_reaudit')
db=B.parent/'relational/RAN1.sqlite'
def pin(p):
 b=p.read_bytes();return {'path':str(p.relative_to(R)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
before=pin(db);assert before['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
c=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
prefix=" FROM TechnicalReport tr JOIN rel_TARGET_RELEASE trr ON trr.src_id=tr.node_id JOIN Release r ON r.node_id=trr.dst_id "
where=" WHERE r.releaseName='Rel-18' "
wi=" JOIN rel_RELATED_TO_WORK_ITEM k ON k.src_id=tr.node_id JOIN WorkItem sw ON sw.node_id=k.dst_id "
candidate=" JOIN WorkItem w ON substr(sw.workItemCode,1,3)='FS_' AND w.workItemCode IN (substr(sw.workItemCode,4),substr(sw.workItemCode,4)||'-Core') "
cr=" JOIN rel_RELATED_TO z ON z.dst_id=w.node_id JOIN CR cr ON cr.node_id=z.src_id "
queries={
'all_TR_release_population':"SELECT tr.*,r.releaseName FROM TechnicalReport tr LEFT JOIN rel_TARGET_RELEASE t ON t.src_id=tr.node_id LEFT JOIN Release r ON r.node_id=t.dst_id ORDER BY tr.trNumber,r.releaseName",
'original_projection':"SELECT DISTINCT tr.trNumber,tr.trTitle,tr.trStatus,ti.impactType,sp.specNumber"+prefix+" LEFT JOIN rel_HAS_TR_IMPACT h ON h.src_id=tr.node_id LEFT JOIN TRImpact ti ON ti.node_id=h.dst_id LEFT JOIN rel_IMPACTS_SPEC m ON m.src_id=ti.node_id LEFT JOIN Spec sp ON sp.node_id=m.dst_id"+where+"ORDER BY tr.trNumber",
'complete_six_original_role_frontier':"SELECT tr.trNumber,ti.*,sp.specNumber,sp.specRelease,s.sectionId,s.sectionTitle"+prefix+" LEFT JOIN rel_HAS_TR_IMPACT h ON h.src_id=tr.node_id LEFT JOIN TRImpact ti ON ti.node_id=h.dst_id LEFT JOIN rel_IMPACTS_SPEC m ON m.src_id=ti.node_id LEFT JOIN Spec sp ON sp.node_id=m.dst_id LEFT JOIN rel_IMPACTS_SECTION k ON k.src_id=ti.node_id LEFT JOIN Section s ON s.node_id=k.dst_id"+where+"ORDER BY tr.trNumber,sp.specNumber,s.sectionId",
'complete_six_direct_study_WI_incidence':"SELECT tr.trNumber,sw.workItemCode,e.*,n.labels"+prefix+wi+" LEFT JOIN edge e ON e.src_id=sw.node_id OR e.dst_id=sw.node_id LEFT JOIN node n ON n.node_id=CASE WHEN e.src_id=sw.node_id THEN e.dst_id ELSE e.src_id END"+where+"ORDER BY tr.trNumber,sw.workItemCode,e.rel_type,e.src_id,e.dst_id",
'complete_six_direct_study_CR':"SELECT tr.trNumber,sw.workItemCode,cr.*"+prefix+wi+" JOIN rel_RELATED_TO z ON z.dst_id=sw.node_id JOIN CR cr ON cr.node_id=z.src_id"+where+"ORDER BY tr.trNumber,cr.id",
'complete_six_naming_candidates':"SELECT tr.trNumber,sw.workItemCode AS study_code,w.*"+prefix+wi+candidate+where+"ORDER BY tr.trNumber,w.workItemCode,w.node_id",
'complete_six_naming_CR_spec_section_projection':"SELECT tr.trNumber,sw.workItemCode AS study_code,w.workItemCode AS candidate_code,cr.*,sp.specNumber,sp.specRelease,s.sectionId,s.sectionTitle"+prefix+wi+candidate+cr+" LEFT JOIN rel_MODIFIES m ON m.src_id=cr.node_id LEFT JOIN Spec sp ON sp.node_id=m.dst_id LEFT JOIN rel_MODIFIES_SECTION v ON v.src_id=cr.node_id LEFT JOIN Section s ON s.node_id=v.dst_id"+where+"ORDER BY tr.trNumber,w.workItemCode,cr.id,sp.specNumber,s.sectionId",
'SBFD_original_CR_source_witness':"SELECT cr.* FROM CR cr WHERE tdocNumber='R1-2504980' ORDER BY node_id"
}
out={}
for name,sql in queries.items():
 rows=[dict(x) for x in c.execute(sql)]
 out[name]={'sql':sql,'sql_sha256':hashlib.sha256(sql.encode()).hexdigest(),'rows':rows,'row_count':len(rows)}
c.close();assert pin(db)==before
p=D/'actual_ROOT_Rel18_complete_roles_SQL_v2.json.gz';assert not p.exists()
p.write_bytes(gzip.compress((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode(),mtime=0))
receipt={'status':'ACTUAL_IMMUTABLE_ORIGINAL_REL18_AND_ALTERNATIVE_ROLE_REPLAY','id':'RAN1_P5_CQ4-1','database':before,'database_unchanged':True,'artifact':pin(p),'roles':{k:v['row_count'] for k,v in out.items()},'API_calls':0,'native_calls':0,'not_a_gold_or_classification':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(D/'actual_ROOT_Rel18_complete_roles_SQL_receipt_v2.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))

