// SpectraCQ RAN1_P5_CQ3-1 (RAN1, phase 5) -- CQ3
// Question: Which TS sections did the RedCap (Reduced Capability) study TR 38.875 affect? (low-power IoT reference)
// Gold: 2 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.875'})-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SECTION]->(s:Section) RETURN tr.trNumber, tr.trTitle, ti.impactType, s.sectionId, ti.impactDescription ORDER BY s.sectionId
