// SpectraCQ RAN5_P3_CQ2-1 (RAN5, phase 3) -- CQ2_TS
// Question: Which sections does section 6.5D.3.3.5 of TS 38.521-1 reference? (outgoing cross-references)
// Gold: 16 rows, primary column "b.sectionId"

MATCH (rk:Spec {specNumber:'38.521-1'})<-[:BELONGS_TO_SPEC]-(a:Section {sectionNumber:'6.5D.3.3.5'}) WHERE rk.specRelease IS NOT NULL WITH a,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (a)-[:REFERENCES_SECTION]->(b:Section) RETURN b.sectionId, b.sectionTitle ORDER BY b.sectionNumber LIMIT 25
