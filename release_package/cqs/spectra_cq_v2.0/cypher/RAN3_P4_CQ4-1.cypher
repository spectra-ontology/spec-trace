// SpectraCQ RAN3_P4_CQ4-1 (RAN3, phase 4) -- CQ4
// Question: List the change reasons of CRs modifying section 9.4.5 of spec 38.473 (section-level change rationale).
// Gold: 10 rows, primary column "tdocNumber"

MATCH (sec:Section {sectionNumber: '9.4.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.473'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason ORDER BY toInteger(replace(sp.specRelease,'Rel-','')) DESC, c.tdocNumber DESC LIMIT 10
