#!/bin/bash

python3 ~/github/scripts/scripts/rofi/smart_launcher.py |
	rofi -dmenu -i -p "Launch" -matching fuzzy -sort -sorting-method fzf -allow-custom |
	python3 ~/github/scripts/scripts/rofi/smart_launcher.py --dispatch
