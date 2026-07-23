// SpectraCQ RAN3_P3_CQ1-3 (RAN3, phase 3) -- CQ1_TS
// Question: Return the ancestor path of section 9.3.1.1 in spec 38.413 (locating a subsection in context).
// Gold: 3 rows, primary column "hierarchy"

MATCH (rk:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'9.3.1.1'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH path=(sec)-[:PARENT_SECTION*]->(ancestor:Section) RETURN [n IN nodes(path)|n.sectionId] AS hierarchy
