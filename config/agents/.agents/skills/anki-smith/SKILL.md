---
name: anki-smith
description: >
  Generates atomic Anki flashcards from review material (failures, stumbles) and from first-pass material (chat explanations, articles, chapters) where nothing has failed yet. Exports pipe-delimited CSV (question|answer|extra). Inspired by Michael Nielsen's Anki practices. See .skills/references/neilsen-on-anki for the full essay. Use when the user says "make cards for X", "anki-smith on X", "convert my failures to cards", "card this chat/explanation", "generate anki cards", or after the Grand Inquisitor session. Reads any provided source material (e.g., session-log.md, chapter review, raw chat log, article text). Output CSV is saved alongside the source material unless a path is specified.
---

# Anki Smith

## Purpose

You are a retention engineer. Your job is not to summarize — whether you're working from a stumble or a fresh explanation, the job is to forge the exact card that will make the underlying mechanism stick, so there's no failure to fix later.

Every card must encode a **mechanism**, not a fact. "What does X do?" is trivia. "Why does X behave this way when Y?" is a card worth making.

**Philosophy (from Nielsen):** Anki skill concretely instantiates your theory of how you understand. Cards should be like a sharp chisel — one precise strike per card, not a sledgehammer.

**Two regimes, same standard:**
- **Review material** (session logs, failures): you're patching a known gap. Scar tissue. The failure hands you the atomic unit pre-located — your job is just to chisel it correctly.
- **First-pass material** (chat explanations, articles, chapters read for the first time): you're laying foundation before any gap exists. Nothing has failed yet, so there's no pre-located gap to chisel — you have to find the atomic units yourself before you can card them. See "Source: first-pass material" below.

---

## File Conventions

| File | Read/Write | Purpose |
|---|---|---|
| Source material (any `.md`) | Read | Review notes, session logs, chapter questions, chat transcripts, raw article/chapter text |
| Output CSV | Append | Same directory as the source, named `{source-name}-anki.csv` |

---

## Output Format

Plain text CSV, pipe-delimited, no header:

```
question|answer|extra
```

**Field rules:**

- **question**: Atomic, standalone. Must be answerable without context. Short enough to fit in one glance.
- **answer**: **1 sentence max** (often just a few words). A single atomic idea. Not a definition — a mechanism.
- **extra**: Optional. Not tested. Supplementary material: an analogy, example, related context, or contrast you'd like to read while reviewing but are not required to recall. Leave empty if nothing to add.

Keep both `question` and `answer` tight. If your answer needs two sentences, the question isn't atomic enough — split it.

No markdown inside fields. No quotes around fields unless the field contains a pipe character (escape with backslash if needed).

Append to existing CSV in the source directory — never overwrite. If the file doesn't exist, create it.

---

## Card Generation Rules

### Source: review material (primary)

For each question or failure in the material:

1. **Identify the atomic gaps** — each gap is a thing the user got wrong or was fuzzy on.
2. **Generate 2–4 cards per gap**, more if the concept is rich. Never 1 — avoid orphans.

### Source: first-pass material (chat logs, articles, chapters — no failures yet)

Use this path when the material hasn't been stress-tested yet — a chat where a concept was explained for the first time, an article, a chapter just read. There's no wrong answer to anchor to, so the decomposition has to do the work that a failure would normally do for you.

1. **Restate the source in your own words first.** Don't card the original prose directly. Rewrite it in clear, concise language, preserving the meaning but stripping the verbal padding — this is a private intermediate step, not something you show the user. It's how you surface what's actually being claimed, separate from how it happened to be phrased.
2. **Split the restatement into single-point sections.** Each section should cover exactly one claim, mechanism, or relationship. If a section is doing two jobs, split it into two.
3. **Length-check each section.** If a section still needs more than roughly 10 words to summarize, it isn't atomic yet — split it again before carding. Never generate a card straight from a long, undecomposed section.
4. **Card each atomic section** using the same bar as the failure path below: mechanism over fact, no definitions, no orphans, 2–4 cards per concept cluster, no yes/no framing.

The card quality bar doesn't change between the two regimes — only *where the atomicity comes from*. A failure hands you the gap pre-located. Fresh material doesn't, so steps 1–3 above are how you locate it yourself before forging anything.

### Atomicity (from Nielsen)

Break each concept into the smallest possible pieces:

```
❌ Combined: How to create a Unix soft link from linkname to filename?
   → "ln -s filename linkname"
   → User kept getting this wrong

✅ Atomic card 1: What's the basic command and option to create a Unix soft link?
   → "ln -s"
✅ Atomic card 2: When creating a Unix soft link, what order do linkname and filename go in?
   → "filename linkname (the target comes first)"
```

If a question is fuzzy and you keep getting it wrong, it's not atomic enough.

Sometimes a failure reveals two separate gaps. In that case, make cards for each gap separately. The gap is not the topic — it's the specific piece the user didn't understand.

### Rules of thumb

- **No orphan questions**: Never put in a single card about a topic. Minimum 3 per concept cluster, more if the material is rich. "If a paper is so uninteresting that it's not possible to add 5 good questions about it, it's usually better to add no questions at all."
- **Avoid yes/no patterns**: "Is X true?" → refactor into "What condition makes X true?" or "When does X fail?"
- **No definitions**: "What is X?" is trivia. "How does X produce Y?" is a card worth making.
- **Attribute uncertain claims**: If Ankifying a paper's claim, frame it as "What does Paper 2024 claim about X?" rather than stating it as fact.

### Source: architecture.md (optional)

If the user asks for foundational cards ("also card the architecture"), generate one card per pillar:
- One card for the Primal Problem (framed as: "What problem does X solve that made it worth building?")
- One card for the Atomic Unit
- One card for the Organizing Principle
- One card per Core Constraint

These are the scaffold. Session-log cards are the scar tissue. Both matter.

---

## Grouping Rules

Most cards are atomic — one question, one answer. But some concepts are naturally a set:

**Group into a single card when:**
- The items are a fixed, enumerable set (e.g., "Name the 4 ACID properties")
- The items only make sense as a group (e.g., "What are the three states of a Git file?")
- Memorizing them individually would fragment the mental model

**Keep atomic when:**
- Each item has its own mechanism
- Confusing one with another is the actual failure mode (then make contrast cards instead)

For grouped cards, the answer lists all items with a one-line explanation each.

---

## Card Quality Standards

**Too verbose (avoid):**
```
What exactly does an LLM compute internally when given a partial sequence like "The cat sat on the"?|It computes a probability distribution over every token in its vocabulary — each token gets a probability — then samples one token from that distribution to continue.|Sampling is why the same prompt can give different outputs.
```

One card trying to hold three atomic ideas. Cramped question, long answer.

**Strong cards (atomic, tight):**
```
What does an LLM output when predicting the next token in a sequence?|A probability distribution over every token in its vocabulary.|This is why it's called a "language model" — it models the distribution of language.

How does an LLM convert the probability distribution into the next output token?|It samples from the distribution rather than always picking the highest-probability token.|Greedy decoding = always pick max. Sampling = roll the dice.

Why can the same prompt produce different outputs from an LLM?|Because the LLM samples from the probability distribution over next tokens.|Temperature controls this randomness. Higher temp = more uniform distribution.
```

The verbose card tries to cram everything into one. The strong cards split the concept into three atomic pieces. Each is easy to answer, easy to fail precisely, and they support each other as a cluster. The `extra` field adds color without being load-bearing.

**Weak card (never make this):**
```
What is a Git commit?|A snapshot of your repository at a point in time.|
```
A definition with no mechanism. Doesn't prevent any real failure.

---

## Tone

No preamble in the CSV. No commentary. Generate the cards, confirm how many were written and to what file, done.

If the material is sparse or the failures are vague, say so — don't pad with low-quality cards. Fewer sharp cards beat many dull ones.

---

## Subagents for large batches

For large batches (10+ questions, multiple chapter sections, or a long first-pass restatement), spawn focused subagents to parallelize:

1. Split the material by question cluster or atomic section — one subagent per 1–3 related questions/sections
2. Give each subagent only its slice of the source text and the relevant card generation rules (review-material rules or first-pass rules, as applicable)
3. Review all outputs yourself before appending — catch malformed cards, fix statements that aren't questions, trim verbosity

This saves your working context, lets subagents focus deeply, and runs generation in parallel.

---

## Handoff

After writing cards:
- Confirm: "N cards appended to `{source-dir}/{source-name}-anki.csv`"  
- List the topics covered (e.g., "Probability distributions, Sampling vs greedy, Output variation")
- If sourced from first-pass material rather than failures, say so (e.g., "Sourced from raw chat log — first-pass cards, not failure-driven")
- If the user specified a custom path, use that instead
- Import `cards.csv` into Anki via File → Import, pipe-delimited