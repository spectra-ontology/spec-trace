// SpectraCQ RAN1_P4_CQ4-3 (RAN1, phase 4) -- CQ4
// Question: List every TS section changed by CRs under Work Item NR_MIMO_evo_DL_UL-Core (NR MIMO Evolution), with each change's reason.
// Gold: 15 rows, primary column "wi.workItemCode"

MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_MIMO_evo_DL_UL-Core'}) MATCH (cr)-[:MODIFIES]->(sp:Spec) WHERE cr.clausesAffected IS NOT NULL AND cr.reasonForChange IS NOT NULL RETURN wi.workItemCode, sp.specNumber + '-' + cr.clausesAffected AS sectionId, cr.tdocNumber, cr.reasonForChange ORDER BY cr.tdocNumber DESC LIMIT 15
