// Multi-hop traceability: which TDoc(s) motivated the current text of TS 38.214 §5.1.3?
// Walks: Section <- modifiesSection <- CR -> presentedAt -> Meeting <- madeAt <- Agreement
//        <- promotedTo <- WorkingAssumption -> references -> Tdoc.
//
// Reach the originating TDoc by joining the CR (which modifies the Section) with the
// Resolution (made at the same meeting that approved the change), then walking back
// through the WA->Agreement promotion to the cited contribution. This pattern is
// exercised in `examples/end_to_end/` against synthetic data; on a live SPECTRA-
// conformant KG it returns the contributions that justify the current text of any
// TS section.

MATCH (sec:Section {sectionId:'38.214-5.1.3'})
      <-[:MODIFIES_SECTION]-(cr:CR)
      -[:PRESENTED_AT]->(m:Meeting)
      <-[:MADE_AT]-(ag:Agreement)
      <-[:PROMOTED_TO]-(wa:WorkingAssumption)
      -[:REFERENCES]->(t:Tdoc)
RETURN DISTINCT t.tdocNumber, t.title, m.meetingNumber
ORDER BY m.meetingNumberInt DESC, t.tdocNumber
