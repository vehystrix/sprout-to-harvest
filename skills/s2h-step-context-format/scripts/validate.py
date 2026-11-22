#!/usr/bin/env python3
"""Validate one or more step context Markdown files against this skill's rules.

Usage: python3 validate.py <file> [<file> ...]

Exits 0 only when every file passes; a failing file prints one line per finding
and the process exits 1. Usage errors print to stderr and exit 2. Pass several
files sharing a chunk_id in one invocation so the cross-file check applies.

Why this script does not share the byte-identical JSON-schema validator body
used by sibling format skills: step context files are Markdown, not JSON, so
there is no reference schema to interpret - the checks below parse frontmatter,
headings, and bullets directly. It stays stdlib-only (sys, pathlib) for the
same reason the sibling validators avoid third-party packages: s2h skills are
self-contained bundles that must run wherever python3 exists.

Behavior rules: fail loud, structural over lexical. Every unparseable or
out-of-form input becomes a named finding; checks parse only the forms the
template fixes (flat-scalar frontmatter, headings, <id>: <excerpt> bullets).
They never guess free text, match keywords, or assume requirement id shapes -
ids are arbitrary non-empty strings.

Per-file checks:
1. Frontmatter is flat scalar key-value lines; quoted values are supported.
   Folded or multi-line values, list items, flow collections, and comments
   produce a named FAIL naming the offending key. Required fields kind,
   schema, run_id, step_id, chunk_id, type are non-empty; kind is
   "step-context" and schema is "step-context/v1".
2. Every template heading from the SKILL.md Template block is present,
   including Contract.
3. Every bullet in Contract takes the form <id>: <excerpt> with a non-empty
   id; the file's id set is exactly those bullet ids. Every Requirements
   Covered bullet takes the same form and its id must be a member of that
   set. An empty Requirements Covered bullet list is a named FAIL.

Across files: when two or more files share a chunk_id, their Contract sections
are byte-identical.
"""

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


def die(message):
    print(f"validate: {message}", file=sys.stderr)
    sys.exit(2)


def short(text):
    """Collapse whitespace and truncate a finding snippet to 48 chars."""
    text = " ".join(text.split())
    return text if len(text) <= 48 else text[:45] + "..."


def unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_frontmatter(lines, findings):
    """Parse flat scalar frontmatter lines; append named findings. Returns dict."""
    result = {}
    last_key = None
    for line in lines:
        if not line.strip():
            continue
        if line[:1] in (" ", "\t"):
            where = f" for key '{last_key}'" if last_key else ""
            findings.append(
                "frontmatter has an indented multi-line value" + where
            )
            continue
        colon = line.find(":")
        if colon < 1:
            findings.append(
                "frontmatter line is not a flat scalar key-value line: "
                f"{short(line)}"
            )
            continue
        key = line[:colon]
        rest = line[colon + 1:]
        if (
            key != key.strip()
            or " " in key
            or "\t" in key
            or rest and not rest.startswith((" ", "\t"))
        ):
            findings.append(
                "frontmatter line is not a flat scalar key-value line: "
                f"{short(line)}"
            )
            continue
        value = rest.strip()
        last_key = key
        if value.startswith((">", "|")):
            findings.append(
                f"frontmatter value for key '{key}' is a folded or "
                "multi-line scalar"
            )
        elif value.startswith(("[", "{")):
            findings.append(
                f"frontmatter value for key '{key}' is a list or flow collection"
            )
        elif " #" in value:
            findings.append(
                f"frontmatter value for key '{key}' contains a comment"
            )
        else:
            result[key] = unquote(value)
    return result


def split_document(text, findings):
    """Return (frontmatter dict or None, body lines)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        findings.append("missing frontmatter at file start")
        return None, lines
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return parse_frontmatter(lines[1:index], findings), lines[index + 1:]
    findings.append("unterminated frontmatter block")
    return None, lines


def sections(body):
    """Map each H2 heading to its verbatim body text (outer blanks trimmed)."""
    found = {}
    current = None
    buffer = []
    for line in body:
        if line.startswith("## "):
            if current is not None:
                found[current] = trim(buffer)
            current = line[3:].strip()
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


def bullet_remainders(section_text):
    """Return the text after each template '- ' bullet marker, in order."""
    remainders = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            remainders.append(stripped[2:].strip())
    return remainders


def check_file(path):
    """Return (findings, info) for one file; info holds chunk_id and contract."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read file: {exc}"], {}
    findings = []
    frontmatter, body = split_document(text, findings)
    info = {}
    if frontmatter is None:
        pass
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
        info["chunk_id"] = frontmatter.get("chunk_id", "")
    headings = sections(body)
    for heading in REQUIRED_HEADINGS:
        if heading not in headings:
            findings.append(f"missing heading: {heading}")
    contract = headings.get("Contract", "")
    ids = set()
    for remainder in bullet_remainders(contract):
        if ":" not in remainder:
            findings.append(
                f"Contract bullet '{short(remainder)}' does not match the "
                "<id>: <excerpt> form"
            )
            continue
        req_id = remainder.split(":", 1)[0].strip()
        if not req_id:
            findings.append("Contract bullet has an empty id")
        else:
            ids.add(req_id)
    covered = []
    for remainder in bullet_remainders(headings.get("Requirements Covered", "")):
        if ":" not in remainder:
            findings.append(
                f"Requirements Covered bullet '{short(remainder)}' does not "
                "match the <id>: <excerpt> form"
            )
            continue
        req_id = remainder.split(":", 1)[0].strip()
        if not req_id:
            findings.append("Requirements Covered bullet has an empty id")
        else:
            covered.append(req_id)
    if not bullet_remainders(headings.get("Requirements Covered", "")):
        findings.append("Requirements Covered has no requirement entries")
    for req_id in covered:
        if req_id not in ids:
            findings.append(
                f"Requirements Covered bullet id '{req_id}' is not a member "
                "of its own Contract id set"
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
            for line in findings:
                print(f"FAIL {name}: {line}")
            failures += 1
        else:
            print(f"PASS {name}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
