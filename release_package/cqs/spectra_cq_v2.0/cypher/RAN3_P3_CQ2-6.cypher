// SpectraCQ RAN3_P3_CQ2-6 (RAN3, phase 3) -- CQ2_TS
// Question: Return the total number of section cross-references (reference-graph size).
// Gold: 1 rows, primary column "totalRefs"

MATCH ()-[:REFERENCES_SECTION]->() RETURN count(*) AS totalRefs
