// SpectraCQ RAN5_P3_CQ1-6 (RAN5, phase 3) -- CQ1_TS
// Question: List the figures in section 5.3.4.1 of TS 38.509 (figure lookup).
// Gold: 5 rows, primary column "f.figureId"

MATCH (rk:Spec {specNumber:'38.509'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'5.3.4.1'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN f.figureId, f.figureNumber, f.figureCaption ORDER BY f.figureNumber LIMIT 15
