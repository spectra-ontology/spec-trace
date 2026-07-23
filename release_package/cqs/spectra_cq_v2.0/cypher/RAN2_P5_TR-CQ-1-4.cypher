// SpectraCQ RAN2_P5_TR-CQ-1-4 (RAN2, phase 5) -- 
// Question: List the TRs currently Living (ongoing studies).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)
                  WHERE tr.trStatus = 'Living'
                  RETURN tr.trNumber, tr.trTitle
