#!/usr/bin/env python3
"""Merge two novels_digest databases with 'longest wins' conflict resolution.

Usage:
    merge_novels.py <source.db> <target.db> [--dry-run]

Merge logic:
    - Books only in source: copied to target
    - Books only in target: kept as-is
    - Books in both (by title):
        - Source has more chapters → replace target's chapters, update metadata
        - Target has more chapters → keep target, append any missing chapter URLs
        - Equal chapter counts → target untouched
"""

import argparse
import sqlite3
import sys

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE,
    start_url TEXT,
    selector TEXT,
    next_selector TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    url TEXT UNIQUE,
    title TEXT,
    html_content TEXT,
    chapter_order INTEGER,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(book_id) REFERENCES books(id)
);
"""


def init_db(conn):
    conn.executescript(SCHEMA)


def get_books(conn):
    return {row[1]: row for row in conn.execute(
        "SELECT id, title, start_url, selector, next_selector, added_at FROM books"
    ).fetchall()}


def get_chapter_count(conn, book_id):
    return conn.execute(
        "SELECT COUNT(*) FROM chapters WHERE book_id = ?", (book_id,)
    ).fetchone()[0]


def get_chapter_urls(conn, book_id):
    return {row[0] for row in conn.execute(
        "SELECT url FROM chapters WHERE book_id = ?", (book_id,)
    ).fetchall()}


def get_chapters_by_title(conn, title):
    return conn.execute(
        """SELECT c.url, c.title, c.html_content, c.chapter_order
           FROM chapters c JOIN books b ON c.book_id = b.id
           WHERE b.title = ? ORDER BY c.chapter_order""",
        (title,)
    ).fetchall()


def merge(source_path, target_path, dry_run=False):
    source_conn = sqlite3.connect(source_path)
    target_conn = sqlite3.connect(target_path)

    init_db(target_conn)

    source_books = get_books(source_conn)
    target_books = get_books(target_conn)

    stats = {"books_added": 0, "books_replaced": 0, "books_extended": 0,
             "chapters_added": 0, "chapters_skipped": 0}

    for title, s_book in source_books.items():
        s_id, _, s_url, s_sel, s_next, _ = s_book
        s_count = get_chapter_count(source_conn, s_id)

        if title not in target_books:
            # New book — copy everything
            print(f"  [ADD] '{title}' ({s_count} chapters)")
            if not dry_run:
                cur = target_conn.execute(
                    "INSERT INTO books (title, start_url, selector, next_selector) VALUES (?, ?, ?, ?)",
                    (title, s_url, s_sel, s_next)
                )
                t_book_id = cur.lastrowid
                new_order = 0
                for url, ch_title, html, _order in get_chapters_by_title(source_conn, title):
                    new_order += 1
                    target_conn.execute(
                        "INSERT OR IGNORE INTO chapters (book_id, url, title, html_content, chapter_order) VALUES (?, ?, ?, ?, ?)",
                        (t_book_id, url, ch_title, html, new_order)
                    )
                    stats["chapters_added"] += 1
            stats["books_added"] += 1
        else:
            # Book exists — compare chapter counts
            t_id = target_books[title][0]
            t_count = get_chapter_count(target_conn, t_id)

            if s_count > t_count:
                # Source wins — replace target's chapters
                print(f"  [REPLACE] '{title}' source={s_count} > target={t_count}")
                if not dry_run:
                    target_conn.execute("DELETE FROM chapters WHERE book_id = ?", (t_id,))
                    # Update metadata in case selectors changed
                    target_conn.execute(
                        "UPDATE books SET start_url = ?, selector = ?, next_selector = ? WHERE id = ?",
                        (s_url, s_sel, s_next, t_id)
                    )
                    for url, ch_title, html, order in get_chapters_by_title(source_conn, title):
                        target_conn.execute(
                            "INSERT OR IGNORE INTO chapters (book_id, url, title, html_content, chapter_order) VALUES (?, ?, ?, ?, ?)",
                            (t_id, url, ch_title, html, order)
                        )
                        stats["chapters_added"] += 1
                stats["books_replaced"] += 1
            elif s_count == t_count:
                print(f"  [KEEP]   '{title}' both have {s_count} chapters")
                stats["chapters_skipped"] += s_count
            else:
                # Target wins — but append any missing chapter URLs
                print(f"  [EXTEND] '{title}' target={t_count} > source={s_count}")
                if not dry_run:
                    existing_urls = get_chapter_urls(target_conn, t_id)
                    max_order = target_conn.execute(
                        "SELECT COALESCE(MAX(chapter_order), 0) FROM chapters WHERE book_id = ?", (t_id,)
                    ).fetchone()[0]
                    for url, ch_title, html, order in get_chapters_by_title(source_conn, title):
                        if url not in existing_urls:
                            max_order += 1
                            target_conn.execute(
                                "INSERT OR IGNORE INTO chapters (book_id, url, title, html_content, chapter_order) VALUES (?, ?, ?, ?, ?)",
                                (t_id, url, ch_title, html, max_order)
                            )
                            stats["chapters_added"] += 1
                        else:
                            stats["chapters_skipped"] += 1
                stats["books_extended"] += 1

    if not dry_run:
        target_conn.commit()

    source_conn.close()
    target_conn.close()

    print(f"\nMerge complete:")
    print(f"  Books added:     {stats['books_added']}")
    print(f"  Books replaced:  {stats['books_replaced']}")
    print(f"  Books extended:  {stats['books_extended']}")
    print(f"  Chapters added:  {stats['chapters_added']}")
    print(f"  Chapters kept:   {stats['chapters_skipped']}")


def main():
    parser = argparse.ArgumentParser(description="Merge two novels_digest databases")
    parser.add_argument("source", help="Source database path")
    parser.add_argument("target", help="Target database path (will be modified)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without modifying target")
    args = parser.parse_args()

    print(f"Merging: {args.source} -> {args.target}")
    if args.dry_run:
        print("(dry run — no changes)\n")
    merge(args.source, args.target, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
