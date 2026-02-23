from __future__ import annotations

from datetime import datetime
import io
import random
import zipfile

from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, url_for

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


def parse_form_settings() -> dict:
    progression_text = request.form.get("progression", "")
    requested_style = request.form.get("style", "jazz")

    tempo = int(request.form.get("tempo", "98"))
    tempo = max(40, min(220, tempo))

    complexity = float(request.form.get("complexity", "65")) / 100.0
    complexity = max(0.0, min(1.0, complexity))

    beats_per_chord = float(request.form.get("beats_per_chord", "4"))
    beats_per_chord = 2.0 if beats_per_chord <= 2 else 4.0

    variations = int(request.form.get("variations", "1"))
    variations = max(1, min(12, variations))

    humanize = request.form.get("humanize") == "on"
    humanize_amount = float(request.form.get("humanize_amount", "30")) / 100.0
    humanize_amount = max(0.0, min(1.0, humanize_amount))

    seed_raw = request.form.get("seed", "")
    seed = int(seed_raw) if seed_raw.strip() else None

    chords = parse_progression(progression_text)
    if requested_style != "random" and requested_style not in STYLES:
        raise ValueError(f"Style nicht gefunden: {requested_style}")

    return {
        "requested_style": requested_style,
        "tempo": tempo,
        "complexity": complexity,
        "beats_per_chord": beats_per_chord,
        "variations": variations,
        "humanize": humanize,
        "humanize_amount": humanize_amount,
        "seed": seed,
        "chords": chords,
    }


def resolve_style(requested_style: str, style_rng: random.Random) -> str:
    if requested_style == "random":
        return style_rng.choice(list(STYLES.keys()))
    return requested_style


@app.post("/generate")
def generate():
    try:
        settings = parse_form_settings()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        outputs: list[tuple[str, bytes]] = []

        base_seed = settings["seed"] if settings["seed"] is not None else random.randint(1, 1_000_000_000)
        style_rng = random.Random(base_seed + 17)

        for index in range(settings["variations"]):
            style = resolve_style(settings["requested_style"], style_rng)
            current_seed = base_seed + index
            arrangement = generate_arrangement(
                chords=settings["chords"],
                style=style,
                complexity=settings["complexity"],
                beats_per_chord=settings["beats_per_chord"],
                tempo=settings["tempo"],
                seed=current_seed,
                humanize=settings["humanize"],
                humanize_amount=settings["humanize_amount"],
            )
            midi_bytes = arrangement_to_midi(arrangement, tempo=settings["tempo"])
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


@app.post("/preview")
def preview():
    try:
        settings = parse_form_settings()
        base_seed = settings["seed"] if settings["seed"] is not None else random.randint(1, 1_000_000_000)
        style = resolve_style(settings["requested_style"], random.Random(base_seed + 17))

        arrangement = generate_arrangement(
            chords=settings["chords"],
            style=style,
            complexity=settings["complexity"],
            beats_per_chord=settings["beats_per_chord"],
            tempo=settings["tempo"],
            seed=base_seed,
            humanize=settings["humanize"],
            humanize_amount=settings["humanize_amount"],
        )
        serialized_events = [
            {
                "start_beat": event.start_beat,
                "duration": event.duration,
                "velocity": event.velocity,
                "left_hand": event.left_hand,
                "right_hand": event.right_hand,
            }
            for event in arrangement.events
        ]

        return jsonify(
            {
                "seed": base_seed,
                "style": arrangement.style,
                "tempo": settings["tempo"],
                "events": serialized_events,
                "total_beats": arrangement.total_beats,
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True)
