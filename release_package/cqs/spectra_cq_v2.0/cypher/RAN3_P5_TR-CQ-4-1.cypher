// SpectraCQ RAN3_P5_TR-CQ-4-1 (RAN3, phase 5) -- 
// Question: Return the Rel-17-targeted TRs with their spec-impact types (release study impact map).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'})
                  OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN tr.trNumber, tr.trTitle, collect({spec: s.specNumber, type: imp.impactType}) AS impacts
