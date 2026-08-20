#!/bin/bash

CACHE_DIR="/tmp/conky_xkcd"
mkdir -p "$CACHE_DIR"

CURRENT=$(cat "$CACHE_DIR/current" 2>/dev/null || echo "0")
MAX=3286

if [ "$CURRENT" -eq 0 ]; then
	NUM=$((RANDOM % MAX + 1))
else
	NUM=$((RANDOM % MAX + 1))
	while [ "$NUM" -eq "$CURRENT" ]; do
		NUM=$((RANDOM % MAX + 1))
	done
fi

DATA=$(curl -sf "https://xkcd.com/$NUM/info.0.json")

if [ $? -eq 0 ]; then
	echo "$NUM" > "$CACHE_DIR/current"

	TITLE=$(echo "$DATA" | jq -r '.title')
	ALT=$(echo "$DATA" | jq -r '.alt')
	IMG_URL=$(echo "$DATA" | jq -r '.img')

	curl -sf -o "$CACHE_DIR/comic.png" "$IMG_URL"

	python3 -c "
from PIL import Image
img = Image.open('$CACHE_DIR/comic.png').convert('RGB')
img.save('$CACHE_DIR/comic_rgb.png')
" 2>/dev/null || cp "$CACHE_DIR/comic.png" "$CACHE_DIR/comic_rgb.png"

	echo "$TITLE" > "$CACHE_DIR/meta.txt"
	echo "$ALT" >> "$CACHE_DIR/meta.txt"

	echo "img $CACHE_DIR/comic_rgb.png"
	echo "title $TITLE"
	echo "alt $ALT"
else
	echo "img none"
	echo "title XKCD #$NUM"
	echo "alt failed to load"
fi
