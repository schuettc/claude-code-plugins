---
name: verify-the-artifact
description: Use when a change's effect is separated from its source by a build step, a bundler, a cascade, or any runtime resolution — CSS, generated assets, compiled bundles, templates, layered config, env precedence. The rule — source is a claim about behaviour; only the running artifact is evidence. Read the resolved value out of the running system rather than reasoning about the source that should have produced it.
---

# Verify the artifact, not the source

## The rule

**Between the file you edited and the behaviour you want, count the steps. If
there is even one, the file is not evidence.**

A bundler, a minifier, the CSS cascade, template inheritance, config layering,
env-var precedence, a Docker layer cache, a symlinked `node_modules` — each is a
place where what you wrote and what runs can differ, silently, with no error
anywhere. Verify at the far end: read the resolved value out of the running
system.

## The incident that names it

A CSS rule in a real editor:

```css
.gly-card button   { border: 1px solid var(--gly-line); color: inherit; }  /* 0,1,1 */
.gly-thread-delete { border-color: transparent; color: var(--gly-muted); } /* 0,1,0 */
```

The intent was that `delete` — irreversible outside version control — should
render quieter than `resolve` beside it. The rule was written, carefully
commented ("it never becomes the loudest thing on the card"), reviewed, and
shipped. **It never applied once.** The container rule out-specifies it, so the
borderless and the muted were both discarded and delete rendered as an ordinary
pill of equal weight to the verb that keeps every word.

Nobody reading that stylesheet could see it — and several people read it,
including the author who wrote the comment defending the behaviour. One call to
`getComputedStyle` in a real browser found it in seconds.

Two more from the same codebase, same shape:

- **Conflict markers committed inside generated CSS.** The full verification
  gate passed green, because that gate compiles Go and Go does not compile CSS.
  Only rebuilding the bundle found them.
- **A stale committed bundle.** Source edited, bundle not regenerated, every
  check green, the browser serving the previous version of the code.

## Why source-reading fails specifically

Reading source answers *"is this rule correct?"* The failure modes above are all
instances of a different question: *"does this rule apply?"* — and that one is
decided by things not present in the file you are reading. Specificity is
decided by every **other** rule. Precedence is decided by the loader. Freshness
is decided by whether someone ran the build.

You cannot reason your way to the answer from one file, and being careful does
not help, because carefulness is aimed at correctness.

## How to apply

**Name the gap before you start.** What sits between this file and the running
behaviour? Bundle? Cascade? Cache? Merge? If the answer is "nothing", source is
fine. Otherwise plan to verify at the far end from the outset — retrofitting
verification after a change is how you end up asserting your own fix.

**Measure where the value resolves.**

| Gap | Where evidence lives |
| --- | --- |
| CSS cascade | `getComputedStyle(el)` in a real browser |
| Bundler / minifier | the built file, or the served HTTP response |
| Template inheritance | the rendered output |
| Layered config / env | the process's own resolved config at runtime |
| Container build | `docker run … env`, or the image's actual layers |

**Make the assertion fail first.** Run it against the *unfixed* system and watch
it fail before you change anything. An assertion only ever run after the fix
cannot distinguish "I fixed it" from "it was never broken" from "I am measuring
the wrong element". This is the whole reason the CSS bug survived review: no
check ever ran that could have gone red.

**Ask what your gate can physically see.** A gate that is green is only
meaningful over what it reads. A Go test suite is blind to CSS. A type checker
is blind to runtime config. A linter is blind to a stale build output. When a
change lands in a medium the gate does not read, the green is not about your
change at all — and it will feel exactly like the green that is.

State that blind spot out loud where the checks are documented, so the next
person does not read the same green as coverage.
