// SpectraCQ RAN1_P3_CQ011 (RAN1, phase 3) -- TS
// Question: Rank the top 15 most-referenced sections across all eight TSs (identifying core sections).
// Gold: 15 rows, primary column "sp.specNumber"

MATCH (tgt:Section)<-[:REFERENCES_SECTION]-(src:Section) WITH tgt, count(src) AS refByCnt MATCH (tgt)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, tgt.sectionNumber, tgt.sectionTitle, refByCnt ORDER BY refByCnt DESC LIMIT 15
