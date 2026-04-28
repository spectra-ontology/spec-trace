// SpectraCQ P1_CQ2-3 — CQ2_Tdoc관계추적
// Question (English): Identify which incoming LS the TDoc R1-2599004 is replying to (replyTo lookup).
// Schema area: classes=['Tdoc'], rels=['REPLY_TO']

MATCH (t:Tdoc {tdocNumber: 'R1-2599004'})-[:REPLY_TO]->(original:Tdoc) RETURN t.tdocNumber AS reply_tdoc, t.title AS reply_title, original.tdocNumber AS original_tdoc, original.title AS original_title ORDER BY t.tdocNumber ASC LIMIT 10
