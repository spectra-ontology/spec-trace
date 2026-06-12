# [RAN1] Question regarding CSI part 2 omission in UCI on PUSCH (Enhanced Type 2 codebook)

- date: 2026-04-29 18:56:16
- author: anonymous
- category: RAN1(Physical) > UL Control Channel
- Source: internal engineering board (anonymized).

## Body

This is a case of transmitting UCI only on UCI on PUSCH.

When ACK/CSI1/CSI2 all exist but the RB/MCS is small, it appears that a case can occur where, in the Enhanced Type 2 codebook, everything is omitted so that CSI part 2 cannot be sent.

That is, regarding omission, 214 states the following, and it does not seem to provide any exception handling such as "omission must not go down to group 0":

> the UE shall omit all of the information at that priority level

If there is any related agreement, discussion content, or other specification content, please let me know.

When CSI part 2 is entirely omitted, the following ambiguities can exist:

1. The Q' calculation formula for CSI part 1 differs between the case "if there is CSI part 2 (@212)" and the case where there is not. In the case where CSI part 2 exists but is omitted, and this is regarded as CSI part 2 not being present:

   -> From the gNB's perspective, the omission level can be known after decoding CSI1, but since it has no choice but to interpret it as the case where CSI part 2 is present and attempt CSI part 1 decoding, a mismatch with the UE operation occurs.

   -> If it must be interpreted this way, there should be an explicit statement related to this. In that case, the gNB needs to attempt decoding twice.

2. In the case where CSI part 2 exists but is omitted, and this is interpreted as CSI part 2 being present, so that the Q' of CSI part 1 is calculated:

   -> There is no ambiguity in the Q' calculation, but I cannot find a statement on how to transmit the remaining resources after CSI part 1 allocation in the UCI-only case.

If you have any material related to the following questions, please share it.

**Question 1**. When the Enhanced Type 2 codebook is supported, does a case occur where CSI part 2 is entirely omitted?

**Question 2**. If there is a case where CSI part 2 is entirely omitted, is there any discussion or agreement content regarding the ambiguities in items 1/2 above?

## Comments (1)

### [1] anonymous — 2026-05-07 20:37

Hello,

Question 1: Yes, a case where CSI part 2 is entirely omitted can occur (when the remaining amount of resources is so small that none of part 2 can be included). However, I think the gNB can schedule so as not to allocate such a small amount of PUSCH resources.

Question 2: There is no separate agreement. As you wrote in the first arrow below item 1 above, from the gNB's perspective, after decoding CSI part 1 it knows the length of CSI part 2, and looking at the remaining amount of PUSCH resources it must decide whether to omit part or all of CSI part 2. Therefore, I think it is self-evident to interpret it as in your item 2, "the case where CSI part 2 exists but is omitted is interpreted as CSI part 2 being present, so that the Q' of CSI part 1 is calculated."

In this case, since there is no ambiguity in the Q' calculation, the gNB can decode CSI part 1 and obtain the part 1 CSI information.

Regarding how to transmit the remaining resources in the UCI-only case after CSI part 1 allocation, I could not find any discussed or defined part (if I find it later, I will answer). Probably the gNB allocates resources so that this situation does not occur, or even if the gNB schedules such that this situation actually occurs, regardless of what is transmitted in the remaining resources, the gNB should be able to obtain the CSI information by identifying and decoding only the CSI part 1 resources.

Thank you.
