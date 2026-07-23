// SpectraCQ RAN2_P4_CQ4-1 (RAN2, phase 4) -- CQ4
// Question: List the change reasons of CRs modifying section 5.3.5 of spec 38.331 (section change history).
// Gold: 10 rows, primary column "tdocNumber"

MATCH (sec:Section {sectionNumber: '5.3.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason ORDER BY toInteger(replace(sp.specRelease,'Rel-','')) DESC, c.tdocNumber DESC LIMIT 10
