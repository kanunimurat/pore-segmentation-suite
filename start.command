#!/bin/bash
# Pore Segmentation Suite — launcher (macOS)
# English-named entry point; runs the Turkish-named launcher "Başlat.command".
# Double-click → Terminal opens → Streamlit starts → the browser opens.
cd "$(dirname "$0")" || exit 1
for f in B*lat.command; do
    [ -f "$f" ] && exec /bin/bash "$f"
done
echo "Başlat.command not found in $(pwd)."
read -p "Press Enter to close..."
exit 1
