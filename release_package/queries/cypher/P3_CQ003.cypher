// P3_CQ003 — Phase 3 (TS structure)
// Return the section breadcrumb (path to root) for TS 38.214 section 5.1.3.2.

MATCH path = (target:Section {sectionId: '38.214-5.1.3.2'})-[:PARENT_SECTION*0..10]->(root:Section) WHERE NOT (root)-[:PARENT_SECTION]->(:Section) UNWIND nodes(path) AS n RETURN n.sectionNumber, n.sectionTitle ORDER BY n.level
