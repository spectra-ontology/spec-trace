// SpectraCQ RAN2_P3_CQ3-7 (RAN2, phase 3) -- CQ3_CR
// Question: List the CRs whose affected clauses resolve to actual sections of spec 38.331 (clause-to-section matching).
// Gold: 10 rows, primary column "cr.tdocNumber"

MATCH (rk:Spec {specNumber:'38.331'})-[:IN_RELEASE_OF]->(hub:Spec {specNumber:'38.331'}) WHERE hub.specRelease IS NULL WITH rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (cr:CR)-[:MODIFIES]->(hub2:Spec {specNumber:'38.331'}) WHERE hub2.specRelease IS NULL AND cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' UNWIND split(cr.clausesAffected, ',') AS clause WITH cr, rk, trim(clause) AS clause MATCH (s:Section {sectionNumber: clause})-[:BELONGS_TO_SPEC]->(rk) RETURN cr.tdocNumber, clause, s.sectionId ORDER BY cr.tdocNumber, clause, s.sectionId LIMIT 10
