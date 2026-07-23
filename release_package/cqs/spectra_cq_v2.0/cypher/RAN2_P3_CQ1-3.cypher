// SpectraCQ RAN2_P3_CQ1-3 (RAN2, phase 3) -- CQ1_TS
// Question: Return the ancestor path of section 5.3.5 in spec 38.331 (breadcrumb location).
// Gold: 2 rows, primary column "breadcrumb"

MATCH (rk:Spec {specNumber:'38.331'})<-[:BELONGS_TO_SPEC]-(s:Section {sectionNumber:'5.3.5'}) WHERE rk.specRelease IS NOT NULL WITH s, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH path = (s)-[:PARENT_SECTION*]->(ancestor:Section) RETURN [n IN nodes(path) | n.sectionId] AS breadcrumb
