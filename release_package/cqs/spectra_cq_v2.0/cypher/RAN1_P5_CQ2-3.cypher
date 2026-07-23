// SpectraCQ RAN1_P5_CQ2-3 (RAN1, phase 5) -- CQ2_TS
// Question: List every TR that affected TS 38.211 and its impact type (revision history of 38.211).
// Gold: 11 rows, primary column "tr.trNumber"

MATCH (sp:Spec {specNumber: '38.211'})<-[:IMPACTS_SPEC]-(ti:TRImpact)<-[:HAS_TR_IMPACT]-(tr:TechnicalReport) RETURN tr.trNumber, tr.trTitle, ti.impactType, ti.affectedSection, ti.impactDescription ORDER BY tr.trNumber
