// SpectraCQ RAN4_P1_CQ6-3 (RAN4, phase 1) -- 
// Question: How many of the TDocs are CRs? (change-request proportion).
// Gold: 1 rows, primary column "total"

MATCH (t:Tdoc) WITH count(t) AS total MATCH (cr:CR) RETURN total, count(cr) AS crs
