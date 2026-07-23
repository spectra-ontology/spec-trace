// SpectraCQ RAN1_P3_CQ014 (RAN1, phase 3) -- TS
// Question: Find section pairs that reference each other (checking for circular dependencies).
// Gold: 20 rows, primary column "sectionA"

MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section)-[:REFERENCES_SECTION]->(a) WHERE a.sectionId < b.sectionId MATCH (a)-[:BELONGS_TO_SPEC]->(sp1:Spec) MATCH (b)-[:BELONGS_TO_SPEC]->(sp2:Spec) RETURN sp1.specNumber + '-' + a.sectionNumber AS sectionA, sp2.specNumber + '-' + b.sectionNumber AS sectionB ORDER BY a.sectionId, b.sectionId LIMIT 20
