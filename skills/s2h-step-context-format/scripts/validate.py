#!/usr/bin/env python3
"""Validate one or more step context Markdown files against this skill's rules.

Usage: python3 validate.py <file> [<file> ...]

Exits 0 only when every file passes; a failing file prints one line per finding
and the process exits 1. Usage errors print to stderr and exit 2. Pass several
files sharing a chunk_id in one invocation so the cross-file check applies.

Why this script does not share the byte-identical JSON-schema validator body
used by sibling format skills: step context files are Markdown, not JSON, so
there is no reference schema to interpret - the checks below parse frontmatter,
headings, and requirement ID references directly. It stays stdlib-only (re, sys,
pathlib) for the same reason the sibling validators avoid third-party packages:
s2h skills are self-contained bundles that must run wherever python3 exists.

Per-file checks:
1. YAML frontmatter present at file start with non-empty values for kind,
   schema, run_id, step_id, chunk_id, type; kind is "step-context" and
   schema is "step-context/v1".
2. Every template heading from the SKILL.md Template block is present,
   including Contract.
3. Every requirement ID named in Requirements Covered also appears in that
   file's own Contract section.

Across files: when two or more files share a chunk_id, their Contract sections
must be verbatim-identical.
"""

import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = (
    "Contract",
    "Objective",
    "Requirements Covered",
    "Dependencies",
    "Interfaces",
    "Likely Files",
    "Exact Scope",
    "Acceptance Criteria",
    "Validation Commands",
    "Expected Failure or Success",
    "Exclusions",
    "Commit Expectations",
)

FRONTMATTER_FIELDS = ("kind", "schema", "run_id", "step_id", "chunk_id", "type")

CONST_FIELDS = {"kind": "step-context", "schema": "step-context/v1"}

ID_RE = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")
HEADING_RE = re.compile(r"##\s+(.+?)\s*$")


def die(message):
    print(f"validate: {message}", file=sys.stderr)
    sys.exit(2)


def split_document(text):
    """Return (frontmatter dict or None, body lines)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, lines
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            frontmatter = {}
            for raw in lines[1:index]:
                key, sep, value = raw.partition(":")
                if sep and key.strip():
                    frontmatter[key.strip()] = value.strip()
            return frontmatter, lines[index + 1:]
    return None, lines


def sections(body):
    """Map each H2 heading to its verbatim body text (outer blanks trimmed)."""
    found = {}
    current = None
    buffer = []
    for line in body:
        match = HEADING_RE.match(line)
        if match:
            if current is not None:
                found[current] = trim(buffer)
            current = match.group(1)
            buffer = []
        elif current is not None:
            buffer.append(line)
    if current is not None:
        found[current] = trim(buffer)
    return found


def trim(lines):
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return "\n".join(lines[start:end])


def check_file(path):
    """Return (findings, info) for one file; info holds chunk_id and contract."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read file: {exc}"], {}
    findings = []
    frontmatter, body = split_document(text)
    if frontmatter is None:
        findings.append("missing or unterminated YAML frontmatter at file start")
        info = {}
    else:
        for field in FRONTMATTER_FIELDS:
            if not frontmatter.get(field):
                findings.append(f"frontmatter field missing or empty: {field}")
        for field, expected in CONST_FIELDS.items():
            value = frontmatter.get(field)
            if value and value != expected:
                findings.append(
                    f'frontmatter {field} must be "{expected}", got "{value}"'
                )
        info = {"chunk_id": frontmatter.get("chunk_id", "")}
    headings = sections(body)
    for heading in REQUIRED_HEADINGS:
        if heading not in headings:
            findings.append(f"missing heading: {heading}")
    contract = headings.get("Contract", "")
    allowed = set(ID_RE.findall(contract))
    covered_ids = sorted(set(ID_RE.findall(headings.get("Requirements Covered", ""))))
    for req_id in covered_ids:
        if req_id not in allowed:
            findings.append(
                f"Requirements Covered names requirement ID {req_id} "
                "that is absent from its own Contract section"
            )
    info["contract"] = contract
    return findings, info


def main(argv):
    if not argv:
        die("no input files given")
    results = []
    by_chunk = {}
    for name in argv:
        findings, info = check_file(Path(name))
        results.append((name, findings, info))
        chunk_id = info.get("chunk_id", "")
        if chunk_id:
            by_chunk.setdefault(chunk_id, []).append(
                (name, info.get("contract", ""))
            )
    for chunk_id, members in sorted(by_chunk.items()):
        if len({member[1] for member in members}) > 1:
            for name, findings, info in results:
                if info.get("chunk_id") == chunk_id:
                    others = [other[0] for other in members if other[0] != name]
                    findings.append(
                        "Contract section is not verbatim-identical to "
                        + ", ".join(others)
                        + f" under shared chunk_id {chunk_id}"
                    )
    failures = 0
    for name, findings, _info in results:
        if findings:
            for line in findings[:20]:
                print(f"FAIL {name}: {line}")
            failures += 1
        else:
            print(f"PASS {name}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
