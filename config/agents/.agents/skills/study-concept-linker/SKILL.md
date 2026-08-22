---
name: study-concept-linker
description: Cross-references topics in the study knowledge base (~/github/study/) and surfaces connections between domains. Use when the user wants to understand how concepts relate across fields, build a cumulative mental model, or discover unexpected links. Triggered by "connect X to Y", "what does X have to do with Y", "find links between", "how is this related to", "show me knowledge graph".
---

# Study Concept Linker

You read across the user's study knowledge base at ~/github/study/ and surface connections between concepts in different domains.

## How it works

1. Scan `syllabus.md` files for related topics, prerequisites, and cross-references.
2. Read concept CSVs for overlapping terminology and concepts.
3. Find concepts that appear in multiple domains.
4. Present connections to the user with concrete examples.

## Connection types

| Type | Example |
|---|---|
| **Direct overlap** | Bayes' theorem appears in both AI and Information Theory |
| **Metaphor** | Cache memory ≈ working memory in psychology |
| **Prerequisite** | Understanding probability enables ML |
| **Application** | Ethics from philosophy applied to AI engineering |
| **Contrast** | How cognitive biases differ from statistical bias in ML |
| **Historical** | Shannon's information theory → modern compression → multimedia |

## Output format

```markdown
## Connection: X ↔ Y

**X domain**: ...
**Y domain**: ...

**How they connect**: ...
**Why this matters for learning**: ...

**Practical exercise**: ...
```

## Guidelines
- Prioritize connections the user is likely to encounter organically.
- Don't force connections — only surface meaningful ones.
- Suggest concrete exercises or cross-domain recall questions.
- If the user is studying a specific topic, proactively surface relevant connections from other parts of their knowledge base.
