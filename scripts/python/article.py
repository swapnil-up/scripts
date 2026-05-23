import os
import sqlite3
import uuid
import subprocess
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from calibre_utils import sync_with_calibre

# Establish the persistent path in ~/github/knowledge
BASE_DIR = os.path.expanduser("~/github/knowledge")
os.makedirs(BASE_DIR, exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "articles_digest.db")
EPUB_PATH = os.path.join(BASE_DIR, "articles_digest.epub")
CALIBRE_BOOK_TITLE = "My Web Articles Digest"

def init_db():
    """Initializes the database inside the designated directory."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                html_content TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

def fetch_wikipedia_article(url):
    """Custom extractor to strip Wikipedia-specific clutter for e-readers."""
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    title_tag = soup.find('h1', id='firstHeading') or soup.find('h1') or soup.find('title')
    title = title_tag.get_text().strip() if title_tag else "Untitled Wikipedia Article"
    
    content_block = soup.select_one('#mw-content-text .mw-parser-output')
    if not content_block:
        raise ValueError("Could not extract main Wikipedia content block.")
        
    # Drop sidebars, maps, infoboxes, and references
    for element in content_block.select('.infobox, .vertical-navbox, .thumb, .floatright, .metadata'):
        element.decompose()
    for toc in content_block.select('#toc, .toc'):
        toc.decompose()
    for edit_section in content_block.select('.mw-editsection'):
        edit_section.decompose()
    for ref in content_block.select('.reference'):
        ref.decompose()

    clean_html = f"<html><body><h1>{title}</h1>{content_block.prettify()}</body></html>"
    return title, clean_html

def fetch_generic_article(url, selector):
    """Standard fallback extractor for general blogs and websites."""
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    title_tag = soup.find('h1') or soup.find('title')
    title = title_tag.get_text().strip() if title_tag else "Untitled Article"
    
    content_block = soup.select_one(selector)
    if not content_block:
        raise ValueError(f"Could not find content with selector: '{selector}'")
        
    clean_html = f"<html><body><h1>{title}</h1>{content_block.prettify()}</body></html>"
    return title, clean_html

def fetch_and_store(url, selector=None):
    """Routing logic: detects if URL is Wikipedia, skips manual inputs if so,
    and prevents duplicates.
    """
    # Check if the URL is already tracking in our database to skip request overhead entirely
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT title FROM articles WHERE url = ?", (url,))
        existing = cursor.fetchone()
        if existing:
            print(f"Skipped: Article '{existing[0]}' is already present in your digest database.")
            return False

    # Extract based on URL footprint
    if "wikipedia.org" in url.lower():
        print("Wikipedia URL detected. Running customized extractor parser automatically...")
        title, html_content = fetch_wikipedia_article(url)
        # Skip preview for Wikipedia as it's a known format
        confirm = 'y'
    else:
        while True:
            if not selector:
                selector = input("Enter CSS selector for text block (e.g., 'article', '#content'): ").strip()
                if not selector:
                    raise ValueError("A CSS selector is required for non-Wikipedia websites.")
            
            try:
                title, html_content = fetch_generic_article(url, selector)
                
                # Preview logic
                soup = BeautifulSoup(html_content, 'html.parser')
                text_preview = soup.get_text().strip()
                print("\n" + "="*40)
                print(f"PREVIEW (Title: {title})")
                print("-" * 40)
                print(text_preview[:500] + "..." if len(text_preview) > 500 else text_preview)
                print("="*40)
                
                confirm = input("\nDoes this look correct? (y/n/retry): ").strip().lower()
                if confirm == 'y':
                    break
                elif confirm == 'n':
                    print("Aborting.")
                    return False
                else:
                    selector = None # Reset selector to prompt again
                    continue
            except Exception as e:
                print(f"Extraction failed: {e}")
                selector = None # Prompt for a new selector
                confirm_retry = input("Try a different selector? (y/n): ").strip().lower()
                if confirm_retry != 'y':
                    return False
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO articles (url, title, html_content) VALUES (?, ?, ?)",
            (url, title, html_content)
        )
        print(f"Stored successfully: {title}")
        return True

def compile_epub_from_db():
    """Rebuilds the entire EPUB structure fresh from SQLite records."""
    print("Compiling fresh EPUB archive from database records...")
    book = epub.EpubBook()
    book.set_identifier("web_digest_master_archive")
    book.set_title(CALIBRE_BOOK_TITLE)
    book.set_language("en")
    book.add_author("Article Scraper Pipeline")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT id, title, html_content FROM articles ORDER BY id ASC")
        rows = cursor.fetchall()

    if not rows:
        print("No articles found in database to compile.")
        return False

    spine = ['nav']
    for row_id, title, html_content in rows:
        file_name = f"article_{row_id}.xhtml"
        chapter = epub.EpubHtml(title=title, file_name=file_name, lang='en')
        chapter.content = html_content
        
        book.add_item(chapter)
        book.toc.append(chapter)
        spine.append(chapter)

    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    if os.path.exists(EPUB_PATH):
        os.remove(EPUB_PATH)
        
    epub.write_epub(EPUB_PATH, book)
    print(f"New clean EPUB generated with {len(rows)} chapters at: {EPUB_PATH}")
    return True


def main():
    init_db()
    print("=== SQLite to Calibre Digest Pipeline ===")
    url = input("Enter article URL: ").strip()
    if not url:
        print("URL cannot be empty.")
        return
        
    try:
        # fetch_and_store returns True if a new article was added, False if skipped
        inserted = fetch_and_store(url)
        if inserted:
            if compile_epub_from_db():
                sync_with_calibre(CALIBRE_BOOK_TITLE, EPUB_PATH)
        else:
            print("No new content added. Recompilation skipped.")
    except Exception as e:
        print(f"Process broke down: {e}")

if __name__ == "__main__":
    main()