from __future__ import annotations

import io

import mido

from .voicings import Arrangement


def arrangement_to_midi(arrangement: Arrangement, tempo: int) -> bytes:
    ticks_per_beat = 480
    midi = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)

    meta_track = mido.MidiTrack()
    midi.tracks.append(meta_track)
    meta_track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(tempo), time=0))
    meta_track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    meta_track.append(mido.MetaMessage("track_name", name=f"Voicings ({arrangement.style})", time=0))

    note_track = mido.MidiTrack()
    midi.tracks.append(note_track)

    timeline: list[tuple[int, int, mido.Message]] = []

    for event in arrangement.events:
        start_tick = int(round(event.start_beat * ticks_per_beat))
        end_tick = int(round((event.start_beat + event.duration) * ticks_per_beat))

        for note in event.notes:
            timeline.append(
                (
                    start_tick,
                    1,
                    mido.Message("note_on", note=note, velocity=event.velocity, channel=0, time=0),
                )
            )
            timeline.append(
                (
                    end_tick,
                    0,
                    mido.Message("note_off", note=note, velocity=0, channel=0, time=0),
                )
            )

    timeline.sort(key=lambda item: (item[0], item[1]))

    previous_tick = 0
    for tick, _, message in timeline:
        delta = tick - previous_tick
        message.time = max(0, delta)
        note_track.append(message)
        previous_tick = tick

    note_track.append(mido.MetaMessage("end_of_track", time=1))

    buffer = io.BytesIO()
    midi.save(file=buffer)
    return buffer.getvalue()
