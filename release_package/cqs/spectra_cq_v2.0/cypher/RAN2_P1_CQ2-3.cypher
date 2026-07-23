// SpectraCQ RAN2_P1_CQ2-3 (RAN2, phase 1) -- CQ2_Tdoc
// Question: Which incoming LS does a given TDoc reply to (reply-to linkage)?
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:REPLY_TO]->(target:Tdoc) RETURN t.tdocNumber, target.tdocNumber AS replyTarget ORDER BY t.tdocNumber DESC LIMIT 10
