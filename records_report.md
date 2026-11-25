# Record files and receipts: regeneration report

This preparation record preserves the measurements and review questions recorded during the
initial packaging of these files. The folder counts and Section 8 describe that stage.
For the current artifact scope, use [README](README.md), the execution guide
[REPRODUCING](REPRODUCING.md), and the [datasheet](datasheet.md).

This report covers the two folders `records/` and `receipts/` of this release folder and the
list `records_redactions.jsonl`. Every number below was measured on the files as they are
stored here. Paths that start with `ontology/` or `logs/` are relative to the root of the
source repository; all other paths are relative to this folder.

## 1. What was produced

| Group | Files | Records | Source bytes | Bytes after redaction | Bytes as stored |
|---|---:|---:|---:|---:|---:|
| `records/` (JSON-LD instance files) | 48 | 1,400,633 nodes | 1,720,271,153 | 1,048,600,380 | 273,937,276 |
| `receipts/` (identity review receipts) | 10 | 13,578 entries | 84,500,577 | 26,155,179 | 26,155,179 |
| Total | 58 | | 1,804,771,730 | 1,074,755,559 | 300,092,455 |

All 58 files named by the earlier redaction list were regenerated. The source files were
found with the sizes and SHA-256 values that the earlier list records for them (58 of 58).

Nodes by record kind: tdocs 552,138; decision_dispositions 358,062;
resolutions_document_dispositions 348,952; cr_extensions 56,819; section_extensions 41,337;
resolutions_agreements 33,509; crpacks 4,345; resolutions_conclusions 3,569;
resolutions_working_assumptions 1,621; meetings 281.

Sixteen record files are byte-identical to their source file, because their record kind has
no dropped field and the namespace is kept: the five `meetings.jsonld` files, the four
`crpacks.jsonld` and four `section_extensions.jsonld` files under `records/phase-4/` for
RAN1 to RAN4, and the three files under `records/RAN5_graph_export/RAN5/`. The redaction
list marks them with `identicalToSource: true`.

## 2. Layout

| Source location | Location in this folder |
|---|---|
| `ontology/output/tsg/RAN/formal/instances/<phase>/<WG>/<kind>.jsonld` | `records/<phase>/<WG>/<kind>.jsonld` |
| `logs/publication/paper/ongoing/sigir-2027-research/RAN5_graph_export/RAN5/<kind>.jsonld` | `records/RAN5_graph_export/RAN5/<kind>.jsonld` |
| `ontology/input/tsg/RAN/formal/meetings/<WG>/<name>.json` | `receipts/<WG>/<name>.json` |

Each row of `records_redactions.jsonl` holds both the source path and the path here.

## 3. Compression

Eight record files exceed 50,000,000 bytes after redaction and are stored with
`gzip -9 -n` under the extension `.gz`. The largest stored file of the two folders is
`records/phase-1/RAN5/tdocs.jsonld` with 42,993,933 bytes; the largest compressed file has
14,847,217 bytes.

| File | Uncompressed bytes | Compressed bytes |
|---|---:|---:|
| `records/phase-1/RAN1/tdocs.jsonld.gz` | 64,179,830 | 2,596,063 |
| `records/phase-1/RAN2/tdocs.jsonld.gz` | 70,313,335 | 3,228,901 |
| `records/phase-1/RAN4/tdocs.jsonld.gz` | 95,389,486 | 4,115,555 |
| `records/phase-2/RAN2/decision_dispositions.jsonld.gz` | 83,767,367 | 5,008,710 |
| `records/phase-2/RAN3/decision_dispositions.jsonld.gz` | 86,794,182 | 5,292,688 |
| `records/phase-2/RAN4/decision_dispositions.jsonld.gz` | 246,138,827 | 14,847,217 |
| `records/phase-2/RAN4/resolutions_document_dispositions.jsonld.gz` | 71,845,398 | 3,442,352 |
| `records/phase-2/RAN5/decision_dispositions.jsonld.gz` | 100,726,217 | 5,960,052 |

In the redaction list, `stagedSha256` and `stagedBytes` describe the uncompressed file, and
`storedSha256` and `storedBytes` describe the file as stored. For a file stored plain the
two pairs are equal.

## 4. What the redaction removes

The staging tool is a copy of the earlier tool with one change of behaviour: the namespace
`https://w3id.org/spectra#` stays as it is. Field lists, link handling, the reduction of
`assessmentMethod`, the receipt handlers and the serialization are those of the earlier
tool. The tool writes a record node from a keep list per record kind and stops on a key
that is in neither the keep list nor the drop list.

Fields dropped from record nodes (count of nodes that carried the field):

| Record kind | Field | Count |
|---|---|---:|
| tdocs | `tdoc:title` | 552,138 |
| tdocs | `submittedBy` | 542,915 |
| tdocs | `hasContact` | 539,132 |
| tdocs | `tdoc:abstract` | 88,215 |
| tdocs | `tdoc:secretaryRemarks` | 53,102 |
| tdocs | `tdoc:clausesAffected` | 23,493 |
| decision_dispositions | `evidenceQuote` | 358,062 |
| resolutions (four kinds) | `content` | 387,651 |
| resolutions (three kinds) | `note` | 3,707 |
| resolutions (three kinds) | `contentWithEquations` | 1,785 |
| cr_extensions | `tdoc:reasonForChange` | 27,373 |
| cr_extensions | `tdoc:summaryOfChange` | 27,351 |
| cr_extensions | `tdoc:consequencesIfNotApproved` | 27,314 |

The serialized `assessmentMethod` of 358,062 disposition nodes is reduced to an allow-list
of keys; 12,325 `identityReview.reason` texts go with it.

The liaison link properties (`sentTo`, `ccTo`, `originatedFrom`, `replyTo`, `replyIn`,
`originalLS`) and the other link properties stay as keys. In TDoc records 254 single link
values are dropped: 8 derived from an e-mail address (`replyTo` 7, `sentTo` 1), 6 that point
to a person (`ccTo` 2, `sentTo` 4) and 240 free-text values (`originalLS` 154, `replyTo` 85,
`replyIn` 1).

The record kinds `contacts` and `companies` are left out as whole files, as in the earlier
staging. The receipts are reduced by three handlers (`reduce_review`, `reduce_dd_review`,
`reduce_alias`); the redaction list gives, per receipt, the number of distinct key paths
dropped and kept.

## 5. Equivalence with the earlier staging

For each record file the tool also computed, in memory, the serialization with the
placeholder namespace of the earlier review staging, and its SHA-256 and size were compared
with the earlier redaction list.

| Check | Result |
|---|---:|
| Source SHA-256 equal to the earlier list | 58 of 58 |
| Drop and reduction counters equal to the earlier list | 343 of 343 |
| Record files whose placeholder-namespace serialization has the earlier staged SHA-256 and size | 48 of 48 |
| Receipts with the earlier staged SHA-256 | 10 of 10 |
| Occurrences of the project namespace in the 48 record files | 16,631 |
| of these inside `@context` | 16,631 |
| Record files whose size differs from the earlier staged size by 7 bytes per occurrence | 48 of 48 |

So the record files differ from the earlier staged files only in the namespace string inside
`@context`, and the receipts are byte-identical to the earlier staged receipts. The staged
SHA-256 values of the 48 record files therefore differ from the earlier list of checksums.

## 6. Verification of the stored files

### 6.1 Per-file check

`verify_release.py` read every stored file, through gzip where it is compressed.

| Check | Result |
|---|---:|
| Stored files | 58 |
| Rows of the staging tool without a stored file | 0 |
| Uncompressed SHA-256 and size equal to the row of the staging tool | 58 of 58 |
| Node or entry count equal to the row of the staging tool | 58 of 58 |
| Node keys outside the keep list of the record kind | 0 |
| Key paths inside `assessmentMethod` outside the allow-list | 0 |
| Keys named like a dropped field at any depth of the data, nested JSON strings included | 0 |

### 6.2 Streaming text scan

The same script scanned the text of every file in chunks. For record files the part before
`"@graph"` (the `@context`) is counted apart from the data.

| Pattern | In the data of 58 files | In `@context` of 48 record files |
|---|---:|---:|
| JSON key named like a dropped field, plain or escaped, with or without `tdoc:` | 0 | 1,300 |
| E-mail address `local@domain.tld` | 0 | 0 |
| Percent-encoded e-mail address `local%40domain.tld` | 0 | 0 |
| Character `@` outside the JSON-LD keywords | 0 | 0 |
| Account name of the build host, any case | 0 | 0 |
| Home-directory path prefix | 0 | 0 |
| Host paths of other shapes (user folders, drive mounts, session temp folders) | 0 | 0 |
| Placeholder namespace of the earlier review staging | 0 | 0 |
| Project namespace `w3id.org/spectra` | 0 | 16,631 |

The key names scanned are: title, abstract, secretaryRemarks, clausesAffected,
evidenceQuote, content, contentWithEquations, note, notes, reasonForChange,
summaryOfChange, consequencesIfNotApproved, hasContact, submittedBy, contacts, companies,
contactName, companyName, reason, reportIdentity, phase1IdentityEvidence, nodeAtReview.

The 1,300 matches in `@context` are term definitions of the vocabulary (a term name mapped
to an IRI), 28 or 30 per file in 45 record files; the three files under
`records/RAN5_graph_export/` have a six-term context with none. The project namespace is
present in all 48 record files (2, 341, 403 or 407 occurrences per file). The 10 receipts
hold plain JSON without a namespace, as their sources do.

A second count with `zcat`, `cat` and `grep` over the stored files gave the same picture:
16,631 occurrences of the project namespace in 48 files, and zero occurrences of the account
name, the home-directory prefix, the placeholder namespace, `%40` and e-mail-shaped strings.

### 6.3 Scans of the earlier procedure

These were run on the uncompressed staged files before compression. The name lists they
read stay outside this folder.

| Scan | Scope | Result |
|---|---|---|
| `residual_scan.py` | 48 record files, 1,048,600,380 bytes | plain e-mail 0; percent-encoded e-mail 0; known address 0; host path 0; account name 0; surname 0; local service 0; phone-like 0; project name 16,631 in 48 files; project namespace 16,631 in 48 files; e-mail-shaped encoded string 278 in 6 files |
| `residual_scan.py` | 10 receipts, 26,155,179 bytes | all classes 0 except e-mail-shaped encoded string 3 in 1 file |
| `class_encoded.py` | 58 files | the 281 encoded-shaped strings are 260 work-item codes in TDoc records, 15 organisation identifiers in `sentTo` and `ccTo` of the RAN4 TDoc records, and 6 copies of one archive file name (3 in the RAN2 receipt, 3 in the RAN2 disposition records) |
| `encoded_email_scan.py` | 5 TDoc record files | the values found sit under `relatedTo` (work-item identifiers; 2, 3, 3, 9 and 2 distinct values for RAN1 to RAN5) and, for RAN4, under `ccTo` (2 distinct) and `sentTo` (3 distinct) |
| `name_scan.py`, word tokens | 58 files | contact-name hits 0; company-name hits 734 in 13 files |
| `name_scan.py`, underscores split | 58 files | contact-name hits 0; company-name hits 7,327 in 13 files |
| `name_part_scan.py` | 58 files | 3,186 name parts looked up; 7 of them occur, 92 hits |
| `hangul_count.py` | 58 files | 0 files, 0 lines |
| `prose_fields.py` | 58 files | record files: 0 key paths with prose-like values; receipts: see below |
| `link_values.py` | 5 TDoc record files | see below |
| `target_hashes.py` | 5 disposition record files | 5 distinct pairs of path and SHA-256, 352,075 uses, all equal to the source SHA-256 of the five TDoc files |

`hangul_keys.py` was not run because `hangul_count.py` found no line. `hangul_tokens.py`
reads Python sources and does not apply to these files.

Where the name hits sit. The scans count registered company and organisation names and
parts of contact names as tokens. A further pass (`class_name_hits.py`) filed each hit
position under the nearest JSON key:

| Token group | Positions | Under which key |
|---|---:|---|
| Company and organisation names | 6,920 | `relatedTo` 4,570; `sentTo` 1,208; `ccTo` 565; `path` 564; `originalLS` 10; `replyTo` 3 |
| Parts of contact names | 92 | `path` 89; `sentTo` 2; `originalLS` 1 |

The position count for company names is lower than the hit count of `name_scan.py` because
that scan counts overlapping multi-word names separately and reads a serialized JSON string
both as a whole and by its parts. The hits under `relatedTo` are parts of work-item codes;
those under `sentTo`, `ccTo`, `originalLS` and `replyTo` are parts of working-group,
organisation and liaison identifiers; those under `path` are parts of archive file names
inside evidence paths. In the contexts read for each of the seven name parts that occur, five
are words of a document title inside a file name and two are company tokens (one in a file
name, one in a `sentTo` identifier and a file name). The scan of full contact names found
none.

Prose-like values in receipts (`prose_fields.py`): eight file-level description strings
(`.scope` in 5 receipts, `.purpose` in 3), four `.reviews[].assessment` strings (3 in the
RAN1 and 1 in the RAN2 disposition review receipt) and four archive member names in the
RAN4 receipts.

Link values in TDoc records (`link_values.py`), by class of the value:

| Property | TDoc identifier | Working-group-like identifier | Other |
|---|---:|---:|---:|
| `sentTo` | 0 | 33,718 | 0 |
| `ccTo` | 0 | 17,143 | 0 |
| `originatedFrom` | 0 | 9,917 | 0 |
| `replyTo` | 11,155 | 122 | 203 |
| `originalLS` | 9,456 | 39 | 687 |
| `replyIn` | 3,168 | 2 | 83 |

The list of the non-TDoc values was not read again in this run; the record data are
byte-equivalent to the earlier staging apart from the namespace (Section 5).

## 7. Deviations from the earlier procedure

1. The namespace `https://w3id.org/spectra#` is kept in `@context`.
2. Files are placed under the compact paths of Section 2. The earlier staging used the full
   repository-relative path below its staging folder.
3. Eight files are stored compressed (Section 3).
4. The tool ran with the Python 3.11.14 interpreter of the project environment, one process
   per file, with a memory cap of 14 GB per run. The highest resident memory of a single
   file was 2,033,288 KB.

## 8. Decisions recorded during initial preparation

1. Vocabulary terms in `@context`. Forty-five record files keep the term definitions of the
   dropped properties (for example `hasContact`, `submittedBy`, `title`, `evidenceQuote`,
   `contactName`, `companyName`). They are names mapped to IRIs and carry no data. Removing
   them would change the files relative to the earlier staging.
2. Archive file names in evidence paths. The `path` values kept in disposition records and
   receipts end in file names of the source archive. Such names contain words of document
   titles and, in places, company tokens (564 company-token positions and 89 name-part
   positions under `path`).
3. Liaison link targets. `sentTo`, `ccTo`, `originatedFrom` and part of `replyTo`,
   `originalLS` and `replyIn` name working groups and outside organisations. Two `sentTo`
   positions match a registered company token.
4. Stored hashes that refer to source files. `targetIdentity.sha256` in the disposition
   records (352,075 uses, 5 distinct values) is the SHA-256 of the unredacted TDoc source
   file, and `receiptSha256` (12,345 uses, 7 distinct values) is the SHA-256 of the
   unredacted receipt. The matching `path` values are repository-relative source paths. A
   reader can map both to the released files through `records_redactions.jsonl`
   (`sourcePath`, `originalSha256`, `releasePath`, `stagedSha256`).
5. Descriptive strings in receipts. The receipts keep the project-written `.scope`,
   `.purpose` and `.reviews[].assessment` strings listed in Section 6.3.
6. Sixteen record files are released byte-identical to their source (Section 1).

## 9. Files

| File | Stored bytes | Uncompressed bytes | Records | SHA-256 of the stored file |
|---|---:|---:|---:|---|
| `receipts/RAN1/decision_disposition_identity_reviews.json` | 2,383 | 2,383 | 3 | `645bbb4e650cb53c299ac49bf3c8d18ee1ce49ce1389d234fb08edbed24a8f0a` |
| `receipts/RAN1/document_decision_identity_reviews.json` | 7,216,648 | 7,216,648 | 3,684 | `30ed696ff3cabf0ce99f3d86c033c1eebcaf45300b6fde8e76890fdd4abe0fe2` |
| `receipts/RAN2/decision_disposition_identity_reviews.json` | 850 | 850 | 1 | `503e10c04d95aa92f2ad73f097184d30507c3199dd944a610e114e395f6ad4f5` |
| `receipts/RAN2/document_decision_identity_reviews.json` | 15,442,931 | 15,442,931 | 8,145 | `72413a4e40bf1e8d6b5493a5b8506e8d21d725aca1da08b8e17f64b9888d2c2a` |
| `receipts/RAN2/document_decision_target_aliases.json` | 3,331 | 3,331 | 1 | `9e72059f61f03ddf26423491607390795d52a2d7160ca6aad96ec1c8d2867e67` |
| `receipts/RAN3/document_decision_identity_reviews.json` | 43,207 | 43,207 | 31 | `988a228f380db0f7c4e3877c43c8cd241d32dcc7e10b8be98b36ac14b61d6db7` |
| `receipts/RAN3/document_decision_target_aliases.json` | 2,950 | 2,950 | 2 | `4bc49d4d816763894254ccd482d11fa9ce61a25e600a7623bbc3f961bb148817` |
| `receipts/RAN4/document_decision_identity_reviews.json` | 3,176,291 | 3,176,291 | 1,571 | `d78b617f92352a1497c51a6591390e827874d84dc37a0e928151ab3eba393115` |
| `receipts/RAN4/document_decision_target_aliases.json` | 4,320 | 4,320 | 3 | `5cc09cbcf721c095e706138a95a6d2fb0d6ab49bfeb52a48f3908fea80794476` |
| `receipts/RAN5/document_decision_identity_reviews.json` | 262,268 | 262,268 | 137 | `938f7a9035d076fe99dc97b66290655ed3c8dbb2d4757e29052a5fcd56c9bfa2` |
| `records/RAN5_graph_export/RAN5/cr_extensions.jsonld` | 5,249,137 | 5,249,137 | 29,438 | `229be48f876707ed56b0a9343c28406f319cc6930632e6f85f48c32e8d6f2212` |
| `records/RAN5_graph_export/RAN5/crpacks.jsonld` | 860,934 | 860,934 | 1,430 | `501f238351bd876d45845d8c1fbcf76dd1c9abf370fcdea2c22465270310ad98` |
| `records/RAN5_graph_export/RAN5/section_extensions.jsonld` | 2,236,184 | 2,236,184 | 13,612 | `c716aad0dee150cf2eae14c4b945ef5631ac12fb7ee1c424141b48d7d0705643` |
| `records/phase-1/RAN1/meetings.jsonld` | 65,446 | 65,446 | 62 | `27aaef077da040b3e5266c63b3d45cc9952e8813145cafad9ebf455a770428ff` |
| `records/phase-1/RAN1/tdocs.jsonld.gz` | 2,596,063 | 64,179,830 | 127,149 | `f425d56bfc492846428c040a85e11c5c71c684dd593c6dd37dc1ea4f6d8a941d` |
| `records/phase-1/RAN2/meetings.jsonld` | 65,368 | 65,368 | 61 | `8c6676182bd72b0d1d022ccb1d138b2d6da5fd3b110e24cedbf32b2d9f60ed01` |
| `records/phase-1/RAN2/tdocs.jsonld.gz` | 3,228,901 | 70,313,335 | 124,271 | `92d7df84f5d12e63944ed7fb18601152c86525dab9ff8ceedde17bfbc4c9cffe` |
| `records/phase-1/RAN3/meetings.jsonld` | 65,102 | 65,102 | 60 | `2b657a76f94600e0b026d50c700bec8d72cb9a90353cae03f3685f71ead1a674` |
| `records/phase-1/RAN3/tdocs.jsonld` | 34,281,196 | 34,281,196 | 60,566 | `9672f49888f5b0038aa4497ed943f221e7c24f148d5142b557f762a95e68de1a` |
| `records/phase-1/RAN4/meetings.jsonld` | 65,284 | 65,284 | 61 | `0a805e30586bd4d09bcb6a55e3875668897dccfd803cfbf42dd39518ae15b471` |
| `records/phase-1/RAN4/tdocs.jsonld.gz` | 4,115,555 | 95,389,486 | 174,739 | `04436b72395c40c85f410fe085d16543ca35d6f3c4a9421ddfd1a16b4de015cc` |
| `records/phase-1/RAN5/meetings.jsonld` | 59,341 | 59,341 | 37 | `147ec32129db1523fe74b42785d2c2db464f63f92726173f8aff71fb68bf7dcf` |
| `records/phase-1/RAN5/tdocs.jsonld` | 42,993,933 | 42,993,933 | 65,413 | `e049829b2b394a6ba0a7497fcd96e42e8985532680ab2130f9750ea06d960414` |
| `records/phase-2/RAN1/decision_dispositions.jsonld` | 36,707,833 | 36,707,833 | 22,649 | `41dd5067b08f4c1d8ae086c52375b6f840b04a3cdd4fc306c9e770ffedc87617` |
| `records/phase-2/RAN1/resolutions_agreements.jsonld` | 6,910,438 | 6,910,438 | 22,094 | `2552ed3f89f4147059d63aabec489fd973ffa349878d9b7d97ddaa8e297d5e6e` |
| `records/phase-2/RAN1/resolutions_conclusions.jsonld` | 974,223 | 974,223 | 2,824 | `f24a5e3337290a2e60ee2404e5247a7207c48d11715186d0ee29e3081bbf5e1b` |
| `records/phase-2/RAN1/resolutions_document_dispositions.jsonld` | 7,250,750 | 7,250,750 | 16,911 | `d4b1d5607e74898aadef4fad0b59a827be485f57f576a5c4d7538703dbb6a0ec` |
| `records/phase-2/RAN1/resolutions_working_assumptions.jsonld` | 339,858 | 339,858 | 938 | `339ff9da8e82089b1494f72b766d817b570529f5d3ab087b6a5d4955b3f55bca` |
| `records/phase-2/RAN2/decision_dispositions.jsonld.gz` | 5,008,710 | 83,767,367 | 47,236 | `7fb8b90c71898ece27d6f3057e285c92175c75b001dbedc3f3428e3ac9003dac` |
| `records/phase-2/RAN2/resolutions_agreements.jsonld` | 1,615,914 | 1,615,914 | 5,026 | `1cbce820ef27da0b08402917bac9bc8ddce6a9b047e0d5cb38e91e9f3ec5f05b` |
| `records/phase-2/RAN2/resolutions_conclusions.jsonld` | 50,375 | 50,375 | 23 | `a3eb9b3fcff1040316c8b8d131a663d119fb026de7386ee3046b6a8a04f5fbff` |
| `records/phase-2/RAN2/resolutions_document_dispositions.jsonld` | 19,235,919 | 19,235,919 | 44,426 | `d2d77a85811b9335b22ea8c9e582045906305f072514c988cf30bea3d9b4b9bd` |
| `records/phase-2/RAN2/resolutions_working_assumptions.jsonld` | 141,436 | 141,436 | 322 | `c4a40874babe8041de4b188168f09f178e11444310dc6011f15ae306c7189104` |
| `records/phase-2/RAN3/decision_dispositions.jsonld.gz` | 5,292,688 | 86,794,182 | 58,512 | `4324c952fa6496dc569d818425c4e2eeebdb14a947a0473a04da5d685e324c38` |
| `records/phase-2/RAN3/resolutions_agreements.jsonld` | 659,454 | 659,454 | 2,028 | `f41cd13528945ba958dc0d9539ee262cd76b39a060a1b5cbd7415fdcfb80bb85` |
| `records/phase-2/RAN3/resolutions_conclusions.jsonld` | 218,177 | 218,177 | 537 | `0e16beb1dea19e76c1ae9fad4d957b003e020f55fcda910e90bbcd62f0c149db` |
| `records/phase-2/RAN3/resolutions_document_dispositions.jsonld` | 25,197,761 | 25,197,761 | 58,183 | `627df170b97a92468cf0dfad1ef8a32d44c6579fa4628c28399232276d664e7e` |
| `records/phase-2/RAN3/resolutions_working_assumptions.jsonld` | 150,289 | 150,289 | 357 | `e3af4c2809901a59816db5333322c7f4499abe77bc74787ea5fe6a499345682f` |
| `records/phase-2/RAN4/decision_dispositions.jsonld.gz` | 14,847,217 | 246,138,827 | 164,176 | `11269df9ec3d74dc64d646e9679a5949a5763da25da16d41fd434d315ec1d704` |
| `records/phase-2/RAN4/resolutions_agreements.jsonld` | 1,368,054 | 1,368,054 | 4,361 | `ce97c674dc3c1e426f96609ce81ae6d3e9a1601929984181da93c94f46fcea1c` |
| `records/phase-2/RAN4/resolutions_conclusions.jsonld` | 74,498 | 74,498 | 98 | `131aae432a222098e03942e4540fe9418c940cc83c62c9879c223aad435a6f85` |
| `records/phase-2/RAN4/resolutions_document_dispositions.jsonld.gz` | 3,442,352 | 71,845,398 | 164,036 | `c66a4cc7217164d5cffb1a0f5cf6ad002426df0160f6df97ab71725e87cf3252` |
| `records/phase-2/RAN4/resolutions_working_assumptions.jsonld` | 43,779 | 43,779 | 4 | `fa1477d7789fade02971c73879229fa1fcd721b513a3ac3fbad55dff36effab4` |
| `records/phase-2/RAN5/decision_dispositions.jsonld.gz` | 5,960,052 | 100,726,217 | 65,489 | `4159bc7441dd6c3c239b5092d42994de6d032ebb7c2c76b47ca1158f935cac1e` |
| `records/phase-2/RAN5/resolutions_conclusions.jsonld` | 73,921 | 73,921 | 87 | `6006d66989c6d5d8ab16b925cfc0596f51a9b08a8e60dd8b314832a30b5a3f03` |
| `records/phase-2/RAN5/resolutions_document_dispositions.jsonld` | 28,529,887 | 28,529,887 | 65,396 | `32b90fd25fa11013da6e0542b7eea3d8e39e2d31dd46c591fa2fc8320540bfbc` |
| `records/phase-4/RAN1/cr_extensions.jsonld` | 649,657 | 649,657 | 2,120 | `53c457ca554fdafafec3cd9c144f8f06f5895d6410f127ca19315f878811c6bc` |
| `records/phase-4/RAN1/crpacks.jsonld` | 187,195 | 187,195 | 522 | `78319d8126488d13318860d6d58a8061c115a9ed2cb334f7bb6b9085b6487d7c` |
| `records/phase-4/RAN1/section_extensions.jsonld` | 392,939 | 392,939 | 1,621 | `bd298cf56a87005c673f7f311153a5f95196f5a9b684b5e2897b6ccdbf9c6322` |
| `records/phase-4/RAN2/cr_extensions.jsonld` | 1,698,885 | 1,698,885 | 8,201 | `9fccba01d875c7a5b5dd15328c46b296c7583926db8032c6d44c3ee45eddd806` |
| `records/phase-4/RAN2/crpacks.jsonld` | 304,870 | 304,870 | 602 | `6f7ccbd1cf941025ed479d430c60dde9a960b503f657257beda9838fbed50171` |
| `records/phase-4/RAN2/section_extensions.jsonld` | 811,390 | 811,390 | 3,798 | `b67c1888e17ecefb63ed1f68dd1885c0420166b87d669d13654fc86321e993a4` |
| `records/phase-4/RAN3/cr_extensions.jsonld` | 1,014,343 | 1,014,343 | 3,040 | `721340c7c3260dbecd94d6d67063c178582d839fbf35b08f77ebc1c9270a1f28` |
| `records/phase-4/RAN3/crpacks.jsonld` | 199,525 | 199,525 | 463 | `c87a4d871e8c2c74bcb275feaebb022fc6f7e054b063ef40d8f0c32209834130` |
| `records/phase-4/RAN3/section_extensions.jsonld` | 742,316 | 742,316 | 3,972 | `74aa7d25cbce8dff491f3937824be10c50bee777c53b288f74fd732ac31e203e` |
| `records/phase-4/RAN4/cr_extensions.jsonld` | 4,198,516 | 4,198,516 | 14,020 | `728736274782d307f6b407cd428d1a9d5fa296b772d1409a4f41e6c617d04fc0` |
| `records/phase-4/RAN4/crpacks.jsonld` | 642,519 | 642,519 | 1,328 | `0c94dd8df64917f2fa32ee64d2b3de771e8c03fb810de080f109933184115f88` |
| `records/phase-4/RAN4/section_extensions.jsonld` | 3,119,092 | 3,119,092 | 18,334 | `691fa5cb85c59f0d527ba24246409d2cb22dba1c5c717fa3ce7f39369fd8eff1` |

## 10. Tools

The scripts of this run are in `rs_tools_vldb/` next to this folder: `stage_records.py`
(the modified copy), `run_stage.sh`, `compare_with_review_staging.py`, `run_scans.sh`,
`run_extras.sh`, `class_name_hits.py`, `run_gzip.sh`, `verify_release.py`,
`run_grep_check.sh` and `build_redaction_list.py`. Their working outputs are in
`rs_tools_vldb/work/` and are not part of the release.
