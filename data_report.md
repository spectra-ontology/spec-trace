# SQLite exports, source manifest, restore script and ontology: data report

This report covers the four folders `sqlite/`, `sources/`, `restore/` and `ontology/` of this
release folder. Every number below was measured on the files named here. Paths that start with
`ontology/`, `scripts/` or `logs/` are relative to the root of the source repository; all other
paths are relative to this folder. The checking tools are listed in section 7.

## 1. Summary

| Folder | Files | Bytes | Content | Changed against the source |
|---|---:|---:|---|---|
| `sqlite/` | 6 | 100,876,837 | five SQLite exports (one plain, four as gzip) and `SHA256SUMS.txt` | no; every database is byte-identical to its source after `gunzip` |
| `sources/` | 1 | 217,489 | `manifest.jsonl`, 280 rows | no |
| `restore/` | 1 | 18,984 | `restore_sources.py` | no |
| `ontology/` | 2 | 132,478 | `tdoc-ontology.ttl`, `tdoc-ontology-shapes.ttl` | no |

No redaction was applied to any file in these four folders. The reasons are measured in
sections 2.4 to 2.7 (SQLite), 3 (manifest) and 4 (restore script). Items that need a decision
by a person are listed in section 8.

## 2. `sqlite/`

### 2.1 Files and hashes

Source folder: `logs/publication/paper/ongoing/sigir-2027-research/integration/sqlite_final/`.
A database of more than 50,000,000 bytes is stored as the output of `gzip -9 -n`.

| Database | Raw bytes | Raw SHA-256 | Stored file | Stored bytes | Stored SHA-256 |
|---|---:|---|---|---:|---|
| `RAN1.sqlite` | 36,360,192 | `5e0d83e8418d887ec17433a883695a7ebcbff25e4c9ff048f4c2bd95f0c16cc1` | `RAN1.sqlite` | 36,360,192 | same as raw |
| `RAN2.sqlite` | 55,386,112 | `c770451677496aec0e4d489f06df68c02369d9347041df99f719842f712040c0` | `RAN2.sqlite.gz` | 10,492,025 | `cd4dc565713f1d49bb389ef2056474380ed78d547f63cf8dd81580d85ec26a9d` |
| `RAN3.sqlite` | 53,866,496 | `c6e69a1472cf035bbe817155275970158b0512e62c38dd4983a63d77e10ab625` | `RAN3.sqlite.gz` | 10,450,482 | `a43e9433f43725c2ba1ad4f9e841a4725245d1bb17cab2678967c12d9baa9b78` |
| `RAN4.sqlite` | 156,041,216 | `b45cdcb406bf2817b98f1055593c2a810862fd177509f3fd11ecb6dd08af1292` | `RAN4.sqlite.gz` | 30,013,958 | `5a7e70679718630e65ca298733a60cf6cb922e466fa17d4f8e6a0cec3289f504` |
| `RAN5.sqlite` | 72,126,464 | `58cc62435eb9a90b830862b5fe4ba18f82b8acd283c92abdfd2a146d6937cfcd` | `RAN5.sqlite.gz` | 13,559,466 | `9a9797eefda6071ea33d6e9f0a26b4ecd43bdd4ead034e88d670d031fb986d27` |

Checks on the stored files:

1. Each of the four gzip files was decompressed again; the result has the raw size and the raw
   SHA-256 of its source (4 of 4).
2. The gzip headers carry no file name and no time (first ten bytes `1f8b0800000000000203` in
   all four).
3. `sqlite/SHA256SUMS.txt` has nine lines in `sha256sum` format: one for every stored file
   and one for every raw database that is stored compressed. `sha256sum -c --ignore-missing
   SHA256SUMS.txt` reports OK for the five stored files; after `gunzip` the same command also
   checks the four raw databases.
4. The SHA-256 values of the five source files were the same before and after the work. The
   source files were opened only with a read-only URI.
5. `PRAGMA integrity_check` returns `ok` for all five databases.

The file `export_manifest.json` of the source folder is not included (see section 8, item 8).

### 2.2 Statements of the paper

| Statement | Measured | Result |
|---|---|---|
| 11 tables in each database | 11 tables in each of the five databases, one schema text shared by all five | holds |
| 36 to 156 MB | 36,360,192 bytes (RAN1) to 156,041,216 bytes (RAN4); in units of 1,000,000 bytes that is 36.36 to 156.04, in units of 1,048,576 bytes it is 34.68 to 148.81 | holds in decimal megabytes |
| largest table 174,739 rows | `document` in `RAN4.sqlite`, 174,739 rows; the next largest is `resolution` in `RAN4.sqlite`, 168,499 rows | holds |

The sum of the five raw sizes is 373,780,480 bytes.

### 2.3 Schema and row counts

All five databases have the same 11 tables and 19 indexes (13 created by the exporter, 6
automatic indexes of the primary keys). Page size 4,096, no free pages, encoding UTF-8.

```
CREATE TABLE document(id TEXT PRIMARY KEY, number TEXT, doc_type TEXT, cr_number TEXT, spec TEXT, target_release TEXT, list_status TEXT, presented_at TEXT, pack_field TEXT);
CREATE TABLE revision(earlier TEXT, later TEXT);
CREATE TABLE meeting(id TEXT PRIMARY KEY, label TEXT, number_int INTEGER, wg TEXT);
CREATE TABLE resolution(id TEXT PRIMARY KEY, meeting_id TEXT);
CREATE TABLE disposition(id TEXT PRIMARY KEY, resolution_id TEXT, target TEXT, code TEXT, evidence_status TEXT, scope TEXT, evidence_path TEXT, evidence_sha256 TEXT);
CREATE TABLE cr_pack(id TEXT PRIMARY KEY, pack_number TEXT, tsg_meeting TEXT, tsg_number INTEGER);
CREATE TABLE cr_in_pack(cr TEXT, pack_id TEXT);
CREATE TABLE pack_member(cr TEXT, pack_id TEXT);
CREATE TABLE section(id TEXT PRIMARY KEY, spec TEXT, release TEXT, clause TEXT);
CREATE TABLE cr_modifies_section(cr TEXT, section_id TEXT);
CREATE TABLE section_modified_by(cr TEXT, section_id TEXT);
```

| Table | RAN1 | RAN2 | RAN3 | RAN4 | RAN5 | Sum |
|---|---:|---:|---:|---:|---:|---:|
| `cr_in_pack` | 2,120 | 5,939 | 3,038 | 13,952 | 29,438 | 54,487 |
| `cr_modifies_section` | 6,141 | 12,732 | 10,064 | 38,102 | 38,324 | 105,363 |
| `cr_pack` | 522 | 602 | 463 | 1,328 | 1,430 | 4,345 |
| `disposition` | 22,649 | 47,236 | 58,512 | 164,176 | 65,489 | 358,062 |
| `document` | 127,149 | 124,271 | 60,566 | 174,739 | 65,413 | 552,138 |
| `meeting` | 62 | 61 | 60 | 61 | 37 | 281 |
| `pack_member` | 2,120 | 5,939 | 3,038 | 13,952 | 29,438 | 54,487 |
| `resolution` | 42,767 | 49,797 | 61,105 | 168,499 | 65,483 | 387,651 |
| `revision` | 12,000 | 22,370 | 15,690 | 23,393 | 18,367 | 91,820 |
| `section` | 1,621 | 3,798 | 3,972 | 18,334 | 13,612 | 41,337 |
| `section_modified_by` | 6,141 | 12,732 | 10,064 | 38,102 | 38,324 | 105,363 |
| All tables | 223,292 | 285,477 | 226,572 | 654,638 | 365,355 | 1,755,334 |

### 2.4 Column census and classification

The databases have 41 columns: 39 declared TEXT and 2 declared INTEGER. The 39 TEXT columns
hold 8,237,436 text values with 199,447,427 characters in total. The longest text value in any
column has 90 characters. One column has values with white space (`document.list_status`,
88,121 values). No column holds a non-ASCII character.

Classification rule: a column is classed as an identifier or a closed vocabulary when every
text value of the column in all five databases matches the pattern in the table (a full match,
zero exceptions). The check ended with 0 failing columns. The counts are sums over the five
databases; "length" is the shortest and the longest text value in characters.

Class of every column: none is document text, a person name, a company name or an e-mail
address.

| Column | Text values | Null | Length | Pattern matched by every text value | Class |
|---|---:|---:|---|---|---|
| `cr_in_pack.cr` | 54,487 | 0 | 14 to 15 | TDOC | record identifier |
| `cr_in_pack.pack_id` | 54,487 | 0 | 21 | `tdoc:crpack/RP-\d{6}` | record identifier |
| `cr_modifies_section.cr` | 105,363 | 0 | 14 to 15 | TDOC | record identifier |
| `cr_modifies_section.section_id` | 105,363 | 0 | 28 to 55 | SECTION | record identifier |
| `cr_pack.id` | 4,345 | 0 | 21 | `tdoc:crpack/RP-\d{6}` | record identifier |
| `cr_pack.pack_number` | 4,345 | 0 | 9 | `RP-\d{6}` | document number |
| `cr_pack.tsg_meeting` | 4,345 | 0 | 6 to 7 | `RAN#\d{2,3}` | meeting label, 36 values (`RAN#77` to `RAN#112`) |
| `cr_pack.tsg_number` | 0 (4,345 integers) | 0 | | integer | number |
| `disposition.id` | 358,062 | 0 | 90 | `tdoc:decision-disposition/[0-9a-f]{64}` | record identifier (hash) |
| `disposition.resolution_id` | 358,062 | 0 | 28 to 48 | `tdoc:resolution/(?:AGR\|DOC\|CON\|WA)-[A-Za-z0-9.-]+` | record identifier |
| `disposition.target` | 358,062 | 0 | 14 to 16 | TDOC | record identifier |
| `disposition.code` | 358,062 | 0 | 5 to 20 | `[a-z]+(?:_[a-z]+)?` | closed vocabulary, 16 values |
| `disposition.evidence_status` | 358,062 | 0 | 7 to 15 | `source_verified\|pending` | closed vocabulary, 2 values |
| `disposition.scope` | 358,062 | 0 | 11 to 12 | `whole_target\|subdocument\|undetermined` | closed vocabulary, 3 values |
| `disposition.evidence_path` | 358,062 | 0 | 82 to 88 | PATH | relative path of a cited report |
| `disposition.evidence_sha256` | 358,062 | 0 | 64 | `[0-9a-f]{64}` | hash |
| `document.id` | 552,138 | 0 | 14 to 15 | TDOC | record identifier |
| `document.number` | 552,138 | 0 | 9 to 10 | `R[1-5]-\d{6,7}\|R5s\d{6}\|RP-\d{6}` | document number |
| `document.doc_type` | 552,138 | 0 | 7 to 9 | `tdoc:(?:Tdoc\|CR\|LS)` | closed vocabulary, 3 values |
| `document.cr_number` | 143,053 | 409,085 | 1 to 4 | `\d{1,4}\|-\|[A-Z]` | change request number |
| `document.spec` | 203,844 | 348,294 | 6 to 12 | SPEC | specification number |
| `document.target_release` | 430,308 | 121,830 | 5 to 6 | `Rel-\d{1,2}` | closed vocabulary, 15 values |
| `document.list_status` | 552,125 | 13 | 5 to 22 | `[A-Za-z]+(?: [A-Za-z]+){0,2}(?: \((?:BL\|IL)\))?\|\?{6}` | status word of the document list, 34 values |
| `document.presented_at` | 552,138 | 0 | 20 to 26 | `tdoc:meeting/` MEET | record identifier |
| `document.pack_field` | 57,490 | 494,648 | 1 to 16 | `RP-\d{6}\|-\|[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*-Core` | document number, or one of 3 work item codes |
| `meeting.id` | 281 | 0 | 20 to 26 | `tdoc:meeting/` MEET | record identifier |
| `meeting.label` | 281 | 0 | 7 to 13 | `RAN[1-5]#\d{2,3}(?:b\|bis\|Bis)?(?:-e)?` | meeting label |
| `meeting.number_int` | 0 (281 integers) | 0 | | integer | number |
| `meeting.wg` | 281 | 0 | 4 | `RAN[1-5]` | closed vocabulary, 5 values |
| `pack_member.cr` | 54,487 | 0 | 14 to 15 | TDOC | record identifier |
| `pack_member.pack_id` | 54,487 | 0 | 21 | `tdoc:crpack/RP-\d{6}` | record identifier |
| `resolution.id` | 387,651 | 0 | 27 to 48 | `tdoc:resolution/(?:AGR\|DOC\|CON\|WA)-[A-Za-z0-9.-]+` | record identifier |
| `resolution.meeting_id` | 387,651 | 0 | 20 to 26 | `tdoc:meeting/` MEET | record identifier |
| `revision.earlier` | 91,820 | 0 | 14 to 15 | TDOC | record identifier |
| `revision.later` | 91,820 | 0 | 14 to 15 | TDOC | record identifier |
| `section.id` | 41,337 | 0 | 28 to 55 | SECTION | record identifier |
| `section.spec` | 41,337 | 0 | 6 to 8 | SPEC | specification number |
| `section.release` | 41,337 | 0 | 6 | `Rel-\d{2}` | closed vocabulary, 5 values |
| `section.clause` | 41,337 | 0 | 1 to 28 | `[A-Za-z0-9][A-Za-z0-9._-]*` | clause number (41,277 rows) or ASN.1 name (60 rows) |
| `section_modified_by.cr` | 105,363 | 0 | 14 to 15 | TDOC | record identifier |
| `section_modified_by.section_id` | 105,363 | 0 | 28 to 55 | SECTION | record identifier |

Named patterns:

```
TDOC    tdoc:(?:R[1-5]-\d{6,8}|R5s\d{6}|RP-\d{6}|S[1-6]-\d{6})
MEET    RAN[1-5]_\d{2,3}(?:b|bis|Bis)?(?:-e)?
SPEC    \d{2}\.\d{3}(?:-\d{1,2}){0,2}
SECTION tdoc:section/ SPEC -Rel-\d{2}- [A-Za-z0-9][A-Za-z0-9._-]*
PATH    ontology/input/tsg/RAN/formal/meetings/RAN[1-5]/Final_Report/Final_Report_RAN[1-5]-\d{2,3}(?:b|bis|Bis|-bis)?(?:[-_]e)?\.docx
```

Further counts from the same check:

1. `document.id` prefixes: R1 127,149; R2 124,271; R3 60,566; R4 174,739; R5 65,413.
2. `resolution.id` prefixes: DOC 348,952; AGR 33,509; CON 3,569; WA 1,621.
3. `revision.earlier` holds 18 values of the form `tdoc:RP-` and 1 value `tdoc:S5-221058`.
4. `disposition.target` holds 3 values with an eight digit number (`tdoc:R2-19012574`,
   `tdoc:R2-23113843`, `tdoc:R4-21043963`).
5. `document.cr_number` holds 259 values `-` and 2 values that are one capital letter.
6. `document.pack_field` holds 52,998 values of the form `RP-\d{6}`, 4,457 values `-` and 35
   values that are a work item code: `5G_V2X_NRSL-Core` 25, `NR_SL_enh-Core` 7,
   `NR_newRAT-Core` 3.
7. `section.clause`: 41,277 rows are a clause number; 60 rows over 55 distinct values are an
   ASN.1 type or message name used as a clause label (for example `CellGroupConfig` 3,
   `RRCReconfiguration` 2, `RadioBearerConfig` 2, `NZP-CSI-RS-ResourceSet` 2, `SIB1`, `Paging`,
   `ShortMAC-I`).
8. `disposition.evidence_path` has six shapes after digits are folded, all of the form PATH.
   The 278 distinct pairs of path and hash are compared with the manifest in section 3.3.

### 2.5 Closed vocabularies in full

`document.list_status` (34 text values and null): noted 129,954; available 94,521; not treated
78,181; revised 74,925; agreed 71,756; approved 22,541; withdrawn 21,558; endorsed 19,746;
reserved 19,182; not pursued 9,240; postponed 5,153; merged 3,184; treated 1,333; endorsed (BL)
469; not concluded 143; rejected 77; Endorsed 45; replied to 42; for email approval 23; Noted
18; null 13; Agreed 5; partially approved 4; reissued 4; Return to 3; conditionally agreed 3;
for email agreement 3; Endorsed (BL) 2; Technically endorsed 2; endorsed (IL) 2; technically
endorsed 2; ?????? 1; Email Approval 1; Endorseed 1; conditionally approved 1.

`disposition.code` (16 values): noted 104,406; agreed 99,564; revised 59,661; ambiguous 24,523;
not_treated 21,651; endorsed 19,626; withdrawn 16,147; not_pursued 4,759; postponed 3,862;
merged 1,834; conditionally_agreed 943; partially_agreed 587; not_agreed 267; not_concluded
117; rejected 77; replied_to 38.

`document.doc_type`: tdoc:Tdoc 320,119; tdoc:CR 204,781; tdoc:LS 27,238.

`disposition.evidence_status`: source_verified 333,539; pending 24,523.

`disposition.scope`: whole_target 331,932; undetermined 24,523; subdocument 1,607.

`meeting.wg`: RAN1 62; RAN2 61; RAN4 61; RAN3 60; RAN5 37.

`section.release`: Rel-18 11,621; Rel-19 10,921; Rel-17 8,213; Rel-16 6,180; Rel-15 4,402.

`document.target_release`: null 121,830; Rel-17 86,668; Rel-16 83,714; Rel-18 80,934; Rel-15
76,867; Rel-19 52,987; Rel-14 23,300; Rel-20 13,742; Rel-13 10,791; Rel-12 821; Rel-11 213;
Rel-10 158; Rel-8 57; Rel-9 46; Rel-21 9; Rel-5 1.

### 2.6 Scans

Lists used by the scans (read from the local working folder, not copied): 6 e-mail addresses
in 24 written forms, 2,816 contact names of more than one token, 1,089 company names, 3,186
name parts, 13 person patterns.

**Scan of every value of every column, five databases.** Result: 0 hits in every column of
every database for each of these scans: plain e-mail address, e-mail address with `%40`, the
character `@`, e-mail address encoded in an identifier, known address, home folder path,
account name, project name, the string `w3id.org/spectra`, local service address, telephone
number shape, Hangul character, non-ASCII character, contact name (token windows with two
token rules), company name (same two token rules), name part, person pattern.

**Positive control of the scanner.** A synthetic database with 14 planted rows was scanned
with the same code. Every scan kind fired: plain e-mail 1, `%40` e-mail 1, `@` 1, encoded
e-mail 1, known address 1, home path 1, account name 1, project name 1, namespace string 1,
local service 1, telephone shape 1, Hangul 2, non-ASCII 2, contact name 2 and 1 under the two
token rules, company name 1 and 1, name part 4, person pattern 1. The synthetic database and
its detailed output were deleted after the run; only the counts were kept.

**Scan of the raw bytes.** Every run of four or more printable ASCII bytes in each file was
scanned with the same patterns, so that page slack and space outside the table rows is covered.

| Database | Bytes | ASCII runs | Characters in runs | Bytes of value 128 or more | Hangul sequences | `@` bytes | Other hits |
|---|---:|---:|---:|---:|---:|---:|---|
| `RAN1.sqlite` | 36,360,192 | 563,988 | 29,169,959 | 1,056,066 | 0 | 4,880 | none |
| `RAN2.sqlite` | 55,386,112 | 805,899 | 46,085,830 | 1,553,680 | 0 | 16,520 | none |
| `RAN3.sqlite` | 53,866,496 | 690,859 | 44,555,176 | 1,417,889 | 0 | 2,421 | none |
| `RAN4.sqlite` | 156,041,216 | 1,940,150 | 128,347,920 | 4,180,314 | 0 | 39,439 | none |
| `RAN5.sqlite` | 72,126,464 | 1,082,387 | 59,679,245 | 2,086,887 | 0 | 12,471 | company token 1 |
| Sum | 373,780,480 | 5,083,283 | 307,838,130 | 10,294,836 | 0 | 75,731 | |

Reading of the raw scan:

1. No e-mail address pattern, known address, contact name, name part, person pattern, home
   path, account name or project name was found in any file.
2. The `@` bytes and the bytes of value 128 or more are not in any stored value: the scan of
   the values found 0 `@` characters and 0 non-ASCII characters in all 8,237,436 text values.
   They are bytes of the page and record structure that happen to fall in a printable run.
3. The one company token hit in `RAN5.sqlite` was located: byte offset 71,634,805, page
   17,489, a leaf page of the index `section_modified_by_section_id`. The token is the last
   digit of the identifier `tdoc:section/38.523-1-Rel-19-7.1.1.7.3` followed by two bytes of
   the next field of the index record. It is not a stored value.

### 2.7 Agreement with the released records

**Column sources.** The exporter `scripts/publication/paper/ongoing/sigir-2027-research/export_chain_records_sqlite.py`
fills every column from a record field that the release keeps. No column derives from a field
that `stage_records.py` drops (the titles, abstracts, secretary remarks, affected clauses,
contact and source company links of the documents; the evidence quote of the dispositions; the
content and note of the resolutions; the three free text fields of the change request
records). The exporter reads these record keys: `@id`, `@type`, `tdoc:tdocNumber`,
`tdoc:crNumber`, `modifies`, `targetRelease`, `tdoc:status`, `presentedAt`, `tdoc:tsgCRPack`,
`isRevisionOf`, `tdoc:meetingNumber`, `tdoc:meetingNumberInt`, `tdoc:workingGroup`, `madeAt`,
`dispositionOf`, `dispositionTarget`, `dispositionCode`, `evidenceStatus`, `assessmentMethod`
(its `scope`), `evidencePath`, `evidenceSha256`, `tdoc:crPackId`, `tdoc:tsgMeeting`, `hasCR`,
`belongsToCRPack`, `modifiesSection` and `modifiedByCR`. All of them are in the keep lists of
`stage_records.py`. The ledger `records_redactions.jsonl` (58 rows) records 254 removed link
values, in the keys `originalLS` 154, `replyTo` 92, `sentTo` 5, `ccTo` 2 and `replyIn` 1; the
exporter reads none of these five keys. The ledger counts 552,138 removed titles, 358,062
removed evidence quotes and 387,651 removed resolution contents, which equal the row sums of
`document`, `disposition` and `resolution` in section 2.3.

**Rebuild from the released records.** The exporter's `export` function was run unchanged on
the 48 files of `records/` in this folder (gzip files decompressed, `records/RAN5_graph_export/RAN5/`
read as the phase 4 input of RAN5), and every table was compared with the source database in
sorted order.

| Working group | Record files read | Files whose hash equals the staged hash in `records_redactions.jsonl` | Rows rebuilt | Rows in the export | Rows that differ | Schema text equal |
|---|---:|---:|---:|---:|---:|---|
| RAN1 | 10 | 10 | 223,292 | 223,292 | 0 | yes |
| RAN2 | 10 | 10 | 285,477 | 285,477 | 0 | yes |
| RAN3 | 10 | 10 | 226,572 | 226,572 | 0 | yes |
| RAN4 | 10 | 10 | 654,638 | 654,638 | 0 | yes |
| RAN5 | 8 | 8 | 365,355 | 365,355 | 0 | yes |

So the five databases hold exactly the rows that the released JSON-LD files give, and a
redaction of the databases is not needed to keep them in step with the released records.

The rebuilt files have the same size as the exports. `RAN2.sqlite` is also byte-identical to
its rebuild. The other four differ in bytes although every row is equal: their header records
SQLite library 3.37.2 as the writer, the rebuild was written by library 3.50.4 (as was
`RAN2.sqlite`). The largest record file read is 246,138,827 bytes after decompression
(`records/phase-2/RAN4/decision_dispositions.jsonld.gz`); the check read the files record by
record.

### 2.8 Redactions

None. Rows, columns and bytes before and after are identical for all five databases (hashes in
section 2.1). The SQL that derives the gold answers runs on unchanged data.

## 3. `sources/`

### 3.1 File

`sources/manifest.jsonl`: 217,489 bytes, 280 lines, SHA-256
`71ff3993589198c1d6dcf24cbf2e86b208ca18ab5eedf50e6e1153dec45daebd`. Byte-identical to
`logs/publication/paper/ongoing/sigir-2027-research/release_preparation/staging_unique/sources/manifest.jsonl`.

### 3.2 Fields

Every row has the same 11 keys: `path`, `sha256`, `wg`, `kind`, `evidenceStatus`, `url`,
`urlAlternates`, `archiveSha256`, `member`, `memberSha256`, `conversion`. The file was read in
full.

| Field | Content | Measured |
|---|---|---|
| `path` | relative path of the cited report, the same string as `disposition.evidence_path` | 280 distinct, all match PATH of section 2.4, the folder in the path equals `wg`, longest 90 characters |
| `sha256` | hash of the cited file | 280 distinct, all 64 hexadecimal characters |
| `wg` | working group | RAN1 61, RAN2 61, RAN3 60, RAN4 61, RAN5 37 |
| `kind` | route to the cited file | native 204, converted 68, direct 7, converted_direct 1 |
| `evidenceStatus` | status values of the dispositions that cite the report | both values 240 rows, `source_verified` only 36, `pending` only 2, empty 2 |
| `url`, `urlAlternates` | archive locations | 479 URLs (280 and 199; 81 rows have no alternate), all on `https://www.3gpp.org` under `/ftp/tsg_ran/`, none with a query, fragment or user part; longest 144 characters |
| `archiveSha256` | hash of the downloaded file | all 64 hexadecimal characters; equal to `sha256` in 7 rows |
| `member`, `memberSha256` | file name inside the archive and its hash | null in 8 rows (kinds direct and converted_direct); member extensions docx 204, doc 64, docm 3, rtf 1; `sha256` equals `memberSha256` in 204 rows |
| `conversion` | conversion parameters | null in 211 rows; method `libreoffice` 66 rows, method `docm-repackage` 3 rows |

URLs by archive folder: `WG1_RL1` 112, `WG2_RL2` 121, `WG3_Iu` 108, `WG4_Radio` 95,
`WG5_Test_ex-T1` 43. URL extensions: zip 272, docx 7, doc 1.

Rows by working group and kind: RAN1 native 58, converted 3; RAN2 native 36, converted 25;
RAN3 native 47, converted 12, direct 1; RAN4 native 44, converted 15, direct 2; RAN5 native
19, converted 13, direct 4, converted_direct 1.

The `conversion` objects of the 66 `libreoffice` rows hold `tool` (LibreOffice), `version`
(7.3.7.2), `command` (one constant argument list with the placeholders `<profile>`, `<outdir>`
and `<member>`), `layout` (relative folder names of the form
`data/data_extracted/meetings/RAN2/TSGR2_100/Report/R2-1801701` and `rootDepth` 4),
`zipDateTime` (one date and time of the ZIP entries per row) and, in 16 rows, `objectIds` (83
values of the form `_` and digits for the part `word/document.xml`).

The manifest has no size field. It holds no document text. Scans of the whole file: 0
non-ASCII characters, 0 home paths, 0 `@` characters, 0 hits for the account name, the project
name, a local service address, `example.org`, "anonym" and "withheld", and 0 hits for the
contact name, company name and name part lists.

### 3.3 Coverage

| Check | Result |
|---|---|
| Distinct pairs of `evidence_path` and `evidence_sha256` in the five databases | 278 (RAN1 61, RAN2 61, RAN3 58, RAN4 61, RAN5 37); all 278 are in the manifest with the same hash |
| Manifest rows that no database row cites | 2: `Final_Report_RAN3-91.docx` and `Final_Report_RAN3-92.docx` (the two rows with an empty `evidenceStatus`) |
| Reports named by the abstention set under `abstention/RAN3`, `abstention/RAN4`, `abstention/RAN5` | 60, 61 and 37 distinct paths; all are in the manifest, and all 60, 61 and 37 pairs of path and hash equal the manifest; no manifest row of these three working groups is left unnamed |
| Cited files present in the source repository | 280 of 280, all with the hash of the manifest |

So the manifest covers all five working groups with 280 reports, and the inputs of the
abstention set (the reports of RAN3, RAN4 and RAN5) are covered in full.

## 4. `restore/`

`restore/restore_sources.py`: 18,984 bytes, 425 lines, SHA-256
`dec2f7df5b3168847820bed6ff19edf1612cb896388ce81581861448ca329682`. Byte-identical to the file
in `staging_unique/restore/`. The script was read in full and was not changed; there was
nothing to change:

| Looked for | Found |
|---|---|
| home folder paths, the account name, the project name | none |
| "anonym", "double-blind", "withheld" | none |
| `example.org/ran-records` or any `example.org` string | none |
| e-mail address, also in the User-Agent | none; the header is `Mozilla/5.0 (compatible; restore-sources/1.0)` |
| contact names, name parts | none |
| company list tokens | 3 hits, all the letters `III` inside a `struct` format string (lines 212, 215, 227) |

What the script does: for each manifest row it downloads the archive from the 3GPP server,
checks the archive hash, takes the member, checks the member hash, converts where the row says
so, and writes the file under `--dest` only when the hash of the result equals `sha256`. It
refuses absolute paths and paths with `..`. It needs Python 3 with `lxml`, and LibreOffice
(`soffice`) for the 66 `libreoffice` rows. Arguments: `--manifest`, `--dest`, `--work`
(required), `--wg`, `--report`, `--convert-tmp`.

Offline checks (the script has no self-test and no dry-run switch; it was not run against the
network):

1. `--help` exits with 0, on the source file and on the copy in this folder.
2. A call without arguments exits with 2 and names the three required arguments.
3. The file compiles.
4. A run with `--wg NONE`, which selects no row and so makes no request, exits with 0, prints
   `{}` and writes an empty report file.

## 5. `ontology/`

| File | Bytes | Lines | SHA-256 | Triples |
|---|---:|---:|---|---:|
| `ontology/tdoc-ontology.ttl` | 94,758 | 1,830 | `d9542b638fcdeed32bf2cfbf33bf7e21f53899197a31267a8f000820c67335c2` | 1,398 |
| `ontology/tdoc-ontology-shapes.ttl` | 37,720 | 787 | `69f87594bd2074793e4a40ae1dbf700de15e03d59c39124109bdccef174855af` | 917 |

Both files are byte-identical to `ontology/schema/tdoc-ontology.ttl` and
`ontology/schema/tdoc-ontology-shapes.ttl` of the source repository as they stand in the
working tree (both differ from the last commit there). Both parse with rdflib 7.6.0.

| Measure | Ontology | Shapes |
|---|---|---|
| `owl:Ontology` subject | `https://w3id.org/spectra` | `https://w3id.org/spectra/shapes` |
| `owl:versionInfo` | `"7.3.0"` | `"7.3.0"` |
| other version links | `owl:versionIRI <https://w3id.org/spectra/7.3.0>`, `owl:priorVersion <https://w3id.org/spectra/7.2.0>` | `owl:imports <https://w3id.org/spectra/7.3.0>` |
| `owl:Class` subjects | 57 (37 IRIs, all in `https://w3id.org/spectra#`, and 20 blank nodes) | 0 |
| `sh:NodeShape` subjects | 0 | 44 (all IRIs) |
| properties | 86 `owl:ObjectProperty`, 112 `owl:DatatypeProperty` | 100 distinct `sh:property` objects, 37 `sh:targetClass` objects, all in the namespace |
| namespace of the prefix `tdoc:` | `https://w3id.org/spectra#` | `https://w3id.org/spectra#` |

The namespace is `https://w3id.org/spectra#` in both files, the same one the released records
keep in their `@context`.

Creator, date, rights and link strings, verbatim. They were not edited.

Ontology file:

```
line 17   dc:title "SPECTRA: A Traceability Ontology for 3GPP RAN Standardization"@en ;
line 19   dc:creator "Sihyeon Choi (Samsung System LSI)" ;
line 20   dc:date "2026-11-17" ;
line 21   dc:rights "Creative Commons Attribution 4.0 International (CC-BY 4.0)" ;
line 22   dcterms:license <https://creativecommons.org/licenses/by/4.0/> ;
line 26   rdfs:seeAlso <https://github.com/spectra-ontology/spectra> .
```

Shapes file:

```
line 10   dc:title "SPECTRA SHACL Shapes for Ontology v7.3"@en ;
line 11   dc:date "2026-11-17" ;
```

The shapes file has no creator line. Neither file holds an e-mail address or a `mailto:` link
(the `@` characters, 481 and 15, are the tokens `@prefix` and `@en`).

Both files hold Korean text (Hangul runs: 588 in the ontology, 617 in the shapes):

| File | Lines with Hangul | Of these, Turtle comment lines (`#`) | Of these, inside a literal of the graph |
|---|---:|---:|---:|
| `ontology/tdoc-ontology.ttl` | 39 | 37 (lines 105 to 149) | 2 (`rdfs:comment` on lines 475 and 564, both tagged `@en`) |
| `ontology/tdoc-ontology-shapes.ttl` | 64 | 52 (lines 21 to 401) | 12 (11 `rdfs:comment` and 1 `sh:message`: lines 103, 121, 136, 169, 198, 224, 261, 371, 448, 458, 493, 508) |

The parsed graphs confirm the last column: 2 literals with Hangul in the ontology and 12 in
the shapes. Line 30 of the shapes file is a comment line and names `http://example.com` as a
former namespace. The ontology declares the classes `tdoc:Company` and `tdoc:Contact`; these
are schema terms, not data.

## 6. Stored anchor list

The benchmark builder `scripts/publication/paper/ongoing/sigir-2027-research/build_chain_items.py`
takes the anchor list through its argument `--anchors-from`. It reads the file line by line
and uses three keys of every line: `wg`, `family` and `anchor`. The final item sets record
which file was given, in the key `anchorsFrom` of their summary files:

| Item set | Anchor list file | Bytes | Lines | SHA-256 | Copy in this folder |
|---|---|---:|---:|---|---|
| core (RAN1 to RAN4, 530 items) | `logs/publication/paper/ongoing/sigir-2027-research/chain_items_rebuilt/chain_items.jsonl` | 743,896 | 530 | `a5188c48c5c0f309ed47451144d309fb2ee07e74edf211b2dd08b25cf9981a05` | `benchmark/chain_items_rebuilt/chain_items.jsonl`, byte-identical |
| RAN5 (140 items) | `logs/publication/paper/ongoing/sigir-2027-research/chain_items_ran5/chain_items.jsonl` | 293,494 | 140 | `f2e895372a079ad24e7c5ab774fff59bccef66701b470a1ba4e0d86e943a72f3` | `benchmark/chain_items_ran5/chain_items.jsonl`, byte-identical |

Both anchor list files are already inside `benchmark/`. They were not copied or changed by
this work. The summaries `benchmark/items_final/core/chain_items_summary.json` and
`benchmark/items_final/ran5/chain_items_summary.json` report 0 anchors that lost eligibility.

## 7. Checking tools

The tools are kept outside this folder, in `rs_tools_vldb/data_work/` of the preparation
folder. None calls a model or the network.

| Tool | Use |
|---|---|
| `census_sqlite.py`, `census_summary.py`, `census_flags.py` | tables, columns, value statistics and scans per column |
| `shape_census.py`, `shape_check.py` | value shapes and the full match check of section 2.4 |
| `positive_control.py` | the positive control of section 2.6 |
| `raw_scan.py` | the raw byte scan of section 2.6 |
| `reexport_check.py` | the rebuild of section 2.7 |
| `build_sqlite_release.py` | the copies, gzip files and hash list of section 2.1 |
| `manifest_check.py`, `coverage_check.py` | sections 3.2 and 3.3 |
| `text_scan.py` | scans of the manifest, the restore script and the ontology files |
| `ontology_check.py` | section 5 |

## 8. Open items for a decision by a person

1. **Creator line of the ontology.** `dc:creator "Sihyeon Choi (Samsung System LSI)"` names a
   person and an employer. The same header holds `rdfs:seeAlso <https://github.com/spectra-ontology/spectra>`,
   `dc:date "2026-11-17"`, and the rights and licence lines. Decide whether these stay as they
   are, and whether the licence stated here agrees with the `LICENSE` file of the package.
2. **Korean text in the ontology files.** 37 and 52 comment lines carry Korean changelog and
   design notes, and line 30 of the shapes file mentions `http://example.com` as a former
   namespace; these lines are outside the parsed graph. In addition 2 literals of the ontology
   and 12 literals of the shapes hold Korean words inside `rdfs:comment` or `sh:message`
   values, 8 of them tagged `@en`. Decide whether the comment lines stay and whether the 14
   literals are translated in the source files.
3. **File names of the cited reports.** `disposition.evidence_path` and the manifest field
   `path` are the builder's own relative names (for example
   `ontology/input/tsg/RAN/formal/meetings/RAN4/Final_Report/Final_Report_RAN4-98-e.docx`),
   not the file names of the 3GPP archive. The manifest maps each one to the 3GPP URL and to
   the member name inside the archive, which are unchanged 3GPP names. Check this against the
   sentence of the paper that says 3GPP file names are kept unchanged.
4. **No size field in the manifest.** A row identifies a file by URL, hashes and member name
   only. Add sizes only if the paper or the README promises them.
5. **Conversion parameters in the manifest.** The 66 `libreoffice` rows carry the relative
   folder layout, `rootDepth` 4 and the ZIP date and time of the original conversion run. The
   restore script needs them to reproduce the hashes. They hold no account name and no home
   path.
6. **Two manifest rows without a citing database row.** `Final_Report_RAN3-91.docx` and
   `Final_Report_RAN3-92.docx` are in the manifest and in the abstention inputs, and no
   `disposition` row cites them.
7. **Strings in the databases that come from 3GPP lists and specifications.** They are single
   status words, work item codes and clause labels, not passages: `document.list_status`
   (34 spellings as written in the 3GPP document lists, among them `??????`, `Endorseed` and
   `Return to`), `document.pack_field` (35 rows with one of 3 work item codes) and
   `section.clause` (60 rows with one of 55 ASN.1 names). The released records keep the same
   values. They are answer or join fields, so removing them would change query results; they
   were left unchanged.
8. **`export_manifest.json`.** The exporter's own manifest in the source folder is not in
   `sqlite/`. It holds the schema, the row counts and the paths, sizes and hashes of the 48
   input files. Those hashes are the hashes of the files before redaction, which the release
   does not hold, and the paths are repository paths. It has no home path and no name.
9. **Compressed storage.** Four databases must be decompressed with `gunzip` before use. The
   README and any code in the package that opens `sqlite/<WG>.sqlite` should say so.
10. **Restore script not exercised end to end here.** It was not run against the 3GPP server
    in this work. The 66 `libreoffice` rows depend on LibreOffice 7.3.7.2 to reproduce the
    recorded hashes.
11. **`anchorsFrom` in the item summaries.** The value in `benchmark/items_final/*/chain_items_summary.json`
    is the repository path of the anchor list (`logs/publication/paper/ongoing/sigir-2027-research/chain_items_rebuilt/chain_items.jsonl`
    and the RAN5 counterpart), while the file sits at `benchmark/chain_items_rebuilt/chain_items.jsonl`
    in this folder. The owner of `benchmark/` and of the README should state the mapping.
12. **Library version of the databases.** Four databases were written by SQLite 3.37.2 and
    `RAN2.sqlite` by 3.50.4. A rebuild with another library version gives equal rows and can
    give different bytes, so the hash list identifies these files, not every possible rebuild.
