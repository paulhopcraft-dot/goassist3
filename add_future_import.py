#!/usr/bin/env python3
"""Add 'from __future__ import annotations' to Python files."""

import sys
from pathlib import Path


def add_future_annotations(filepath: Path) -> bool:
    """Add future annotations import if not present.

    Returns:
        True if file was modified, False otherwise
    """
    content = filepath.read_text(encoding='utf-8')

    # Skip if already present
    if 'from __future__ import annotations' in content:
        return False

    lines = content.splitlines(keepends=True)

    # Find insertion point (after docstring, before first import)
    in_docstring = False
    docstring_end_idx = None
    first_import_idx = None

    for idx, line in enumerate(lines):
        stripped = line.strip()

        # Track docstring
        if '"""' in line or "'''" in line:
            in_docstring = not in_docstring
            if not in_docstring:
                docstring_end_idx = idx

        # Find first import
        if not in_docstring and (stripped.startswith('import ') or stripped.startswith('from ')):
            first_import_idx = idx
            break

    if first_import_idx is None:
        # No imports found, skip
        return False

    # Insert after docstring (if exists) or at beginning
    insert_idx = docstring_end_idx + 1 if docstring_end_idx is not None else 0

    # Skip blank lines after docstring
    while insert_idx < len(lines) and not lines[insert_idx].strip():
        insert_idx += 1

    # Insert the import
    lines.insert(insert_idx, 'from __future__ import annotations\n')
    lines.insert(insert_idx + 1, '\n')

    # Write back
    filepath.write_text(''.join(lines), encoding='utf-8')
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python add_future_import.py <file1> [file2] ...")
        sys.exit(1)

    modified_count = 0
    for filepath_str in sys.argv[1:]:
        filepath = Path(filepath_str)
        if filepath.exists() and filepath.suffix == '.py':
            if add_future_annotations(filepath):
                print(f"[OK] {filepath}")
                modified_count += 1
            else:
                print(f"[SKIP] {filepath}")

    print(f"\nModified {modified_count} file(s)")
