// SpectraCQ RAN3_P3_CQ1-6 (RAN3, phase 3) -- CQ1_TS
// Question: List the figures in section 8.7.5.2 of spec 38.413 (locating diagrams).
// Gold: 4 rows, primary column "f.figureId"

MATCH (rk:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'8.7.5.2'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN f.figureId, f.figureNumber, f.figureCaption
