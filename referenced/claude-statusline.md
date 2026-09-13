# claude-statusline

**Upstream:** [`locriani/claude-statusline`](https://github.com/locriani/claude-statusline)
**Local checkout:** `~/Developer/claude-statusline`
**Status:** referenced, not installed.

A three-line [Claude Code status line](https://docs.claude.com/en/docs/claude-code/statusline)
for macOS — directory, session, git, model, machine vitals, context and
rate-limit meters — rendered with truecolor, clickable OSC-8 links and Nerd Font
icons.

## Why it is worth having

Claude Code pipes a JSON payload to the `statusLine` command on every render, and
the default line spends it on a path. The payload actually carries the model,
effort level, thinking state, PR review status, 5-hour / 7-day rate-limit usage,
git repo info and per-session diff stats. This surfaces all of it with no network
calls — everything comes from the payload or a shared local snapshot.

## Why it is referenced rather than absorbed

It has its own repo and its own release cadence, which this marketplace does not
vendor (see [`../CLAUDE.md`](../CLAUDE.md)). It is also the least portable thing
on the list: Rust, built from source, macOS-only, and it installs **two binaries
plus a LaunchAgent collector** rather than a skill or a hook.

That last point is worth flagging — it is closer to machine configuration than to
portable Claude behaviour, so `Standard Configs` may be its more natural owner.
It is recorded here because it was approved here; the split is a live question,
not a settled one.

## Install (when enabled)

Requires macOS and a Rust toolchain (`brew install rust`).

```sh
git clone https://github.com/locriani/claude-statusline.git ~/Developer/claude-statusline
cd ~/Developer/claude-statusline
./launchd/install.sh
```

`install.sh` builds in release, installs `claude-statusline` and
`claude-statusline-collector` into `$PREFIX/bin` (default `~/.local/bin`), then
hands off to `claude-statusline-collector setup`, which writes the LaunchAgent
plist, points `~/.claude/statusline` at the render binary, and starts the agent.
Everything runs from the installed copies, so the build tree can be cleaned or
moved afterward. `./launchd/uninstall.sh` reverses all of it.

Nothing above has been run as part of adding this entry.
