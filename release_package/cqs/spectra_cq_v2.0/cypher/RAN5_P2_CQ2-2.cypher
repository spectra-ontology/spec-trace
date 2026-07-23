// SpectraCQ RAN5_P2_CQ2-2 (RAN5, phase 2) -- CQ2_Tdoc-Resolution
// Question: For each resolution, list the TDocs it references (resolution-to-document mapping).
// Gold: 10 rows, primary column "rid"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH r.resolutionId AS rid, collect(t.tdocNumber) AS tdocs, count(t) AS cnt ORDER BY cnt DESC, rid LIMIT 10 RETURN rid, cnt, tdocs[..5] AS sample_tdocs
