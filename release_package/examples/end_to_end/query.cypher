// SPECTRA E2E synthetic example - multi-hop traceability query (Cypher)
// Equivalent to query.sparql.
// Recovers the originating TDoc(s) for the current text of TS 38.214 §5.1.3.

MATCH (sec:Section {sectionId:'38.214-5.1.3'})
      <-[:MODIFIES_SECTION]-(cr:CR)
      -[:PRESENTED_AT]->(m:Meeting)
      <-[:MADE_AT]-(ag:Agreement)
      <-[:PROMOTED_TO]-(wa:WorkingAssumption)
      -[:REFERENCES]->(t:Tdoc)
RETURN DISTINCT t.tdocNumber, t.title, m.meetingNumber

// Expected output:
//   t.tdocNumber: "R1-2599998"
//   t.title:      "Discussion on PTRS density for low-MCS configurations"
//   m.meetingNumber: "RAN1#121"
