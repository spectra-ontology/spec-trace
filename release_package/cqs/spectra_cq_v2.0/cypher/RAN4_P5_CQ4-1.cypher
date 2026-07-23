// SpectraCQ RAN4_P5_CQ4-1 (RAN4, phase 5) -- 
// Question: List the Rel-17 study TRs and their impact types (release study overview).
// Gold: 22 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN tr.trNumber, tr.trTitle, collect(DISTINCT imp.impactType) AS impactTypes ORDER BY tr.trNumber
