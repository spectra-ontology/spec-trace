// SpectraCQ P5_CQ5-1 — CQ5_TR간참조관계
// Question (English): Return TRs that TR 38.859 (Ambient IoT for NR) references (related-research overview).
// Schema area: classes=['TechnicalReport'], rels=['REFERENCES_TR']

MATCH (tr:TechnicalReport {trNumber: '38.859'})-[:REFERENCES_TR]->(ref:TechnicalReport) RETURN tr.trNumber, tr.trTitle, ref.trNumber, ref.trTitle ORDER BY ref.trNumber
