"""SPECTRA pipeline — Stage 03a: parse CR DOCX body to JSON-LD.

Extracts CR cover-template fields (3GPP TR 21.801 template) into
SPECTRA-conformant JSON-LD: reasonForChange, summaryOfChange, otherComments,
modifiesSection list.

Sanitized for public release.

Usage:
    python parse_cr.py --in /path/to/CR.docx --out cr_bodies.jsonld
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any

from docx import Document

SPECTRA = "https://w3id.org/spectra#"

# 3GPP CR cover-template header labels (variants seen in the wild)
COVER_LABELS = {
    "tdoc_number": [r"^CR-Form-v\d", r"^Tdoc\s*$", r"^TDoc\s*$"],
    "spec_number": [r"^Spec\s*number", r"^Specification\s*Number"],
    "cr_number": [r"^CR-Number", r"^CR\s*number\s*$"],
    "version": [r"^Current\s*Version", r"^CR\s*revision\s*$"],
    "release": [r"^Release\s*$"],
    "category": [r"^Category\s*$"],
    "reason_for_change": [r"^Reason\s*for\s*change", r"^Reason\s*for\s*Change"],
    "summary_of_change": [r"^Summary\s*of\s*change", r"^Summary\s*of\s*Change"],
    "other_comments": [r"^Other\s*comments", r"^Other\s*Comments"],
    "clauses_affected": [r"^Clauses\s*affected", r"^Clauses\s*Affected"],
}


def match_label(cell_text: str, label: str) -> bool:
    """Case-insensitive label match against COVER_LABELS patterns."""
    text = cell_text.strip()
    for pat in COVER_LABELS.get(label, []):
        if re.match(pat, text, re.IGNORECASE):
            return True
    return False


def extract_cover_fields(doc: Document) -> Dict[str, str]:
    """Walk DOCX tables and pick the cover-template grid (typically the
    first table containing 'CR-Form' or the first ~4-column 2-row block)."""
    fields: Dict[str, str] = {}
    for table in doc.tables:
        # Iterate cells; left-cell == label, right-cell == value
        for row in table.rows:
            cells = row.cells
            for i in range(len(cells) - 1):
                left = cells[i].text.strip()
                right = cells[i + 1].text.strip()
                for label in COVER_LABELS:
                    if match_label(left, label) and right:
                        fields.setdefault(label, right)
        # Stop after first table that yields ≥ 3 cover fields
        if len(fields) >= 3:
            break
    return fields


def parse_clauses_affected(field_value: str, spec_number: str) -> List[str]:
    """'5.1.3, 6.2, 8.4.1' + spec '38.214' → list of Section IRIs."""
    if not field_value or not spec_number:
        return []
    sections = re.split(r"[,;]\s*", field_value.strip())
    return [
        f"{SPECTRA}section/{spec_number}/{s.strip()}"
        for s in sections if s.strip()
    ]


def parse_cr_docx(docx_path: Path) -> Dict[str, Any]:
    """Parse one CR DOCX into a SPECTRA JSON-LD record."""
    doc = Document(str(docx_path))
    fields = extract_cover_fields(doc)
    cr_num = fields.get("cr_number", "").strip() or docx_path.stem
    spec_num = fields.get("spec_number", "").strip()
    rec: Dict[str, Any] = {
        "@id": f"{SPECTRA}cr/{cr_num}",
        "@type": f"{SPECTRA}CR",
        f"{SPECTRA}crNumber": cr_num,
    }
    if spec_num:
        rec[f"{SPECTRA}modifies"] = [{"@id": f"{SPECTRA}spec/{spec_num}"}]
    for src, pred in [
        ("reason_for_change", "reasonForChange"),
        ("summary_of_change", "summaryOfChange"),
        ("other_comments", "crOtherComments"),
        ("version", "currentVersion"),
        ("release", "targetRelease"),
        ("category", "crCategory"),
    ]:
        v = fields.get(src, "").strip()
        if v:
            rec[f"{SPECTRA}{pred}"] = v
    sections = parse_clauses_affected(fields.get("clauses_affected", ""), spec_num)
    if sections:
        rec[f"{SPECTRA}modifiesSection"] = [{"@id": s} for s in sections]
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="input", required=True, type=Path,
                    help="Path to CR DOCX (or directory; processes all *.docx)")
    ap.add_argument("--out", required=True, type=Path, help="Output JSON-LD path")
    args = ap.parse_args()

    if not args.input.exists():
        sys.exit(f"ERROR: input not found: {args.input}")

    docx_files: List[Path]
    if args.input.is_dir():
        docx_files = sorted(args.input.glob("*.docx"))
    else:
        docx_files = [args.input]

    records = [parse_cr_docx(f) for f in docx_files]
    graph = {
        "@context": {"@vocab": SPECTRA, "tdoc": SPECTRA},
        "@graph": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(graph, indent=2, ensure_ascii=False))
    print(f"[parse_cr] Wrote {len(records)} CR records to {args.out}")


if __name__ == "__main__":
    main()
