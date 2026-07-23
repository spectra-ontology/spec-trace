// SpectraCQ RAN1_P5_CQ3-2 (RAN1, phase 5) -- CQ3
// Question: Which new sections did the LP-WUS (Low-Power Wake-Up Signal) study TR 38.869 add to TS 38.211 and 38.213? (UE power-saving implementation)
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.869'})-[:HAS_TR_IMPACT]->(ti:TRImpact {impactType: 'NewSection'})-[:IMPACTS_SECTION]->(s:Section) RETURN tr.trNumber, ti.affectedSection, s.sectionId, ti.impactDescription ORDER BY s.sectionId
