// SpectraCQ RAN1_P3_CQ036 (RAN1, phase 3) -- 
// Question: Compare the top 5 TSs by CR count against their section counts (complexity vs. change frequency).
// Gold: 5 rows, primary column "ts"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] WITH sp.specNumber AS ts, count(cr) AS crCount ORDER BY crCount DESC LIMIT 5 MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec {specNumber: ts}) RETURN ts, crCount, count(sec) AS sectionCount ORDER BY crCount DESC
