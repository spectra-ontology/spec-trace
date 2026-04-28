// SpectraCQ P5_CQ2-4 — CQ2_TS반영영향추적
// Question (English): Identify which TR study the TS 38.211 §16 (NR-U physical-layer procedures) section originated from.
// Schema area: classes=['Section', 'TRImpact', 'TechnicalReport'], rels=['HAS_TR_IMPACT', 'IMPACTS_SECTION']

MATCH (s:Section {sectionId: '38.211-16'})<-[:IMPACTS_SECTION]-(ti:TRImpact)<-[:HAS_TR_IMPACT]-(tr:TechnicalReport) RETURN tr.trNumber, tr.trTitle, ti.impactType, ti.impactDescription
