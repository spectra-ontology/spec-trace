// SpectraCQ P5_CQ4-3 — CQ4_릴리스별연구영향
// Question (English): Return the conclusions and TS-impact status of TR 38.808 (52.6 GHz--71 GHz) — mmWave product planning.
// Schema area: classes=['Spec', 'TRImpact', 'TechnicalReport'], rels=['HAS_TR_IMPACT', 'IMPACTS_SPEC']

MATCH (tr:TechnicalReport {trNumber: '38.808'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SPEC]->(sp:Spec) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.conclusions, ti.impactType, sp.specNumber
