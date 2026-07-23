// SpectraCQ RAN5_P3_CQ4-4 (RAN5, phase 3) -- CQ4_Resolution
// Question: How many CRs do conclusions reference? (resolution-to-CR coverage)
// Gold: 1 rows, primary column "resCount"

MATCH (res:Conclusion)-[:REFERENCES]->(t:Tdoc:CR) RETURN count(DISTINCT res) AS resCount, count(DISTINCT t) AS crCount
