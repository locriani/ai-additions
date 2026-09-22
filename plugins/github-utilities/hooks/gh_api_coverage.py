"""Which `gh api` calls a `gh` subcommand already covers, and which ones write issue text.

Zach, 2026-09-22 14:50: allow `gh api` for features that are not in the CLI yet. So `gh api` is the
surface wherever `gh` has no subcommand, and a violation only where one exists — `COVERED` is that
line, and the one place to edit when `gh` grows a subcommand.

Allowing `gh api` must not become the way around GITHUB.md's issue rules, so `issue_text_write`
names the calls that would write an issue's title, body, or a comment without `gh-issue check`.

Standard library only: both hooks import this, and the PreToolUse one runs on every Bash call.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field

OPERATORS = set("();<>|&\n")
ASSIGNMENT = re.compile(r"^[A-Za-z_]\w*=")

_REPO = r"repos/[^/]+/[^/]+"
COVERED: list[tuple[re.Pattern, str]] = [
    (re.compile(rf"^{_REPO}/issues(?:/|$)"), "gh issue"),
    (re.compile(rf"^{_REPO}/pulls(?:/|$)"), "gh pr"),
    (re.compile(rf"^{_REPO}/actions/runs(?:/|$)"), "gh run"),
    (re.compile(rf"^{_REPO}/actions/workflows(?:/|$)"), "gh workflow"),
    (re.compile(rf"^{_REPO}/actions/secrets(?:/|$)"), "gh secret"),
    (re.compile(rf"^{_REPO}/actions/variables(?:/|$)"), "gh variable"),
    (re.compile(rf"^{_REPO}/releases(?:/|$)"), "gh release"),
    (re.compile(rf"^{_REPO}/labels(?:/|$)"), "gh label"),
    (re.compile(rf"^{_REPO}/forks$"), "gh repo fork"),
    (re.compile(rf"^{_REPO}$"), "gh repo view"),
    (re.compile(r"^search/(?:issues|repositories|code|commits)$"), "gh search"),
    (re.compile(r"^gists(?:/|$)"), "gh gist"),
]

# `gh api` flags that take a value; the endpoint is the first argument that is none of these.
VALUE_FLAGS = {"-X", "--method", "-H", "--header", "-f", "--raw-field", "-F", "--field", "--input",
               "-q", "--jq", "-t", "--template", "-p", "--preview", "--hostname", "--cache"}
FIELD_FLAGS = {"-f", "--raw-field", "-F", "--field"}

ISSUE_TEXT_MUTATIONS = re.compile(r"\b(?:createIssue|updateIssue|addComment|updateIssueComment)\b")
TEXT_FIELDS = {"title", "body"}


@dataclass(frozen=True)
class ApiCall:
    endpoint: str
    method: str
    fields: dict = field(default_factory=dict)
    has_input: bool = False

    @property
    def query(self) -> str:
        return str(self.fields.get("query", ""))


def segments(command: str) -> list[list[str]]:
    """Simple commands, split at shell operators and newlines. Raises ValueError when unparseable."""
    lex = shlex.shlex(command, posix=True, punctuation_chars="();<>|&\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    out, current = [], []
    for token in lex:
        if token and set(token) <= OPERATORS:
            if "<<" in token:
                current.append("<<")  # a heredoc: the text arrives on stdin
            out.append(current)
            current = []
        else:
            current.append(token)
    out.append(current)
    return [s for s in out if s]


def strip_assignments(words: list[str]) -> list[str]:
    while words and ASSIGNMENT.match(words[0]):
        words = words[1:]
    return words


def normalize(endpoint: str) -> str:
    endpoint = re.sub(r"^https?://[^/]+/", "", endpoint)
    return endpoint.split("?", 1)[0].strip("/")


def parse(args: list[str]) -> ApiCall:
    """The arguments after `gh api`. No method given and any field or --input present means POST, as in gh."""
    endpoint, method, fields, has_input = "", "", {}, False
    i = 0
    while i < len(args):
        arg = args[i]
        flag, eq, inline = arg.partition("=") if arg.startswith("--") else (arg, "", "")
        if flag in VALUE_FLAGS:
            value = inline if eq else (args[i + 1] if i + 1 < len(args) else "")
            i += 0 if eq else 1
            if flag in ("-X", "--method"):
                method = value.upper()
            elif flag in FIELD_FLAGS:
                key, _, val = value.partition("=")
                fields[key] = val
            elif flag == "--input":
                has_input = True
        elif not arg.startswith("-") and not endpoint:
            endpoint = arg
        i += 1
    if not method:
        method = "POST" if fields or has_input else "GET"
    return ApiCall(endpoint=normalize(endpoint), method=method, fields=fields, has_input=has_input)


def api_calls(command: str) -> list[ApiCall]:
    """Every `gh api` call in a Bash command. Raises ValueError when the command does not parse."""
    out = []
    for words in segments(command):
        words = strip_assignments(words)
        if words[:2] == ["gh", "api"]:
            out.append(parse(words[2:]))
    return out


def covered(endpoint: str) -> str | None:
    """The `gh` subcommand that already reaches this endpoint, or None when `gh api` is the only way."""
    endpoint = normalize(endpoint)
    return next((sub for pattern, sub in COVERED if pattern.search(endpoint)), None)


def issue_text_write(call: ApiCall) -> str | None:
    """Why this call writes issue text past `gh-issue check`, or None."""
    ep, method = call.endpoint, call.method
    if ep == "graphql":
        m = ISSUE_TEXT_MUTATIONS.search(call.query)
        return f"GraphQL {m.group(0)} writes issue text" if m else None
    if re.fullmatch(rf"{_REPO}/issues", ep) and method == "POST":
        return "POST .../issues creates an issue"
    if re.fullmatch(rf"{_REPO}/issues/\d+", ep) and method == "PATCH":
        if call.has_input or TEXT_FIELDS & set(call.fields):
            return "PATCH .../issues/N edits an issue's title or body"
    if re.fullmatch(rf"{_REPO}/issues/\d+/comments", ep) and method == "POST":
        return "POST .../issues/N/comments adds a comment"
    if re.fullmatch(rf"{_REPO}/issues/comments/\d+", ep) and method == "PATCH":
        return "PATCH .../issues/comments/N edits a comment"
    return None
