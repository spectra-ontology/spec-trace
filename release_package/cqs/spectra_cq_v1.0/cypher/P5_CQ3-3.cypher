// SpectraCQ P5_CQ3-3 — CQ3_기술별영향범위
// Question (English): Return TR 38.824 (URLLC) impacts on TS 38.211 and 38.214 with details (low-latency industrial communications).
// Schema area: classes=['Spec', 'TRImpact', 'TechnicalReport'], rels=['HAS_TR_IMPACT', 'IMPACTS_SPEC']

MATCH (tr:TechnicalReport {trNumber: '38.824'})-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SPEC]->(sp:Spec) RETURN tr.trNumber, sp.specNumber, ti.impactType, ti.affectedSection, ti.impactDescription ORDER BY sp.specNumber
