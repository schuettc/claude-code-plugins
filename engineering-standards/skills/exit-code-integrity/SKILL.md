---
name: exit-code-integrity
description: Use when running any check, test, build, lint, or deploy from a shell — especially when piping its output through tail/head/grep, or wrapping it in a compound command to keep the output short. The rule — a pipeline reports the LAST command's exit code, so `check | tail` turns a failing check into a passing one. Never read a check's result through another command.
---

# Exit-code integrity

## The rule

**Never pipe a check into another command and then read the result.**

```bash
just verify | tail -5 && echo "OK"      # ← reports tail's exit code. Always 0.
go test ./... | grep -v "^ok"           # ← reports grep's. Inverted, too.
npm run build 2>&1 | head -20           # ← reports head's.
```

A pipeline's exit status is the status of its **last** command. `tail` succeeds
at tailing a failure. `head` succeeds at heading a stack trace. The check ran,
it failed, and the shell told you it passed.

## Why this one is worth a skill

It is not that the mistake is subtle. It is that the mistake is **invisible and
convincing**: you get clean-looking output and a zero status, and then you tell a
human the check passed. A laundered exit code does not just hide a bug — it
converts into a false statement you make to someone who is relying on you.

Four times in one codebase, by the same hands that had already written the rule
down:

- A `staticcheck` finding masked by `| tail -1`.
- A `govulncheck` failure on a dependency, masked the same way.
- Again while verifying the very tool built to report coverage honestly.
- `just build 2>&1 | tail -5 && echo "=== BUILD OK ==="` — printed BUILD OK over
  a wasm build that had died with `error obtaining VCS status: exit status 128`.
  The failure text was **in the printed output**, three lines above the word OK.

That last one is the tell. The evidence was on screen and the conclusion still
came from the exit code. Reading output is not checking status.

## The forms it takes

| Construct | What you read | What you wanted |
| --- | --- | --- |
| `cmd \| tail` / `\| head` / `\| less` | the pager's status | `cmd`'s |
| `cmd \| tee log` | `tee`'s status | `cmd`'s |
| `cmd \| grep FAIL` | **inverted** — `grep` exits 1 when it finds nothing, so a clean run "fails" | `cmd`'s |
| `[ -n "$(cmd)" ]` | whether output was non-empty | `cmd`'s |
| `cmd1 \| cmd2 && deploy` | `cmd2`'s | both |

`set -o pipefail` fixes pipelines, and is **off by default** in every
non-interactive `sh`/`bash` invocation you did not write yourself. Do not rely
on it being set; rely on not needing it.

## How to apply

**Let the check exit on its own, then filter the file.** Capture the status
immediately — the next command overwrites `$?`.

```bash
just verify > /tmp/verify.log 2>&1; rc=$?
tail -20 /tmp/verify.log
echo "rc=$rc"
```

Now the output is for reading and `rc` is for deciding, and they cannot be
confused. If a step must gate another, chain on the command itself
(`cmd && next`) with nothing between them.

**When output volume is the problem, solve it at the far end.** The reason
people reach for `| tail` is a wall of text. Redirect to a file and tail the
file — same brevity, real status.

**Red flags in your own drafts.** If a command you are about to run contains
`| tail`, `| head`, `| grep`, or `2>&1 |` and its result will become a claim
about whether something passed, stop and rewrite it. If you already ran it, run
it again properly before reporting.

**Never report a green from a laundered status.** If you catch it after the
fact, say so plainly and re-run — a correction costs a sentence; an
unverified "it passes" costs whatever gets built on it.
