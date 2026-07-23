// SpectraCQ RAN4_P5_CQ5-2 (RAN4, phase 5) -- 
// Question: List the TRs that reference TR 38.803 (inbound TR citations).
// Gold: 6 rows, primary column "ref.trNumber"

MATCH (ref:TechnicalReport)-[:REFERENCES_TR]->(tr:TechnicalReport {trNumber: '38.803'}) RETURN ref.trNumber, ref.trTitle ORDER BY ref.trNumber
