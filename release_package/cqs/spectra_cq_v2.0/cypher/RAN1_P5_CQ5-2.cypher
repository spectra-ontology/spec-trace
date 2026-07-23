// SpectraCQ RAN1_P5_CQ5-2 (RAN1, phase 5) -- CQ5_TR
// Question: List the TRs that reference TR 38.802 (RedCap) (reverse lookup, tracing follow-on studies).
// Gold: 4 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.802'})<-[:REFERENCES_TR]-(src:TechnicalReport) RETURN tr.trNumber, tr.trTitle, src.trNumber, src.trTitle ORDER BY src.trNumber
