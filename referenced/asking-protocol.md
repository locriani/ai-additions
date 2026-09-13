# asking-protocol

**Upstream:** [`locriani/asking-protocol`](https://github.com/locriani/asking-protocol) (private)
**Local checkout:** `~/Developer/asking-protocol`
**Status:** referenced, not installed. **MCP to be left disabled** when it is.

Governs when Claude asks anything, how the question is rendered, and where the
answer is kept. Four parts:

| Part | What it does |
|---|---|
| `ask-question-ban.py` (PreToolUse) | Denies every `AskUserQuestion` call. |
| `ask-record-gate.py` (Stop) | Blocks turn-end on an ask that was never recorded. |
| `asking` MCP | `ask_open` / `ask_close` — renders the block and stores it in one act. |
| `asking` skill | The rule itself. |

## Why

`AskUserQuestion` renders a card grid. The grid hides the question's logic — you
pick a label instead of checking what was actually asked — and having several
cards available invites bundling unrelated concerns into one turn.

Replacing it with plain text fixes the rendering but not the record. An ask that
lives only in the transcript cannot be re-asked when it goes unanswered, cannot
be shown as blocking anything, and drifts from whatever Claude later claims was
decided. So the question is rendered and stored in the same call, and the Stop
hook is what makes that hold.

## Note for whoever enables this

`Standard Configs/claude-plugins/ask-question-ban/` is an **older fork** of the
first hook. Upstream is ahead in four ways: it honours `CLAUDE_CONFIG_DIR` (the
fork hardcodes `~/.claude`, which breaks under `claude-as` profiles), logs to
`~/.claude/asking/`, points its deny reason at `ask_open`, and ships the Stop
gate the fork has no equivalent of.

Enabling both would put two PreToolUse denies on the same tool. The fork should
go when this is turned on.

## Install (when enabled)

```sh
claude plugin marketplace add locriani/asking-protocol   # private; needs an SSH key
claude plugin install asking-protocol@asking-protocol
```

Nothing above has been run.
