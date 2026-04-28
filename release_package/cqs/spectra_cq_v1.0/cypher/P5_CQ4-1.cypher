// SpectraCQ P5_CQ4-1 — CQ4_릴리스별연구영향
// Question (English): List Rel-18-target TRs and each TR's impact types on TSes.
// Schema area: classes=['Release', 'Spec', 'TRImpact', 'TechnicalReport'], rels=['HAS_TR_IMPACT', 'IMPACTS_SPEC', 'TARGET_RELEASE']

MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-18'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SPEC]->(sp:Spec) RETURN DISTINCT tr.trNumber, tr.trTitle, tr.trStatus, ti.impactType, sp.specNumber ORDER BY tr.trNumber
