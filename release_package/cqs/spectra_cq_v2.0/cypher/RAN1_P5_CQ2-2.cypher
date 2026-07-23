// SpectraCQ RAN1_P5_CQ2-2 (RAN1, phase 5) -- CQ2_TS
// Question: Which new sections did the NR-U study (TR 38.889) add to TS 38.211-38.214? (PHY-layer reference)
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.889'})-[:HAS_TR_IMPACT]->(ti:TRImpact {impactType: 'NewSection'})-[:IMPACTS_SECTION]->(s:Section) RETURN tr.trNumber, ti.affectedSection, s.sectionId, ti.impactDescription ORDER BY s.sectionId
