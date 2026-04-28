// SpectraCQ P4_CQ4-1 — CQ4_연계분석
// Question (English): Return change-reason patterns for recent CRs modifying TS 38.214 §5.1.5 (PDSCH MIMO, most-modified).
// Schema area: classes=['CR', 'Spec'], rels=['MODIFIES']

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) WHERE cr.clausesAffected CONTAINS '5.1.5' AND cr.reasonForChange IS NOT NULL RETURN '38.214-5.1.5' AS sectionId, cr.tdocNumber, cr.reasonForChange ORDER BY cr.tdocNumber DESC LIMIT 15
