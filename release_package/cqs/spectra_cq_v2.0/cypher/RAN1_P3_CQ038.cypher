// SpectraCQ RAN1_P3_CQ038 (RAN1, phase 3) -- 
// Question: Return the top 10 most-referenced sections and how many CRs modified each (stability of core sections).
// Gold: 8 rows, primary column "sp.specNumber"

MATCH (tgt:Section)<-[:REFERENCES_SECTION]-(src:Section) WITH tgt, count(src) AS refCount ORDER BY refCount DESC LIMIT 10 MATCH (tgt)-[:BELONGS_TO_SPEC]->(sp:Spec) OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(sp) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected CONTAINS tgt.sectionNumber RETURN sp.specNumber, tgt.sectionNumber, tgt.sectionTitle, refCount, count(cr) AS crCount ORDER BY refCount DESC
