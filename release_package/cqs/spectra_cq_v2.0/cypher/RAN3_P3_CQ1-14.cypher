// SpectraCQ RAN3_P3_CQ1-14 (RAN3, phase 3) -- CQ1_TS
// Question: Return the total counts of sections, tables, and figures (corpus-size overview).
// Gold: 1 rows, primary column "secCnt"

MATCH (s:Section) WITH count(s) AS secCnt MATCH (t:TSTable) WITH secCnt, count(t) AS tblCnt MATCH (f:TSFigure) WITH secCnt, tblCnt, count(f) AS figCnt RETURN secCnt, tblCnt, figCnt
