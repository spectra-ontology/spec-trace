// SpectraCQ P3_CQ019 — CR_TS_변경추적
// Question (English): Compare CR counts across the 8 TSes (where standardization is most active).
// Schema area: classes=['CR', 'Spec'], rels=['MODIFIES']

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC
