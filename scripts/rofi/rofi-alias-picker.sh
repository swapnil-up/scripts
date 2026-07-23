#!/bin/bash
# rofi-alias-picker.sh — Pick and run a curated alias via rofi

entries=(
  "bootstrap:~/github/scripts/setup/bootstrap.sh:run full bootstrap"
  "review:python3 ~/github/obsidian-vault/scripts/incremental.py:obsidian incremental review"
  "whisper:~/github/scripts/scripts/utils/whisper.sh:speech-to-text (hold to record)"
  "piper:~/github/scripts/scripts/utils/piper.sh:text-to-speech (clipboard)"
  "crawler:~/github/scripts/scripts/python/crawler.py:web crawler"
  "k:systemctl --user restart kanata:restart kanata"
  "docker-clean:docker container prune -f; docker image prune -f; docker network prune -f; docker volume prune -f:prune docker"
  "clickpaste:sleep 3; xdotool type \"\$(xclip -o -selection clipboard)\":type clipboard contents"
)

menu=$(printf '%s\n' "${entries[@]}" | awk -F: '{printf "%-20s → %s\n", $1, $3}')

selected=$(echo "$menu" | rofi -dmenu -i -p "Alias")

[ -z "$selected" ] && exit 0

name=$(echo "$selected" | awk '{print $1}')
cmd=$(printf '%s\n' "${entries[@]}" | awk -F: -v n="$name" '$1 == n {print $2; exit}')

[ -z "$cmd" ] && exit 0

alacritty --title "Alias" -e bash -c "$cmd; echo; read -p 'Press Enter to close.'"
