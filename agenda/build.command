#!/bin/bash
# Double-cliquez ce fichier dans le Finder pour generer le pack complet.
cd "$(dirname "$0")" || exit 1
echo "→ Verification de reportlab…"
python3 -c "import reportlab" 2>/dev/null || python3 -m pip install --user reportlab || exit 1
echo "→ Generation…"
python3 generate.py --lang both --week-start both --layout both "$@" || exit 1
open export 2>/dev/null
echo
echo "Termine. Appuyez sur une touche pour fermer."
read -r -n 1
