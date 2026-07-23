// SpectraCQ RAN5_P3_CQ1-3 (RAN5, phase 3) -- CQ1_TS
// Question: Return the ancestor path of section 6.2.1 in TS 38.521-1 (locating a clause in the hierarchy).
// Gold: 2 rows, primary column "hierarchy"

MATCH (rk:Spec {specNumber:'38.521-1'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'6.2.1'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH path = (sec)-[:PARENT_SECTION*]->(ancestor:Section) RETURN [n IN nodes(path) | n.sectionId] AS hierarchy
