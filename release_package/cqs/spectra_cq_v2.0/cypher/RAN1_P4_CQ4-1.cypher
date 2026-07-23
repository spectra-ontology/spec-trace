// SpectraCQ RAN1_P4_CQ4-1 (RAN1, phase 4) -- CQ4
// Question: What patterns run through the reason-for-change of recent CRs modifying TS 38.214 Section 5.1.5 (PDSCH MIMO, the most-revised section)?
// Gold: 15 rows, primary column "sectionId"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) WHERE cr.clausesAffected CONTAINS '5.1.5' AND cr.reasonForChange IS NOT NULL RETURN '38.214-5.1.5' AS sectionId, cr.tdocNumber, cr.reasonForChange ORDER BY cr.tdocNumber DESC LIMIT 15
