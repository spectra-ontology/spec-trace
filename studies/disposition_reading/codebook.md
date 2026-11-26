# Codebook: what the meeting decided about one target document

Each packet gives a target document number, the meeting report it comes from, and a few consecutive body blocks of that
report. Blocks marked `cited: true` are the passage under review; the other blocks are context. Tables appear as rows
`| cell | cell |`. `[cut]` marks a long block that was shortened.

Read only the text in the packet. Decide what this passage says the meeting did with the **target document** (not with
another document mentioned on the same line), then choose one code and one scope.

## Codes

| Code | Use when the passage says the target document was |
|---|---|
| agreed | approved or agreed as it stands, without a condition, a restriction to a part, or a change still to be made |
| conditionally_agreed | agreed with a condition or a pending change: agreed in principle, agreed assuming an update, agreed with a change to itself |
| partially_agreed | agreed only in part: a named proposal, TP, section, annex or subset of its changes |
| endorsed | endorsed (for example a draft CR or draft LS endorsed, as distinct from agreed or approved) |
| revised | revised into another document number (the outcome is carried by the new number) |
| merged | merged into another document |
| noted | noted |
| withdrawn | withdrawn |
| rejected | rejected |
| not_agreed | stated as not agreed |
| not_pursued | stated as not pursued |
| not_treated | not treated, not handled or not available at the meeting |
| postponed | postponed to a later meeting |
| not_concluded | discussed without conclusion |
| replied_to | the incoming document was answered by a reply (for example an LS replied to) |
| ambiguous | the passage mentions the target but its outcome for the target is not determined by the passage: it agrees content to be incorporated into another document, approves another number with no stated relation, asks whether to agree, states a plan, or gives outcomes that cannot be assigned to the target |
| cannot_tell | the passage does not let you decide at all (for example the target is not mentioned, or the text is unreadable) |

A past approval quoted from another meeting, a question about approval, or a future plan is not an approval at this
meeting. "Agreed with no changes" and "without changes" are unconditional.

## Scope

| Scope | Use when the outcome applies to |
|---|---|
| whole_target | the target document as a whole |
| subdocument | a part of it (a proposal, TP, section or list item), or its adoption into a rapporteur CR or reply rather than the document as a whole |
| undetermined | the passage does not let you tell |

## Output

One JSON line per packet: `{"packetId": "...", "code": "...", "scope": "...", "evidence": "<the sentence or row that decides it, copied from the packet>"}`.
