// SpectraCQ RAN1_P5_CQ5-1 (RAN1, phase 5) -- CQ5_TR
// Question: List the other TRs referenced by TR 38.859 (Ambient IoT for NR) (surveying related studies).
// Gold: 6 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.859'})-[:REFERENCES_TR]->(ref:TechnicalReport) RETURN tr.trNumber, tr.trTitle, ref.trNumber, ref.trTitle ORDER BY ref.trNumber
