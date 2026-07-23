// SpectraCQ RAN1_P3_CQ019 (RAN1, phase 3) -- CR_TS
// Question: Compare CR counts across the eight TSs (where standardization activity concentrates).
// Gold: 8 rows, primary column "sp.specNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC
