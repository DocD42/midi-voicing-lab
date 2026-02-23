from __future__ import annotations

from dataclasses import dataclass
import random

from .theory import (
    ChordSymbol,
    chord_tone_intervals,
    degree_to_semitone,
    is_dominant_quality,
    is_minor_quality,
    quality_bucket,
)


@dataclass(frozen=True)
class StyleProfile:
    name: str
    note_count_min: int
    note_count_max: int
    register_low: int
    register_high: int
    base_velocity: int
    hit_pattern: list[tuple[float, float, float]]
    default_tensions: dict[str, tuple[str, ...]]
    modal_colors: tuple[str, ...]


@dataclass(frozen=True)
class VoicedChord:
    chord: ChordSymbol
    style: str
    start_beat: float
    duration: float
    notes: list[int]
    left_hand: list[int]
    right_hand: list[int]
    velocity: int


@dataclass(frozen=True)
class Arrangement:
    style: str
    events: list[VoicedChord]
    total_beats: float


STYLES: dict[str, StyleProfile] = {
    "jazz": StyleProfile(
        name="Jazz",
        note_count_min=4,
        note_count_max=5,
        register_low=47,
        register_high=82,
        base_velocity=82,
        hit_pattern=[(0.0, 2.25, 1.0), (2.75, 1.0, 0.92)],
        default_tensions={
            "major": ("9", "13"),
            "minor": ("9", "11"),
            "dominant": ("13", "b9", "#11"),
        },
        modal_colors=("dorian", "lydian", "mixolydian", "aeolian"),
    ),
    "soul": StyleProfile(
        name="Soul",
        note_count_min=4,
        note_count_max=5,
        register_low=45,
        register_high=80,
        base_velocity=88,
        hit_pattern=[(0.0, 1.75, 1.0), (2.0, 1.5, 0.9), (3.75, 0.25, 0.85)],
        default_tensions={
            "major": ("6", "9"),
            "minor": ("9", "11"),
            "dominant": ("9", "13"),
        },
        modal_colors=("dorian", "mixolydian", "ionian"),
    ),
    "pop": StyleProfile(
        name="Pop",
        note_count_min=3,
        note_count_max=4,
        register_low=48,
        register_high=84,
        base_velocity=92,
        hit_pattern=[(0.0, 4.0, 1.0)],
        default_tensions={
            "major": ("9",),
            "minor": ("9",),
            "dominant": ("9",),
        },
        modal_colors=("ionian", "mixolydian", "aeolian"),
    ),
    "indie": StyleProfile(
        name="Indie",
        note_count_min=4,
        note_count_max=5,
        register_low=50,
        register_high=86,
        base_velocity=84,
        hit_pattern=[(0.0, 2.0, 0.98), (2.0, 2.0, 0.96)],
        default_tensions={
            "major": ("9", "#11"),
            "minor": ("9", "11"),
            "dominant": ("9", "13"),
        },
        modal_colors=("dorian", "lydian", "aeolian"),
    ),
    "alternative-rock": StyleProfile(
        name="Alternative Rock",
        note_count_min=3,
        note_count_max=4,
        register_low=43,
        register_high=79,
        base_velocity=97,
        hit_pattern=[(0.0, 1.75, 1.0), (2.0, 1.75, 0.95)],
        default_tensions={
            "major": ("9",),
            "minor": ("11",),
            "dominant": ("9", "b13"),
        },
        modal_colors=("aeolian", "dorian", "mixolydian"),
    ),
}


def generate_arrangement(
    chords: list[ChordSymbol],
    style: str,
    complexity: float,
    beats_per_chord: float,
    tempo: int,
    seed: int | None = None,
    humanize: bool = False,
    humanize_amount: float = 0.0,
) -> Arrangement:
    if style not in STYLES:
        raise ValueError(f"Style nicht gefunden: {style}")

    profile = STYLES[style]
    complexity = min(max(complexity, 0.0), 1.0)
    humanize_amount = min(max(humanize_amount, 0.0), 1.0)
    rng = random.Random(seed)

    cadence_roles = analyze_cadences(chords)
    mode_track = [rng.choice(profile.modal_colors) for _ in chords]

    events: list[VoicedChord] = []
    current_beat = 0.0
    previous_voice: list[int] | None = None

    for idx, chord in enumerate(chords):
        role = cadence_roles[idx]
        pitch_classes = build_pitch_class_palette(chord, profile, complexity, mode_track[idx], role, rng)
        voice = build_voice(chord, pitch_classes, previous_voice, profile, complexity, role, rng)
        previous_voice = voice
        left_hand, right_hand = split_voice_hands(chord, voice, complexity)

        for offset, duration, velocity_scale in profile.hit_pattern:
            if offset >= beats_per_chord:
                continue
            clipped_duration = min(duration, beats_per_chord - offset)
            velocity = int(profile.base_velocity * velocity_scale)
            events.append(
                VoicedChord(
                    chord=chord,
                    style=style,
                    start_beat=current_beat + offset,
                    duration=max(0.1, clipped_duration),
                    notes=voice,
                    left_hand=left_hand,
                    right_hand=right_hand,
                    velocity=max(45, min(118, velocity)),
                )
            )

        current_beat += beats_per_chord

    if humanize and humanize_amount > 0:
        humanize_seed = (seed if seed is not None else rng.randint(1, 1_000_000_000)) + 7919
        events = apply_humanize(
            events=events,
            total_beats=current_beat,
            amount=humanize_amount,
            rng=random.Random(humanize_seed),
        )

    return Arrangement(style=style, events=events, total_beats=current_beat)


def analyze_cadences(chords: list[ChordSymbol]) -> list[str]:
    roles = ["neutral" for _ in chords]

    for i in range(len(chords) - 2):
        c1, c2, c3 = chords[i], chords[i + 1], chords[i + 2]
        ii_to_v = (c2.root_pc - c1.root_pc) % 12 == 5
        v_to_i = (c3.root_pc - c2.root_pc) % 12 == 5

        if ii_to_v and v_to_i and is_minor_quality(c1.quality) and is_dominant_quality(c2.quality):
            roles[i] = "ii"
            roles[i + 1] = "V"
            roles[i + 2] = "I"

    for i in range(len(chords) - 1):
        if roles[i] != "neutral":
            continue
        c1, c2 = chords[i], chords[i + 1]
        if is_dominant_quality(c1.quality) and (c2.root_pc - c1.root_pc) % 12 == 5:
            roles[i] = "V"
            if roles[i + 1] == "neutral":
                roles[i + 1] = "I"

    return roles


def build_pitch_class_palette(
    chord: ChordSymbol,
    profile: StyleProfile,
    complexity: float,
    mode_color: str,
    role: str,
    rng: random.Random,
) -> list[int]:
    root = chord.root_pc
    pcs = {(root + interval) % 12 for interval in chord_tone_intervals(chord.quality)}
    bucket = quality_bucket(chord.quality)

    default_tensions = list(profile.default_tensions.get(bucket, ()))
    if complexity < 0.4:
        default_tensions = default_tensions[:1]

    extra = list(chord.extensions) + list(chord.alterations)

    if role == "ii":
        extra += ["9", "11"]
    elif role == "V":
        extra += ["b9", "13"]
        if complexity > 0.6:
            extra += ["#11"]
    elif role == "I":
        extra += ["9", "13"]

    if mode_color == "lydian" and bucket == "major":
        extra.append("#11")
    if mode_color == "dorian" and bucket == "minor":
        extra.append("13")
    if mode_color == "aeolian" and bucket == "minor":
        extra.append("b13")

    all_tensions = default_tensions + extra
    for tension in all_tensions:
        try:
            pcs.add((root + degree_to_semitone(tension)) % 12)
        except ValueError:
            continue

    if complexity > 0.65 and bucket == "dominant" and rng.random() < 0.6:
        altered = rng.choice(["b9", "#9", "#11", "b13"])
        pcs.add((root + degree_to_semitone(altered)) % 12)

    return sorted(pcs)


def build_voice(
    chord: ChordSymbol,
    pitch_classes: list[int],
    previous_voice: list[int] | None,
    profile: StyleProfile,
    complexity: float,
    role: str,
    rng: random.Random,
) -> list[int]:
    note_count = int(round(profile.note_count_min + (profile.note_count_max - profile.note_count_min) * complexity))
    note_count = max(profile.note_count_min, min(profile.note_count_max, note_count))

    required = required_pitch_classes(chord)
    preferred = prioritize_pitch_classes(chord, pitch_classes, role, complexity, rng)

    chosen: list[int] = []
    for pc in required + preferred:
        if pc in chosen:
            continue
        chosen.append(pc)
        if len(chosen) >= note_count:
            break

    while len(chosen) < note_count:
        chosen.append(chosen[-1])

    if previous_voice:
        notes = [
            nearest_note_for_pc(
                pc=pc,
                anchor=previous_voice[min(i, len(previous_voice) - 1)],
                low=profile.register_low,
                high=profile.register_high,
            )
            for i, pc in enumerate(chosen)
        ]
    else:
        base = profile.register_low + 6
        notes = [fit_note_to_range(base + (i * 5), profile.register_low, profile.register_high, pc) for i, pc in enumerate(chosen)]

    notes.sort()

    for i in range(1, len(notes)):
        while notes[i] - notes[i - 1] < 3:
            notes[i] += 12

    for i in range(len(notes)):
        notes[i] = min(notes[i], profile.register_high)
        notes[i] = max(notes[i], profile.register_low)

    if role == "V" and complexity > 0.5:
        notes[-1] = min(profile.register_high, notes[-1] + 1)
    if role == "I" and complexity > 0.5:
        notes[-1] = max(profile.register_low, notes[-1] - 1)

    return sorted(set(notes)) if complexity < 0.2 else notes


def required_pitch_classes(chord: ChordSymbol) -> list[int]:
    root = chord.root_pc
    intervals = chord_tone_intervals(chord.quality)

    req = [root]
    if len(intervals) >= 2:
        req.append((root + intervals[1]) % 12)
    if len(intervals) >= 4:
        req.append((root + intervals[3]) % 12)
    return req


def prioritize_pitch_classes(
    chord: ChordSymbol,
    pitch_classes: list[int],
    role: str,
    complexity: float,
    rng: random.Random,
) -> list[int]:
    root = chord.root_pc

    def ranking(pc: int) -> tuple[int, int]:
        distance = (pc - root) % 12
        role_weight = {
            "ii": {2: 0, 5: 1, 9: 2},
            "V": {10: 0, 1: 1, 6: 2, 8: 3},
            "I": {4: 0, 11: 1, 2: 2, 9: 3},
            "neutral": {4: 0, 7: 1, 2: 2},
        }
        priority = role_weight.get(role, role_weight["neutral"]).get(distance, 10)
        return priority, distance

    ordered = sorted(pitch_classes, key=ranking)
    if complexity > 0.75:
        tail = ordered[2:]
        rng.shuffle(tail)
        ordered = ordered[:2] + tail
    return ordered


def nearest_note_for_pc(pc: int, anchor: int, low: int, high: int) -> int:
    candidates = []
    for octave in range(-3, 4):
        note = pc + 12 * (((anchor // 12) + octave))
        if low <= note <= high:
            candidates.append(note)

    if not candidates:
        return fit_note_to_range(anchor, low, high, pc)

    return min(candidates, key=lambda n: abs(n - anchor))


def fit_note_to_range(note: int, low: int, high: int, pc: int) -> int:
    candidate = note
    while candidate < low:
        candidate += 12
    while candidate > high:
        candidate -= 12

    shift_up = (pc - candidate) % 12
    shift_down = shift_up - 12

    up_note = candidate + shift_up
    down_note = candidate + shift_down

    options = [n for n in (up_note, down_note) if low <= n <= high]
    if not options:
        return max(low, min(high, candidate))
    return min(options, key=lambda n: abs(n - note))


def split_voice_hands(chord: ChordSymbol, voice: list[int], complexity: float) -> tuple[list[int], list[int]]:
    sorted_voice = sorted(voice)
    root_pc = chord.bass_pc if chord.bass_pc is not None else chord.root_pc

    left_bass = fit_note_to_range(40, 33, 52, root_pc)
    guide_pcs = required_pitch_classes(chord)[1:]
    left: list[int] = [left_bass]

    if complexity >= 0.35 and guide_pcs:
        left_guide = fit_note_to_range(50, 41, 60, guide_pcs[0])
        while left_guide - left_bass < 4:
            left_guide += 12
        while left_guide > 60:
            left_guide -= 12
        left.append(max(36, min(60, left_guide)))

    right: list[int] = []
    for note in sorted_voice:
        candidate = note
        while candidate < 58:
            candidate += 12
        while candidate > 92:
            candidate -= 12
        right.append(max(55, min(92, candidate)))

    right = sorted(set(right))

    if not right:
        root_high = fit_note_to_range(64, 58, 88, root_pc)
        right = [root_high, min(92, root_high + 7)]

    if complexity >= 0.55 and len(right) < 3 and len(sorted_voice) >= 2:
        extra = right[-1] + 5
        if extra <= 92:
            right.append(extra)
            right = sorted(set(right))

    lowest_right = right[0]
    adjusted_left: list[int] = []
    for note in sorted(left):
        candidate = note
        while candidate >= lowest_right - 3:
            candidate -= 12
        adjusted_left.append(max(28, candidate))

    return sorted(set(adjusted_left)), right


def apply_humanize(
    events: list[VoicedChord],
    total_beats: float,
    amount: float,
    rng: random.Random,
) -> list[VoicedChord]:
    max_timing_shift = 0.01 + (0.05 * amount)
    max_duration_shift = max_timing_shift * 0.7
    max_velocity_shift = int(round(2 + (12 * amount)))

    humanized: list[VoicedChord] = []
    for event in events:
        start_shift = rng.uniform(-max_timing_shift, max_timing_shift)
        duration_shift = rng.uniform(-max_duration_shift, max_duration_shift)
        velocity_shift = rng.randint(-max_velocity_shift, max_velocity_shift)

        new_start = event.start_beat + start_shift
        new_start = max(0.0, min(max(0.0, total_beats - 0.1), new_start))

        new_duration = max(0.12, event.duration + duration_shift)
        max_duration = max(0.12, total_beats - new_start)
        new_duration = min(max_duration, new_duration)

        new_velocity = max(38, min(120, event.velocity + velocity_shift))

        humanized.append(
            VoicedChord(
                chord=event.chord,
                style=event.style,
                start_beat=new_start,
                duration=new_duration,
                notes=event.notes,
                left_hand=event.left_hand,
                right_hand=event.right_hand,
                velocity=new_velocity,
            )
        )

    return sorted(humanized, key=lambda event: event.start_beat)
