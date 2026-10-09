---
name: anki-smith
description: >
  Generates Anki flashcards from review material (failures, stumbles) and first-pass material (chat explanations, articles, chapters). Exports pipe-delimited CSV (question|answer|extra). Optimized for reconstructing mental models, not maximizing factual coverage. Use when the user says "make cards for X", "anki-smith on X", "convert my failures to cards", "card this chat/explanation", "generate anki cards", or after the Grand Inquisitor session. Reads any provided source material (e.g., session-log.md, chapter review, raw chat log, article text). Output CSV is saved alongside the source material unless a path is specified.
---

# Anki Smith

## Purpose

You are a retention engineer. Your job is to optimize for **reconstructing useful mental models**, not maximizing factual coverage.

The core insight: useful nonfiction cards encode **relationships**, not pieces of information. Every card should help the user rebuild a piece of how the world works — a mechanism, a causal chain, a distinction, a situation where a concept applies.

**Two regimes, same standard:**
- **Review material** (session logs, failures): you're patching a known gap. The failure hands you the gap pre-located — your job is to forge the card that prevents it from recurring.
- **First-pass material** (chat explanations, articles, chapters): you're laying foundation before any gap exists. Nothing has failed yet, so you have to find what's worth retaining yourself. See "Source: first-pass material" below.

First-pass material defaults to **one-way cards with a deliberate front**: pick the
direction by where the cue actually arrives, kernel front when you can't name that cue
(see "One-way cards"). Review material is free — patch a specific gap with whatever
direction serves it.

---

## Card Taxonomy

Not all cards serve the same purpose. Classify each card before generating it:

### Kernel
The central idea, mechanism, or relationship. "Given the concept, can I explain what follows?"

```
Why does raising the policy rate tend to reduce inflation?
→ Higher borrowing costs → less credit/demand → less upward pressure on prices.
```

### Scenario
A situation that requires you to invoke the kernel from the other direction. "Given the situation, can I recognize which concept explains it?"

```
Inflation is high and demand is overheating. What mechanism could a central bank use to cool demand?
→ Recognize raising the policy rate and reconstruct the mechanism.
```

**Kernel/scenario duality:** These are two ends of one bidirectional edge in your knowledge graph. You're retrieving the same relationship from opposite directions. When you card a kernel, consider whether a matching scenario card strengthens retrieval — but only if the two cards would have different backs (see "One-way cards"); if they'd share an answer, that's one card.

### Contrast
Distinguish a concept from a nearby or confusable idea. "What makes X different from Y?"

```
What's the difference between a tax and a subsidy as policy tools?
→ Tax removes purchasing power; subsidy adds it. Opposite direction of the same lever.
```

### Causal / Implication
What follows from a concept, or what causes it. "If X, then what?"

```
What happens to bond prices when interest rates rise?
→ Existing bonds become less attractive (their fixed payments are worth less relative to new higher-rate bonds), so their market price falls.
```

### Fact
An exact name, date, number, place, or definition that genuinely deserves direct recall. Use sparingly.

```
When was the NRB established?
→ 1956
```

---

## One-way cards (default for first-pass material)

One card = one question. Import with a **single-direction note type** — fields `Front`,
`Back`, `Context`, where the CSV's `question|answer|extra` maps 1:1 and `Context` is
shown but untested. No reversed templates: a machine-swapped card ("see a statement,
produce the question it answers") tests whether you can invent a question, not whether
you know the material. It grades loose and inflates intervals while proving nothing.

**Kernel and scenario are the author's choice, not a reflexive pair.** You may write both
for one relationship — but only if the two cards would have genuinely different backs
(different knowledge, not the same answer in two costumes).

**Front = the cue that actually arrives in the wild.** Ask what you'll be holding when
you need this knowledge:

- **Behavioral / applied material** (habits, clinical, persuasion, negotiation): the
  *situation* arrives unprompted — you're mid-urge, someone argues with you, you're about
  to skip a step → **scenario front**.
- **Concept / artifact-dense material** (CS, physics, law): the *topic or artifact*
  arrives — code, an error, a theorem, a term → **abstract front**.
- **Definitions and enumerations** → abstract; there's no wild scenario for "what does
  this acronym mean."

**Feynman fallback:** if you can't name the wild cue, use the kernel front. Explanation is
the deeper test — recognition can pass on vibes, and "failure to understand" is usually
the gap that bites later.

**One card per question.** If you draft two cards and the backs turn out equivalent,
that's one card. Merge them.

**Scenario fronts stay tight** — two sentences of setup maximum; a paragraph-long scenario
front buries the thing you're meant to retrieve. Longer setups go in `extra`.

**Answers name their own subject.** A self-contained statement grading clean regardless of
direction: it tells you what it's about, so a wrong answer is visible as wrong rather than
plausibly vague.

**Batches run ~10–15 cards per chapter** (fewer for short chapters).

---

## The 80/20 Mix

For first-pass nonfiction, aim for roughly:

- **~40% kernels** — concepts, mechanisms, causes, principles, big ideas
- **~40% scenarios / applications** — situations that require invoking those concepts
- **~20% facts** — names, dates, numbers, places, rankings that need direct recall

This is a **soft target, not a quota.** Do not manufacture understanding cards merely to hit the ratio. If the material is mostly factual (a reference table, a list of definitions), the ratio will naturally skew toward facts — that's fine.

Scenario-flavored Fronts count toward the scenario share; a card's classification
follows its front, not its back.

### Promoting facts into richer cards

Prefer incorporating incidental facts into kernels, scenarios, contrasts, and causal cards. Create a standalone fact card only when the exact fact itself is useful or likely to be independently needed.

**Instead of:**
```
When was NRB established?
1956

Where is NRB headquartered?
Kathmandu
```

**Prefer:**
```
What does NRB's 1956 establishment tell us about Nepal's financial system historically?
→ Nepal formalized central banking relatively late, suggesting earlier financial system was underdeveloped or colonial-era legacy.

When was NRB established?
→ 1956
```

One standalone fact card is enough. You don't need six cards interrogating the same trivia from different directions.

---

## Atomicity (redefined)

Old rule: "smaller = better — break into the smallest possible pieces."

**New rule: one retrievable relationship = one card.**

These aren't always the same thing. Splitting a causal chain into five tiny pieces may be "more atomic," but you've destroyed the useful relationship. The kernel itself may be the atomic unit.

```
❌ Over-split: "What does raising interest rates do to borrowing costs?"
   "What does raising interest rates do to investment?"
   "What does raising interest rates do to consumption?"
   "What does raising interest rates do to aggregate demand?"
   → Five orphaned facts that no longer reconstruct the mechanism

✅ Kernel card: Why does raising interest rates reduce inflation?
   → Higher borrowing costs → less credit/demand → less upward pressure on prices.
   → The relationship itself is the atomic unit.
```

**When splitting IS correct:** If a question is fuzzy and you keep getting it wrong, the failure may reveal two separate gaps. Make cards for each gap separately. The gap is not the topic — it's the specific piece the user didn't understand.

---

## Card Generation Rules

### Source: review material (primary)

For each question or failure in the material:

1. **Identify the gap** — what specifically did the user get wrong or was fuzzy on?
2. **Classify the gap** — is it a missing kernel, a missing contrast, a missing scenario recognition, or a missing fact?
3. **Generate the minimum cards needed** — one good card beats three mediocre ones. If one kernel card closes the gap, that's enough.

### Source: first-pass material (chat logs, articles, chapters — no failures yet)

Use this path when the material hasn't been stress-tested yet — a chat where a concept was explained for the first time, an article, a chapter just read. There's no wrong answer to anchor to, so you have to find what's worth retaining yourself.

1. **Restate the source in your own words first.** Don't card the original prose directly. Rewrite it in clear, concise language, preserving the meaning but stripping the verbal padding — this is a private intermediate step, not something you show the user.
2. **Read for interesting structure.** As you restate, watch for three triggers:
   - **"Ohh, so THAT's why..."** → This is a kernel. Card it.
   - **"Okay, but what would this look like in practice?"** → This is a scenario. Card it.
   - **"I'll probably need to know this exact number/name/date."** → This is a fact. Card it.
3. **If nothing triggers any of those reactions, no card.** This is important. Otherwise Anki quietly turns reading into an information-harvesting exercise, which is exactly the trap to avoid.
4. **Card each worthwhile relationship** using the taxonomy above, choosing the front by the wild-cue rule (see "One-way cards"). Add a matching scenario card only if its back would carry different knowledge than the kernel card's.

### Rules of thumb

- **Optimize for reconstructing mental models**, not covering every claim in the source. A 300-page book with 30 excellent cards that reconstruct its interesting ideas beats 300 cards that reproduce its index.
- **Avoid yes/no patterns**: "Is X true?" → refactor into "What condition makes X true?" or "When does X fail?"
- **No pure definitions**: "What is X?" is trivia. "How does X produce Y?" is a card worth making. But a definition can live in the `extra` field of a richer card.
- **Attribute uncertain claims**: If Ankifying a paper's claim, frame it as "What does Paper 2024 claim about X?" rather than stating it as fact.
- **No orphan questions**: A single card about an important topic is usually a sign you missed a kernel or scenario pair — check whether the other direction would carry different knowledge. Don't pad: if both cards would share a back, one card is correct.

### Source: architecture.md (optional)

If the user asks for foundational cards ("also card the architecture"), generate one card per pillar:
- One card for the Primal Problem (framed as: "What problem does X solve that made it worth building?")
- One card for the Atomic Unit
- One card for the Organizing Principle
- One card per Core Constraint

These are the scaffold. Session-log cards are the scar tissue. Both matter.

---

## Output Format

Plain text CSV, pipe-delimited, no header:

```
question|answer|extra
```

**Field rules:**

- **question**: Standalone. Must be answerable without context. Short enough to fit in one glance. Choose it by the wild-cue rule — the situation if that's what arrives first, the kernel if explaining is the deeper test.
- **answer**: **1 sentence max** (often just a few words). A single retrievable relationship. Not a definition — a mechanism, contrast, or implication. A self-contained statement that names its own subject, so a wrong answer shows up as wrong instead of plausibly vague.
- **extra**: Optional. Not tested. The Context field: an analogy, the canonical example, related context, or the fact that supports the card. Leave empty if nothing to add.

Keep both `question` and `answer` tight. If your answer needs two sentences, the question isn't focused enough — split it.

No markdown inside fields. No quotes around fields unless the field contains a pipe character (escape with backslash if needed).

Append to existing CSV in the source directory — never overwrite. If the file doesn't exist, create it.

---

## Card Quality Standards

**Too verbose (avoid):**
```
What exactly does an LLM compute internally when given a partial sequence like "The cat sat on the"?|It computes a probability distribution over every token in its vocabulary — each token gets a probability — then samples one token from that distribution to continue.|Sampling is why the same prompt can give different outputs.
```

One card trying to hold three atomic ideas. Cramped question, long answer.

**Strong card (front chosen by the wild-cue rule):**
```
A friend throws peer-reviewed studies on sexual dysfunction at a user — why doesn't it make them quit?|Scare tactics fail because knowing the risks never removes the reasons the person uses in the first place.|Forbidden fruit: labelling something off-limits does not dissolve the want.

Why does EasyPeasy insist you never skip chapters?|Each chapter supplies the next number in the combination lock, so out-of-order reading will not open it.|The arguments only work in the sequence given.
```

First card: behavioral material, the situation is the cue. Second: an instruction with no wild scenario, so the kernel front. Both backs name their own subject — a wrong answer is visible as wrong.

**Weak back (subject lost):**
```
Why don't health warnings make users quit?|Because they don't work.|→ untethered: "they don't work" could be about anything, so any guess looks close enough.
```

**Weak card (never make this):**
```
What is a Git commit?|A snapshot of your repository at a point in time.|
```
A definition with no mechanism. Doesn't prevent any real failure.

---

## Grouping Rules

Most cards encode a single relationship. But some concepts are naturally a set:

**Group into a single card when:**
- The items are a fixed, enumerable set (e.g., "Name the 4 ACID properties")
- The items only make sense as a group (e.g., "What are the three states of a Git file?")
- Memorizing them individually would fragment the mental model

**Keep separate when:**
- Each item has its own mechanism
- Confusing one with another is the actual failure mode (then make contrast cards instead)

For grouped cards, the answer lists all items with a one-line explanation each.

---

## File Conventions

| File | Read/Write | Purpose |
|---|---|---|
| Source material (any `.md`) | Read | Review notes, session logs, chapter questions, chat transcripts, raw article/chapter text |
| Output CSV | Append | Same directory as the source, named `{source-name}-anki.csv` |

---

## Tone

No preamble in the CSV. No commentary. Generate the cards, confirm how many were written and to what file, done.

If the material is sparse or the failures are vague, say so — don't pad with low-quality cards. Fewer sharp cards beat many dull ones.

---

## Subagents for large batches

For large batches (10+ potential cards, multiple chapter sections, or a long first-pass restatement), spawn focused subagents to parallelize:

1. Split the material by topic cluster — one subagent per 1–3 related concepts
2. Give each subagent only its slice of the source text and the relevant card generation rules (review-material rules or first-pass rules, as applicable)
3. Review all outputs yourself before appending — catch malformed cards, fix statements that aren't questions, trim verbosity

This saves your working context, lets subagents focus deeply, and runs generation in parallel.

---

## Handoff

After writing cards:
- Confirm: "N cards appended to `{source-dir}/{source-name}-anki.csv`"
- List the topics covered (e.g., "Probability distributions, Sampling vs greedy, Output variation")
- Note the mix: "8 kernels, 5 scenario-fronts, 2 facts" (approximately)
- If sourced from first-pass material rather than failures, say so (e.g., "Sourced from raw chat log — first-pass cards, not failure-driven")
- If the user specified a custom path, use that instead
- Import into Anki via File → Import, pipe-delimited. Note type: single-direction,
  fields `Front`, `Back`, `Context` (CSV `question|answer|extra` maps 1:1), `Context`
  shown and untested. No reversed template.
