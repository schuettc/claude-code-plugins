---
name: testing-interactions-over-time
description: Use when writing or reviewing tests for a UI, a live-updating view, or anything with a second actor — a poll, a websocket, a background job, another user, an agent. The rule — most real defects are interactions across TIME (something arrives while you are typing; an element grows after it was measured), and a test that sets a state and asserts it cannot see any of them.
---

# Test interactions over time, not states

## The rule

**A test that sets up a state and asserts that state can only find bugs that are
already visible in a screenshot.** The defects users actually hit live in the
gap between two moments: something arrived while they were typing, something
grew after it was measured, two actors touched the same thing at once.

To find those, a test must **hold something across a change** — capture it,
cause the event, then re-read the same thing — rather than arrange a world and
describe it.

## The evidence

A markdown editor with a full browser test suite. The first time a human used it
for real work, ten defects surfaced in minutes. **None had been found by any
test**, and every one was an interaction over time:

- **The reply box cleared while being typed into.** A background poll rebuilt
  every card on refresh, destroying a half-written sentence with its card. Worse
  when the agent was live, because the agent's own reply triggered the repaint —
  answering a reviewer actively destroyed what they were writing back.
- **Cards drew on top of each other.** The stack was computed from each card's
  *measured* height; a card that grew afterwards — a textarea dragged taller, a
  new message arriving — left every position below it stale.
- **The agent's writes woke the agent.** Every mutation reached the notifier,
  including the server's own.

The suite had many tests. They set a state and asserted it. The one check that
had ever caught this class was a caret probe — the only one that held a position
**across** a change.

A later regression makes the same point from the other side: a layout fix was
verified with "does it overflow?" and "does the count stay on one line?" — both
green — while the actual failure was two elements occupying the same pixels. The
question that would have caught it was never asked.

## Why state tests structurally cannot see these

A state test's world has one actor: the test. Its timeline has one moment: now.
Every defect above needs **two actors** (a reviewer and a poll; a layout pass and
a resize) or **two moments** (measured, then changed). Neither is expressible in
`arrange → act → assert` over a single frame, so no amount of adding state tests
increases coverage of this class. It stays exactly zero.

## How to apply

**Hold something across the change.** The shape is capture → cause → re-read the
*same* handle, not cause → assert final state.

```js
const before = await el.boundingBox();
await somethingElseHappens();          // the poll, the arrival, the other actor
const after  = await el.boundingBox();
expect(after).toEqual(before);
```

**Name the second actor explicitly.** Write the test as a sentence with two
subjects: *"the reviewer is typing while the agent replies."* If you cannot name
two, the test is a state test wearing different clothes.

**Assert on what must NOT change.** State tests assert the new value; over-time
tests assert stability — the caret is still in the sentence, the neighbour did
not move, the draft survived. Bugs in this class are things being *taken away*,
which no assertion about a new value can see.

**Cover measure-then-grow wherever geometry is computed.** Anything laid out
from measured sizes needs a case where a measured thing changes size afterwards.
This is a bug generator, not a bug: it recurs every time the layout code is
extended.

**Split claims that sound like one claim.** "Nothing moved" and "what you
clicked is still under the cursor" are different assertions, and only the second
one describes the misclick a user experiences. Likewise "it does not overflow"
and "no two elements share pixels". When a check passes and the bug is still
there, suspect you asserted the neighbouring claim.

**Let the real thing run.** These defects need real timers, real repaints, a
real second process. A mocked poll fires when the test says so, which removes
the interleaving that *is* the bug.
