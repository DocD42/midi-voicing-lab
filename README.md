# MIDI Voicing Lab

Web-App, die aus Akkordfolgen Piano-Voicings erzeugt und als MIDI-Datei exportiert.

## Features

- Input: freie Akkordfolge (`Dm7 G7 Cmaj7 A7` usw.)
- Styles: `Jazz`, `Soul`, `Pop`, `Indie`, `Alternative Rock`, plus `Random`
- Zufallsknopf für Style, Beispiel-Progression, Tempo und Seed
- Spannungsaufbau durch:
  - 2-5-1-Erkennung und kadenzabhängige Tensions
  - modale Farbwechsel (z. B. Lydian/Dorian/Aeolian)
  - voice-led Voicings statt statischer Blockakkorde
- Output: Standard MIDI (Type 1), direkt in Logic Pro importierbar

## Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Dann im Browser öffnen: `http://127.0.0.1:5000`

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Neue GitHub Repo verbinden

Wenn du in diesem Ordner eine neue Remote-Repo erstellen willst:

```bash
git add .
git commit -m "Initial commit: MIDI voicing generator"
git branch -M main
gh repo create midi-voicing-lab --public --source=. --remote=origin --push
```

Ohne `gh`:

1. Repo auf GitHub im Browser erstellen.
2. Dann lokal:

```bash
git branch -M main
git remote add origin <DEIN_GITHUB_REPO_URL>
git push -u origin main
```

## Nächste Ausbaustufen

- Drum/Groove MIDI Track als zweite Spur
- Humanize (Timing/Velocity)
- Separate Left-/Right-Hand-Distribution
- Export von mehreren Variationen in einem Durchlauf
