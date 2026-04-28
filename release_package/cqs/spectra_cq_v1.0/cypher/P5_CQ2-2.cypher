// SpectraCQ P5_CQ2-2 — CQ2_TS반영영향추적
// Question (English): Which new sections did TR 38.889 (NR-U) add to TS 38.211--38.214 (PHY-team reference)?
// Schema area: classes=['Section', 'TRImpact', 'TechnicalReport'], rels=['HAS_TR_IMPACT', 'IMPACTS_SECTION']

MATCH (tr:TechnicalReport {trNumber: '38.889'})-[:HAS_TR_IMPACT]->(ti:TRImpact {impactType: 'NewSection'})-[:IMPACTS_SECTION]->(s:Section) RETURN tr.trNumber, ti.affectedSection, s.sectionId, ti.impactDescription ORDER BY s.sectionId
