// SpectraCQ P3_CQ003 — TS_구조탐색
// Question (English): Return the breadcrumb (path-to-root) of TS 38.214 §5.1.3.2.
// Schema area: classes=['Section'], rels=['PARENT_SECTION']

MATCH path = (target:Section {sectionId: '38.214-5.1.3.2'})-[:PARENT_SECTION*0..10]->(root:Section) WHERE NOT (root)-[:PARENT_SECTION]->(:Section) UNWIND nodes(path) AS n RETURN n.sectionNumber, n.sectionTitle ORDER BY n.level
