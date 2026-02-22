from __future__ import annotations

from datetime import datetime
import io
import random

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from music_generator.midi_export import arrangement_to_midi
from music_generator.theory import BUILTIN_PROGRESSIONS, parse_progression
from music_generator.voicings import STYLES, generate_arrangement

app = Flask(__name__)
app.secret_key = "change-me-in-production"


@app.get("/")
def index():
    return render_template(
        "index.html",
        styles=STYLES,
        samples=BUILTIN_PROGRESSIONS,
    )


@app.post("/generate")
def generate():
    progression_text = request.form.get("progression", "")
    requested_style = request.form.get("style", "jazz")

    try:
        tempo = int(request.form.get("tempo", "98"))
        tempo = max(40, min(220, tempo))

        complexity = float(request.form.get("complexity", "65")) / 100.0
        complexity = max(0.0, min(1.0, complexity))

        beats_per_chord = float(request.form.get("beats_per_chord", "4"))
        beats_per_chord = 2.0 if beats_per_chord <= 2 else 4.0

        seed_raw = request.form.get("seed", "")
        seed = int(seed_raw) if seed_raw.strip() else None

        chords = parse_progression(progression_text)

        if requested_style == "random":
            style = random.choice(list(STYLES.keys()))
        else:
            style = requested_style

        arrangement = generate_arrangement(
            chords=chords,
            style=style,
            complexity=complexity,
            beats_per_chord=beats_per_chord,
            tempo=tempo,
            seed=seed,
        )
        midi_bytes = arrangement_to_midi(arrangement, tempo=tempo)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"voicings_{style}_{timestamp}.mid"

        return send_file(
            io.BytesIO(midi_bytes),
            mimetype="audio/midi",
            as_attachment=True,
            download_name=filename,
        )
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
