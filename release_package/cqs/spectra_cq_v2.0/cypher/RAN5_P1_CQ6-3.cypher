// SpectraCQ RAN5_P1_CQ6-3 (RAN5, phase 1) -- 
// Question: Compare the total TDoc count against the CR count (CR proportion).
// Gold: 1 rows, primary column "total"

MATCH (t:Tdoc) WITH count(t) AS total MATCH (cr:CR) RETURN total, count(cr) AS crs
