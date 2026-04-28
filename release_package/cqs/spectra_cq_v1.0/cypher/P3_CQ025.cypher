// SpectraCQ P3_CQ025 — Resolution_TS_의사결정
// Question (English): Summarize Agreement counts per TS (where consensus is most active).
// Schema area: classes=['Agreement', 'CR', 'Spec'], rels=['MODIFIES', 'REFERENCES']

MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] RETURN sp.specNumber, count(DISTINCT agr) AS agrCount ORDER BY agrCount DESC
