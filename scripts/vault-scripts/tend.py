#!/usr/bin/env python3
"""Tend personal notes: audit, dashboard, hybrid link suggestions, and guided sessions."""

import argparse
import difflib
import hashlib
import json
import math
import os
import random
import re
import shlex
import shutil
import subprocess
import sys
import urllib.parse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
except ImportError:
    console = None

DEFAULT_VAULT = Path.home() / "github" / "obsidian-vault"
DEFAULT_EDITOR = "code --wait"
TODAY = date.today()

VAULT = DEFAULT_VAULT
REFLECTIONS = VAULT / "Reflections"
UNFINISHED = VAULT / "unfinished"
DASHBOARD = REFLECTIONS / "Tending.md"
MAPS = REFLECTIONS / "Maps"
ARCHIVE = REFLECTIONS / "Archive"
TEMPLATES = VAULT / "rough Notes" / "zTemplates"

EXCLUDED_DIRS = {
    ".git",
    ".obsidian",
    ".stversions",
    ".tend",
    ".trash",
    "__pycache__",
    "node_modules",
}
SPECIAL_REVIEW_FILES = {"Tending.md"}

WIKILINK_RE = re.compile(r"\[\[([^\]\n]+?)\]\]")
FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
HEADING_RE = re.compile(r"^#{1,6}\s+", re.M)
RELATED_RE = re.compile(r"^##\s+Related\s*$", re.M)
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9'-]{3,}")

TITLE_GENERIC_WORDS = {"template", "untitled", "notes", "note", "thoughts", "draft", "test"}

STOPWORDS = {
    "about", "after", "again", "against", "almost", "also", "although", "always",
    "another", "anything", "because", "before", "being", "between", "both", "could",
    "does", "doing", "done", "down", "during", "each", "even", "ever", "every",
    "from", "have", "having", "here", "into", "just", "like", "little", "make",
    "many", "maybe", "more", "most", "much", "must", "never", "only", "other",
    "over", "really", "same", "should", "since", "some", "something", "still",
    "such", "than", "that", "their", "them", "then", "there", "these", "they",
    "thing", "things", "this", "those", "through", "time", "under", "until",
    "very", "want", "well", "were", "what", "when", "where", "which", "while",
    "will", "with", "without", "would", "your", "yourself",
}


@dataclass
class Record:
    path: Path
    rel: str
    stem: str
    title: str
    body: str
    raw: str
    frontmatter: dict
    aliases: list
    words: int
    links: list
    mtime: date
    status: str
    reviewed: date | None
    tokens: set = field(default_factory=set)
    embedding_text: str = ""

    @property
    def last_touched(self):
        return max(self.mtime, self.reviewed) if self.reviewed else self.mtime


@dataclass
class Note(Record):
    outlinks: set = field(default_factory=set)
    inlinks: set = field(default_factory=set)


@dataclass
class Suggestion:
    target: Note
    reason: str
    kind: str
    matched: str = ""
    score: float = 0.0
    evidence: str = ""


def feedback_path():
    return VAULT / ".tend" / "feedback.json"


def feedback_key(source, target):
    return tuple(sorted((source, target)))


@dataclass
class FeedbackStore:
    dismissed: dict = field(default_factory=dict)

    @classmethod
    def load(cls):
        store = cls()
        path = feedback_path()
        if not path.exists():
            return store
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return store
        if not isinstance(data, dict):
            return store
        items = data.get("items", [])
        if not isinstance(items, list):
            return store
        for item in items:
            if not isinstance(item, dict):
                continue
            source = item.get("source")
            target = item.get("target")
            if not source or not target:
                continue
            store.dismissed[feedback_key(source, target)] = item
        return store

    def is_dismissed(self, source, target):
        return feedback_key(source, target) in self.dismissed

    def dismiss(self, source, target, kind="", score=0.0, evidence=""):
        key = feedback_key(source, target)
        self.dismissed[key] = {
            "source": source,
            "target": target,
            "kind": kind,
            "score": round(float(score), 4),
            "evidence": evidence,
            "dismissed_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.save()

    def undismiss(self, source, target):
        key = feedback_key(source, target)
        if key in self.dismissed:
            del self.dismissed[key]
            self.save()
            return True
        return False

    def save(self):
        path = feedback_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "items": [self.dismissed[key] for key in sorted(self.dismissed)],
        }
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)


def configure(vault_value=None):
    global VAULT, REFLECTIONS, UNFINISHED, DASHBOARD, MAPS, ARCHIVE, TEMPLATES
    VAULT = Path(
        vault_value
        or os.environ.get("TEND_VAULT")
        or DEFAULT_VAULT
    ).expanduser().resolve()
    REFLECTIONS = VAULT / "Reflections"
    UNFINISHED = VAULT / "unfinished"
    DASHBOARD = REFLECTIONS / "Tending.md"
    MAPS = REFLECTIONS / "Maps"
    ARCHIVE = REFLECTIONS / "Archive"
    TEMPLATES = VAULT / "rough Notes" / "zTemplates"


def as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        text = value.strip()
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None
    return None


def split_frontmatter(raw):
    match = FM_RE.match(raw)
    if not match:
        return {}, raw
    data = {}
    if yaml:
        try:
            loaded = yaml.safe_load(match.group(1)) or {}
            if isinstance(loaded, dict):
                data = loaded
        except Exception:
            data = {}
    return data, raw[match.end():]


def normalize_boilerplate_line(line):
    return re.sub(r"\s+", " ", line.strip()).lower()


def load_template_lines():
    lines = set()
    if not TEMPLATES.exists():
        return lines
    for path in TEMPLATES.rglob("*.md"):
        try:
            _, body = split_frontmatter(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
        in_code = False
        for raw in body.splitlines():
            stripped = raw.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            normalized = normalize_boilerplate_line(stripped)
            if len(normalized) >= 6 and not normalized.startswith("#"):
                lines.add(normalized)
    return lines


def clean_embedding_text(body, boilerplate_lines=None):
    boilerplate_lines = boilerplate_lines or set()
    text = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    text = re.sub(r"(?ms)^##\s+Related\s*$.*?(?=^#{1,6}\s|\Z)", "", text)
    lines = []
    in_code = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            lines.append(raw.rstrip())
            continue
        if in_code:
            lines.append(raw.rstrip())
            continue
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if re.fullmatch(r"[-*_]{3,}", stripped):
            continue
        if re.fullmatch(r"\|?[\s:|-]+\|?", stripped) and "-" in stripped:
            continue
        normalized = normalize_boilerplate_line(stripped)
        if normalized in boilerplate_lines:
            continue
        if (
            re.match(r"(?i)^(created|date|tags?|updated|status|aliases?):", stripped)
            and len(stripped) <= 160
        ):
            continue
        if re.fullmatch(r"[-*+]\s*(\[\s*\]\s*)?", stripped):
            continue
        if re.fullmatch(r"\d+\.\s*", stripped):
            continue
        if re.fullmatch(r"([-*+]\s*)?(\[\[[^\]]+\]\]\s*)+", stripped):
            continue
        lines.append(stripped)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def aliases_from(frontmatter):
    value = frontmatter.get("aliases") or frontmatter.get("alias") or []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def title_from(frontmatter, path):
    value = frontmatter.get("title")
    return str(value).strip() if value else path.stem


def parse_wikilinks(body):
    links = []
    for match in WIKILINK_RE.finditer(body):
        target = match.group(1).split("|")[0].split("#")[0].strip()
        if target:
            links.append(target)
    return links


def word_count(body):
    return len(re.findall(r"\S+", body))


def tokenize(text):
    return {token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in STOPWORDS}


def read_record(path):
    raw = path.read_text(encoding="utf-8", errors="ignore")
    frontmatter, body = split_frontmatter(raw)
    rel = str(path.relative_to(VAULT))
    status = str(frontmatter.get("status") or "unset").strip()
    reviewed = as_date(frontmatter.get("reviewed"))
    mtime = datetime.fromtimestamp(path.stat().st_mtime).date()
    return Record(
        path=path,
        rel=rel,
        stem=path.stem,
        title=title_from(frontmatter, path),
        body=body,
        raw=raw,
        frontmatter=frontmatter,
        aliases=aliases_from(frontmatter),
        words=word_count(body),
        links=parse_wikilinks(body),
        mtime=mtime,
        status=status,
        reviewed=reviewed,
        tokens=tokenize(f"{path.stem}\n{body}"),
    )


def iter_all_paths():
    if not VAULT.exists():
        return
    for path in VAULT.rglob("*.md"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path == DASHBOARD or path.name in SPECIAL_REVIEW_FILES:
            continue
        if TEMPLATES in path.parents:
            continue
        yield path


def is_scoped(path):
    if path == DASHBOARD or path.name in SPECIAL_REVIEW_FILES:
        return False
    if MAPS in path.parents or ARCHIVE in path.parents:
        return False
    if path.suffix.lower() != ".md":
        return False
    return UNFINISHED in path.parents or REFLECTIONS in path.parents


def build_lookup(records):
    lookup = defaultdict(list)
    for rel, record in records.items():
        no_ext = rel[:-3] if rel.lower().endswith(".md") else rel
        names = {
            record.stem,
            record.path.name,
            no_ext,
            record.title,
            *record.aliases,
        }
        for name in names:
            key = name.strip().lower().lstrip("./")
            if key and rel not in lookup[key]:
                lookup[key].append(rel)
    return lookup


def resolve_target(target, lookup, scoped_rels):
    text = target.strip()
    text = text.split("|")[0].split("#")[0].strip()
    if not text:
        return None
    candidates = []
    for key in (
        text.lower().lstrip("./"),
        Path(text).stem.lower(),
    ):
        candidates.extend(lookup.get(key, []))
    if not candidates:
        return None
    for candidate in candidates:
        if candidate in scoped_rels:
            return candidate
    return candidates[0]


def is_utility(record):
    return bool(re.search(r"```(?:dataview|query)\b", record.body, re.IGNORECASE))


def is_suggestable(path):
    if path.name in SPECIAL_REVIEW_FILES or path == DASHBOARD:
        return False
    if MAPS in path.parents or ARCHIVE in path.parents:
        return False
    excluded = {"daily n gratitude", "Clippings", "scripts", "llm"}
    return not any(part in excluded for part in path.parts)


def load_vault():
    records = {}
    for path in iter_all_paths():
        try:
            records[str(path.relative_to(VAULT))] = read_record(path)
        except OSError:
            continue

    boilerplate_lines = load_template_lines()
    for record in records.values():
        record.embedding_text = clean_embedding_text(record.body, boilerplate_lines)
        record.tokens = tokenize(f"{record.stem}\n{record.embedding_text}")

    lookup = build_lookup(records)
    scoped_rels = {
        rel for rel, record in records.items()
        if is_scoped(record.path) and not is_utility(record)
    }
    all_rels = set(records)

    all_notes = {}
    for rel, record in records.items():
        all_notes[rel] = Note(**record.__dict__)

    for rel, note in all_notes.items():
        for target in note.links:
            resolved = resolve_target(target, lookup, all_rels)
            if resolved and resolved != rel:
                note.outlinks.add(resolved)

    for source_rel, note in all_notes.items():
        for target in note.outlinks:
            if target in all_notes and target != source_rel:
                all_notes[target].inlinks.add(source_rel)

    notes = {rel: all_notes[rel] for rel in scoped_rels}
    return notes, records, all_notes


def protected_spans(text):
    spans = []
    for regex in (
        WIKILINK_RE,
        re.compile(r"```.*?```", re.S),
        re.compile(r"`[^`\n]+`"),
        re.compile(r"https?://\S+"),
    ):
        for match in regex.finditer(text):
            spans.append((match.start(), match.end()))
    return spans


def in_spans(position, spans):
    return any(start <= position < end for start, end in spans)


def meaningful_name(name):
    cleaned = name.strip()
    if not cleaned or cleaned.lower().startswith("untitled"):
        return False
    if len(cleaned) >= 12:
        return True
    return len(cleaned.split()) >= 3


def note_match_names(note):
    names = {note.stem, *note.aliases}
    if note.title and note.title != note.stem:
        names.add(note.title)
    return [name for name in names if meaningful_name(name)]


def find_mention(source, target, spans=None):
    spans = protected_spans(source.body) if spans is None else spans
    body_lower = source.body.lower()
    for name in note_match_names(target):
        if name.lower() not in body_lower:
            continue
        pattern = re.compile(
            r"(?<![A-Za-z0-9])" + re.escape(name) + r"(?![A-Za-z0-9])",
            re.IGNORECASE,
        )
        for match in pattern.finditer(source.body):
            if not in_spans(match.start(), spans):
                return match.group(0)
    return None


def unlinked_mentions_for(source, notes):
    spans = protected_spans(source.body)
    mentions = []
    for rel, target in notes.items():
        if rel == source.rel or rel in source.outlinks:
            continue
        matched = find_mention(source, target, spans)
        if matched:
            mentions.append((target, matched))
    mentions.sort(key=lambda item: (-len(item[1]), item[0].stem.lower()))
    return mentions


def all_unlinked_mentions(notes):
    pairs = []
    for source in notes.values():
        for target, matched in unlinked_mentions_for(source, notes):
            pairs.append((source, target, matched))
    pairs.sort(
        key=lambda item: (
            -len(item[1].inlinks),
            -item[0].words,
            item[0].stem.lower(),
        )
    )
    return pairs


def duplicate_pairs(notes):
    values = list(notes.values())
    pairs = []
    seen = set()
    body_groups = defaultdict(list)
    for note in values:
        normalized = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", note.body.lower())).strip()
        if normalized:
            body_groups[normalized[:1200]].append(note)

    for group in body_groups.values():
        for left, right in zip(group, group[1:]):
            key = tuple(sorted((left.rel, right.rel)))
            if key not in seen:
                seen.add(key)
                pairs.append((left, right, 1.0, "same body"))

    title_norms = {
        note.rel: re.sub(r"[^a-z0-9 ]", "", note.stem.lower()).strip()
        for note in values
    }
    for index, left in enumerate(values):
        for right in values[index + 1:]:
            key = tuple(sorted((left.rel, right.rel)))
            if key in seen:
                continue
            ratio = difflib.SequenceMatcher(None, title_norms[left.rel], title_norms[right.rel]).ratio()
            if ratio >= 0.86:
                seen.add(key)
                pairs.append((left, right, ratio, f"{int(ratio * 100)}% title match"))

    pairs.sort(key=lambda item: (-item[2], item[0].stem.lower()))
    return pairs


def wikilink(note, stem_counts):
    target = note.stem
    if stem_counts.get(note.stem.lower(), 0) > 1:
        target = note.rel[:-3]
    if note.title and note.title != note.stem:
        return f"[[{target}|{note.title}]]"
    return f"[[{target}]]"


def needs_reason(note):
    reasons = []
    if not note.outlinks:
        reasons.append("no outgoing links")
    if not note.inlinks:
        reasons.append("no incoming links")
    if not note.embedding_text.strip():
        reasons.append("no prose")
    if note.words < 150:
        reasons.append(f"short ({note.words} words)")
    days = (TODAY - note.last_touched).days
    if days >= 60:
        reasons.append(f"untouched for {days} days")
    if not note.reviewed:
        reasons.append("never reviewed")
    return reasons or ["due for a look"]


def tend_score(note, rng):
    score = 0.0
    if not note.outlinks:
        score += 4
    elif len(note.outlinks) < 2:
        score += 2
    if not note.inlinks:
        score += 2
    score += min(max((TODAY - note.last_touched).days, 0) / 30, 6)
    if note.words < 150:
        score += 1.5
    if not note.reviewed:
        score += 1
    if note.status in {"archived", "evergreen"}:
        score -= 1
    score += rng.uniform(0, 1.5)
    return score


def ranked_notes(notes, limit=None):
    rng = random.Random(TODAY.toordinal())
    candidates = [note for note in notes.values() if note.words > 0]
    if not candidates:
        candidates = list(notes.values())
    ranked = sorted(candidates, key=lambda note: tend_score(note, rng), reverse=True)
    return ranked[:limit] if limit else ranked


def status_counts(notes):
    counts = Counter(note.status or "unset" for note in notes.values())
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def stats_payload(notes, mentions, duplicates):
    total = len(notes)
    linked = sum(1 for note in notes.values() if note.outlinks)
    orphans = sum(1 for note in notes.values() if not note.outlinks and not note.inlinks)
    no_out = sum(1 for note in notes.values() if not note.outlinks)
    no_in = sum(1 for note in notes.values() if not note.inlinks)
    empty = sum(1 for note in notes.values() if note.words == 0)
    return {
        "total": total,
        "linked": linked,
        "linked_pct": round(linked / total * 100, 1) if total else 0,
        "orphans": orphans,
        "no_out": no_out,
        "no_in": no_in,
        "empty": empty,
        "mentions": len(mentions),
        "duplicates": len(duplicates),
        "statuses": status_counts(notes),
    }


def print_stats(notes, mentions, duplicates):
    payload = stats_payload(notes, mentions, duplicates)
    if console:
        table = Table(title="Tend audit", box=box.SIMPLE, show_header=False)
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")
        for label, key in (
            ("Notes reviewed", "total"),
            ("With outgoing links", "linked"),
            ("Link coverage", "linked_pct"),
            ("True orphans", "orphans"),
            ("No outgoing links", "no_out"),
            ("No incoming links", "no_in"),
            ("Empty notes", "empty"),
            ("Unlinked-mention pairs", "mentions"),
            ("Duplicate candidates", "duplicates"),
        ):
            value = payload[key]
            if key == "linked_pct":
                value = f"{value}%"
            table.add_row(label, str(value))
        console.print(table)

        status_table = Table(title="Status", box=box.SIMPLE, show_header=False)
        status_table.add_column("Status", style="bold")
        status_table.add_column("Count", justify="right")
        for status, count in payload["statuses"].items():
            status_table.add_row(status, str(count))
        console.print(status_table)
    else:
        print(f"Notes reviewed: {payload['total']}")
        print(f"With outgoing links: {payload['linked']} ({payload['linked_pct']}%)")
        print(f"True orphans: {payload['orphans']}")
        print(f"No outgoing links: {payload['no_out']}")
        print(f"No incoming links: {payload['no_in']}")
        print(f"Empty notes: {payload['empty']}")
        print(f"Unlinked-mention pairs: {payload['mentions']}")
        print(f"Duplicate candidates: {payload['duplicates']}")
        print("Status:", ", ".join(f"{k}={v}" for k, v in payload["statuses"].items()))

    values = list(notes.values())
    shortest = sorted(values, key=lambda note: note.words)[:5]
    neglected = sorted(values, key=lambda note: note.last_touched)[:5]
    print("\nShortest:")
    for note in shortest:
        print(f"  {note.stem} ({note.words} words)")
    print("\nMost neglected:")
    for note in neglected:
        days = (TODAY - note.last_touched).days
        print(f"  {note.stem} ({days} days)")
    print(f"\nDashboard: {DASHBOARD}")


def build_dashboard(notes, mentions, duplicates, semantic=None, feedback=None):
    values = list(notes.values())
    stem_counts = Counter(note.stem.lower() for note in values)
    lines = [
        "---",
        "status: evergreen",
        "type: dashboard",
        f"generated: {TODAY.isoformat()}",
        "---",
        "",
        "# Tending",
        "",
        f"*Generated {TODAY.isoformat()}. Edit notes, not this dashboard.*",
        "",
        "## Start here",
        "",
    ]

    for note in ranked_notes(notes, 3):
        link = wikilink(note, stem_counts)
        reasons = " · ".join(needs_reason(note))
        lines.append(f"- {link} — {reasons}")

    lines.extend(["", "## Needs links", ""])
    no_out = sorted(
        (note for note in values if not note.outlinks),
        key=lambda note: (-len(note.inlinks), note.words),
    )[:10]
    for note in no_out:
        lines.append(
            f"- {wikilink(note, stem_counts)} — {note.words} words · "
            f"{len(note.inlinks)} backlinks · {note.status}"
        )

    lines.extend(["", "## Unlinked mentions", ""])
    for source, target, matched in mentions[:15]:
        lines.append(
            f"- {wikilink(source, stem_counts)} mentions \"{matched}\" — "
            f"link to {wikilink(target, stem_counts)}"
        )

    if semantic is not None:
        pairs = semantic.neighbor_pairs(
            notes,
            threshold=0.62,
            per_note=2,
            feedback=feedback,
        )[:12]
        if pairs:
            lines.extend(["", "## Semantic neighbors", ""])
            for left, right, score, evidence in pairs:
                lines.append(
                    f"- {wikilink(left, stem_counts)} ↔ {wikilink(right, stem_counts)} — "
                    f"{score:.2f} · \"{evidence}\""
                )

    lines.extend(["", "## Possible duplicates", ""])
    for left, right, score, reason in duplicates[:10]:
        lines.append(
            f"- {wikilink(left, stem_counts)} ≈ {wikilink(right, stem_counts)} — {reason}"
        )

    lines.extend(["", "## Empty notes", ""])
    for note in sorted(
        (item for item in values if not item.embedding_text.strip()),
        key=lambda item: item.stem.lower(),
    )[:10]:
        lines.append(f"- {wikilink(note, stem_counts)} — no prose (empty or template-only)")

    lines.extend(["", "## Short notes", ""])
    for note in sorted(values, key=lambda item: item.words)[:10]:
        lines.append(
            f"- {wikilink(note, stem_counts)} — {note.words} words · {len(note.outlinks)} links"
        )

    lines.extend(["", "## Neglected", ""])
    for note in sorted(values, key=lambda item: item.last_touched)[:10]:
        days = (TODAY - note.last_touched).days
        lines.append(
            f"- {wikilink(note, stem_counts)} — {days} days · {note.status}"
        )

    lines.extend(["", "## Recently improved", ""])
    recent = [
        note for note in values
        if (TODAY - note.last_touched).days <= 14
    ]
    recent.sort(key=lambda note: note.last_touched, reverse=True)
    for note in recent[:10]:
        lines.append(
            f"- {wikilink(note, stem_counts)} — touched {note.last_touched.isoformat()}"
        )

    payload = stats_payload(notes, mentions, duplicates)
    lines.extend(
        [
            "",
            "## Stats",
            "",
            f"- Notes: {payload['total']}",
            f"- With outgoing links: {payload['linked']} ({payload['linked_pct']}%)",
            f"- True orphans: {payload['orphans']}",
            f"- Unlinked-mention pairs: {payload['mentions']}",
            f"- Duplicate candidates: {payload['duplicates']}",
            "",
            "Status: "
            + ", ".join(f"{key}={value}" for key, value in payload["statuses"].items()),
            "",
        ]
    )
    return "\n".join(lines)


def write_dashboard(notes, mentions, duplicates, semantic=None, feedback=None):
    DASHBOARD.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD.write_text(
        build_dashboard(notes, mentions, duplicates, semantic, feedback),
        encoding="utf-8",
    )
    return DASHBOARD


def replace_body(path, new_body):
    raw = path.read_text(encoding="utf-8", errors="ignore")
    match = FM_RE.match(raw)
    prefix = raw[:match.end()] if match else ""
    if not new_body.endswith("\n"):
        new_body += "\n"
    path.write_text(prefix + new_body, encoding="utf-8")


def update_frontmatter(path, updates):
    raw = path.read_text(encoding="utf-8", errors="ignore")
    match = FM_RE.match(raw)
    if match:
        lines = match.group(1).splitlines()
        body = raw[match.end():]
        for key, value in updates.items():
            pattern = re.compile(rf"^{re.escape(key)}\s*:.*$")
            replaced = False
            for index, line in enumerate(lines):
                if pattern.match(line):
                    lines[index] = f"{key}: {value}"
                    replaced = True
                    break
            if not replaced:
                lines.append(f"{key}: {value}")
        new_raw = "---\n" + "\n".join(lines) + "\n---\n" + body
    else:
        fields = "\n".join(f"{key}: {value}" for key, value in updates.items())
        new_raw = f"---\n{fields}\n---\n\n{raw.lstrip()}"
    path.write_text(new_raw, encoding="utf-8")


def insert_inline(body, target, matched):
    pattern = re.compile(
        r"(?<![A-Za-z0-9])" + re.escape(matched) + r"(?![A-Za-z0-9])",
        re.IGNORECASE,
    )
    spans = protected_spans(body)
    for match in pattern.finditer(body):
        if in_spans(match.start(), spans):
            continue
        if match.group(0).lower() == target.stem.lower():
            replacement = f"[[{target.stem}]]"
        else:
            replacement = f"[[{target.stem}|{match.group(0)}]]"
        return body[:match.start()] + replacement + body[match.end():], True
    return body, False


def link_target(note):
    if note.title and note.title != note.stem:
        return f"[[{note.stem}|{note.title}]]"
    return f"[[{note.stem}]]"


def append_related(body, target, reason):
    line = f"- {link_target(target)} — {reason.strip() or 'related'}"
    if line in body:
        return body, False
    match = RELATED_RE.search(body)
    if match:
        insert_at = match.end()
        return body[:insert_at] + "\n" + line + body[insert_at:], True
    body = body.rstrip() + f"\n\n## Related\n{line}\n"
    return body, True


def title_tokens(note):
    return tokenize(f"{note.stem} {note.title}")


def rare_term_suggestions(note, candidates, limit=4):
    document_frequency = Counter()
    for other in candidates.values():
        document_frequency.update(other.tokens)
    total = max(len(candidates), 1)
    current_tokens = note.tokens
    current_title_tokens = title_tokens(note)
    title_vocabulary = set()
    for other in candidates.values():
        title_vocabulary.update(title_tokens(other))
    scored = []
    for rel, other in candidates.items():
        if rel == note.rel or rel in note.outlinks:
            continue
        shared = current_tokens & other.tokens
        other_title_tokens = title_tokens(other)
        title_shared = current_title_tokens & other_title_tokens
        other_title_shared = shared & other_title_tokens
        if not title_shared and not other_title_shared:
            continue
        relevant = title_shared | other_title_shared | (shared & current_title_tokens)
        relevant -= TITLE_GENERIC_WORDS
        if not relevant:
            continue
        score = 0.0
        for token in relevant:
            idf = math.log((total + 1) / (document_frequency[token] + 1)) + 1
            score += idf * (5 if token in other_title_tokens else 2)
        score += 8 * len(title_shared)
        if score < 12:
            continue
        top_terms = sorted(
            relevant,
            key=lambda token: document_frequency[token],
        )[:3]
        scored.append((score, other, top_terms))
    scored.sort(key=lambda item: -item[0])
    return [
        Suggestion(
            target=other,
            reason="shared terms: " + ", ".join(top_terms),
            kind="terms",
        )
        for _, other, top_terms in scored[:limit]
    ]


def title_pattern_suggestions(note, candidates, limit=2):
    words = re.findall(r"[a-z0-9']+", note.stem.lower())
    if len(words) < 2 or words[0] in TITLE_GENERIC_WORDS:
        return []
    results = []
    for other in candidates.values():
        if other.rel == note.rel or other.rel in note.outlinks:
            continue
        other_words = re.findall(r"[a-z0-9']+", other.stem.lower())
        if len(other_words) < 2:
            continue
        if words[:2] == other_words[:2]:
            reason = "same title opening: " + " ".join(words[:2])
        elif (
            words[0] == other_words[0]
            and len(words[0]) >= 5
            and len(words) <= 5
            and len(other_words) <= 5
        ):
            reason = "same topic word: " + words[0]
        else:
            continue
        results.append(Suggestion(target=other, reason=reason, kind="title"))
    results.sort(
        key=lambda item: (
            0 if item.reason.startswith("same title opening") else 1,
            item.target.stem.lower(),
        )
    )
    return results[:limit]


def map_suggestions(note, records):
    suggestions = []
    for rel, record in records.items():
        path = record.path
        if MAPS not in path.parents and "published/maps" not in rel:
            continue
        targets = set()
        for raw_target in record.links:
            target = raw_target.split("|")[0].split("#")[0].strip()
            if Path(target).stem.lower() == note.stem.lower():
                targets.add(rel)
                break
        if not targets:
            continue
        for raw_target in record.links:
            target = raw_target.split("|")[0].split("#")[0].strip()
            stem = Path(target).stem
            if stem and stem.lower() != note.stem.lower():
                suggestions.append((stem, record.stem))
    seen = set()
    results = []
    for stem, map_name in suggestions:
        if stem.lower() in seen:
            continue
        seen.add(stem.lower())
        results.append((stem, map_name))
    return results[:3]


SEMANTIC_MODEL = "all-MiniLM-L6-v2"
SEMANTIC_CACHE_VERSION = 3


def semantic_cache_path():
    cache_root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "tend"
    cache_root.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(str(VAULT).encode()).hexdigest()[:12]
    return cache_root / f"{digest}.npz"


def note_hash(note):
    payload = f"{note.stem}\n{note.title}\n{note.embedding_text}"
    return hashlib.sha1(payload.encode("utf-8", errors="ignore")).hexdigest()


def chunk_note(note):
    body = note.embedding_text.strip()
    if not body:
        return []
    sections = re.split(r"(?m)(?=^#{1,6}\s)", body)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        while len(section) > 1200:
            split = section.rfind("\n\n", 0, 1200)
            if split < 400:
                split = section.rfind(". ", 0, 1200)
                if split >= 400:
                    chunks.append(section[:split + 1].strip())
                    section = section[split + 1:].strip()
                    continue
            if split < 400:
                split = 1200
            chunks.append(section[:split].strip())
            section = section[split:].strip()
        if section:
            chunks.append(section)
    if not chunks:
        chunks = [body]
    return [f"{note.stem}\n{chunk}" for chunk in chunks[:16]]


def clean_evidence(text):
    return re.sub(r"\s+", " ", clean_embedding_text(text)).strip()[:180]


def embed_texts(texts):
    import numpy as np
    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

    embedder = ONNXMiniLM_L6_V2()
    vectors = []
    batch_size = 32
    for start in range(0, len(texts), batch_size):
        vectors.extend(embedder(texts[start:start + batch_size]))
    array = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    return np.divide(array, np.maximum(norms, 1e-9))


@dataclass
class SemanticIndex:
    vectors: object
    meta: dict

    def suggestions(self, note, candidates, limit=4, threshold=0.45, feedback=None):
        import numpy as np

        query_indices = self.meta["note_chunks"].get(note.rel, [])
        if not query_indices:
            return []
        query = self.vectors[query_indices]
        results = []
        for rel, target in candidates.items():
            if rel == note.rel or rel in note.outlinks:
                continue
            if feedback is not None and feedback.is_dismissed(note.rel, rel):
                continue
            target_indices = self.meta["note_chunks"].get(rel, [])
            if not target_indices:
                continue
            sims = query @ self.vectors[target_indices].T
            position = np.unravel_index(int(np.argmax(sims)), sims.shape)
            score = float(sims[position])
            if score < threshold or score > 0.985:
                continue
            chunk = self.meta["chunks"][target_indices[position[1]]]
            snippet = clean_evidence(chunk.split("\n", 1)[-1]) or clean_evidence(target.embedding_text)
            if not snippet:
                snippet = "(no prose text)"
            results.append(
                Suggestion(
                    target=target,
                    reason=f"semantic neighbor ({score:.2f})",
                    kind="semantic",
                    score=score,
                    evidence=snippet,
                )
            )
        results.sort(key=lambda item: -item.score)
        return results[:limit]

    def neighbor_pairs(self, notes, threshold=0.62, per_note=2, feedback=None):
        import numpy as np

        note_chunks = self.meta.get("note_chunks", {})
        ordered = sorted(note_chunks.items(), key=lambda item: item[1][0])
        contiguous = True
        offset = 0
        for _, indices in ordered:
            if indices != list(range(offset, offset + len(indices))):
                contiguous = False
                break
            offset += len(indices)

        if contiguous and ordered and len(self.vectors):
            starts = np.asarray([indices[0] for _, indices in ordered], dtype=np.int64)
            similarities = self.vectors @ self.vectors.T
            row_max = np.maximum.reduceat(similarities, starts, axis=1)
            note_similarities = np.maximum.reduceat(row_max, starts, axis=0)
            rels = [rel for rel, _ in ordered]
            pairs = []
            seen = set()
            for left_index, rel in enumerate(rels):
                note = notes.get(rel)
                if note is None:
                    continue
                added = 0
                for right_index in np.argsort(-note_similarities[left_index]):
                    if right_index == left_index:
                        continue
                    score = float(note_similarities[left_index, right_index])
                    if score < threshold:
                        break
                    other_rel = rels[right_index]
                    other = notes.get(other_rel)
                    if other is None or other_rel in note.outlinks:
                        continue
                    if feedback is not None and feedback.is_dismissed(rel, other_rel):
                        continue
                    key = tuple(sorted((rel, other_rel)))
                    if key in seen:
                        continue
                    left_chunks = note_chunks[rel]
                    right_chunks = note_chunks[other_rel]
                    block = similarities[np.ix_(left_chunks, right_chunks)]
                    position = np.unravel_index(int(np.argmax(block)), block.shape)
                    chunk = self.meta["chunks"][right_chunks[position[1]]]
                    evidence = clean_evidence(chunk.split("\n", 1)[-1]) or clean_evidence(other.embedding_text)
                    pairs.append((note, other, score, evidence or "(no prose text)"))
                    seen.add(key)
                    added += 1
                    if added >= per_note:
                        break
            pairs.sort(key=lambda item: -item[2])
            return pairs

        pairs = []
        seen = set()
        for note in notes.values():
            for suggestion in self.suggestions(note, notes, limit=per_note, threshold=threshold, feedback=feedback):
                key = tuple(sorted((note.rel, suggestion.target.rel)))
                if key in seen:
                    continue
                seen.add(key)
                pairs.append((note, suggestion.target, suggestion.score, suggestion.evidence))
        pairs.sort(key=lambda item: -item[2])
        return pairs


def build_semantic_index(notes, force=False):
    import numpy as np

    cache_path = semantic_cache_path()
    old_meta = {}
    old_vectors = None
    if cache_path.exists() and not force:
        try:
            data = np.load(cache_path, allow_pickle=True)
            raw_meta = data["meta"]
            if hasattr(raw_meta, "item"):
                raw_meta = raw_meta.item()
            old_meta = json.loads(raw_meta)
            old_vectors = data["vectors"]
            if (
                old_meta.get("model") != SEMANTIC_MODEL
                or old_meta.get("version") != SEMANTIC_CACHE_VERSION
            ):
                old_meta = {}
                old_vectors = None
        except Exception:
            old_meta = {}
            old_vectors = None

    new_meta = {
        "model": SEMANTIC_MODEL,
        "version": SEMANTIC_CACHE_VERSION,
        "hashes": {},
        "note_chunks": {},
        "chunks": [],
    }
    vector_list = []
    pending = []

    for rel, note in sorted(notes.items()):
        digest = note_hash(note)
        new_meta["hashes"][rel] = digest
        if not note.embedding_text.strip():
            continue
        cached_chunks = old_meta.get("note_chunks", {}).get(rel)
        if (
            old_vectors is not None
            and old_meta.get("hashes", {}).get(rel) == digest
            and cached_chunks
        ):
            indices = []
            for index in cached_chunks:
                if index >= len(old_vectors) or index >= len(old_meta.get("chunks", [])):
                    continue
                indices.append(len(vector_list))
                vector_list.append(old_vectors[index])
                new_meta["chunks"].append(old_meta["chunks"][index])
            if indices:
                new_meta["note_chunks"][rel] = indices
                continue
        pending.append(note)

    if pending:
        print(f"Embedding {len(pending)} changed note(s)...", file=sys.stderr)
        chunks_by_note = []
        all_chunks = []
        for note in pending:
            chunks = chunk_note(note)
            chunks_by_note.append((note, chunks))
            all_chunks.extend(chunks)
        if all_chunks:
            vectors = embed_texts(all_chunks)
            offset = 0
            for note, chunks in chunks_by_note:
                if not chunks:
                    continue
                indices = []
                for chunk in chunks:
                    indices.append(len(vector_list))
                    vector_list.append(vectors[offset])
                    new_meta["chunks"].append(chunk)
                    offset += 1
                new_meta["note_chunks"][note.rel] = indices

    vectors = np.asarray(vector_list, dtype=np.float32)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = cache_path.with_suffix(".tmp.npz")
    np.savez_compressed(temporary, vectors=vectors, meta=json.dumps(new_meta))
    temporary.replace(cache_path)
    return SemanticIndex(vectors=vectors, meta=new_meta)


def suggestions_for(note, notes, records, semantic=None, feedback=None):
    candidates = {
        rel: other
        for rel, other in notes.items()
        if is_suggestable(other.path) and not is_utility(other)
    }
    results = []
    seen = set()
    for target, matched in unlinked_mentions_for(note, candidates)[:5]:
        if feedback is not None and feedback.is_dismissed(note.rel, target.rel):
            continue
        results.append(
            Suggestion(
                target=target,
                reason=f'mentioned in this note: "{matched}"',
                kind="mention",
                matched=matched,
            )
        )
        seen.add(target.rel)
    for suggestion in title_pattern_suggestions(note, candidates):
        if suggestion.target.rel in seen:
            continue
        if feedback is not None and feedback.is_dismissed(note.rel, suggestion.target.rel):
            continue
        results.append(suggestion)
        seen.add(suggestion.target.rel)
    for stem, map_name in map_suggestions(note, records):
        for target in candidates.values():
            if target.stem.lower() != stem.lower() or target.rel in seen:
                continue
            if feedback is not None and feedback.is_dismissed(note.rel, target.rel):
                continue
            results.append(
                Suggestion(
                    target=target,
                    reason=f"both in [[{map_name}]]",
                    kind="map",
                )
            )
            seen.add(target.rel)
            break
    scoped_candidates = {
        rel: other
        for rel, other in candidates.items()
        if is_scoped(other.path)
    }
    for suggestion in rare_term_suggestions(note, scoped_candidates):
        if suggestion.target.rel in seen:
            continue
        if feedback is not None and feedback.is_dismissed(note.rel, suggestion.target.rel):
            continue
        results.append(suggestion)
        seen.add(suggestion.target.rel)
    if semantic is not None:
        for suggestion in semantic.suggestions(note, candidates, limit=4, feedback=feedback):
            if suggestion.target.rel not in seen:
                results.append(suggestion)
                seen.add(suggestion.target.rel)
    return results[:10]


def show_note(note):
    reasons = " · ".join(needs_reason(note))
    if console:
        content = (
            f"[bold]{note.stem}[/bold]\n"
            f"{note.words} words · {note.status} · "
            f"{len(note.outlinks)} out · {len(note.inlinks)} in\n"
            f"[dim]{note.rel}[/dim]\n"
            f"[yellow]{reasons}[/yellow]"
        )
        console.print(Panel(content, box=box.ROUNDED, border_style="cyan"))
    else:
        print(f"\n{note.stem}")
        print(f"  {note.words} words · {note.status} · {len(note.outlinks)} out · {len(note.inlinks)} in")
        print(f"  {note.rel}")
        print(f"  {reasons}")


def show_suggestions(suggestions, stem_counts):
    if not suggestions:
        print("  No suggestions found.")
        return
    for index, suggestion in enumerate(suggestions, 1):
        print(
            f"  {index}. {wikilink(suggestion.target, stem_counts)} — "
            f"{suggestion.reason}"
        )
        if suggestion.kind == "semantic" and suggestion.evidence:
            print(f"     \"{suggestion.evidence[:150]}\"")


def prompt(text, default=""):
    try:
        value = input(text).strip()
    except (EOFError, KeyboardInterrupt):
        return default
    return value or default


def ask_status(note):
    current = note.status
    print(f"  Status is {current}.")
    answer = prompt("  [s]eed [g]seedling [e]vergreen [a]rchive [k]eep > ", "k").lower()
    mapping = {
        "s": "seed",
        "g": "seedling",
        "e": "evergreen",
        "a": "archived",
    }
    if answer in mapping:
        update_frontmatter(note.path, {"status": mapping[answer]})
        note.status = mapping[answer]
        print(f"  status: {note.status}")


def ask_improved(note):
    print("  What improved? [l]ink [e]xample [c]laim [n]othing")
    answer = prompt("  > ", "n").lower()
    if answer in {"l", "e", "c"}:
        update_frontmatter(note.path, {"reviewed": TODAY.isoformat()})
        note.reviewed = TODAY
        print("  marked reviewed")
        ask_status(note)
        return True
    print("  no change recorded")
    return False


def open_note(note):
    editor = os.environ.get("TEND_EDITOR", DEFAULT_EDITOR)
    if editor in {"obsidian", "obsidian-uri"}:
        vault_name = VAULT.name
        uri = (
            "obsidian://open?vault="
            + urllib.parse.quote(vault_name)
            + "&file="
            + urllib.parse.quote(note.rel)
        )
        subprocess.run(["xdg-open", uri], check=False)
        prompt("  Press Enter when you are done in Obsidian > ")
        return
    command = shlex.split(editor)
    if not command:
        print(f"  Open this file: {note.path}")
        return
    try:
        subprocess.run(command + [str(note.path)], check=False)
    except FileNotFoundError:
        fallback = os.environ.get("EDITOR")
        if fallback:
            subprocess.run(shlex.split(fallback) + [str(note.path)], check=False)
        else:
            print(f"  Could not launch {command[0]}. Open this file: {note.path}")


def do_link(note, all_notes, records, semantic=None, feedback=None):
    feedback = feedback or FeedbackStore.load()
    stem_counts = Counter(other.stem.lower() for other in all_notes.values())
    while True:
        suggestions = suggestions_for(note, all_notes, records, semantic, feedback)
        show_suggestions(suggestions, stem_counts)
        if not suggestions:
            return False
        choice = prompt("  Choose a number, d <number> to dismiss, Enter to cancel > ")
        if not choice:
            return False
        if choice.lower().startswith("d"):
            number = choice[1:].strip()
            if not number.isdigit():
                print("  Use d <number>, for example: d 2")
                continue
            index = int(number) - 1
            if index < 0 or index >= len(suggestions):
                print("  No suggestion at that number.")
                continue
            suggestion = suggestions[index]
            feedback.dismiss(
                note.rel,
                suggestion.target.rel,
                kind=suggestion.kind,
                score=suggestion.score,
                evidence=suggestion.evidence or suggestion.reason,
            )
            print(f"  dismissed {wikilink(suggestion.target, stem_counts)} (both directions)")
            continue
        if not choice.isdigit():
            return False
        index = int(choice) - 1
        if index < 0 or index >= len(suggestions):
            return False
        suggestion = suggestions[index]
        target = suggestion.target
        break
    print(f"  Selected {wikilink(target, stem_counts)}")
    mode = prompt("  [1] link in place [2] add to Related [3] cancel > ", "3")
    if mode == "1":
        if not suggestion.matched:
            print("  No inline mention to replace; using Related instead.")
            mode = "2"
        else:
            new_body, changed = insert_inline(note.body, target, suggestion.matched)
            if not changed:
                print("  Could not find the mention outside protected text.")
                mode = "2"
            else:
                replace_body(note.path, new_body)
                note.body = new_body
                update_frontmatter(note.path, {"reviewed": TODAY.isoformat()})
                note.reviewed = TODAY
                print(f"  linked in place: {link_target(target)}")
                return True
    if mode == "2":
        default_reason = suggestion.reason
        reason = prompt(f"  Reason [{default_reason}] > ", default_reason)
        new_body, changed = append_related(note.body, target, reason)
        if changed:
            replace_body(note.path, new_body)
            note.body = new_body
            update_frontmatter(note.path, {"reviewed": TODAY.isoformat()})
            note.reviewed = TODAY
            print(f"  added to Related: {link_target(target)}")
            return True
        print("  Link already present.")
    return False


def show_duplicates_for(note, duplicates):
    matches = [
        (left, right, score, reason)
        for left, right, score, reason in duplicates
        if note.rel in {left.rel, right.rel}
    ]
    if not matches:
        print("  No duplicate candidates for this note.")
        return
    for left, right, score, reason in matches[:5]:
        other = right if left.rel == note.rel else left
        print(f"  possible merge: [[{other.stem}]] — {reason}")


def session(notes, records, all_notes, limit=3, links_only=False, semantic=None, feedback=None):
    mentions = all_unlinked_mentions(notes)
    duplicates = duplicate_pairs(notes)
    write_dashboard(notes, mentions, duplicates, semantic, feedback)

    ranked = ranked_notes(notes)
    if links_only:
        ranked = sorted(
            (note for note in notes.values() if not note.outlinks),
            key=lambda note: (-len(note.inlinks), note.words),
        )
    candidates = ranked[:limit]
    if not candidates:
        print("No notes to tend.")
        return

    print(f"\nTending {len(candidates)} note(s). q to quit.\n")
    for position, note in enumerate(candidates, 1):
        print(f"[{position}/{len(candidates)}]")
        show_note(note)
        action = prompt(
            "  [o]pen [l]ink [m]erge [a]rchive [s]kip [q]uit > ",
            "s",
        ).lower()
        if action == "q":
            break
        if action == "o":
            open_note(note)
            ask_improved(note)
        elif action == "l":
            do_link(note, all_notes, records, semantic, feedback)
        elif action == "m":
            show_duplicates_for(note, duplicates)
        elif action == "a":
            if prompt(f"  Archive {note.stem}? [y/N] > ", "n").lower() == "y":
                update_frontmatter(note.path, {"status": "archived", "reviewed": TODAY.isoformat()})
                note.status = "archived"
                note.reviewed = TODAY
                print("  archived")
        else:
            print("  skipped")

    notes, records, all_notes = load_vault()
    if semantic is not None:
        semantic = build_semantic_index(notes)
    mentions = all_unlinked_mentions(notes)
    duplicates = duplicate_pairs(notes)
    path = write_dashboard(notes, mentions, duplicates, semantic, feedback)
    print(f"\nDashboard refreshed: {path}")


def triage(notes, records, all_notes, limit=10, semantic=None, feedback=None):
    candidates = sorted(
        (note for note in notes.values() if note.status != "archived"),
        key=lambda note: (note.words, note.last_touched),
    )[:limit]
    if not candidates:
        print("No notes to triage.")
        return

    mentions = all_unlinked_mentions(notes)
    duplicates = duplicate_pairs(notes)
    print(f"\nTriage: {len(candidates)} note(s). q to quit.\n")
    for position, note in enumerate(candidates, 1):
        print(f"[{position}/{len(candidates)}]")
        show_note(note)
        action = prompt(
            "  [k]eep as seed [m]erge [a]rchive [d]elete [s]kip [q]uit > ",
            "s",
        ).lower()
        if action == "q":
            break
        if action == "k":
            update_frontmatter(note.path, {"status": "seed"})
            note.status = "seed"
            print("  kept as seed")
        elif action == "m":
            show_duplicates_for(note, duplicates)
        elif action == "a":
            update_frontmatter(note.path, {"status": "archived", "reviewed": TODAY.isoformat()})
            note.status = "archived"
            note.reviewed = TODAY
            print("  archived")
        elif action == "d":
            if prompt(f"  Delete {note.stem}? [y/N] > ", "n").lower() == "y":
                trash = VAULT / ".trash" / f"tend-{TODAY.isoformat()}"
                trash.mkdir(parents=True, exist_ok=True)
                target = trash / note.path.name
                shutil.move(str(note.path), str(target))
                print(f"  moved to {target}")
        else:
            print("  skipped")

    notes, records, all_notes = load_vault()
    if semantic is not None:
        semantic = build_semantic_index(notes)
    mentions = all_unlinked_mentions(notes)
    duplicates = duplicate_pairs(notes)
    path = write_dashboard(notes, mentions, duplicates, semantic, feedback)
    print(f"\nDashboard refreshed: {path}")


def suggest_for_query(query, notes, records, all_notes, semantic=None, feedback=None):
    values = list(notes.values())
    exact = [note for note in values if note.stem.lower() == query.lower()]
    if exact:
        note = exact[0]
    else:
        matches = [note for note in values if query.lower() in note.stem.lower()]
        if not matches:
            matches = difflib.get_close_matches(query, [note.stem for note in values], n=1, cutoff=0.4)
            matches = [note for note in values if note.stem in matches]
        if not matches:
            print(f"No note matching {query!r}.")
            return
        note = matches[0]

    suggestions = suggestions_for(note, all_notes, records, semantic, feedback)
    stem_counts = Counter(other.stem.lower() for other in all_notes.values())
    show_note(note)
    print("\nSuggestions:")
    show_suggestions(suggestions, stem_counts)


def run_review():
    script = VAULT / "scripts" / "incremental.py"
    if not script.exists():
        print(f"Legacy review script not found: {script}")
        return
    subprocess.run([sys.executable, str(script)], check=False)


def main():
    parser = argparse.ArgumentParser(description="Tend personal Obsidian notes.")
    parser.add_argument("--vault", help="Path to the Obsidian vault")
    parser.add_argument("--stats", action="store_true", help="Print a read-only audit")
    parser.add_argument("--refresh", action="store_true", help="Rebuild Reflections/Tending.md")
    parser.add_argument("--links", action="store_true", help="Session focused on notes without links")
    parser.add_argument("--triage", action="store_true", help="Triage a batch of short notes")
    parser.add_argument("--review", action="store_true", help="Run the legacy SM-2 review script")
    parser.add_argument("--suggest", metavar="NOTE", help="Show link suggestions for one note")
    parser.add_argument("--limit", type=int, default=3, help="Notes per session")
    parser.add_argument(
        "--semantic",
        dest="semantic",
        action="store_true",
        default=None,
        help="Enable local embedding-based link suggestions (default)",
    )
    parser.add_argument(
        "--no-semantic",
        dest="semantic",
        action="store_false",
        help="Disable local embedding-based link suggestions",
    )
    parser.add_argument("--reindex", action="store_true", help="Rebuild the semantic embedding cache")
    parser.add_argument("--index-info", action="store_true", help="Show semantic index cache details")
    parser.add_argument("--dismissed", action="store_true", help="List dismissed link pairs")
    parser.add_argument(
        "--undismiss",
        nargs=2,
        metavar=("SOURCE", "TARGET"),
        help="Restore a dismissed link pair",
    )
    parser.add_argument("--editor", help="Editor command, e.g. 'code --wait' or 'obsidian'")
    args = parser.parse_args()
    if args.semantic is None:
        args.semantic = os.environ.get("TEND_SEMANTIC", "1") != "0"
    if args.reindex or args.index_info:
        args.semantic = True

    if args.editor:
        os.environ["TEND_EDITOR"] = args.editor

    configure(args.vault)
    if not VAULT.exists():
        print(f"Vault not found: {VAULT}")
        return 1

    notes, records, all_notes = load_vault()
    if not notes:
        print(f"No personal notes found under {REFLECTIONS} and {UNFINISHED}.")
        return 1

    if args.review:
        run_review()
        return 0

    feedback = FeedbackStore.load()

    if args.dismissed:
        if not feedback.dismissed:
            print("No dismissed link pairs.")
        for item in sorted(feedback.dismissed.values(), key=lambda value: value["source"]):
            print(
                f"{item['source']} <-> {item['target']} "
                f"({item.get('kind', 'unknown')}, {item.get('dismissed_at', '')})"
            )
        return 0

    if args.undismiss:
        def find_note(value):
            if value in all_notes:
                return all_notes[value]
            matches = [
                note
                for note in all_notes.values()
                if note.stem.lower() == value.lower() or note.rel.lower() == value.lower()
            ]
            return matches[0] if len(matches) == 1 else None

        source = find_note(args.undismiss[0])
        target = find_note(args.undismiss[1])
        if not source or not target:
            print("Could not resolve both notes for --undismiss.")
            return 1
        if feedback.undismiss(source.rel, target.rel):
            print(f"Restored {source.stem} <-> {target.stem}.")
        else:
            print("That pair was not dismissed.")
        return 0

    mentions = all_unlinked_mentions(notes)
    duplicates = duplicate_pairs(notes)

    if args.stats and not args.index_info:
        print_stats(notes, mentions, duplicates)
        return 0

    semantic = None
    if args.semantic:
        try:
            semantic = build_semantic_index(notes, force=args.reindex)
        except Exception as exc:
            print(f"Semantic mode unavailable: {exc}", file=sys.stderr)

    if args.index_info:
        if semantic is None:
            print("Semantic index unavailable.")
            return 1
        print(f"Index: {semantic_cache_path()}")
        print(f"Model: {semantic.meta.get('model')}")
        print(f"Notes: {len(semantic.meta.get('note_chunks', {}))}")
        print(f"Chunks: {len(semantic.meta.get('chunks', []))}")
        return 0

    if args.suggest:
        suggest_for_query(args.suggest, notes, records, all_notes, semantic, feedback)
        return 0

    path = write_dashboard(notes, mentions, duplicates, semantic, feedback)
    if args.refresh:
        print(f"Dashboard refreshed: {path}")
        return 0

    if args.triage:
        triage(notes, records, all_notes, limit=args.limit, semantic=semantic, feedback=feedback)
        return 0

    session(notes, records, all_notes, limit=args.limit, links_only=args.links, semantic=semantic, feedback=feedback)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
