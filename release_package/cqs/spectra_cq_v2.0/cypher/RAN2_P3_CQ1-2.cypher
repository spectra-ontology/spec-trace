// SpectraCQ RAN2_P3_CQ1-2 (RAN2, phase 3) -- CQ1_TS
// Question: List the subsections under section 5 of spec 38.321 (MAC structure drill-down).
// Gold: 41 rows, primary column "child.sectionId"

MATCH (rk:Spec {specNumber:'38.321'})<-[:BELONGS_TO_SPEC]-(parent:Section {sectionNumber:'5'}) WHERE rk.specRelease IS NOT NULL WITH parent, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (parent)-[:HAS_SUB_SECTION]->(child:Section) RETURN child.sectionId, child.sectionNumber, child.sectionTitle ORDER BY child.sectionNumber
