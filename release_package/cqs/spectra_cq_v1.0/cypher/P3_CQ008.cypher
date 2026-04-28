// SpectraCQ P3_CQ008 — TS_구조탐색
// Question (English): Compare the section/table/figure counts across the 8 TSes (TS-complexity comparison).
// Schema area: classes=['Section', 'Spec', 'TSFigure', 'TSTable'], rels=['BELONGS_TO_SPEC', 'FIGURE_IN_SECTION', 'TABLE_IN_SECTION']

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WITH sp.specNumber AS ts, count(sec) AS secCnt OPTIONAL MATCH (tbl:TSTable)-[:TABLE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec) WHERE sp2.specNumber = ts WITH ts, secCnt, count(DISTINCT tbl) AS tblCnt OPTIONAL MATCH (fig:TSFigure)-[:FIGURE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp3:Spec) WHERE sp3.specNumber = ts RETURN ts, secCnt, tblCnt, count(DISTINCT fig) AS figCnt ORDER BY secCnt DESC
