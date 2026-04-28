// SpectraCQ P4_CQ3-3 — CQ3_CRPack분석
// Question (English): Return CR Packs submitted at RAN#109 with the CR count per pack.
// Schema area: classes=['CR', 'CRPack'], rels=['HAS_CR']

MATCH (pack:CRPack)-[:HAS_CR]->(cr:CR) WHERE pack.tsgMeeting = 'RAN#109' RETURN pack.tsgMeeting, pack.crPackId, count(cr) AS crCount ORDER BY crCount DESC
