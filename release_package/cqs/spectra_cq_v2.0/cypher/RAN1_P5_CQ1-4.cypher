// SpectraCQ RAN1_P5_CQ1-4 (RAN1, phase 5) -- CQ1_TR
// Question: Return the scope and conclusions of TR 38.885 on V2X Sidelink (automotive-communications product planning).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.885'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.scope, tr.conclusions
