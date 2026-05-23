import subprocess


def sync_with_calibre(book_title, epub_path):
    """Search Calibre library for book_title and update or add the EPUB."""
    print(f"Syncing '{book_title}' with Calibre library...")
    try:
        search_cmd = ["calibredb", "search", f"title:\"{book_title}\""]
        result = subprocess.run(search_cmd, capture_output=True, text=True)
        book_ids = result.stdout.strip()

        if book_ids and result.returncode == 0:
            book_id = book_ids.split(",")[0]
            print(f"Updating existing Calibre Book Entry ID: {book_id}")
            add_cmd = ["calibredb", "add_format", book_id, epub_path]
            subprocess.run(add_cmd, check=True)
        else:
            print(f"Adding '{book_title}' to Calibre as a brand new catalog item...")
            add_cmd = ["calibredb", "add", epub_path]
            subprocess.run(add_cmd, check=True)

        print("Calibre database successfully refreshed.")
    except FileNotFoundError:
        print("\n[Warning]: 'calibredb' command utility was not found in system PATH.")
        print("Compilation complete, but automated Calibre indexing skipped.")
    except subprocess.CalledProcessError as e:
        stderr_msg = e.stderr if e.stderr else str(e)
        if "Another calibre program" in stderr_msg:
            print("\n[Error]: Calibre database is locked because the Calibre desktop app is open.")
            print("Please close Calibre and run the script again, or update the book manually in Calibre.")
