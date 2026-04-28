// Multi-hop traceability: which TDoc(s) motivated the current text of TS 38.214 §5.1.3?
//
// Pattern: Section <- modifiesSection <- CR -> presentedAt -> Meeting <- madeAt <- Resolution -> references -> Tdoc.
// The Resolution may be a WorkingAssumption (which optionally promotedTo an Agreement)
// or an Agreement made directly at the meeting; the pattern below handles both via
// OPTIONAL MATCH so the query degrades gracefully on per-WG KGs that do not emit
// WorkingAssumption resolutions (e.g., RAN5, scoped to conformance testing, records
// only Conclusions; running this query against a Conclusion-only KG returns no rows
// rather than an error). The released `examples/end_to_end/` exercises the WA->Agreement
// branch against synthetic data; on a live SPECTRA-conformant KG it returns the
// contributions that justify the current text of any TS section.

MATCH (sec:Section {sectionId:'38.214-5.1.3'})
      <-[:MODIFIES_SECTION]-(cr:CR)
      -[:PRESENTED_AT]->(m:Meeting)
WITH sec, cr, m
OPTIONAL MATCH (m)<-[:MADE_AT]-(wa:WorkingAssumption)-[:REFERENCES]->(t1:Tdoc)
OPTIONAL MATCH (m)<-[:MADE_AT]-(ag:Agreement)-[:REFERENCES]->(t2:Tdoc)
OPTIONAL MATCH (m)<-[:MADE_AT]-(ag2:Agreement)<-[:PROMOTED_TO]-(wa2:WorkingAssumption)-[:REFERENCES]->(t3:Tdoc)
WITH m, COLLECT(DISTINCT t1) + COLLECT(DISTINCT t2) + COLLECT(DISTINCT t3) AS tdocs
UNWIND tdocs AS t
WITH DISTINCT t, m
WHERE t IS NOT NULL
RETURN t.tdocNumber, t.title, m.meetingNumber
ORDER BY m.meetingNumberInt DESC, t.tdocNumber
