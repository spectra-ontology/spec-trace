// SPECTRA E2E synthetic example - Neo4j Cypher CREATE script
// Equivalent to data.ttl. Run :source data.cypher in cypher-shell or Neo4j Browser.
// Property and relationship names follow the Neo4j SCREAMING_SNAKE_CASE convention
// derived from the camelCase OPs in the released ontology TTL.

CREATE
  (m120:Meeting {meetingNumber:'RAN1#120', meetingNumberInt:120, date:'2024-11-18'}),
  (m121:Meeting {meetingNumber:'RAN1#121', meetingNumberInt:121, date:'2024-12-09'}),

  (acme:Company {companyName:'Acme Telecom'}),

  (t1:Tdoc {tdocNumber:'R1-2599998',
            title:'Discussion on PTRS density for low-MCS configurations',
            type:'discussion', status:'noted'}),
  (t1)-[:PRESENTED_AT]->(m120),
  (t1)-[:SUBMITTED_BY]->(acme),

  (wa:WorkingAssumption {resolutionId:'WA1-RAN1#120',
                         description:'PTRS density follows simplified formula for low-MCS.'}),
  (wa)-[:MADE_AT]->(m120),
  (wa)-[:REFERENCES]->(t1),

  (ag:Agreement {resolutionId:'A1-RAN1#121',
                 description:'Adopt simplified PTRS density for low-MCS.'}),
  (ag)-[:MADE_AT]->(m121),
  (wa)-[:PROMOTED_TO]->(ag),

  (sp:Spec {specNumber:'38.214',
            title:'Physical layer procedures for data'}),

  (sec:Section {sectionNumber:'5.1.3', sectionId:'38.214-5.1.3'}),
  (sec)-[:BELONGS_TO_SPEC]->(sp),

  (crpack:CRPack {crPackId:'RP-RAN1-121'}),

  (cr:CR {tdocNumber:'R1-2599999',
          title:'CR on TS 38.214: PTRS density for low-MCS',
          reasonForChange:'Implement RAN1#121 agreement on simplified PTRS density.'}),
  (cr)-[:MODIFIES]->(sp),
  (cr)-[:MODIFIES_SECTION]->(sec),
  (cr)-[:SUBMITTED_BY]->(acme),
  (cr)-[:PRESENTED_AT]->(m121),
  (cr)-[:BELONGS_TO_CR_PACK]->(crpack),
  (crpack)-[:HAS_CR]->(cr);
