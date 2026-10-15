MATCH (hub:Spec {specNumber: '38.133'})
WHERE hub.specRelease IS NULL
MATCH (edition:Spec)-[:IN_RELEASE_OF]->(hub)
MATCH (anchor:Section {sectionNumber: '9.2.5.1'})-[:BELONGS_TO_SPEC]->(edition)
MATCH (anchor)-[:CONTAINS_TABLE]->(obj:TSTable)
RETURN DISTINCT obj.tableId AS tableId, obj.tableNumber AS tableNumber, obj.tableCaption AS tableCaption
ORDER BY tableId
