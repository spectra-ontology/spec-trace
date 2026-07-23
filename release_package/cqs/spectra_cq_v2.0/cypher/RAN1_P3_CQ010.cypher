// SpectraCQ RAN1_P3_CQ010 (RAN1, phase 3) -- TS
// Question: Which sections reference TS 38.211 Section 5.2.1 (Pseudo-random sequence)? (finding users of this base algorithm)
// Gold: 26 rows, primary column "src.sectionNumber"

MATCH (rk:Spec {specNumber:'38.211'})<-[:BELONGS_TO_SPEC]-(tgt:Section {sectionNumber:'5.2.1'}) WHERE rk.specRelease IS NOT NULL WITH tgt, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (tgt)<-[:REFERENCES_SECTION]-(src:Section) RETURN src.sectionNumber, src.sectionTitle ORDER BY src.sectionNumber LIMIT 30
