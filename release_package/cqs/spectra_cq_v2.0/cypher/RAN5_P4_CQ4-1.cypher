// SpectraCQ RAN5_P4_CQ4-1 (RAN5, phase 4) -- CQ4
// Question: Give the change reasons of CRs modifying section 6.2 of TS 38.521-1 (clause-level rationale).
// Gold: 7 rows, primary column "tdocNumber"

MATCH (sec:Section {sectionNumber: '6.2'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-1'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason ORDER BY toInteger(replace(sp.specRelease,'Rel-','')) DESC, c.tdocNumber DESC LIMIT 10
