// SpectraCQ RAN1_P3_CQ021 (RAN1, phase 3) -- CR_TS
// Question: Which are the large CRs touching many clauses? List CRs affecting five or more sections of TS 38.214.
// Gold: 20 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) WHERE cr.clausesAffected IS NOT NULL AND size(split(cr.clausesAffected, ',')) >= 5 RETURN cr.tdocNumber, cr.title, cr.clausesAffected, size(split(cr.clausesAffected, ',')) AS affectedCount ORDER BY affectedCount DESC, cr.tdocNumber LIMIT 20
