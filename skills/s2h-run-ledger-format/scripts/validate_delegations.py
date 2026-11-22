#!/usr/bin/env python3
"""Validate a delegations.jsonl file: one JSON object per appended line.

Usage: python3 validate_delegations.py <file> [<file> ...]

Exits 0 only when every line of every named file parses as a flat JSON
object with exactly the six fields defined by this skill's SKILL.md and no
out-of-form value; each failing line is reported once per finding, naming
the line number. Stdlib-only (json, sys).

Why this script stands alone instead of extending validate.py: the shared
schema interpreter validates whole documents against a schema file under
references/; delegations.jsonl has no such file - it is an append-only
stream of single-line records checked structurally, one JSON parse plus
field presence and type per line. A per-line stdlib check suffices for that
shape, so the byte-identical validator body stays untouched.

Documented cost: a blank line anywhere in the stream is a named FAIL, not a
skip - an append-only record should never contain one, and a stray blank
line means a partial write. The file need not end with a trailing newline;
a final line without one still validates.
"""

import json
import sys

FIELDS = {
    "id": str,
    "role": str,
    "requested_portable_id": (str, type(None)),
    "resolved_model": str,
    "selection_source": str,
    "fallback": (str, type(None)),
}

NONEMPTY = {"id", "role", "resolved_model", "selection_source"}


def describe(allowed):
    if isinstance(allowed, tuple):
        return "a string or null"
    return "a string"


def type_ok(value, allowed):
    if isinstance(allowed, tuple):
        return isinstance(value, allowed)
    return isinstance(value, allowed) and not isinstance(value, bool)


def check_line(raw):
    """Return a list of findings for one record; empty when the line passes."""
    try:
        record = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [f"not valid JSON ({exc})"]
    if not isinstance(record, dict):
        kind = type(record).__name__
        return [f"expected a flat JSON object, got {kind}"]
    findings = []
    for key in sorted(set(FIELDS) - set(record)):
        findings.append(f"missing field {key!r}")
    for key in sorted(set(record) - set(FIELDS)):
        findings.append(f"unexpected field {key!r}")
    for key, allowed in FIELDS.items():
        if key not in record:
            continue
        value = record[key]
        if not type_ok(value, allowed):
            findings.append(
                f"field {key!r} must be {describe(allowed)}, "
                f"got {type(value).__name__}"
            )
        elif key in NONEMPTY and isinstance(value, str) and value == "":
            findings.append(f"field {key!r} must be a non-empty string")
    return findings


def main(argv):
    if not argv:
        print("validate_delegations: no input files given", file=sys.stderr)
        sys.exit(2)
    failures = 0
    for name in argv:
        try:
            with open(name, encoding="utf-8") as handle:
                lines = handle.read().splitlines()
        except OSError as exc:
            print(f"FAIL {name}: cannot read ({exc})")
            failures += 1
            continue
        bad = 0
        for number, raw in enumerate(lines, start=1):
            if raw == "":
                findings = ["blank line; the stream appends one record per line"]
            else:
                findings = check_line(raw)
            for finding in findings:
                print(f"FAIL {name}:{number}: {finding}")
                bad += 1
        if bad:
            failures += 1
        else:
            print(f"PASS {name} ({len(lines)} line(s))")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
