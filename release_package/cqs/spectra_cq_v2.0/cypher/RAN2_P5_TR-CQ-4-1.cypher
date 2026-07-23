// SpectraCQ RAN2_P5_TR-CQ-4-1 (RAN2, phase 5) -- 
// Question: List the Rel-17 TRs with their spec impacts and impact types (release impact map).
// Gold: 2 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'})
                  OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN tr.trNumber, tr.trTitle, collect({spec: s.specNumber, type: imp.impactType}) AS impacts
