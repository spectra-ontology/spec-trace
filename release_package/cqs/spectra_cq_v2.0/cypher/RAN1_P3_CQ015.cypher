// SpectraCQ RAN1_P3_CQ015 (RAN1, phase 3) -- TS
// Question: What does TS 38.214 Section 5.1 reach two hops out via references? (2-hop dependencies)
// Gold: 6 rows, primary column "via"

MATCH (rk:Spec {specNumber:'38.214'})<-[:BELONGS_TO_SPEC]-(start:Section {sectionNumber:'5.1'}) WHERE rk.specRelease IS NOT NULL WITH start, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (start)-[:REFERENCES_SECTION]->(mid:Section)-[:REFERENCES_SECTION]->(end:Section) MATCH (mid)-[:BELONGS_TO_SPEC]->(sp1:Spec) MATCH (end)-[:BELONGS_TO_SPEC]->(sp2:Spec) RETURN sp1.specNumber + '-' + mid.sectionNumber AS via, sp2.specNumber + '-' + end.sectionNumber AS target, end.sectionTitle LIMIT 20
