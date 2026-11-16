#!/usr/bin/env python3
"""Validate one or more documentation context Markdown files against this
skill's rules.

Usage: python3 validate.py <file> [<file> ...]

Exits 0 only when every file passes; a failing file prints one line per finding
and the process exits 1. Usage errors print to stderr and exit 2.

Why this script does not share the byte-identical JSON-schema validator body
used by sibling format skills: documentation context files are Markdown, not
JSON, so there is no reference schema to interpret - the checks below parse
frontmatter and template headings directly. It stays stdlib-only (re, sys,
pathlib) for the same reason the sibling validators avoid third-party packages:
s2h skills are self-contained bundles that must run wherever python3 exists.

The SKILL.md Validation section also requires "no claim supported only by the
plan when implementation evidence is available". That rule compares file content
against repository state and cannot be checked statically, so it is enforced by
s2h-DocumentationVerifier instead of this script.

Per-file checks:
1. YAML frontmatter present at file start with non-empty values for kind,
   schema, run_id, context_type; kind is "documentation-context", schema is
   "documentation-context/v1", and context_type is source or user.
2. The H1 title matches the template for that context_type.
3. Every H2 template heading required by that context_type is present.
4. Requirements has at least one requirement entry (a list line naming a
   requirement ID) or an explicit no-obligation statement containing
   "no documentation obligation".
"""

import re
import sys
from pathlib import Path

FRONTMATTER_FIELDS = ("kind", "schema", "run_id", "context_type")

CONST_FIELDS = {
    "kind": "documentation-context",
    "schema": "documentation-context/v1",
}

CONTEXT_TYPES = ("source", "user")

TITLES = {
    "source": "# Source Documentation Context",
    "user": "# User Documentation Context",
}

REQUIRED_HEADINGS = {
    "source": (
        "Purpose",
        "Audiences",
        "Requirements",
        "Topics",
        "Interfaces and Constraints",
        "Risks and Questions",
        "Expected Evidence",
    ),
    "user": (
        "Purpose",
        "Audiences",
        "Requirements",
        "Workflows",
        "Prerequisites and Configuration",
        "Examples and Expected Results",
        "Limitations and Recovery",
        "Risks and Questions",
        "Expected Evidence",
    ),
}

ID_RE = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")
LIST_ENTRY_RE = re.compile(r"^\s*[-*]\s+\S")
HEADING_RE = re.compile(r"##\s+(.+?)\s*$")
TITLE_RE = re.compile(r"^#\s+(.+)$")


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
    """Return the list of findings for one file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read file: {exc}"]
    findings = []
    frontmatter, body = split_document(text)
    if frontmatter is None:
        findings.append("missing or unterminated YAML frontmatter at file start")
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
    context_type = (frontmatter or {}).get("context_type", "")
    if context_type not in CONTEXT_TYPES:
        findings.append(
            "frontmatter context_type must be one of: source, user"
            + f" (got {context_type!r})"
        )
        return findings
    title = None
    for line in body:
        match = TITLE_RE.match(line)
        if match:
            title = match.group(0)
            break
    if title is None:
        findings.append(f"missing H1 title: {TITLES[context_type]}")
    elif title != TITLES[context_type]:
        findings.append(f"H1 title must be {TITLES[context_type]!r}, got {title!r}")
    headings = sections(body)
    for heading in REQUIRED_HEADINGS[context_type]:
        if heading not in headings:
            findings.append(f"missing heading: {heading}")
    requirements = headings.get("Requirements", "")
    has_entry = any(
        LIST_ENTRY_RE.match(line) and ID_RE.search(line)
        for line in requirements.splitlines()
    )
    disclaimed = "no documentation obligation" in requirements.lower()
    if not (has_entry or disclaimed):
        findings.append(
            "Requirements has no requirement entry and no explicit "
            'no-obligation statement ("no documentation obligation")'
        )
    return findings


def main(argv):
    if not argv:
        die("no input files given")
    failures = 0
    for name in argv:
        findings = check_file(Path(name))
        if findings:
            for line in findings[:20]:
                print(f"FAIL {name}: {line}")
            failures += 1
        else:
            print(f"PASS {name}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
