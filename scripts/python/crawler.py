import os
import sqlite3
import time
import subprocess
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from ebooklib import epub
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from calibre_utils import sync_with_calibre

# Persistence configuration
BASE_DIR = os.path.expanduser("~/github/knowledge")
os.makedirs(BASE_DIR, exist_ok=True)
DB_PATH = os.path.join(BASE_DIR, "novels_digest.db")
USER_DATA_DIR = os.path.join(BASE_DIR, ".browser_profile")

def init_db():
    """Initializes the database for multi-chapter books."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                start_url TEXT,
                selector TEXT,
                next_selector TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Schema migration: Add next_selector if it doesn't exist
        try:
            conn.execute("ALTER TABLE books ADD COLUMN next_selector TEXT")
        except sqlite3.OperationalError:
            pass # Column already exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                url TEXT UNIQUE,
                title TEXT,
                html_content TEXT,
                chapter_order INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(book_id) REFERENCES books(id)
            )
        """)

def clean_html_content(raw_html):
    """Strips out structural navigation nodes, ads, and code scripts."""
    soup = BeautifulSoup(raw_html, "html.parser")
    garbage_selectors = [
        "script", "style", "iframe", "ins", "button", 
        ".chapter-nav", ".ads", ".sharedaddy", ".wpcnt",
        "nav", "header", "footer"
    ]
    for selector in garbage_selectors:
        for tag in soup.select(selector):
            tag.decompose()
    return str(soup)



def save_diagnostic(page, name):
    """Saves a screenshot and HTML dump for debugging."""
    diag_dir = os.path.join(BASE_DIR, "debug")
    os.makedirs(diag_dir, exist_ok=True)
    ts = int(time.time())
    
    ss_path = os.path.join(diag_dir, f"{name}_{ts}.png")
    html_path = os.path.join(diag_dir, f"{name}_{ts}.html")
    
    try:
        page.screenshot(path=ss_path)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page.content())
        print(f"  [Diagnostic] Saved screenshot to {ss_path}")
        print(f"  [Diagnostic] Saved HTML to {html_path}")
    except Exception as e:
        print(f"  [Diagnostic] Failed to save diagnostics: {e}")

def get_next_url(page, current_url, next_selector=None):
    """Extracts the 'Next' link using common selectors, avoiding 'Previous' links."""
    # Ensure page is at least somewhat settled
    try:
        page.wait_for_load_state("domcontentloaded", timeout=5000)
    except:
        pass

    # Some sites (RoyalRoad) might need a scroll to trigger visibility or just for lazy loading
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(0.5)
    except:
        pass

    candidates = []
    if next_selector:
        candidates.append(page.locator(next_selector))
    
    # Aggressive standard-compliant selectors
    candidates.extend([
        page.locator("link[rel='next']"),
        page.locator("a[rel='next']")
    ])
    
    # Aggressive AO3-specific selectors
    if "archiveofourown.org" in current_url:
        candidates.extend([
            page.locator("li.chapter.next a"),
            page.locator("li.next a"),
            page.locator("a:has-text('Next Chapter')"),
            page.locator("span.next a")
        ])
        
    # RoyalRoad specific selectors
    if "royalroad.com" in current_url:
        candidates.extend([
            page.locator("a.btn-primary:has-text('Next')"),
            page.locator("a.btn-primary:has-text('Chapter')"),
            page.locator(".nav-buttons a:has-text('Next')"),
            page.locator("a:has-text('Next Chapter')")
        ])

    # General heuristics
    candidates.extend([
        page.locator("a[rel='next']"),
        page.locator("[title*='ext chapter']"), 
        page.locator("[title*='ext Chapter']"),
        page.locator("a.next_page"),
        page.locator("a.next-page"),
        page.locator("a:has-text('Next')"),
        page.locator("button:has-text('Next')")
    ])
    
    for i, candidate_locator in enumerate(candidates):
        try:
            count = candidate_locator.count()
            for j in range(count):
                el = candidate_locator.nth(j)
                
                # Check for href first (works for link[rel='next'])
                href = el.get_attribute("href")
                if not href: continue

                # Be more patient for visibility only if it's an interactive element
                tag_name = el.evaluate("el => el.tagName.toLowerCase()")
                if tag_name != "link":
                    if not el.is_visible(timeout=3000):
                        continue
                        
                    text = el.inner_text().strip().lower()
                    # Hard-exclude common 'Previous' patterns
                    if any(x in text for x in ["prev", "back", "上一章", "previous"]):
                        continue
                    if any(x in href.lower() for x in ["prev", "back", "previous"]):
                        continue
                
                if href:
                    parsed_url = urlparse(current_url)
                    base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    new_url = base_domain + href if href.startswith("/") else href
                    
                    # Smart AO3 handling: Append view_adult=true
                    if "archiveofourown.org" in new_url and "view_adult=true" not in new_url:
                        base_part, *fragment = new_url.split("#")
                        sep = "&" if "?" in base_part else "?"
                        new_url = f"{base_part}{sep}view_adult=true"
                        if fragment:
                            new_url += f"#{fragment[0]}"

                    # Strip fragments for comparison
                    clean_new = new_url.split("#")[0].split("?")[0]
                    clean_current = current_url.split("#")[0].split("?")[0]
                    
                    if clean_new != clean_current:
                        print(f"  Found Next Link: {new_url}")
                        return new_url
        except Exception:
            continue
    
    # Last resort: JS-click navigation for SPA sites (Next.js, etc.)
    for selector in ["[title='Next chapter']", "[aria-label='Next chapter']",
                     "[title='Next Chapter']", "[aria-label='Next Chapter']"]:
        try:
            locator = page.locator(selector)
            if locator.count() > 0 and locator.first.is_visible(timeout=2000):
                old_url = page.url
                locator.first.click()
                try:
                    page.wait_for_function(f"window.location.href !== '{old_url}'", timeout=10000)
                except:
                    pass
                new_url = page.url
                clean_new = new_url.split("#")[0].split("?")[0]
                clean_old = old_url.split("#")[0].split("?")[0]
                if clean_new != clean_old:
                    print(f"  Found Next Link (JS): {new_url}")
                    return new_url
        except Exception:
            continue
    
    return None

def handle_ao3_gate(page):
    """Checks for and bypasses AO3 age/tos gate efficiently."""
    if "archiveofourown.org" not in page.url:
        return False

    gate_found = False
    try:
        # Check for TOS/Consent Gate
        tos_agree = page.locator("#tos_agree")
        if tos_agree.count() > 0 and tos_agree.is_visible(timeout=2000):
            print("  AO3 TOS Gate detected. Accepting...")
            tos_agree.check(force=True)
            data_agree = page.locator("#data_processing_agree")
            if data_agree.count() > 0 and data_agree.is_visible(timeout=500):
                data_agree.check(force=True)
            
            accept_btn = page.locator("#accept_tos")
            if accept_btn.count() > 0 and accept_btn.is_visible(timeout=500):
                accept_btn.click(force=True)
                page.wait_for_load_state("domcontentloaded")
                gate_found = True

        # Check for Age Gate (Proceed button)
        proceed_btn = page.locator("input[name='commit'][value='Proceed']")
        if proceed_btn.count() > 0 and proceed_btn.is_visible(timeout=2000):
            print("  AO3 Age Gate detected. Proceeding...")
            proceed_btn.click(force=True)
            page.wait_for_load_state("domcontentloaded")
            gate_found = True
            
        if gate_found:
            time.sleep(1) # Settle
    except Exception as e:
        print(f"  Error handling AO3 gate: {e}")
    
    return gate_found

def scrape_incremental(book_id, start_url, selector, next_selector=None, target_chapter=None):
    """Scrapes new chapters starting from the provided URL until target_chapter is reached."""
    new_chapters_count = 0
    current_url = start_url
    visited_this_session = set()
    
    # Find current total chapters
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM chapters WHERE book_id = ?", (book_id,))
        current_total = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT MAX(chapter_order) FROM chapters WHERE book_id = ?", (book_id,))
        max_order = cursor.fetchone()[0] or 0

    if target_chapter and current_total >= target_chapter:
        print(f"Target chapter {target_chapter} already reached (Current: {current_total}).")
        return 0

    with sync_playwright() as p:
        # Use a persistent context to save cookies/session
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        context = p.firefox.launch_persistent_context(
            USER_DATA_DIR,
            headless=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        page.set_default_timeout(15000)

        # Smart Start: Check if start_url is already in DB. If so, find the REAL start.
        with sqlite3.connect(DB_PATH) as conn:
            if conn.execute("SELECT 1 FROM chapters WHERE url = ?", (current_url,)).fetchone():
                print(f"Resuming from existing chapter: {current_url}")
                try:
                    # RoyalRoad often needs more time for CF checks or just layout
                    page.goto(current_url, wait_until="domcontentloaded", timeout=20000)
                    handle_ao3_gate(page)
                    
                    # Try to find next link
                    next_url = get_next_url(page, current_url, next_selector)
                    if not next_url:
                        # Retry with scroll and more wait
                        print("  [Debug] Next link not found immediately, scrolling and retrying...")
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(3)
                        next_url = get_next_url(page, current_url, next_selector)
                    
                    if next_url:
                        current_url = next_url
                        print(f"  Starting crawl at: {current_url}")
                    else:
                        print(f"  [Info] Could not find a 'Next' link from {current_url}.")
                        save_diagnostic(page, "start_failure")
                        current_url = None
                except Exception as e:
                    print(f"Error initializing crawl: {e}")
                    save_diagnostic(page, "init_error")
                    current_url = None

        while current_url:
            # Check target chapter condition
            if target_chapter and current_total >= target_chapter:
                print(f"Reached target chapter {target_chapter}.")
                break

            # Smart AO3 handling: Force append view_adult=true
            if "archiveofourown.org" in current_url and "view_adult=true" not in current_url:
                base_part, *fragment = current_url.split("#")
                sep = "&" if "?" in base_part else "?"
                current_url = f"{base_part}{sep}view_adult=true"
                if fragment:
                    current_url += f"#{fragment[0]}"

            if current_url in visited_this_session:
                print(f"Loop detected at {current_url}. Stopping.")
                break
            visited_this_session.add(current_url)

            # Verification: is it already in DB?
            with sqlite3.connect(DB_PATH) as conn:
                if conn.execute("SELECT 1 FROM chapters WHERE url = ?", (current_url,)).fetchone():
                    print(f"Chapter already in DB: {current_url}. Skipping...")
                    try:
                        page.goto(current_url, wait_until="domcontentloaded", timeout=15000)
                        handle_ao3_gate(page)
                        current_url = get_next_url(page, current_url, next_selector)
                        continue
                    except:
                        break

            print(f"[{current_total + 1}/{target_chapter if target_chapter else '?'}] Fetching: {current_url}")
            try:
                # Retry logic for page navigation
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        page.goto(current_url, wait_until="domcontentloaded", timeout=15000)
                        break
                    except (Exception, PlaywrightTimeoutError) as e:
                        if attempt < max_retries - 1:
                            print(f"  [Warning] Navigation timeout, retrying ({attempt + 1}/{max_retries})...")
                            time.sleep(2)
                        else:
                            print(f"  [Warning] Final timeout on {current_url}, checking if content is visible anyway...")
                            break

                handle_ao3_gate(page)
                
                # Check for content selector
                try:
                    page.wait_for_selector(selector, timeout=10000)
                except Exception:
                    if handle_ao3_gate(page):
                        page.wait_for_selector(selector, timeout=10000)
                    else:
                        print(f"  [Error] Content selector '{selector}' not found.")
                        save_diagnostic(page, "fetch_failure")
                        raise Exception(f"Content selector not found.")
                
                page_title = page.title()
                raw_content = page.locator(selector).first.inner_html()
                pristine_html = clean_html_content(raw_content)
                
                # Preview for the first new chapter of the session
                if new_chapters_count < 1:
                    text_preview = BeautifulSoup(pristine_html, "html.parser").get_text().strip()
                    print("\n" + "="*50)
                    print(f"PREVIEW: {page_title}")
                    print("-" * 50)
                    print(text_preview[:400] + "...")
                    print("="*50)
                    confirm = input(f"\nDoes preview look correct? (y/n): ").strip().lower()
                    if confirm != 'y':
                        print("Aborting.")
                        break

                max_order += 1
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute(
                        "INSERT INTO chapters (book_id, url, title, html_content, chapter_order) VALUES (?, ?, ?, ?, ?)",
                        (book_id, current_url, page_title, pristine_html, max_order)
                    )
                
                new_chapters_count += 1
                current_total += 1
                
                # Find the NEXT url
                next_url = get_next_url(page, current_url, next_selector)
                if not next_url:
                    time.sleep(3)
                    next_url = get_next_url(page, current_url, next_selector)
                
                if next_url:
                    current_url = next_url
                else:
                    print(f"  [Info] No Next Link found. Reached end of content.")
                    current_url = None
                    
                time.sleep(1) # Modest pacing
                
            except Exception as e:
                print(f"Error parsing {current_url}: {e}")
                break
        
        context.close()
    return new_chapters_count

def compile_epub(book_id, book_title):
    """Generates an EPUB from stored chapters."""
    print(f"Compiling EPUB for '{book_title}'...")
    epub_filename = os.path.join(BASE_DIR, f"{book_title.replace(' ', '_')}.epub")
    
    book = epub.EpubBook()
    book.set_title(book_title)
    book.set_language("en")
    book.add_author("Crawler Pipeline")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT title, html_content, chapter_order FROM chapters WHERE book_id = ? ORDER BY chapter_order ASC",
            (book_id,)
        )
        rows = cursor.fetchall()

    if not rows:
        print("No chapters found to compile.")
        return None

    chapters = []
    for title, html_content, order in rows:
        filename = f"chap_{order}.xhtml"
        chapter = epub.EpubHtml(title=title, file_name=filename, lang="en")
        chapter.content = f"<h1>{title}</h1>{html_content}"
        book.add_item(chapter)
        chapters.append(chapter)

    book.toc = tuple(chapters)
    book.spine = ["nav"] + chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    if os.path.exists(epub_filename):
        os.remove(epub_filename)
    
    epub.write_epub(epub_filename, book)
    print(f"EPUB created: {epub_filename}")
    return epub_filename

def main():
    init_db()
    print("=== Multi-Chapter Novel Scraper & Digest ===")
    
    # List existing books
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT id, title FROM books")
        existing_books = cursor.fetchall()

    book_id = None
    if existing_books:
        print("\nExisting Books:")
        for idx, (bid, title) in enumerate(existing_books, 1):
            print(f"{idx}. {title}")
        print(f"{len(existing_books) + 1}. [Add New Book]")
        
        choice = input("\nSelect a book or add new (number): ").strip()
        if choice.isdigit():
            choice_idx = int(choice)
            if 1 <= choice_idx <= len(existing_books):
                book_id, book_title = existing_books[choice_idx - 1]
            elif choice_idx == len(existing_books) + 1:
                book_id = None
    
    if not book_id:
        book_title = input("Enter new Book Title: ").strip()
        start_url = input("Enter the STARTING chapter URL: ").strip()
        
        # Try to suggest selectors from existing book on same domain
        selector = None
        next_selector = None
        parsed = urlparse(start_url)
        domain = parsed.netloc
        with sqlite3.connect(DB_PATH) as conn:
            match = conn.execute(
                "SELECT title, selector, next_selector FROM books WHERE start_url LIKE ? LIMIT 1",
                (f"%{domain}%",)
            ).fetchone()
        
        if match:
            existing_title, suggested_selector, suggested_next = match
            print(f"\nFound existing book '{existing_title}' from the same site.")
            print(f"  Suggested content selector: {suggested_selector}")
            print(f"  Suggested next selector:    {suggested_next if suggested_next else '[Auto-Detect]'}")
            if input("Use these selectors? (Y/n): ").strip().lower() != 'n':
                print("  Testing selector on the new URL...")
                try:
                    with sync_playwright() as p:
                        ctx = p.firefox.launch_persistent_context(
                            USER_DATA_DIR,
                            headless=True,
                            user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
                            viewport={'width': 1280, 'height': 800}
                        )
                        page = ctx.new_page()
                        page.set_default_timeout(15000)
                        page.goto(start_url, wait_until="domcontentloaded", timeout=20000)
                        handle_ao3_gate(page)
                        page.wait_for_selector(suggested_selector, timeout=10000)
                        raw = page.locator(suggested_selector).first.inner_html()
                        text = BeautifulSoup(raw, "html.parser").get_text().strip()
                        print("\n" + "=" * 50)
                        print("PREVIEW:")
                        print("-" * 50)
                        print(text[:400] + ("..." if len(text) > 400 else ""))
                        print("=" * 50)
                        ctx.close()
                    if input("Does this look correct? (Y/n): ").strip().lower() != 'n':
                        selector = suggested_selector
                        next_selector = suggested_next
                except Exception as e:
                    print(f"  Preview failed: {e}")
        
        if not selector:
            selector = input("Enter the CSS selector for the content block: ").strip()
            next_input = input("Enter CSS selector for 'Next' link (optional, press Enter for auto): ").strip()
            if next_input:
                next_selector = next_input
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                "INSERT INTO books (title, start_url, selector, next_selector) VALUES (?, ?, ?, ?)",
                (book_title, start_url, selector, next_selector)
            )
            book_id = cursor.lastrowid
    else:
        # For existing books, find the last URL to resume
        with sqlite3.connect(DB_PATH) as conn:
            res = conn.execute(
                "SELECT chapters.url, books.selector, books.next_selector, books.title "
                "FROM chapters JOIN books ON chapters.book_id = books.id "
                "WHERE book_id = ? ORDER BY chapter_order DESC LIMIT 1", 
                (book_id,)
            ).fetchone()
            if res:
                last_url, selector, next_selector, book_title = res
                start_url = last_url
            else:
                # Book exists but no chapters yet
                res = conn.execute("SELECT start_url, selector, next_selector, title FROM books WHERE id = ?", (book_id,)).fetchone()
                start_url, selector, next_selector, book_title = res
        
        print(f"\nCurrent Selectors for '{book_title}':")
        print(f"  Content: {selector}")
        print(f"  Next:    {next_selector if next_selector else '[Auto-Detect]'}")
        
        change = input("\nUpdate selectors? (y/N): ").strip().lower()
        if change == 'y':
            new_selector = input(f"Enter new content selector (Enter to keep '{selector}'): ").strip()
            if new_selector: selector = new_selector
            
            new_next = input(f"Enter new Next selector (Enter to keep '{next_selector}'): ").strip()
            if new_next: next_selector = new_next
            
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("UPDATE books SET selector = ?, next_selector = ? WHERE id = ?", (selector, next_selector, book_id))
                print("Selectors updated.")

    # Show current chapter count
    with sqlite3.connect(DB_PATH) as conn:
        count = conn.execute("SELECT COUNT(*) FROM chapters WHERE book_id = ?", (book_id,)).fetchone()[0]
        print(f"\nCurrent chapter count: {count}")

    # Reference link to check what chapter you're on
    if count > 0:
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT url FROM chapters WHERE book_id = ? ORDER BY chapter_order DESC LIMIT 1",
                (book_id,)
            ).fetchone()
            if row:
                print(f"  Last chapter: {row[0]}")
    else:
        print(f"  Start URL: {start_url}")

    target_chapter = input("Fetch until which chapter number? (Press Enter for 10 more): ").strip()
    if target_chapter.isdigit():
        target_chapter = int(target_chapter)
    else:
        target_chapter = count + 10
    
    new_count = scrape_incremental(book_id, start_url, selector, next_selector, target_chapter)
    
    if new_count > 0:
        epub_path = compile_epub(book_id, book_title)
        if epub_path:
            sync_with_calibre(book_title, epub_path)
    else:
        print("No new chapters fetched. EPUB remains unchanged.")

if __name__ == "__main__":
    main()
