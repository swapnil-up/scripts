#!/bin/bash
set -euo pipefail

output_file="output.txt"

if ! command -v tesseract &>/dev/null; then
	echo "Error: tesseract is not installed."
	exit 1
fi

shopt -s nullglob
files=(*.jpg *.jpeg *.png *.tiff)
shopt -u nullglob

if [ ${#files[@]} -eq 0 ]; then
	echo "No image files found (*.jpg, *.jpeg, *.png, *.tiff)"
	exit 0
fi

>"$output_file"

total=${#files[@]}
current=1

for x in "${files[@]}"; do
	echo "Processing file $current of $total: $x"
	tesseract "$x" - >>"$output_file"
	echo "Done $current of $total"
	current=$((current + 1))
done

echo "OCR conversion complete. Text saved in $output_file"
