// SpectraCQ RAN1_P3_CQ035 (RAN1, phase 3) -- 
// Question: Which sections mention measurement or reporting? (scope for measurement-reporting implementation)
// Gold: 20 rows, primary column "sp.specNumber"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*(measurement|reporting).*' RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle ORDER BY sp.specNumber, sec.sectionNumber LIMIT 20
