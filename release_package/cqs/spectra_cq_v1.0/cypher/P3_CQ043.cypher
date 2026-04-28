// SpectraCQ P3_CQ043 — 통합분석
// Question (English): Return a Neo4j graph summary (node and relationship counts by type).
// Schema area: classes=['CR', 'Company', 'Meeting', 'Resolution', 'Section', 'Spec', 'TSFigure', 'TSTable'], rels=[]

CALL { MATCH (n:Section) RETURN 'Section' AS label, count(n) AS cnt UNION ALL MATCH (n:TSTable) RETURN 'TSTable' AS label, count(n) AS cnt UNION ALL MATCH (n:TSFigure) RETURN 'TSFigure' AS label, count(n) AS cnt UNION ALL MATCH (n:Spec) RETURN 'Spec' AS label, count(n) AS cnt UNION ALL MATCH (n:CR) RETURN 'CR' AS label, count(n) AS cnt UNION ALL MATCH (n:Meeting) RETURN 'Meeting' AS label, count(n) AS cnt UNION ALL MATCH (n:Company) RETURN 'Company' AS label, count(n) AS cnt UNION ALL MATCH (n:Resolution) RETURN 'Resolution' AS label, count(n) AS cnt } RETURN label, cnt ORDER BY cnt DESC
