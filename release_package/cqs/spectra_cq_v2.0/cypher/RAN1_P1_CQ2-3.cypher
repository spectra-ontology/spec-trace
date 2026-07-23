// SpectraCQ RAN1_P1_CQ2-3 (RAN1, phase 1) -- CQ2_Tdoc
// Question: Which LS does TDoc R1-2000004 reply to? (reply-chain tracing)
// Gold: 1 rows, primary column "reply_tdoc"

MATCH (t:Tdoc {tdocNumber: 'R1-2000004'})-[:REPLY_TO]->(original:Tdoc) RETURN t.tdocNumber AS reply_tdoc, t.title AS reply_title, original.tdocNumber AS original_tdoc, original.title AS original_title ORDER BY t.tdocNumber ASC LIMIT 10
