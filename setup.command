#!/bin/bash
# Pore Segmentation Suite — first-time setup (macOS)
# English-named entry point; runs the Turkish-named setup script "İlk Kurulum.command".
# Run once: installs the required Python libraries (and, optionally, SAM 2 / Cellpose).
cd "$(dirname "$0")" || exit 1
for f in *lk\ Kurulum.command; do
    [ -f "$f" ] && exec /bin/bash "$f"
done
echo "İlk Kurulum.command not found in $(pwd)."
read -p "Press Enter to close..."
exit 1
