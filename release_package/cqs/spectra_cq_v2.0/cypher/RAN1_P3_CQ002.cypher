// SpectraCQ RAN1_P3_CQ002 (RAN1, phase 3) -- TS
// Question: Show the sub-structure under TS 38.214 Section 5.1 (implementing PDSCH procedures).
// Gold: 7 rows, primary column "sub.sectionNumber"

MATCH (rk:Spec {specNumber:'38.214'})<-[:BELONGS_TO_SPEC]-(root:Section {sectionNumber:'5.1'}) WHERE rk.specRelease IS NOT NULL WITH root, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (root)-[:HAS_SUB_SECTION]->(sub:Section) RETURN sub.sectionNumber, sub.sectionTitle ORDER BY sub.sectionNumber
