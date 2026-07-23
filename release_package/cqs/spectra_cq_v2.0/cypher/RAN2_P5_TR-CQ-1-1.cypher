// SpectraCQ RAN2_P5_TR-CQ-1-1 (RAN2, phase 5) -- 
// Question: List the completed TRs targeting Rel-17 (release study inventory).
// Gold: 2 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release)
                  WHERE r.releaseName = 'Rel-17' AND tr.trStatus = 'Completed'
                  RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
