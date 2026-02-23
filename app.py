from __future__ import annotations

from datetime import datetime
import io
import random
import zipfile

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
        variations = int(request.form.get("variations", "1"))
        variations = max(1, min(12, variations))

        seed_raw = request.form.get("seed", "")
        seed = int(seed_raw) if seed_raw.strip() else None

        chords = parse_progression(progression_text)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        outputs: list[tuple[str, bytes]] = []

        for index in range(variations):
            if requested_style == "random":
                style = random.choice(list(STYLES.keys()))
            else:
                style = requested_style

            current_seed = (seed + index) if seed is not None else random.randint(1, 1_000_000_000)
            arrangement = generate_arrangement(
                chords=chords,
                style=style,
                complexity=complexity,
                beats_per_chord=beats_per_chord,
                tempo=tempo,
                seed=current_seed,
            )
            midi_bytes = arrangement_to_midi(arrangement, tempo=tempo)
            outputs.append((f"voicings_{style}_{index + 1:02d}.mid", midi_bytes))

        if len(outputs) == 1:
            filename, midi_bytes = outputs[0]
            return send_file(
                io.BytesIO(midi_bytes),
                mimetype="audio/midi",
                as_attachment=True,
                download_name=filename,
            )

        archive_name = f"voicings_batch_{timestamp}.zip"
        archive_buffer = io.BytesIO()
        with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for filename, payload in outputs:
                archive.writestr(filename, payload)
        archive_buffer.seek(0)

        return send_file(
            archive_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=archive_name,
        )
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
