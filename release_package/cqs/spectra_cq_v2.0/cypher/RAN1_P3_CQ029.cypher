// SpectraCQ RAN1_P3_CQ029 (RAN1, phase 3) -- 
// Question: Which TSs define antenna-related sections? (locating specs for antenna-port implementation)
// Gold: 23 rows, primary column "sp.specNumber"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*antenna.*' RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, sec.level ORDER BY sp.specNumber, sec.sectionNumber
