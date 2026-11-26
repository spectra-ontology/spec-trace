# Answer universe and family contracts

SPECTRA supplies exact answer sets for documentary operations over its released record snapshot. Each item identifies its working-group partition, anchor and requested fields. The table below states which records contribute rows; the machine-readable contract includes both executable reference directions and their input hashes.

| Family | Items | Identity and universe | Eligibility |
|---|---:|---|---|
| `pack_lookup` | 100 | Document TDoc ID; CR number is qualified by specification. All packs containing the anchor, joined to their plenary meeting. | Pack membership and document-list pack fields agree at admission. |
| `pack_lookup_empty` | 86 | Exact TDoc and specification/CR identity in the snapshot. The pack-lookup row set is empty for this identity. | Whole-target source-verified dispositions use the five closed-without-pack codes; same-identity pack/list checks also pass. |
| `disposition_pack` | 99 | Anchor TDoc ID. Every eligible disposition/working-group meeting crossed with every recorded pack/plenary meeting. | Disposition evidence_status=source_verified and scope=whole_target; its resolution has a meeting. |
| `full_chain` | 100 | Anchor TDoc ID; stored section IDs project to clause labels. Disposition-pack rows crossed with the anchor's stored section-change links having a parsed clause label. | Same disposition eligibility as disposition_pack. This family uses all stored section links, including edition-projected links; it applies no target-release filter. |
| `revision_chain` | 82 | Directed revision reachability from the anchor, with duplicate reachable IDs removed. Every later reachable document with an eligible disposition and pack, including qualifying intermediate versions. | Anchor has revised dispositions at construction; returned versions have source_verified, whole_target dispositions whose resolution exists. |
| `clause_history` | 100 | Exact section ID: specification, release and clause; children are separate IDs. All documents changing that exact section in their own target release, with eligible dispositions/meetings/packs. | document.target_release=section.release, source_verified and whole_target; admission checks relevant pack sources. |
| `pack_origin` | 100 | Anchor pack ID and its recorded member document IDs. All recorded member documents having eligible dispositions and working-group meetings. | source_verified and whole_target; returned membership comes from pack-side records in the first reference direction. |
| `clause_neighbours` | 100 | Anchor document's exact section IDs in its target release; other document ID differs from anchor. Every same-release other document changing a shared exact section, with eligible disposition/meeting/pack. | Both documents' target releases equal the section release; other document has source_verified, whole_target disposition. |
| `first_change` | 98 | Anchor pack; exact section ID and CR target release. Each eligible anchor-pack member/section with no same-release changer in any pack at a smaller plenary meeting number. | Current member has source_verified, whole_target disposition; earlier changers use recorded membership regardless of disposition eligibility. |
| `previous_pack` | 99 | Anchor pack; exact section ID and CR target release. All packs tied at the largest plenary meeting number strictly below the anchor meeting for each touched section. | Current member has source_verified, whole_target disposition; earlier changers use recorded membership regardless of disposition eligibility. Sections with no earlier pack contribute no row. |

The two reference directions independently use CR-side and container-side membership/change records. The checker compares both with every released main and extension gold set and reports actual differences.

## Coverage and interpretation

Snapshot completeness means that every qualifying projected row in the specified records is returned. Source-document coverage and source recall are evaluated by the separate censuses and native-source readers. Stored-link confirmation uses the stored-link population as its denominator.

The historical solver tasks, schemas and questions retain their original bytes. This explicit evaluation contract and the separately recorded task-exposure audit distinguish the scoring definition from information actually supplied to a historical model.

Recompute the contract and its row-set comparisons from the release root:

```sh
free -h
python3 -B restore/check_answer_contract.py --release . --out work/answer_contract.json --markdown work/ANSWER_CONTRACT.md
```
