# Case-006 — NR NTN T430 epochTime handling (EpochTime IE serving/neighbour SFN interpretation + wrap-around)

> Source: internal engineering board (anonymized). Real engineering question from day-to-day standards work (translated from the Korean original; question content preserved verbatim in meaning)
> WG / Spec domain: 3GPP RAN2 (RRC — NR NTN; TS 38.331 EpochTime IE, T430 timer; SFN wrap-around conversion)

---

## Question Body

While implementing the epochTime handling logic for the start of the NR NTN T430 timer, I have a question about how to interpret the following two sentences in the TS 38.331 EpochTime IE description.

TS 38.331 EpochTime field description

For serving cell, the field sfn indicates the current SFN or the next upcoming SFN after the frame where the message indicating the epochTime is received.

For neighbour cell when explicit epoch time is present, the sfn indicates the SFN nearest to the frame where the message indicating the epochTime is received.

To align the times relative to the reception instant from the UE's perspective, we convert both times onto a single ms axis.

receivedTime = the message reception subframe converted to ms (0–10239 ms)
epochTime = sfn of the epochTime IE × 10 + subframeNR (0–10239 ms)
timeDiff = receivedTime − epochTime
Positive: epochTime occurred before the reception instant (past)
Negative: epochTime occurs after the reception instant (future)

However, since the SFN wraps back to 0 every 1024 frames (= 10240 ms) (wrap-around), there are cases where simple subtraction alone cannot determine the actual temporal relationship.

(A) Serving cell
Spec wording: sfn is the current SFN or the next upcoming SFN.
Interpretation: epochTime lies at the reception instant or immediately after it (the next frame). That is, the epoch is always the present or the near future, and can never be the past.
Case1 timeDiff ≤ 0: epochTime is at or after reception within the same SFN (no wrap)
ex) receivedTime: 1000ms epochTime: 1010ms → timeDiff: -10
ex) receivedTime: 1000ms epochTime: 1000ms → timeDiff: 0
Case2 timeDiff > 0: the next upcoming SFN has wrapped into the next SFN cycle (corrected by −10240)
ex) receivedTime: 10230ms epochTime: 0ms → timeDiff: +10230 -> 10230 - 10240 = -10ms
ex) receivedTime: 1000ms epochTime: 990ms → timeDiff: +10 -> 10 - 10240 = -10230ms

(B) Neighbour cell
Spec wording: sfn is the SFN nearest to the reception frame.
Interpretation: the epoch can be either past or future relative to the reception instant, but it lies at the shortest distance on the 10240 ms (SFN cycle). That is, if the absolute value of timeDiff exceeds the half-cycle (5120 ms), the epoch is actually in the opposite direction (the next or previous cycle).
Case1: 0 < timeDiff ≤ 5120 — the epoch is in the past within the same cycle
ex) receivedTime: 1050, EpochTime 1000 -> timeDiff= 1050 - 1000 = 50 (past)
Case2: −5120 ≤ timeDiff ≤ 0 — the epoch is in the future within the same cycle
ex) receivedTime: 1000, EpochTime 1050 -> timeDiff= 1000 - 1050 = -50 (future)
Case3: timeDiff < −5120 — the epoch is in the previous cycle
ex) receivedTime: 100, EpochTime 10000 (past) timeDiff= 100 - 10000 = -9900 -9900 + 10240 = 340
Case4: timeDiff > 5120 — the epoch is in the next cycle
ex) receivedTime: 10000, EpochTime 100 (future) timeDiff= 10000 - 100 = 9900 9900 - 10240 = -340

Questions
1. Please confirm whether the interpretations and implementations in (A) and (B) match the spec intent.
2. (A) Range of the epoch position for the serving cell: is it correct to interpret the wording "sfn = current SFN or next upcoming SFN" as "the epoch is at the reception instant or in the near future, and cannot be in the past"?
3. (A) Serving cell wrap-around decision method: following the above interpretation, is the logic that decides wrap based only on the sign of timeDiff, without a ±5120 ms half-cycle threshold (negative → normal, positive → wrapped into the next cycle, so apply a −10240 correction), consistent with the spec intent?
4. (B) Definition of "nearest SFN" for the neighbour cell: is it correct to interpret "sfn = nearest SFN" as "the SFN located at the shortest-path distance from the reception frame on 10240 ms", and to decide wrap with a ±5120 ms threshold?
