# Source fidelity of the released graph

## Context

Sixteen consistency checks were run over the five per-group graphs. Nine of them flag 2,637 records in total; the other seven flag none. The checks and the two lists below were produced after the 2.0.0 graph was built. Neither list is applied in the 2.0.0 TTL files: re-reading the five body TTL files finds every stored value, every missing inverse edge and every own-group origin edge unchanged, and every held record present.

## What ships

- `source_fidelity_repair_manifest.json`: 2,035 value repairs, 153 missing inverse revision edges and 979 own-group origin edges, each with its rule and the stored value it replaces.
- `source_fidelity_quarantine.json`: 334 held entries over 332 distinct records, each with its check class and the reason it is held.

## Applying the lists

Subjects follow the released IRI patterns `<https://w3id.org/spectra/inst/{WG}/Tdoc/tdoc:{id}>` and `<https://w3id.org/spectra/inst/{WG}/Resolution/{id}>` (the Resolution identifier carries no prefix). Date values are plain literals. A value repair replaces the one plain literal of its property; `clear` and `drop` remove that triple. An inverse entry adds `spectra:revisedTo` from the revised document to its revision. An origin entry removes `spectra:originatedFrom` pointing to `<https://w3id.org/spectra/inst/{WG}/WorkingGroup/tdoc:wg%2F{WG}>` of the document's own group.

Applied to 2.0.0, the node counts do not change. Relationships change by RAN1 +153, RAN3 -553, RAN4 -426 (total 4,908,024); RDF triples change by RAN1 +153, RAN3 -596, RAN4 -468 (total 12,930,931).

The RAN3 revision re-read described below is not itemised in the repair manifest. Applying the two lists alone leaves 132 RAN3 records under the reservation-order check instead of 29, so 2,200 of the 2,637 flagged records are cleared and 437 stay flagged.

## Rules

- **R1** (1,003 values): the stored reservation date is the typed date of the source list with day and month swapped (same year and time, day and month differ). Each list's order is fixed by its unambiguous cells:

| Group | Entries | Order from unambiguous cells | Unambiguous cells | Ambiguous cells with day equal to month |
|---|---|---|---|---|
| RAN3 | 554 | month first | 168 | 21 |
| RAN3 | 431 | day first | 433 | 0 |
| RAN5 | 18 | day first | 1,521 | 1 |

- **R2** (RAN3 and RAN4): in 495 RAN3 rows the values from the seventh column onward sit one column to the left of their headers. `realign` takes the value one column to the right (495 reservation dates, 452 upload dates); `clear` removes 43 upload dates whose true cell is empty. `drop` removes 42 RAN4 upload values that carry a time and no date.
- **R3** (153 links, RAN1): a revision edge whose inverse is missing.
- **R4** (979 edges: RAN3 553, RAN4 426): an origin edge to the document's own group that its source row does not declare.

## Checks

| Check | Flagged | Population | After both lists and the re-read |
|---|---|---|---|
| Uploaded before its number was reserved | 575 | 460,663 | 51 |
| Non-date value in a date field | 537 | 516,534 | 0 |
| Section with no specification | 0 | 188,060 | 0 |
| Specification of a section unidentified | 0 | 188,060 | 0 |
| Change request editing another spec's section | 2 | 81,954 | 2 |
| Revision of a later meeting's document | 3 | 81,261 | 3 |
| Revision of a later reservation | 350 | 81,145 | 240 |
| Cycle in a revision chain | 0 | 81,261 | 0 |
| Revision edge without its inverse | 153 | 81,261 | 0 |
| Outgoing liaison addressed to itself | 18 | 17,642 | 18 |
| Incoming liaison originating at itself | 994 | 10,230 | 15 |
| Outgoing liaison carrying an origin group | 0 | 10,230 | 0 |
| Liaison edge on a non-liaison document | 0 | 41,631 | 0 |
| Decision with no meeting | 0 | 32,420 | 0 |
| Decision at another group's meeting | 0 | 32,666 | 0 |
| Decision on a later meeting's document | 5 | 49,669 | 5 |

Identities: the non-date values (537) are the 495 shifted RAN3 reservation values plus the 42 RAN4 time-only values; the edges without inverse are R3; the incoming liaisons originating at themselves minus those held equal R4. 2,637 = 2,303 cleared + 334 held, none unaccounted.

## Held records

| Check | RAN1 | RAN2 | RAN3 | RAN4 | RAN5 | Total |
|---|---|---|---|---|---|---|
| Uploaded before its number was reserved | 0 | 0 | 23 | 28 | 0 | 51 |
| Change request editing another spec's section | 0 | 0 | 2 | 0 | 0 | 2 |
| Revision of a later meeting's document | 2 | 0 | 0 | 0 | 1 | 3 |
| Revision of a later reservation | 100 | 56 | 29 | 48 | 7 | 240 |
| Outgoing liaison addressed to itself | 0 | 8 | 8 | 1 | 1 | 18 |
| Incoming liaison originating at itself | 0 | 5 | 1 | 9 | 0 | 15 |
| Decision on a later meeting's document | 2 | 1 | 2 | 0 | 0 | 5 |

The 334 entries cover 332 records; 2 records are held under two checks. Of the 51 held upload-order records, 51 are uploaded strictly before their reservation, 3 of them with an upload date in or before 1900. The 240 held reservation-order records stay strict under every reading of the dates; 28 parent and 3 revision values admit two readings. 26 RAN4 reservation cells hold the spreadsheet zero date (serial 0).

## RAN3 revision re-read

Reading the revision column at its true position retracts 103 released revision pairs and adds 97. It resolves 103 of the 132 RAN3 reservation-order records left after the lists and introduces 0.

## Shifted properties not repaired

In the 495 shifted RAN3 rows, R2 repairs the two date properties only. For the other properties, V is the released value, D the cell under the property's header and T the true cell one column to the right: `both_empty` (V and T empty), `lost` (V empty, T not), `equal` (V = T = D), `neighbour` (V = D, not T), `other`.

| Property | Rows | Classes |
|---|---|---|
| `abstract` | 495 | both_empty 109, lost 17, neighbour 369 |
| `belongsTo` | 495 | lost 495 |
| `ccTo` | 60 | both_empty 4, neighbour 56 |
| `crCategory` | 111 | both_empty 45, lost 40, neighbour 26 |
| `crNumber` | 111 | both_empty 24, neighbour 87 |
| `crRevision` | 111 | both_empty 52, neighbour 59 |
| `for` | 495 | both_empty 126, lost 369 |
| `modifies` | 111 | both_empty 22, equal 78, lost 10, other 1 |
| `originalLs` | 33 | both_empty 1, lost 32 |
| `originatedFrom` | 33 | both_empty 8, lost 25 |
| `relatedTo` | 495 | both_empty 251, lost 170, neighbour 74 |
| `replyIn` | 495 | both_empty 493, other 2 |
| `replyTo` | 495 | both_empty 491, lost 4 |
| `reservationDate` | 495 | neighbour 495 |
| `secretaryRemarks` | 495 | both_empty 463, neighbour 32 |
| `sentTo` | 60 | both_empty 4, lost 52, neighbour 4 |
| `status` | 495 | neighbour 495 |
| `targetRelease` | 495 | both_empty 204, lost 291 |
| `title` | 495 | equal 495 |
| `tsgCRPack` | 111 | both_empty 45, neighbour 66 |
| `type` | 495 | equal 495 |
| `uploadedDate` | 495 | neighbour 495 |

## Benchmark reach

Over the 560 Core key items, one (RAN3_P2_CQ1-6) lists a held record in its gold and one more (RAN3_P4_CQ4-5) only in its evidence. 5 items list a document touched by R3 or R4 in their gold (RAN1_P4_CQ1-3: R3, RAN1_P4_CQ2-4: R3, RAN3_P1_CQ1-2: R4, RAN3_P1_CQ2-7: R4, RAN4_P1_CQ1-1: R4); none of their queries reads a changed relation of its own group. 12 queries traverse a relation type the lists change (IS_REVISION_OF 3, MODIFIES_SECTION 8, ORIGINATED_FROM 1, REVISED_TO 1), 8 of them `MODIFIES_SECTION` only. No Core query reads a date property, an untyped pattern, `properties()` or `keys()`.

Of the 112 RAN3 Core queries, 45 name a property shifted by R2. 18 are settled by their structure; the other 27 were ported to both readings. 6 cannot bind a shifted row; for the 21 recomputed, the released reading (V) reproduces the gold, and the true-cell reading (T) keeps every gold admissible except RAN3_P3_CQ5-1, whose count changes by 3.

Each SpectraCQ v2.0 gold answer is defined by executing its reference query against the released 2.0.0 graph, which does not apply these lists, so the lists do not change any gold answer.
