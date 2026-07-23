// SpectraCQ RAN2_P3_CQ2-5 (RAN2, phase 3) -- CQ2_TS
// Question: Return the cross-spec references from spec 38.300 into spec 38.331 (inter-spec dependency).
// Gold: 2 rows, primary column "from_section"

MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp1:Spec {specNumber: '38.300'}), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec {specNumber: '38.331'}) RETURN s1.sectionId AS from_section, s2.sectionId AS to_section LIMIT 10
