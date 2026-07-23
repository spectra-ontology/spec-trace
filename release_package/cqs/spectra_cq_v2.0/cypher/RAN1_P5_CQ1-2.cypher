// SpectraCQ RAN1_P5_CQ1-2 (RAN1, phase 5) -- CQ1_TR
// Question: Is the NR-U study TR 38.889 completed and ready to fold into the standard? Return its status and conclusions.
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.889'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.conclusions
