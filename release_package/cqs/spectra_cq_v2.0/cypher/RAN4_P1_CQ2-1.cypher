// SpectraCQ RAN4_P1_CQ2-1 (RAN4, phase 1) -- 
// Question: How many TDocs target Rel-18? (release workload sizing).
// Gold: 1 rows, primary column "cnt"

MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName:'Rel-18'}) RETURN count(t) AS cnt
