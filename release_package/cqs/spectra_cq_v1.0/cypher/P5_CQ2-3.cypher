// SpectraCQ P5_CQ2-3 — CQ2_TS반영영향추적
// Question (English): Return all TRs that affected TS 38.211 with their impact types (TS 38.211 revision history).
// Schema area: classes=['Spec', 'TRImpact', 'TechnicalReport'], rels=['HAS_TR_IMPACT', 'IMPACTS_SPEC']

MATCH (sp:Spec {specNumber: '38.211'})<-[:IMPACTS_SPEC]-(ti:TRImpact)<-[:HAS_TR_IMPACT]-(tr:TechnicalReport) RETURN tr.trNumber, tr.trTitle, ti.impactType, ti.affectedSection, ti.impactDescription ORDER BY tr.trNumber
