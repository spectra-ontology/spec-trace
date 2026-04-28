// SpectraCQ P5_CQ2-1 — CQ2_TS반영영향추적
// Question (English): Did TR 38.769 (Ambient IoT) generate a new TS? If so, which TS and impact type?
// Schema area: classes=['Spec', 'TRImpact', 'TechnicalReport'], rels=['HAS_TR_IMPACT', 'IMPACTS_SPEC']

MATCH (tr:TechnicalReport {trNumber: '38.769'})-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SPEC]->(sp:Spec) RETURN tr.trNumber, tr.trTitle, ti.impactType, sp.specNumber, ti.impactDescription
