// SpectraCQ RAN1_P5_CQ1-3 (RAN1, phase 5) -- CQ1_TR
// Question: List the TRs still in Draft and the technologies they study (anticipating future standard impact).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trStatus: 'Draft'}) RETURN tr.trNumber, tr.trTitle, tr.scope ORDER BY tr.trNumber
