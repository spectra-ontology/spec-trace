// SpectraCQ P5_CQ3-1 — CQ3_기술별영향범위
// Question (English): Which TS sections did TR 38.875 (RedCap) impact (low-power-IoT team reference)?
// Schema area: classes=['Section', 'TRImpact', 'TechnicalReport'], rels=['HAS_TR_IMPACT', 'IMPACTS_SECTION']

MATCH (tr:TechnicalReport {trNumber: '38.875'})-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SECTION]->(s:Section) RETURN tr.trNumber, tr.trTitle, ti.impactType, s.sectionId, ti.impactDescription ORDER BY s.sectionId
