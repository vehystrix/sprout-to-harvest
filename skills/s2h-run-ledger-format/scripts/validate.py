#!/usr/bin/env python3
"""Validate one or more JSON files against this skill's reference schema.

Usage: python3 validate.py [KIND] <file> [<file> ...]

When the first argument names a schema variant shipped under
references/schema-<KIND>.json, it is treated as KIND and the remaining
arguments are files; otherwise every argument is a file and the schema is
references/schema.json. Exits 0 only when every file parses as JSON and
conforms to the selected schema.

Why this is stdlib-only instead of using the `jsonschema` module:
1. Zero dependencies. This script ships inside each skill directory and runs
   on whatever host executes verification. Stdlib imports (json, re, sys,
   pathlib) mean it works anywhere python3 exists - no pip install, no
   vendored package. s2h skills are self-contained portable bundles; a
   third-party import would break that.
2. Deliberately narrow scope. The reference schemas only need about ten
   keywords (type, const, enum, properties, required, additionalProperties,
   items, minItems, minLength, minimum, maximum, pattern). A strict-subset
   interpreter is short, fully reviewable, and predictable; full jsonschema
   adds $ref resolution, formats, and unevaluated* handling that invite
   subtle failure modes for no benefit on fixed-shape run artifacts.
3. Byte-identical copies. One validator body is copied verbatim into every
   format skill; a library dependency would make each copy heavier and couple
   the bundle to package availability at verification time.

Documented cost: schema keywords outside the supported set are silently
ignored - unknown keys are inert by design.

The interpreter supports exactly these keywords: type (string | number |
integer | boolean | object | array | null, or a list of them), const, enum,
properties, required, additionalProperties (false or a schema), items,
minItems, minLength, minimum, maximum, and pattern. All other keys in the
schema documents ($schema, $id, title, description, ...) are inert metadata.
"""

import json
import re
import sys
from pathlib import Path


def die(message):
    print(f"validate: {message}", file=sys.stderr)
    sys.exit(2)


def type_ok(value, name):
    checks = {
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "null": value is None,
    }
    if name not in checks:
        die(f"validator bug: unsupported type {name!r}")
    return checks[name]


def check(value, schema, path, errors):
    expected = schema.get("type")
    if expected is not None:
        names = [expected] if isinstance(expected, str) else list(expected)
        if not any(type_ok(value, name) for name in names):
            kinds = " or ".join(names)
            errors.append(f"{path}: expected {kinds}, got {type(value).__name__}")
            return
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        allowed = ", ".join(repr(item) for item in schema["enum"])
        errors.append(f"{path}: {value!r} is not one of [{allowed}]")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(
                f'{path}: does not match pattern {schema["pattern"]!r}'
            )
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: above maximum {schema['maximum']}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(
                f"{path}: fewer than minItems {schema['minItems']}"
            )
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                check(item, item_schema, f"{path}[{index}]", errors)
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")
        additional = schema.get("additionalProperties")
        for key, item in value.items():
            if key in properties:
                check(item, properties[key], f"{path}.{key}", errors)
            elif additional is False:
                errors.append(f'{path}: unexpected property {key!r}')
            elif isinstance(additional, dict):
                check(item, additional, f"{path}.{key}", errors)


def main(argv):
    base = Path(__file__).resolve().parents[1] / "references"
    args = list(argv)
    if (
        args
        and re.fullmatch(r"[a-z][a-z0-9-]*", args[0])
        and (base / f"schema-{args[0]}.json").is_file()
    ):
        kind = args.pop(0)
    else:
        kind = None
    schema_name = f"schema-{kind}.json" if kind else "schema.json"
    schema_path = base / schema_name
    if not schema_path.is_file():
        die(f"missing schema {schema_path}")
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read schema: {exc}")
    if not args:
        die("no input files given")

    failures = 0
    for name in args:
        try:
            with open(name, encoding="utf-8") as handle:
                document = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL {name}: {exc}")
            failures += 1
            continue
        errors = []
        check(document, schema, "$", errors)
        if errors:
            for line in errors[:20]:
                print(f"FAIL {name}: {line}")
            failures += 1
        else:
            print(f"PASS {name} (schema: {schema_name})")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
