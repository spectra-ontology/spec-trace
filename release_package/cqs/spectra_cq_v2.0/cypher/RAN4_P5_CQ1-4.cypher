// SpectraCQ RAN4_P5_CQ1-4 (RAN4, phase 5) -- 
// Question: List the TRs currently in draft status (ongoing studies).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport) WHERE tr.trStatus = 'Draft' RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
