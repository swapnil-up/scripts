#!/bin/bash

# Configuration: Update this path to your specific Obsidian vault location
OBSIDIAN_VAULT="${OBSIDIAN_VAULT:-$HOME/github/obsidian-vault}"
NUM_NOTES=3

# --- Key Fixes ---
# Use stat -c %Y to reliably get the modification time without printing the timestamp
# Use basename and sed to clean the output precisely.

/usr/bin/find "$OBSIDIAN_VAULT" -type f -name "*.md" -print0 |
	/usr/bin/xargs -0 /usr/bin/stat -c $'%Y\t%n' |
	/usr/bin/sort -nr |
	/usr/bin/head -"$NUM_NOTES" |
	/usr/bin/cut -f 2 |
	while read -r file; do
		/usr/bin/basename "$file" | /usr/bin/sed 's/\.md$//g' | /usr/bin/sed 's/^/- /'
	done
