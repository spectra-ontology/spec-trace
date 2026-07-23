// SpectraCQ RAN1_P3_CQ012 (RAN1, phase 3) -- TS
// Question: Are there mutually referencing section pairs within TS 38.213? (tightly coupled procedures)
// Gold: 20 rows, primary column "sectionA"

MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section)-[:REFERENCES_SECTION]->(a) WHERE a.sectionId STARTS WITH '38.213' AND b.sectionId STARTS WITH '38.213' AND a.sectionId < b.sectionId RETURN a.sectionNumber AS sectionA, a.sectionTitle AS titleA, b.sectionNumber AS sectionB, b.sectionTitle AS titleB ORDER BY a.sectionId, b.sectionId LIMIT 20
