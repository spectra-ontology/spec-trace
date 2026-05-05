#!/usr/bin/env bash
# Build the standalone Supplementary Appendix PDF and copy it to the user's
# Windows Desktop (WSL path ${SPECTRA_BUILD_OUTDIR:-$HOME/Desktop}).
#
# Run from any directory; the script cd's into its own location first.
#
# Output:
#   release_package/supplement/standalone_appendix.pdf      (build artifact)
#   ${SPECTRA_BUILD_OUTDIR:-$HOME/Desktop}/SPECTRA_Supplementary_Appendix.pdf
#
# Source of truth: PAPER_APPENDIX.tex (the supplement content).
# standalone_appendix.tex is the wrapper providing preamble + title + main-paper
# label stubs so cross-references resolve to "main paper §X" text.

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Symlink llncs.cls + splncs04.bst from the main paper's TeX directory if missing.
LATEX_SRC_DIR="$SCRIPT_DIR/../../docs/paper/iswc/latex"
[ ! -e llncs.cls ]      && ln -sf "$LATEX_SRC_DIR/llncs.cls" llncs.cls
[ ! -e splncs04.bst ]   && ln -sf "$LATEX_SRC_DIR/splncs04.bst" splncs04.bst

echo "[1/3] pdflatex pass 1..."
pdflatex -interaction=nonstopmode standalone_appendix.tex > /tmp/sup_build_p1.log 2>&1 \
  || { echo "FAIL pass 1; see /tmp/sup_build_p1.log"; tail -20 /tmp/sup_build_p1.log; exit 1; }

echo "[2/3] pdflatex pass 2 (resolve refs)..."
pdflatex -interaction=nonstopmode standalone_appendix.tex > /tmp/sup_build_p2.log 2>&1 \
  || { echo "FAIL pass 2; see /tmp/sup_build_p2.log"; tail -20 /tmp/sup_build_p2.log; exit 1; }

# Sanity check: 0 unresolved cross-references.
QQ=$(python3 -c "import fitz; doc=fitz.open('standalone_appendix.pdf'); print(sum(p.get_text().count('??') for p in doc))")
if [ "$QQ" -ne 0 ]; then
  echo "WARN: $QQ unresolved '??' refs in PDF — check stublabel coverage in standalone_appendix.tex"
fi

PAGES=$(python3 -c "import fitz; print(len(fitz.open('standalone_appendix.pdf')))")

# Copy to Windows Desktop (WSL).
DESKTOP="${SPECTRA_BUILD_OUTDIR:-$HOME/Desktop}"
DEST_NAME="SPECTRA_Supplementary_Appendix.pdf"
if [ -d "$DESKTOP" ]; then
  cp standalone_appendix.pdf "$DESKTOP/$DEST_NAME"
  echo "[3/3] copied to $DESKTOP/$DEST_NAME"
else
  echo "[3/3] skipped Desktop copy (no $DESKTOP)"
fi

# Clean intermediate files (keep .pdf + .tex).
rm -f standalone_appendix.aux standalone_appendix.log standalone_appendix.out standalone_appendix.toc

echo ""
echo "Done. Pages: $PAGES, '??' unresolved: $QQ"
md5sum standalone_appendix.pdf
[ -f "$DESKTOP/$DEST_NAME" ] && md5sum "$DESKTOP/$DEST_NAME"
