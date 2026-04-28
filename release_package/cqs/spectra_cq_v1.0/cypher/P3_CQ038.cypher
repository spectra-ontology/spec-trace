// SpectraCQ P3_CQ038 — 통합분석
// Question (English): Return the top-10 most-referenced sections and their CR-modification count (stability assessment).
// Schema area: classes=['CR', 'Section', 'Spec'], rels=['BELONGS_TO_SPEC', 'MODIFIES', 'REFERENCES_SECTION']

MATCH (tgt:Section)<-[:REFERENCES_SECTION]-(src:Section) WITH tgt, count(src) AS refCount ORDER BY refCount DESC LIMIT 10 MATCH (tgt)-[:BELONGS_TO_SPEC]->(sp:Spec) OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(sp) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected CONTAINS tgt.sectionNumber RETURN sp.specNumber, tgt.sectionNumber, tgt.sectionTitle, refCount, count(cr) AS crCount ORDER BY refCount DESC
