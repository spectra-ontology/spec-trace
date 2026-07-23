// SpectraCQ RAN1_P5_CQ2-4 (RAN1, phase 5) -- CQ2_TS
// Question: Which TR study did TS 38.211 Section 8 (Sidelink) originate from?
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (s:Section {sectionId: '38.211-Rel-19-8'})<-[:IMPACTS_SECTION]-(ti:TRImpact)<-[:HAS_TR_IMPACT]-(tr:TechnicalReport) RETURN tr.trNumber, tr.trTitle, ti.impactType, ti.impactDescription
