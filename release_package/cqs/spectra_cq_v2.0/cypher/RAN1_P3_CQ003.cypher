// SpectraCQ RAN1_P3_CQ003 (RAN1, phase 3) -- TS
// Question: Show the breadcrumb path to TS 38.214 Section 5.1.3.2 (locating a section in the hierarchy).
// Gold: 4 rows, primary column "n.sectionNumber"

MATCH (rk:Spec {specNumber:'38.214'})<-[:BELONGS_TO_SPEC]-(target:Section {sectionNumber:'5.1.3.2'}) WHERE rk.specRelease IS NOT NULL WITH target, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH path = (target)-[:PARENT_SECTION*0..10]->(root:Section) WHERE NOT (root)-[:PARENT_SECTION]->(:Section) UNWIND nodes(path) AS n RETURN n.sectionNumber, n.sectionTitle ORDER BY n.level
