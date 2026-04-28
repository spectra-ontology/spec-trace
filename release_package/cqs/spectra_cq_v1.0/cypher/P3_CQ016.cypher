// SpectraCQ P3_CQ016 — CR_TS_변경추적
// Question (English): Return the total CR count for TS 38.214 (amendment activity).
// Schema area: classes=['CR', 'Spec'], rels=['MODIFIES']

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) RETURN count(cr) AS totalCR
