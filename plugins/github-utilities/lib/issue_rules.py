"""The two rules for GitHub issue text, per `rules/GITHUB.md`.

1. An issue never cites another issue in prose. It links it with a native relationship: parent,
   sub-issue, blocked-by, blocking.
2. The body is a filled issue template, and each field's type sets its cap. Walls of text do not fit.

Stated as values, never raised: every check returns a list of problems, empty when the text passes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

NO_RESPONSE = "_No response_"
TITLE_MAX = 72
INPUT_MAX = 100
TEXTAREA_LINES, TEXTAREA_WIDTH = 6, 160
RENDER_LINES = 20

LINK_INSTEAD = (
    "link it instead: --parent / --blocked-by / --blocking on create, or "
    "gh issue edit --add-sub-issue / --add-blocked-by / --add-blocking"
)

# Longest forms first: a match inside an earlier match's span is the same reference.
REFERENCES = [
    re.compile(r"https?://(?:www\.)?github\.com/[^\s/]+/[^\s/]+/(?:issues|pull)/\d+", re.I),
    re.compile(r"https?://\S+?/-/(?:issues|merge_requests|work_items)/\d+", re.I),
    re.compile(r"\b[\w.-]+/[\w.-]+#\d+\b"),
    re.compile(r"\b(?:issues?|tickets?|PRs?|pull requests?|MRs?|merge requests?)\s+[#!]?\d+\b", re.I),
    re.compile(r"\bGH-\d+\b", re.I),
    re.compile(r"(?<![\w&/#])#\d+\b"),
]

FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
HEADING = re.compile(r"^### (.+?)\s*$")


@dataclass(frozen=True)
class Field:
    id: str
    label: str
    kind: str
    required: bool = False
    options: tuple[str, ...] = ()
    render: str | None = None


@dataclass(frozen=True)
class Template:
    file: str
    name: str
    labels: tuple[str, ...]
    fields: tuple[Field, ...]

    @property
    def key(self) -> str:
        return self.file.rsplit(".", 1)[0]

    @property
    def headings(self) -> list[str]:
        return [f.label for f in self.fields]


def parse_template(file: str, text: str) -> Template:
    """One `.github/ISSUE_TEMPLATE/*.yml` issue form. `markdown` blocks are page text, not fields."""
    import yaml  # the CLI carries PyYAML; nothing else in this module needs it

    doc = yaml.safe_load(text) or {}
    labels = doc.get("labels") or ()
    if isinstance(labels, str):
        labels = [s.strip() for s in labels.split(",") if s.strip()]
    fields = []
    for item in doc.get("body") or ():
        kind = item.get("type", "")
        if kind == "markdown":
            continue
        attrs = item.get("attributes") or {}
        options = tuple(o["label"] if isinstance(o, dict) else str(o) for o in attrs.get("options") or ())
        fields.append(
            Field(
                id=str(item.get("id") or attrs.get("label", "")),
                label=str(attrs.get("label", "")),
                kind=kind,
                required=bool((item.get("validations") or {}).get("required")),
                options=options,
                render=attrs.get("render"),
            )
        )
    return Template(file=file, name=str(doc.get("name", file)), labels=tuple(labels), fields=tuple(fields))


def cap(field: Field) -> str:
    if field.kind == "input":
        return f"1 line, {INPUT_MAX} chars"
    if field.kind == "textarea" and field.render:
        return f"{RENDER_LINES} lines"
    if field.kind == "textarea":
        return f"{TEXTAREA_LINES} lines, {TEXTAREA_WIDTH} chars each"
    if field.kind == "dropdown":
        return "one of " + ", ".join(field.options)
    return field.kind


def render(template: Template, values: dict[str, str]) -> str:
    """The body GitHub writes when the form is submitted on the web: `### Label`, blank line, value."""
    parts = []
    for f in template.fields:
        value = (values.get(f.id) or "").strip()
        if not value:
            value = NO_RESPONSE
        elif f.render:
            value = f"```{f.render}\n{value}\n```"
        parts.append(f"### {f.label}\n\n{value}")
    return "\n\n".join(parts)


# --- references ------------------------------------------------------------------------------


def _prose(text: str) -> str:
    """Text with fenced blocks and inline code removed: code is evidence, not a citation."""
    out, fenced = [], False
    for line in text.split("\n"):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            out.append(INLINE_CODE.sub("", line))
    return "\n".join(out)


def references(text: str) -> list[str]:
    prose, taken, found = _prose(text), [], []
    for pattern in REFERENCES:
        for m in pattern.finditer(prose):
            if any(s <= m.start() and m.end() <= e for s, e in taken):
                continue
            taken.append(m.span())
            if m.group(0) not in found:
                found.append(m.group(0))
    return found


def _reference_problems(text: str) -> list[str]:
    return [f'"{ref}" cites an issue in text; {LINK_INSTEAD}' for ref in references(text)]


# --- caps ------------------------------------------------------------------------------------


def _lines_problem(what: str, lines: list[str], max_lines: int, width: int | None) -> str | None:
    lines = [ln for ln in lines if ln.strip()]
    rule = f"{what}: {max_lines} lines" + (f", {width} chars each" if width else "")
    if len(lines) > max_lines:
        return f"{rule} (got {len(lines)} lines)"
    for n, ln in enumerate(lines, 1):
        if width and len(ln) > width:
            return f"{rule} (line {n} is {len(ln)} chars)"
    return None


def _unfence(value: str) -> str:
    lines = value.split("\n")
    if len(lines) >= 2 and FENCE.match(lines[0]) and FENCE.match(lines[-1]):
        return "\n".join(lines[1:-1])
    return value


def _field_problem(f: Field, value: str) -> str | None:
    if value in ("", NO_RESPONSE):
        return f"{f.label} is required" if f.required else None
    if f.kind == "input":
        lines = value.split("\n")
        if len(lines) > 1:
            return f"{f.label}: {cap(f)} (got {len(lines)} lines)"
        if len(value) > INPUT_MAX:
            return f"{f.label}: {cap(f)} (got {len(value)} chars)"
    elif f.kind == "textarea" and f.render:
        return _lines_problem(f.label, _unfence(value).split("\n"), RENDER_LINES, None)
    elif f.kind == "textarea":
        return _lines_problem(f.label, value.split("\n"), TEXTAREA_LINES, TEXTAREA_WIDTH)
    elif f.kind == "dropdown" and f.options:
        chosen = [v.strip() for v in value.split(",")]
        if any(v not in f.options for v in chosen):
            return f"{f.label}: {cap(f)} (got {value})"
    return None


# --- the checks ------------------------------------------------------------------------------


def sections(body: str) -> tuple[list[tuple[str, str]], bool]:
    """(heading, value) pairs, and whether any text came before the first heading."""
    out: list[tuple[str, list[str]]] = []
    preamble, fenced = False, False
    for line in body.replace("\r\n", "\n").split("\n"):
        if FENCE.match(line):
            fenced = not fenced
        m = None if fenced else HEADING.match(line)
        if m:
            out.append((m.group(1), []))
        elif out:
            out[-1][1].append(line)
        elif line.strip():
            preamble = True
    return [(h, "\n".join(v).strip("\n")) for h, v in out], preamble


def check_body(body: str, templates) -> list[str]:
    found, preamble = sections(body)
    headings = [h for h, _ in found]
    match = next((t for t in templates if t.headings == headings), None) if not preamble else None
    if match is None:
        shapes = "; ".join(f"{t.name}: {', '.join(t.headings)}" for t in templates)
        return [f"body matches no template; its sections must be exactly, in order — {shapes}"]
    problems = [p for f, (_, v) in zip(match.fields, found) if (p := _field_problem(f, v))]
    return problems + _reference_problems(body)


def check_title(title: str) -> list[str]:
    title = title.strip()
    if not title:
        return ["title is empty"]
    problems = []
    if len(title) > TITLE_MAX:
        problems.append(f"title: {TITLE_MAX} chars at most (got {len(title)})")
    return problems + _reference_problems(title)


def check_comment(body: str) -> list[str]:
    problems = []
    prose = _lines_problem("comment", _prose(body).split("\n"), TEXTAREA_LINES, TEXTAREA_WIDTH)
    if prose:
        problems.append(prose)
    block, fenced = 0, False
    for line in body.split("\n"):
        if FENCE.match(line):
            if fenced and block > RENDER_LINES:
                problems.append(f"comment: code blocks {RENDER_LINES} lines at most (got {block})")
            fenced, block = not fenced, 0
        elif fenced:
            block += 1
    return problems + _reference_problems(body)
