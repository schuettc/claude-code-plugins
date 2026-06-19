# Anti-pattern self-audit checklist

Used by `/ghost:draft-post` Phase 5 and `/ghost:revise-post`. Each entry lists: the pattern, a concrete grep/regex to detect it, and a one-line reason to avoid it.

For every pattern found: **fix it in the draft, then note the fix.** Do not leave issues in place and report them — repair first.

---

## 1. Forbidden heading styles

### 1a. ALL-CAPS headings

**Grep:**
```
grep -nE '^#{1,6} [A-Z][A-Z ]{3,}$'
```

**Why:** ALL-CAPS headings read as shouting and break the calm, direct register the author is going for.

**Fix:** Convert to sentence case — capitalize only the first word and any proper nouns.

---

### 1b. Question-only headings

**Grep:**
```
grep -nE '^#{1,6} .+\?$'
```

**Why:** A heading that is purely a question (no declarative anchor) feels like clickbait and gives the reader no information before they decide whether to read the section.

**Fix:** Rewrite as a declarative or partially declarative heading that still captures the question's intent. Example: "Why this approach breaks at scale" instead of "Why does this break at scale?"

---

## 2. Editorial restatements

**Grep:**
```
grep -niE '(in other words|to put it simply|what i mean is|what i('m| am) saying is|let me rephrase|put another way)'
```

**Why:** Editorial restatements signal the previous sentence failed — rewrite the original instead of explaining it again.

**Fix:** Delete the restatement and revise the sentence it was clarifying so it stands on its own.

---

## 3. Hedge words

**Grep:**
```
grep -niE '\b(just|simply|basically|obviously|of course|clearly|needless to say)\b'
```

**Why:** These words weaken assertions and condescend to the reader (implying what follows should be obvious to them). Strip them and let the claim stand without qualification.

**Fix:** Delete the hedge word. If the sentence still sounds uncertain, rewrite the claim more precisely instead of hedging.

---

## 4. AI-flavored transitions and filler phrases

**Grep:**
```
grep -niE '(in conclusion|in summary|to summarize|it(\'s| is) worth noting|it(\'s| is) important to (note|remember|understand)|delve into|certainly|absolutely|moreover,|furthermore,|additionally,)'
```

**Why:** These phrases are hallmarks of AI-generated text and corporate prose. They add no information and signal to readers that the author is padding.

**Fix:** Delete the phrase and restructure the sentence or paragraph to flow without it. "In conclusion" → just write the conclusion. "It's worth noting that X" → just write X.

---

## 5. Cleft and focus-frame constructions

**Grep:**
```
grep -niE '(what (this|that) means is|the thing about .{1,40} is|what('s| is) (interesting|important|notable) (here|about this) is|the (point|key|takeaway) (here|is that))'
```

**Why:** These meta-commentary frames step outside the content to announce what you're about to say instead of just saying it. They bloat the sentence and slow the reader down.

**Fix:** Delete the frame and state the point directly. "What this means is the cache is invalidated" → "The cache is invalidated."

---

## 6. Cute closers

**Grep:**
```
grep -niE '(happy coding|until next time|stay curious|hope this helps|happy (building|shipping|hacking)|that(\'s| is) a wrap|catch you (next time|later)|keep (coding|building|hacking))'
```

**Why:** Cheerful sign-off phrases undermine the post's authority and feel performative rather than genuine. The close should land on the substance of the post, not a pep talk.

**Fix:** Delete the phrase. Replace with a closing line that reinforces the post's main point, poses an open question, or points to a logical next step — without a greeting-card sign-off.

---

## 7. Code fence issues

### 7a. Missing language tag

**Grep:**
```
grep -nP '^```\s*$'
```

**Why:** Ghost's syntax highlighter skips un-tagged fences, producing plain gray boxes even for code that should be colored. A language tag also tells readers what they're looking at before they read a line.

**Fix:** Add the correct language tag. Defaults: `typescript`, `javascript`, `bash`, `json`, `yaml`, `text` (for plain output or pseudocode).

---

### 7b. Lines exceeding 70 characters inside code blocks

**Grep:**
```
awk '/^```/{inside=!inside} inside && length($0)>70{print NR": "length($0)" chars: "$0}' <draft-file>
```

**Why:** Ghost's default content width renders code blocks at a narrower viewport than desktop terminals. Lines over ~70 characters trigger horizontal scrollbars or force awkward wrapping, degrading the reading experience on mobile and Ghost's default theme.

**Fix:** Break long lines using the language's idiomatic line-continuation style. For shell commands use `\` continuation; for TypeScript/JavaScript use intermediate variables or line breaks at operators.

---

## Usage notes

- Run all checks in order — some fixes (e.g., removing a hedge word) can reveal a restatement pattern in the same sentence that now needs fixing.
- The grep patterns are case-insensitive (`-i` flag) wherever casing varies by context.
- Code-fence line-length check uses `awk` rather than `grep` to track whether you're inside a fenced block — plain `grep` cannot do this.
- After all fixes are applied, write the corrected draft back to the file before handing off.
