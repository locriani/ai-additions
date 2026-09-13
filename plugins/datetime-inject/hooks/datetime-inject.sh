#!/usr/bin/env bash
# UserPromptSubmit hook — inject the current LOCAL date+time into context, once per turn.
#
# Emits exactly one bracketed line to stdout (human long-form | ISO machine-form); Claude Code
# appends it to the conversation as context. Example:
#   [Current TimeStamp: Tuesday, June 2nd, 2026 | 2026-06-02 14:33:07 PDT (UTC-07:00)]
#
# Mutation surface: NONE — reads the clock, writes one line to stdout, touches nothing else.
# Ignores its stdin (the UserPromptSubmit JSON payload); it needs no input.
# Deliberately NO `set -e`: a non-zero exit from a UserPromptSubmit hook can block the user's
# prompt submission, so this script always exits 0 even if something below misbehaves.

# Single date(1) snapshot so every field refers to the same instant (no cross-call second-skew).
read -r wday month dd yyyy iso clock tz off <<<"$(date '+%A %B %d %Y %F %H:%M:%S %Z %z')"

day=$((10#$dd))                       # "02" -> 2  (10# forces base-10; avoids octal parse of 08/09)
case $day in
  11|12|13) ord=th ;;                 # 11th/12th/13th are always "th"
  *) case $((day % 10)) in 1) ord=st ;; 2) ord=nd ;; 3) ord=rd ;; *) ord=th ;; esac ;;
esac

printf '[Current TimeStamp: %s, %s %d%s, %s | %s %s %s (UTC%s:%s)]\n' \
  "$wday" "$month" "$day" "$ord" "$yyyy" "$iso" "$clock" "$tz" "${off:0:3}" "${off:3:2}"

exit 0
