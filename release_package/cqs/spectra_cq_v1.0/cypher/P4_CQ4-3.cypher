// SpectraCQ P4_CQ4-3 — CQ4_연계분석
// Question (English): Return the full list of TS sections modified by CRs from Work Item NR_MIMO_evo_DL_UL-Core, with each change reason.
// Schema area: classes=['CR', 'Spec', 'WorkItem'], rels=['MODIFIES', 'RELATED_TO']

MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_MIMO_evo_DL_UL-Core'}) MATCH (cr)-[:MODIFIES]->(sp:Spec) WHERE cr.clausesAffected IS NOT NULL AND cr.reasonForChange IS NOT NULL RETURN wi.workItemCode, sp.specNumber + '-' + cr.clausesAffected AS sectionId, cr.tdocNumber, cr.reasonForChange ORDER BY cr.tdocNumber DESC LIMIT 15
