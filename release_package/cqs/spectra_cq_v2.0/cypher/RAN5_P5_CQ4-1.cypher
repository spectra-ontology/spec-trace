// SpectraCQ RAN5_P5_CQ4-1 (RAN5, phase 5) -- 
// Question: List the TRs targeting Rel-19 (release-scoped studies).
// Gold: 2 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-19'}) RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
