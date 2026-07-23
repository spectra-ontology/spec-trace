// SpectraCQ RAN4_P5_CQ1-1 (RAN4, phase 5) -- 
// Question: List the completed TRs targeting Rel-17 (release study inventory).
// Gold: 15 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'}) WHERE tr.trStatus = 'Completed' RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
