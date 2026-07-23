// SpectraCQ RAN4_P1_CQ5-4 (RAN4, phase 1) -- 
// Question: Show the distribution of TDocs by release (per-release volume).
// Gold: 10 rows, primary column "r.releaseName"

MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release) RETURN r.releaseName, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
