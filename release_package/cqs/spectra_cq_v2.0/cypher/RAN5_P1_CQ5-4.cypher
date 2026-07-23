// SpectraCQ RAN5_P1_CQ5-4 (RAN5, phase 1) -- 
// Question: Break down TDocs by target release (release distribution).
// Gold: 10 rows, primary column "r.releaseName"

MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release) RETURN r.releaseName, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
