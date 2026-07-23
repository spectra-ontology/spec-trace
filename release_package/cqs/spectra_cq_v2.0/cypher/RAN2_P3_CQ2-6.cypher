// SpectraCQ RAN2_P3_CQ2-6 (RAN2, phase 3) -- CQ2_TS
// Question: Return the total number of section-to-section references (cross-reference volume).
// Gold: 1 rows, primary column "totalRefs"

MATCH ()-[:REFERENCES_SECTION]->() RETURN count(*) AS totalRefs
