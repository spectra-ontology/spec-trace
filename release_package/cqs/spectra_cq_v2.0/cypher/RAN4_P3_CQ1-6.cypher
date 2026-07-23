// SpectraCQ RAN4_P3_CQ1-6 (RAN4, phase 3) -- CQ1_TS
// Question: List the figures in section J.3 of spec 38.141-2 (locating test-setup figures).
// Gold: 9 rows, primary column "f.figureId"

MATCH (rk:Spec {specNumber:'38.141-2'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'J.3'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN f.figureId, f.figureNumber, f.figureCaption ORDER BY f.figureNumber LIMIT 15
