// SpectraCQ P5_CQ2-5 — CQ2_TS반영영향추적
// Question (English): List TRs that produced an entirely new TS (NewTS impact type) with the new TS number.
// Schema area: classes=['Spec', 'TRImpact', 'TechnicalReport'], rels=['HAS_TR_IMPACT', 'IMPACTS_SPEC']

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(ti:TRImpact {impactType: 'NewTS'})-[:IMPACTS_SPEC]->(sp:Spec) RETURN DISTINCT tr.trNumber, tr.trTitle, sp.specNumber, ti.impactDescription ORDER BY tr.trNumber
