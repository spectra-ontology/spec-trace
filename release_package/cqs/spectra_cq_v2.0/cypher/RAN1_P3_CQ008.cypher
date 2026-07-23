// SpectraCQ RAN1_P3_CQ008 (RAN1, phase 3) -- TS
// Question: Compare the eight TSs by section, table, and figure counts (which spec is most complex).
// Gold: 8 rows, primary column "ts"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WITH sp.specNumber AS ts, count(sec) AS secCnt OPTIONAL MATCH (tbl:TSTable)-[:TABLE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec) WHERE sp2.specNumber = ts WITH ts, secCnt, count(DISTINCT tbl) AS tblCnt OPTIONAL MATCH (fig:TSFigure)-[:FIGURE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp3:Spec) WHERE sp3.specNumber = ts RETURN ts, secCnt, tblCnt, count(DISTINCT fig) AS figCnt ORDER BY secCnt DESC
