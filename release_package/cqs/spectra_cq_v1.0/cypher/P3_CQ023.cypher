// SpectraCQ P3_CQ023 — Resolution_TS_의사결정
// Question (English): Return the count of Agreements that approved CRs modifying TS 38.214 (decision-making activity).
// Schema area: classes=['Agreement', 'CR', 'Spec'], rels=['MODIFIES', 'REFERENCES']

MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) RETURN count(DISTINCT agr) AS agrCount
