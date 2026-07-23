// SpectraCQ RAN3_P3_CQ2-5 (RAN3, phase 3) -- CQ2_TS
// Question: List cross-spec references from spec 38.401 to other specs (inter-spec dependencies).
// Gold: 10 rows, primary column "sec.sectionId"

MATCH (sec:Section)-[:REFERENCES_SPEC]->(sp:Spec) WHERE sec.sectionId STARTS WITH '38.401-' AND sp.specNumber <> '38.401' RETURN sec.sectionId, sp.specNumber ORDER BY sec.sectionId, sp.specNumber LIMIT 10
