// SpectraCQ P3_CQ021 — CR_TS_변경추적
// Question (English): Return CRs that modify 5+ sections in a single change (large-scope CRs).
// Schema area: classes=['CR', 'Spec'], rels=['MODIFIES']

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) WHERE cr.clausesAffected IS NOT NULL AND size(split(cr.clausesAffected, ',')) >= 5 RETURN cr.tdocNumber, cr.title, cr.clausesAffected, size(split(cr.clausesAffected, ',')) AS affectedCount ORDER BY affectedCount DESC LIMIT 20
