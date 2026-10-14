
CREATE TABLE cr (source_identity TEXT PRIMARY KEY, tdoc TEXT NOT NULL,
 specification TEXT NOT NULL, release TEXT NOT NULL, archive TEXT NOT NULL,
 member TEXT NOT NULL, archive_sha256 TEXT NOT NULL, member_sha256 TEXT NOT NULL);
CREATE TABLE declared_clause (source_identity TEXT NOT NULL REFERENCES cr,
 declared_clause TEXT NOT NULL, PRIMARY KEY(source_identity,declared_clause));
CREATE TABLE discrepancy (source_identity TEXT PRIMARY KEY REFERENCES cr,
 kind TEXT NOT NULL, native_field_locators TEXT NOT NULL);
CREATE TABLE cr_unresolved (source_identity TEXT PRIMARY KEY, tdoc TEXT NOT NULL,
 reason TEXT NOT NULL);
CREATE TABLE liaison (row_id TEXT PRIMARY KEY, observed_wg TEXT NOT NULL,
 tdoc TEXT NOT NULL, raw_to TEXT NOT NULL, source_path TEXT NOT NULL,
 source_sha256 TEXT NOT NULL, sheet TEXT NOT NULL, source_row TEXT NOT NULL);
CREATE TABLE recipient (row_id TEXT NOT NULL REFERENCES liaison,
 addressed_recipient TEXT NOT NULL, PRIMARY KEY(row_id,addressed_recipient));
CREATE TABLE ls_excluded (source_identity TEXT PRIMARY KEY, observed_wg TEXT NOT NULL,
 raw_to TEXT NOT NULL, reason TEXT NOT NULL);
