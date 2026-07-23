// SpectraCQ RAN1_P5_CQ4-1 (RAN1, phase 5) -- CQ4
// Question: List the TR studies targeting Rel-18 and the type of impact each had on the TSs.
// Gold: 7 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-18'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SPEC]->(sp:Spec) RETURN DISTINCT tr.trNumber, tr.trTitle, tr.trStatus, ti.impactType, sp.specNumber ORDER BY tr.trNumber
