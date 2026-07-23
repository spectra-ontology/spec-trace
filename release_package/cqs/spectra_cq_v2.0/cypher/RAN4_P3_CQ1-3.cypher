// SpectraCQ RAN4_P3_CQ1-3 (RAN4, phase 3) -- CQ1_TS
// Question: Return the parent-section path of section 10.1.1 in spec 38.133 (clause hierarchy tracing).
// Gold: 2 rows, primary column "hierarchy"

MATCH (rk:Spec {specNumber:'38.133'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'10.1.1'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH path=(sec)-[:PARENT_SECTION*]->(ancestor:Section) RETURN [n IN nodes(path)|n.sectionId] AS hierarchy
