// SpectraCQ P5_CQ3-2 — CQ3_기술별영향범위
// Question (English): Which new sections did TR 38.869 (LP-WUS) add to TS 38.211 and 38.213 (UE power-saving feature implementation)?
// Schema area: classes=['Section', 'TRImpact', 'TechnicalReport'], rels=['HAS_TR_IMPACT', 'IMPACTS_SECTION']

MATCH (tr:TechnicalReport {trNumber: '38.869'})-[:HAS_TR_IMPACT]->(ti:TRImpact {impactType: 'NewSection'})-[:IMPACTS_SECTION]->(s:Section) RETURN tr.trNumber, ti.affectedSection, s.sectionId, ti.impactDescription ORDER BY s.sectionId
