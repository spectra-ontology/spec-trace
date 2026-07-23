// SpectraCQ RAN4_P4_CQ4-1 (RAN4, phase 4) -- CQ4
// Question: List the reasons-for-change of CRs that modify section 7.3A.5 of spec 38.101-1 (clause-level change rationale).
// Gold: 10 rows, primary column "tdocNumber"

MATCH (sec:Section {sectionNumber: '7.3A.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.101-1'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason ORDER BY toInteger(replace(sp.specRelease,'Rel-','')) DESC, c.tdocNumber DESC LIMIT 10
