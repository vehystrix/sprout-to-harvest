#!/usr/bin/env python3
"""Validate one or more documentation context Markdown files against this skill's rules.

Usage: python3 validate.py <file> [<file> ...]

Exits 0 only when every file passes; a failing file prints one line per finding
and the process exits 1. Usage errors print to stderr and exit 2.

Why this script does not share the byte-identical JSON-schema validator body
used by sibling format skills: documentation context files are Markdown, not
JSON, so there is no reference schema to interpret - the checks below parse
frontmatter, headings, and bullets directly. It stays stdlib-only (sys,
pathlib) for the same reason the sibling validators avoid third-party
packages: s2h skills are self-contained bundles that must run wherever python3
exists.

Behavior rules: fail loud, structural over lexical. Every unparseable or
out-of-form input becomes a named finding; checks parse only the forms the
template fixes (flat-scalar frontmatter, headings, bullets). They never guess
free text, match keywords, or assume id shapes - ids are arbitrary non-empty
strings.

Per-file checks:
1. Frontmatter is flat scalar key-value lines; quoted values are supported.
   Folded or multi-line values, list items, flow collections, and comments
   produce a named FAIL naming the offending key. Required fields kind,
   schema, run_id, context_type are non-empty; kind is
   "documentation-context" and schema is "documentation-context/v1";
   context_type is source or user.
2. The H1 title must equal the fixed title for that context type, and every
   template heading for that type from the SKILL.md Template block is
   present.
3. The Requirements section MUST contain at least one bullet with a
   non-empty description; prose alone (even id-bearing prose) is not enough.

The content rule about plan-only claims is checked by s2h-DocumentationVerifier,
not this script.
"""

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

SOURCE_HEADINGS = (
    "Purpose",
    "Audiences",
    "Requirements",
    "Topics",
    "Interfaces and Constraints",
    "Risks and Questions",
    "Expected Evidence",
)

USER_HEADINGS = (
    "Purpose",
    "Audiences",
    "Requirements",
    "Workflows",
    "Prerequisites and Configuration",
    "Examples and Expected Results",
    "Limitations and Recovery",
    "Risks and Questions",
    "Expected Evidence",
)


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
    """Return the findings list for one file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read file: {exc}"]
    findings = []
    frontmatter, body = split_document(text, findings)
    if frontmatter is None:
        return findings
    for field in FRONTMATTER_FIELDS:
        if not frontmatter.get(field):
            findings.append(f"frontmatter field missing or empty: {field}")
    for field, expected in CONST_FIELDS.items():
        value = frontmatter.get(field)
        if value and value != expected:
            findings.append(
                f'frontmatter {field} must be "{expected}", got "{value}"'
            )
    context_type = frontmatter.get("context_type", "")
    if context_type not in CONTEXT_TYPES:
        findings.append(
            "frontmatter context_type must be one of: source, user "
            f"(got '{context_type}')"
        )
        return findings
    title = None
    for line in body:
        if line.startswith("# "):
            title = line.strip()
            break
    expected_title = TITLES[context_type]
    if title is None:
        findings.append(f"missing H1 title: {expected_title}")
    elif title != expected_title:
        findings.append(f"H1 title must be '{expected_title}', got '{title}'")
    headings = sections(body)
    for heading in SOURCE_HEADINGS if context_type == "source" else USER_HEADINGS:
        if heading not in headings:
            findings.append(f"missing heading: {heading}")
    requirements = headings.get("Requirements", "")
    remainders = bullet_remainders(requirements)
    if not remainders:
        findings.append("Requirements has no bullet entries")
    for remainder in remainders:
        description = (
            remainder.split(":", 1)[1].strip() if ":" in remainder else remainder
        )
        if not description:
            head = remainder.split(":", 1)[0].strip() or "<no colon>"
            findings.append(
                f"Requirements bullet '{head}' has an empty description"
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
