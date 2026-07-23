// SpectraCQ RAN3_P1_CQ1-4 (RAN3, phase 1) -- CQ1_Tdoc
// Question: List the TDocs discussed under Rel-19 (release-scoped document survey).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-19'}) RETURN t.tdocNumber, t.title, t.type ORDER BY t.tdocNumber DESC LIMIT 10
