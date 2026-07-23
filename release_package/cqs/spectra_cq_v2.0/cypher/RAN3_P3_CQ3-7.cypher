// SpectraCQ RAN3_P3_CQ3-7 (RAN3, phase 3) -- CQ3_CR
// Question: List CRs whose affected clauses match actual sections of spec 38.423 (clause-to-section validation).
// Gold: 10 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(hub:Spec {specNumber:'38.423'}) WHERE hub.specRelease IS NULL AND cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' WITH cr, hub, split(cr.clausesAffected, ',') AS clauses MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub) WITH cr, clauses, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC WITH cr, clauses, collect(rk)[0] AS latestRk UNWIND clauses AS clause WITH cr, latestRk, trim(clause) AS clause MATCH (s:Section)-[:BELONGS_TO_SPEC]->(latestRk) WHERE s.sectionNumber = clause RETURN cr.tdocNumber, clause, s.sectionId ORDER BY cr.tdocNumber, clause, s.sectionId LIMIT 10
