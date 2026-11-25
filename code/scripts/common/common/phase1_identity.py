"""Read Phase-1 document identities before company normalization is available.

Only identifiers leave this probe. The original parser validates each workbook;
its normalized company properties remain the responsibility of the normalizer
and the production JSON-LD entry point after input promotion.
"""
from __future__ import annotations

from contextlib import redirect_stdout
import inspect
import io


def tdoc_ids(parser, path) -> frozenset[str]:
    """Return actual parser IDs without loading or publishing company mappings."""
    args = [path, {}]
    if len(inspect.signature(parser.process_file).parameters) >= 3:
        args.append(set())
    with redirect_stdout(io.StringIO()):
        output = parser.process_file(*args)
    instances = output[0] if isinstance(output, tuple) else output
    return frozenset(row['@id'].split(':', 1)[-1] for row in instances
                     if isinstance(row, dict) and isinstance(row.get('@id'), str))
