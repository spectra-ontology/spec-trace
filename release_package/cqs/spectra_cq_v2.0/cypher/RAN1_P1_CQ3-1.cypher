// SpectraCQ RAN1_P1_CQ3-1 (RAN1, phase 1) -- CQ3
// Question: List the TDocs Samsung submitted under Work Item NR_MIMO_evo_DL_UL-Core (NR MIMO Evolution).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (c:Company {companyName: 'Samsung'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_MIMO_evo_DL_UL-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10
