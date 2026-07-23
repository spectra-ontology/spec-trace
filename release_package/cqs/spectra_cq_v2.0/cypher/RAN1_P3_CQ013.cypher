// SpectraCQ RAN1_P3_CQ013 (RAN1, phase 3) -- TS
// Question: Compare cross-section reference density across the TSs (how tightly each is internally linked).
// Gold: 8 rows, primary column "ts"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WITH sp.specNumber AS ts, count(sec) AS secCnt OPTIONAL MATCH (src:Section)-[:REFERENCES_SECTION]->(tgt:Section) WHERE src.sectionId STARTS WITH ts WITH ts, secCnt, count(*) AS refCnt RETURN ts, secCnt, refCnt, round(toFloat(refCnt) / secCnt * 100) / 100 AS refDensity ORDER BY refDensity DESC
