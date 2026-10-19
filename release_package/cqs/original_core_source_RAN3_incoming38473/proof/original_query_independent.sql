SELECT c."tdocNumber",c."summaryOfChange"
FROM "Spec" AS s
JOIN edge AS e ON e.dst_id=s.node_id
  AND e.rel_type IN ('AFFECTS_CORE_SPEC','AFFECTS_TEST_SPEC','AFFECTS_OM_SPEC')
JOIN "CR" AS c ON c.node_id=e.src_id
WHERE s."specNumber"='38.473'
ORDER BY c."tdocNumber" COLLATE BINARY DESC LIMIT 10
