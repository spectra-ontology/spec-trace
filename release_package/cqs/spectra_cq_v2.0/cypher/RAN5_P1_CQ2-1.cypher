// SpectraCQ RAN5_P1_CQ2-1 (RAN5, phase 1) -- 
// Question: How many TDocs target Rel-18? (release volume check)
// Gold: 1 rows, primary column "cnt"

MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName:'Rel-18'}) RETURN count(t) AS cnt
