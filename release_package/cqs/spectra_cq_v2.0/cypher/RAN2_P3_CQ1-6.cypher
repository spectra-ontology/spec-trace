// SpectraCQ RAN2_P3_CQ1-6 (RAN2, phase 3) -- CQ1_TS
// Question: List the figures in section 6.1.3.1 of spec 38.321 (figure lookup).
// Gold: 5 rows, primary column "f.figureId"

MATCH (rk:Spec {specNumber:'38.321'})<-[:BELONGS_TO_SPEC]-(s:Section {sectionNumber:'6.1.3.1'}) WHERE rk.specRelease IS NOT NULL WITH s, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (s)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN f.figureId, f.figureNumber, f.figureCaption
