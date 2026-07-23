// SpectraCQ RAN1_P5_CQ4-2 (RAN1, phase 5) -- CQ4
// Question: Return the current status and scope of the 6G Radio study TR 38.760-1 (next-generation roadmap review).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.760-1'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.trVersion, tr.scope
