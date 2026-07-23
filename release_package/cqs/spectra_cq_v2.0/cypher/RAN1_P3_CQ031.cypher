// SpectraCQ RAN1_P3_CQ031 (RAN1, phase 3) -- 
// Question: How are HARQ-related sections distributed across the TSs? (scope of HARQ implementation)
// Gold: 2 rows, primary column "sp.specNumber"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*HARQ.*' RETURN sp.specNumber, count(sec) AS sectionCount, collect(sec.sectionNumber) AS sections ORDER BY sectionCount DESC
