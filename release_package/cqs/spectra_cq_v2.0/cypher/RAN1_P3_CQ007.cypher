// SpectraCQ RAN1_P3_CQ007 (RAN1, phase 3) -- TS
// Question: Find sections whose title contains 'PDSCH' across all TSs (locating PDSCH content).
// Gold: 57 rows, primary column "sp.specNumber"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PDSCH.*' RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, sec.level ORDER BY sp.specNumber, sec.sectionNumber
