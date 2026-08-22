---
name: study-sprint
description: >
  Sprint-based learning cycle: probe → plan → teach → cards → log. Use when
  the user says "sprint on X", "learn X", "start learning X", "teach me X".
  Replaces waterfall read→grill→cards flow with incremental sprints that
  map understanding first, then teach at the edge.
---

# Study Sprint

Sprint-based learning cycle for ~/github/study/.

## Sprint Cycle

### Phase 1: Load Context
1. Read the topic's `syllabus.md` for structure and prerequisites.
2. Read existing CSVs to avoid duplicating cards.
3. Read previous sprint logs (if any) to continue where you left off.
4. Read `sprints/{topic}/graph.md` if it exists (the master dependency graph).

### Phase 2: Probe

**First sprint on a topic (comprehensive):**
- Generate 15-20 graded MCQs covering the ENTIRE topic scope.
- Binary search approach: start broad across all major strands, narrow to knowledge edge.
- Include questions you EXPECT the user to get wrong — the goal is to map the full knowledge landscape.
- Record each result: correct / incorrect / partial.
- Output: knowledge map (solid / edge / missing).

**Later sprints (edge-focused):**
- Generate 5-8 MCQs focused on concepts marked "edge" or "missing" in previous sprint.
- Re-probe previously weak concepts to check retention.
- Output: updated knowledge map showing progress.

### Phase 3: Plan

Based on probe results, generate a mermaid dependency graph:

1. Identify all concepts the topic depends on.
2. Map prerequisite relationships between concepts.
3. Color-code by knowledge state:
   - Green (#90EE90): solid understanding
   - Yellow (#FFD700): edge of understanding
   - Red (#FF6B6B): missing
4. Show the learning path from current understanding to goal.

**First sprint:** Create the master graph in `sprints/{topic}/graph.md`. This persists across sprints.
**Later sprints:** Reference the master graph, update node colors based on new probe results. Include a snapshot in the sprint log.

### Phase 4: Teach

**One concept at a time, one reasoning step at a time.**

1. Pick the first yellow/red node that has all its prerequisites met (green).
2. Teach that single concept. Do not rush forward.
3. Use websearch (via subagent) to fetch current data, stats, or recent discoveries when teaching.
4. Wait for the user to confirm understanding or ask questions before moving on.
5. Quiz on that specific concept before proceeding.
6. Repeat for 1-2 concepts per sprint.

**Teaching rules:**
- Never skip ahead — each step must be understood before the next.
- If the user asks questions, answer them fully before continuing.
- If the user is confused, re-explain from a different angle.
- Keep explanations tight — one idea per message.

### Phase 5: Cards

For each gap identified in this sprint:

1. Generate 2-4 mechanism-focused cards per gap (follow anki-smith philosophy).
2. Cards answer "why does X behave this way when Y?" not "what is X?"
3. Append to the topic's CSV file (create if needed).
4. Run `build.sh` to update `master-anki.csv`.

**Card quality bar:**
- No definitions ("What is X?" is trivia)
- No yes/no patterns
- No orphan questions (minimum 3 per concept cluster)
- Atomic — one mechanism per card
- Answer: 1 sentence max

### Phase 6: Log

Save sprint log to `sprints/{topic-slug}/{date}-sprint-{N}-{concept-slug}.md`.

Sprint log format:

```
# Sprint: {Topic} — Sprint {N}: {Concept Slug}
**Date:** YYYY-MM-DD
**Duration:** ~Xm

## Probe Results
| # | Question | Concept | Result | Notes |
|---|----------|---------|--------|-------|
| 1 | ... | ... | correct/incorrect/partial | ... |

## Knowledge Map (Updated)
- **Solid:** [concepts]
- **Edge:** [concepts]
- **Missing:** [concepts]

## Dependency Graph
[Snapshots or reference to graph.md]

## Teaching Log
### Concept: {Name}
- Taught: [summary]
- Quiz: [question] → [result]
- Cards generated: N

## Cards Generated
| Question | Answer | Extra | Tags |
|----------|--------|-------|------|
| ... | ... | ... | topic::slug::concept |

## Status
- Sprint completed: Yes
- Graph updated: Yes
- Syllabus updated: Yes
- Next sprint focus: {concept}
```

### Phase 7: Update

1. Update `graph.md` — change node colors based on new knowledge state.
2. Update `syllabus.md`:
   - If section's concepts are all solid → flip `[ ]` to `[x]`
   - If section is being probed/taught → flip `[ ]` to `[~]`
   - Update `Last touched` date.

## Trigger Phrases

| User says | Action |
|-----------|--------|
| "sprint on {topic}" | Start new sprint. First sprint = comprehensive probe. |
| "next sprint" | Continue with next concept in current topic's graph. |
| "show sprint history for {topic}" | Display sprint logs. |
| "resume sprint" | Pick up where you left off. |

## Subagent Usage

**Websearch subagent:** When teaching requires current data, spawn a subagent to:
1. Search the web for current stats, recent discoveries, or authoritative sources.
2. Return a concise summary with sources.
3. The orchestrator incorporates findings into the teaching.

**Card generation subagent:** For large batches (10+ cards), spawn subagents to parallelize card generation, following anki-smith rules.

## File Operations

| Operation | File |
|-----------|------|
| Read | `topics/{topic}/syllabus.md`, `topics/{topic}/*.csv`, `sprints/{topic}/*.md`, `sprints/{topic}/graph.md` |
| Write | `sprints/{topic}/graph.md` (first probe), sprint logs |
| Append | `topics/{topic}/{concept}.csv` (new cards) |
| Execute | `build.sh` (after card generation) |
| Update | `topics/{topic}/syllabus.md` (checkboxes) |
